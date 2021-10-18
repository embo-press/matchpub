import unittest

from src.decision import decision_matching_regex


class TestDecisionMatching(unittest.TestCase):
    def test_decisions(self):
        decisions = {
            "accepted": [
                "accepted",
                "Accept",
                "RC - Accept",
                "Suggest Posting of Reviews"
            ],
            "rejected before review": [
                "rejected before review",
                "Reject Before Review",
                "Reject Before Review with Editorial Board Advice",
                "Reject and Refer",
                "Reject with Board Advice & Refer",
                "RC - Editorial Reject",
                "RC - Reject with EBA",
                "RC - Reject and Refer",
                "Reject Before Review Editorial Board Advice",
            ],
            "rejected after review": [
                "reject after review",
                "Reject Post Review - 2 Reviewers",
                "Reject post review",
                "Reject post-review & Refer",
                "RC - Reject post review",
                "Reject Post Review (Invite resubmission)",
                "Rejection",
                "Reject post-review",
                "Reject and encourage resubmission",
            ]
        }

        for normal_decision, variations in decisions.items():
            for v in variations:
                for dec, regex in decision_matching_regex.items():
                    if dec == normal_decision:
                        self.assertIsNotNone(regex.search(v), f"'{v}' not matched for with '{dec}' regex {regex} decision type '{normal_decision}'")
                    else:
                        self.assertIsNone(regex.search(v), f"'{v}' erroneously matched with '{dec}' regex {regex} for decision type '{normal_decision}'")


if __name__ == '__main__':
    unittest.main()
