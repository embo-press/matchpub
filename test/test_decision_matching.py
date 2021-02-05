import unittest

from src.decision import decision_matching_regex


class TestDecisionMatching(unittest.TestCase):
    def test_decisions(self):
        decisions = {
            "accepted": [
                "accept",
                "RC - Accept",
            ],
            "rejected before review": [
                "reject and refer"
                "reject before review"
                "reject before review advisory editorial board",
                "reject with board advice & refer",
                "editorial rejection",
                "editorial rejection (EBA)",
                "RC - Reject and Refer",
                "RC - Editorial Reject",
                "RC - Reject with EBA",
            ],
            "rejected after review": [
                "reject post review",
                "reject post review - 2 reviewer",
                "reject post review (invite resubmission)",
                "Revise and Re-Review - Border Line Reject",
                "reject post review & refer",
                "rejection",
                "reject",
            ]
        }

        for decision, variations in decisions.items():
            for v in variations:
                for dec, regex in decision_matching_regex.items():
                    if dec == decision:
                        self.assertIsNotNone(regex.search(v), f"'{v}' not matched for with '{dec}' regex {regex} decision type '{decision}'")
                    else:
                        self.assertIsNone(regex.search(v), f"'{v}' erroneously matched with '{dec}' regex {regex} for decision type '{decision}'")


if __name__ == '__main__':
    unittest.main()
