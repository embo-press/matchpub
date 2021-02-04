from enum import Enum, unique

"""Application-wide preferences"""


@unique
class PreprintInclusion(Enum):
    NO_PREPRINT = "no_preprint"
    ONLY_PREPRINT = "only_preprint"
    WITH_PREPRINT = "with_preprint"


class Config:
    preprint_inclusion: PreprintInclusion = PreprintInclusion.NO_PREPRINT
    include_citations: bool = True


config = Config()
