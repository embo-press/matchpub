import re

"""Regex to aggregate decision types into accepted, rejected before review, rejected after review"""

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
        r"""
        accept
        """,
        re.IGNORECASE | re.VERBOSE
    )
}
