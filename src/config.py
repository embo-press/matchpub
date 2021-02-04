from enum import Enum, unique

"""Application-wide preferences"""


@unique
class PreprintInclusion(Enum):
    """The elvel of inclusion/exclusion of preprints when searching the literature.

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
    include_citations: bool = True


config = Config()
