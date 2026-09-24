"""
Fraud Policy Engine (Version 1.0)
Implements all actions, approval routing (auto, L1, L2), and rules R1 through R10.
"""

from typing import Dict, List, Any, Tuple


class FraudPolicy:
    # 1. Allowed actions
    VALID_ACTIONS = {
        "ALLOW_TRANSACTION",
        "DECLINE_TRANSACTION",
        "MONITOR_CARD",
        "MONITOR_CONNECTED_CARDS",
        "WARN_CUSTOMER",
        "VERIFY_WITH_CUSTOMER",
        "STEP_UP_AUTH",
        "BLOCK_CARD",
        "BLOCK_ALL_CARDS",
        "GENERATE_REPORT",
        "CREATE_CASE",
        "FILE_REPORT",
        "ESCALATE_TO_ANALYST",
        "CLOSE_NO_FRAUD"
    }

    # 2. Approval routes
    ROUTES = {"auto", "L1", "L2"}

    @staticmethod
    def get_approval_route(action: str, exposure_usd: float = 0.0) -> str:
        """
        Determines the policy-mandated approval route:
        - auto: agent executes directly
        - L1 (team lead): DECLINE_TRANSACTION; BLOCK_CARD when exposure <= $2,500
        - L2 (fraud manager): BLOCK_CARD when exposure > $2,500; BLOCK_ALL_CARDS always; FILE_REPORT always
        """
        if action == "DECLINE_TRANSACTION":
            return "L1"
        elif action == "BLOCK_CARD":
            return "L2" if exposure_usd > 2500.0 else "L1"
        elif action in {"BLOCK_ALL_CARDS", "FILE_REPORT"}:
            return "L2"
        else:
            # ALLOW_TRANSACTION, MONITOR_CARD, MONITOR_CONNECTED_CARDS, WARN_CUSTOMER,
            # VERIFY_WITH_CUSTOMER, STEP_UP_AUTH, GENERATE_REPORT, CREATE_CASE,
            # ESCALATE_TO_ANALYST, CLOSE_NO_FRAUD
            return "auto"

    @classmethod
    def make_action(cls, action: str, reason: str, exposure_usd: float = 0.0) -> Dict[str, str]:
        """Creates a policy-compliant action item."""
        if action not in cls.VALID_ACTIONS:
            raise ValueError(f"Unknown policy action: {action}")
        route = cls.get_approval_route(action, exposure_usd)
        return {
            "action": action,
            "route": route,
            "reason": reason
        }

    @classmethod
    def evaluate_initial_actions(cls,
                                 fraud_prob: float,
                                 pattern: str,
                                 single_signal: bool,
                                 exposure_usd: float,
                                 has_testing_sequence: bool = False,
                                 is_shared_origin: bool = False,
                                 is_recurring_dispute: bool = False,
                                 is_customer_denial: bool = False) -> List[Dict[str, str]]:
        """
        Calculates initial next best actions before requested evidence arrives.
        Enforces Rules R1, R5, R6, R7, R8, R9.
        """
        actions = []

        # R7: Disputed recurring charge
        if is_recurring_dispute:
            actions.append(cls.make_action("CREATE_CASE", "R7: Customer dispute on matching recurring charge pattern"))
            actions.append(cls.make_action("VERIFY_WITH_CUSTOMER", "R7: Confirm recurring subscription with customer"))
            actions.append(cls.make_action("WARN_CUSTOMER", "R7: Provide recurring charge reminder without blocking card"))
            return actions

        # R5: Card testing sequence observed
        if has_testing_sequence:
            actions.append(cls.make_action("DECLINE_TRANSACTION", "R5: Testing sequence observed, decline pending authorization", exposure_usd))
            actions.append(cls.make_action("STEP_UP_AUTH", "R5: Require step-up authentication on card before further activity"))
            actions.append(cls.make_action("CREATE_CASE", "R5: Open case for card testing investigation"))
            if exposure_usd > 100.0:
                actions.append(cls.make_action("BLOCK_CARD", "R5: Large purchase over $100 cleared following test authorizations", exposure_usd))
            return actions

        # R6: Shared origin across multiple cards
        if is_shared_origin:
            actions.append(cls.make_action("CREATE_CASE", "R6: Multi-card compromise linked by shared device/origin"))
            actions.append(cls.make_action("FILE_REPORT", "R6: Coordinated shared origin activity requires regulatory SAR", exposure_usd))
            actions.append(cls.make_action("MONITOR_CONNECTED_CARDS", "R6: Place all connected cards sharing the origin under monitoring"))
            if fraud_prob >= 0.70:
                actions.append(cls.make_action("DECLINE_TRANSACTION", "R6: Decline flagged transaction on compromised origin", exposure_usd))
            return actions

        # R1: Weak signal verification
        if single_signal and fraud_prob < 0.70:
            actions.append(cls.make_action("VERIFY_WITH_CUSTOMER", "R1: Probability below 0.70 on single signal; verify before blocking"))
            if fraud_prob >= 0.30:
                actions.append(cls.make_action("CREATE_CASE", "Policy 3a: Open internal case as fraud probability >= 0.30"))
            return actions

        # Customer report trigger (initial state before validation)
        if is_customer_denial:
            actions.append(cls.make_action("VERIFY_WITH_CUSTOMER", "R1: Customer report received, verify details and confirm card possession"))
            actions.append(cls.make_action("CREATE_CASE", "Policy 3a: Customer dispute received, create internal case"))
            return actions

        # High probability initial
        if fraud_prob >= 0.70:
            actions.append(cls.make_action("DECLINE_TRANSACTION", "Policy: High fraud probability on observed activity", exposure_usd))
            actions.append(cls.make_action("CREATE_CASE", "Policy 3a: Fraud probability >= 0.30"))
            if single_signal:
                actions.append(cls.make_action("VERIFY_WITH_CUSTOMER", "R1: Verify with customer to confirm compromise"))
            else:
                actions.append(cls.make_action("BLOCK_CARD", "Policy: Multi-signal confirmed unauthorized pattern", exposure_usd))
            return actions

        # Low probability / likely legitimate
        if fraud_prob <= 0.20:
            actions.append(cls.make_action("ALLOW_TRANSACTION", "Policy: Low risk assessed, normal cardholder behavior"))
            actions.append(cls.make_action("CLOSE_NO_FRAUD", "Policy: Activity cleared as legitimate"))
            return actions

        # Uncertain fallback
        actions.append(cls.make_action("MONITOR_CARD", "Policy: Monitor card activity for 72 hours"))
        if exposure_usd > 500.0:
            actions.append(cls.make_action("ESCALATE_TO_ANALYST", "R8: Uncertain verdict with exposure exceeding $500"))
        return actions

    @classmethod
    def evaluate_final_actions(cls,
                               fraud_prob: float,
                               verdict: str,
                               pattern: str,
                               exposure_usd: float,
                               assumed_customer_response: str,
                               is_shared_origin: bool = False,
                               connected_cards_count: int = 0) -> Tuple[List[Dict[str, str]], bool, str]:
        """
        Calculates final next best actions after evidence response.
        Enforces Rules R2, R3, R4, R6, R8, R9.
        Returns: (final_actions, file_sar, sar_reason)
        """
        actions = []
        file_sar = False
        sar_reason = ""
        resp_lower = assumed_customer_response.lower()

        # Syndicate or Customer denial (R2, R6, R9)
        if "syndicate" in resp_lower or "did not" in resp_lower or "denied" in resp_lower or "never made" in resp_lower or "unauthorized" in resp_lower or "stolen" in resp_lower:
            actions.append(cls.make_action("BLOCK_CARD", f"Policy: Confirmed unauthorized use; exposure ${exposure_usd:.2f}", exposure_usd))
            actions.append(cls.make_action("CREATE_CASE", "Policy 3a: Confirmed unauthorized activity; internal case created"))
            
            # Policy 3a / R2: File SAR if exposure > $1,000 OR shared device profile / ring OR coordinated/undocumented
            if exposure_usd > 1000.0 or is_shared_origin or pattern == "undocumented":
                file_sar = True
                sar_reason = "R2/R6/R9 & Policy 3a: Confirmed unauthorized use "
                if is_shared_origin or pattern == "undocumented":
                    sar_reason += "linked by shared device/origin to other cards"
                elif exposure_usd > 1000.0:
                    sar_reason += f"with exposure ${exposure_usd:.2f} exceeding $1,000 threshold"
                else:
                    sar_reason += "exhibiting coordinated undocumented pattern"
                    
                actions.append(cls.make_action("FILE_REPORT", sar_reason, exposure_usd))
                
            if is_shared_origin or connected_cards_count > 0 or pattern == "undocumented":
                actions.append(cls.make_action("MONITOR_CONNECTED_CARDS", "R6: Place all connected cards linked to shared origin under monitoring"))
                
            if pattern == "undocumented":
                actions.append(cls.make_action("ESCALATE_TO_ANALYST", "R9: Coordinated undocumented syndicate pattern escalated to fraud analyst"))
                
            return actions, file_sar, sar_reason

        # Customer confirmed legitimate (R3)
        if "customer confirmed" in resp_lower or "cardholder confirmed" in resp_lower or "made the purchase" in resp_lower or "authorized" in resp_lower or "biometric" in resp_lower or "subscription" in resp_lower:
            actions.append(cls.make_action("ALLOW_TRANSACTION", "R3: Customer confirmed transaction was authorized"))
            actions.append(cls.make_action("CLOSE_NO_FRAUD", "R3: Closed as legitimate following customer confirmation"))
            return actions, False, ""

        # No reply within 24 hours (R4)
        if "no reply" in resp_lower or "timeout" in resp_lower:
            actions.append(cls.make_action("MONITOR_CARD", "R4: No customer reply within 24 hours; raise monitoring sensitivity"))
            actions.append(cls.make_action("DECLINE_TRANSACTION", "R4: Decline pending authorization pending cardholder contact", exposure_usd))
            if exposure_usd > 500.0:
                actions.append(cls.make_action("ESCALATE_TO_ANALYST", "R4: Exposure exceeds $500 with no customer reply"))
            return actions, False, ""

        # If no explicit customer denial but high fraud probability
        if verdict == "fraud":
            actions.append(cls.make_action("BLOCK_CARD", f"Policy: Confirmed fraud pattern; exposure ${exposure_usd:.2f}", exposure_usd))
            actions.append(cls.make_action("CREATE_CASE", "Policy 3a: Open case and write to graph"))
            if exposure_usd > 1000.0 or is_shared_origin:
                file_sar = True
                sar_reason = "Policy 3a: Confirmed fraud exceeding $1,000 or linked to shared entity"
                actions.append(cls.make_action("FILE_REPORT", sar_reason, exposure_usd))
            if is_shared_origin:
                actions.append(cls.make_action("MONITOR_CONNECTED_CARDS", "R6: Monitor cards sharing compromised profile"))
            return actions, file_sar, sar_reason

        # Legitimate verdict
        if verdict == "legitimate":
            actions.append(cls.make_action("ALLOW_TRANSACTION", "Policy: Activity confirmed legitimate"))
            actions.append(cls.make_action("CLOSE_NO_FRAUD", "Policy: Alert cleared as legitimate"))
            return actions, False, ""

        # Uncertain verdict (R8)
        actions.append(cls.make_action("MONITOR_CARD", "Policy: Card placed under enhanced 72-hour monitoring"))
        if exposure_usd > 500.0:
            actions.append(cls.make_action("ESCALATE_TO_ANALYST", "R8: Uncertain verdict with exposure exceeding $500"))
        return actions, False, ""
