import unittest

from src.utils import ed_rej_matcher, accept_matcher, post_review_rej_matcher


class TestDecisionMatching(unittest.TestCase):
    def test_decisions(self):
        decisions = {
            "accepted": ["accept"],
            "rejected before review": [
                "reject and refer"
                "reject before review"
                "reject before review advisory editorial board",
                "reject with board advice & refer",
                "editorial rejection",
                "editorial rejection (EBA)",
            ],
            "rejected after review": [
                "reject post review",
                "reject post review - 2 reviewer",
                "reject post review (invite resubmission)",
                "Revise and Re-Review - Border Line Reject",
                "reject post review & refer",
                "rejection",
                "reject"
            ]
        }
        matchers = {
            "accepted": accept_matcher,
            "rejected before review": ed_rej_matcher,
            "rejected after review": post_review_rej_matcher
        }
        for decision, variations in decisions.items():
            for v in variations:
                for dec, matcher in matchers.items():
                    if dec == decision:
                        self.assertIsNotNone(matcher.match(v))
                    else:
                        self.assertIsNone(matcher.match(v))


if __name__ == '__main__':
    unittest.main()
