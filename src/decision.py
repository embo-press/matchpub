import re

"""Regex to aggregate decision types into accepted, rejected before review, rejected after review.
Regex should be designed to be used with re.search()
"""

# REJECTED BEFORE REVIEW

decision_matching_regex = {}

# all current variations for rejected before review

# rejected before review
# Reject Before Review
# Reject Before Review with Editorial Board Advice
# Reject and Refer
# Reject with Board Advice & Refer
# RC - Editorial Reject
# RC - Reject with EBA
# RC - Reject and Refer
# Reject Before Review Editorial Board Advice
# EDREJECT
decision_matching_regex['rejected before review'] = re.compile(
    r"""
    (reject(ed)?\ before)|
    (reject(ed)?\ and\ refer)|
    (reject(ed)?\ with)|
    (ed\w*\ ?rej)
    """,
    re.IGNORECASE | re.VERBOSE
)

# all current variations for rejected before review

# reject after review
# Reject Post Review - 2 Reviewers
# Reject post review
# Reject post-review & Refer
# RC - Reject post review
# Reject Post Review (Invite resubmission)
# Rejection
# Reject post-review
# Reject and encourage resubmission
# Reject Open  # LSA!
# Reject after Re-review  # LSA!
decision_matching_regex['rejected after review'] = re.compile(
    r"""
    (reject(ed)?\ post)|
    (reject(ed)?\ after)|
    (^reject(ion|ed)?$)|
    (border\ line\ reject)|
    (reject(ed)?\ and\ encourage)|
    (reject\ open)
    """,
    re.IGNORECASE | re.VERBOSE
)

# accepted
# Accept
# RC - Accept
# Accept (no review)
# Suggest Posting of Reviews

decision_matching_regex['accepted'] = re.compile(
    r"""
    (accept(ed)?)|(suggest\ posting\ of\ reviews)
    """,
    re.IGNORECASE | re.VERBOSE
)


# def normalize_decision(analysis: pd.DataFrame):
#     """Normalizes inplace decisions into 3 fundamental decision types: 'accepted', 'rejected before review', 'rejected after review'.
#     Each type is defined by regexp provided in 'decision_matching_regex'

#     Args:
#         analysis (pd.DataFrame): the analysis whose column 'decision' will be normalized.

#     """
#     rejected_ed = analysis['journal_decision'].apply(lambda x: decision_matching_regex['rejected before review'].search(x) is not None)
#     rejected_post = analysis['journal_decision'].apply(lambda x: decision_matching_regex['rejected after review'].search(x) is not None)
#     accepted = analysis['journal_decision'].apply(lambda x: decision_matching_regex['accepted'].search(x) is not None)
#     analysis['decision'] = None
#     analysis.loc[rejected_ed, 'decision'] = 'rejected before review'
#     analysis.loc[rejected_post, 'decision'] = 'rejected after review'
#     analysis.loc[accepted, 'decision'] = 'accepted'
#     import pdb; pdb.set_trace()


def normalize_decision(decision: str) -> str:
    """Normalize decisions into  3 fundamental decision types: 'accepted', 'rejected before review', 'rejected after review'.
    Each type is defined by matching ot regex provded in decision_matching_regex

    Args:
        decision (str): the decision to normalize
    """
    if decision_matching_regex['rejected before review'].search(decision) is not None:
        normalized_decision = 'rejected before review'
    elif decision_matching_regex['rejected after review'].search(decision) is not None:
        normalized_decision = 'rejected after review'
    elif decision_matching_regex['accepted'].search(decision) is not None:
        normalized_decision = 'accepted'
    else:
        normalized_decision = 'unknown decision type'
    return normalized_decision
