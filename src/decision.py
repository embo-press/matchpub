import re

import pandas as pd

"""Regex to aggregate decision types into accepted, rejected before review, rejected after review.
Regex should be designed to be used with re.search()
"""

# REJECTED BEFORE REVIEW

decision_matching_regex = {
    'rejected before review': re.compile(
        # "reject and refer"
        # "reject before review"
        # "reject before review advisory editorial board",
        # "reject with board advice & refer",
        # "editorial rejection",
        # "editorial rejection (EBA)",
        # "RC - Reject and Refer",
        # "RC - Editorial Reject",
        # "RC - Reject with EBA",
        r"""
        (reject\ before)|
        (reject\ and\ refer)|
        (reject\ with)|
        (editorial\ reject)
        """,
        re.IGNORECASE | re.VERBOSE
    ),
    'rejected after review': re.compile(
        # "reject post review"
        # "reject post review - 2 reviewer"
        # "reject post review (invite resubmission)"
        # "Revise and Re-Review - Border Line Reject"
        # "reject post review & refer"
        # "rejection"
        # "reject"
        r"""
        (reject\ post)|
        (^reject(ion)?$)|
        (border\ line\ reject)
        """,
        re.IGNORECASE | re.VERBOSE
    ),
    'accepted': re.compile(
        # "accepted"
        # "rejected before review"
        # "rejected after review"
        # "suggest posting of reviews"
        r"""
        (accept)|(suggest posting of reviews)
        """,
        re.IGNORECASE | re.VERBOSE
    )
}


def normalize_decision(analysis: pd.DataFrame):
    """Normalizes inplace decisions into 3 fundamental decision types: 'accepted', 'rejected before review', 'rejected after review'.
    Each type is defined by regexp provided in 'decision_matching_regex'

    Args:
        analysis (pd.DataFrame): the analysis whose column 'decision' will be normalized.

    """
    rejected_ed = analysis['decision'].apply(lambda x: decision_matching_regex['rejected before review'].search(x) is not None)
    rejected_post = analysis['decision'].apply(lambda x: decision_matching_regex['rejected after review'].search(x) is not None)
    accepted = analysis['decision'].apply(lambda x: decision_matching_regex['accepted'].search(x) is not None)
    analysis.loc[rejected_ed, 'decision'] = 'rejected before review'
    analysis.loc[rejected_post, 'decision'] = 'rejected after review'
    analysis.loc[accepted, 'decision'] = 'accepted'
