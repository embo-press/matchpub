from enum import Enum, unique
from dataclasses import dataclass, field
from typing import Dict
# from .models import PreprintInclusion, Config

from .descriptions import ejp

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


@dataclass
class Config:
    """Application-wide preferences.

    Fields:
        preprint_inclusion (PreprintInclusion): the level of preprint inclusion/exclusion.
        include_citations (bool): whether to include citation data.
        input_description (Dict): description of rows and columns of the input file.
        dayfirst (bool): whether to interpret the first value in an ambiguous 3-integer date (e.g. 01/05/09) as the day (True) or month (False)
    """
    preprint_inclusion: PreprintInclusion = field(default=PreprintInclusion.NO_PREPRINT)
    include_citations: bool = field(default=False)
    input_description: Dict = field(default_factory=dict)
    dayfirst: bool = field(default=False)


config = Config(
    preprint_inclusion=PreprintInclusion.NO_PREPRINT,
    include_citations=False,
    input_description=ejp,
    dayfirst=False
)
