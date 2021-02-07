from enum import Enum, unique
from typing import List, Dict

"""Application-wide preferences"""


@unique
class PreprintInclusion(Enum):
    """The level of inclusion/exclusion of preprints when searching the literature.

    Attributes:
        NO_PREPRINT: search and search results will exclude preprints.
        ONLY_PREPRINT: search and search results will only include preprints.
        WITH_PREPRINT: search and search resutls will includ preprints and published papers.
    """
    NO_PREPRINT = "no_preprint"
    ONLY_PREPRINT = "only_preprint"
    WITH_PREPRINT = "with_preprint"


class Config:
    # the level of preprpint inclusion/exclusion
    preprint_inclusion: PreprintInclusion = PreprintInclusion.NO_PREPRINT
    # whether to include citation data
    include_citations: bool = False

    metadata_keys: List[str] = [
        "report_name", "editors", "time_window", "article_types", "creation_date"
    ]
    header_signature: List[str] = [
        r"manu", r"manu", r"ed", r".*editor|colleague", r"reviewer|referee",
        r"sub", r".*decision", r".*decision", r".*status", r".*title",
        r"auth", r".*decision"
    ]
    feature_index: Dict[str, int] = {
        "manuscript_nm": 0,
        "editor": 2,
        "decision": 7,
        "title": 9,
        "authors": 10,
    }


config = Config()
