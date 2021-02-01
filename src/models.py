from dataclasses import dataclass, field, InitVar
import dataclasses
from collections import OrderedDict, UserDict, UserList
from typing import List, Tuple
import re
from lxml.etree import Element
import pandas as pd

from .utils import process_authors, last_name


@dataclass
class Paper:
    title: str = field(default='')
    author_list: List[str] = field(default_factory=list)
    expanded_author_list: List[List[str]] = field(default_factory=list)


@dataclass
class Submission(Paper):
    manuscript_nm: str = field(default='')
    editor: str = field(default='')
    decision: str = field(default='')

    row: InitVar[pd.Series] = None

    def __post_init__(self, row):
        self.manuscript_nm: str = row['manuscript_nm']
        self.editor: str = row['editor']
        self.title: str = row['title']
        self.decision: str = row['decision']
        self.author_list: List[str] = self.split_author_list(row['authors'])
        self.expanded_author_list: List[List[str]] = process_authors(self.author_list)

    @staticmethod
    def split_author_list(content: str) -> List[str]:
        full_names = content.split(",")
        stripped_full_names = [au.strip() for au in full_names]  # ejp has a bug which duplicates names with an added space
        unique_names = list(set(stripped_full_names))
        full_names_clean = [re.sub(r"-corr$", "", au).strip() for au in unique_names]
        full_names_clean = list(filter(None, full_names_clean))  # remove empty names
        full_names_super_clean = [re.sub(r"\s+", " ", au) for au in full_names_clean]  # some names have apparently several spaces or non-breaking spaces between first and last name
        last_names = [last_name(au) for au in full_names_super_clean]  # extract last names including particle
        return last_names

    def __str__(self):
        authors = ", ".join(self.author_list)
        s = f'{self.manuscript_nm}: {authors}. "{self.title}" ({self.decision} by {self.editor})'
        return s


@dataclass
class Article(Paper):
    doi: str = field(default='')
    pmid: str = field(default='')
    pub_type: str = field(default='')
    year: str = field(default='')
    month: str = field(default='')
    journal_name: str = field(default='')
    journal_abbr: str = field(default='')
    abstract: str = field(default='')
    citations: int = field(default=None)
    strategy: str = field(default='')
    author_overlap_score: float = field(default=None)
    title_similarity_score: float = field(default=None)
    discard: bool = field(default=False)

    xml: InitVar[Element] = None

    def __post_init__(self, xml: Element):
        self.pmid: str = xml.findtext('./pmid', '')
        self.pub_type: str = xml.findtext('.//pubType', '').lower()
        if self.pub_type == 'preprint':
            self.journal_name: str = xml.findtext('.//publisher', '')
            self.journal_abbr: str = self.journal_name
        else:
            self.journal_name: str = xml.findtext('./journalInfo/journal/title', '')
            self.journal_abbr: str = xml.findtext('./journalInfo/journal/medlineAbbreviation', '')
        self.year: str = xml.findtext('./journalInfo/yearOfPublication', '')
        self.month: str = xml.findtext('./journalInfo/monthOfPublication', '')
        self.title: str = xml.findtext('./title', '')
        self.doi: str = xml.findtext('./doi', '')
        self.abstract: str = xml.findtext('./abstractText', '')
        self.author_list: List[str] = [au.text for au in xml.findall('./authorList/author/lastName')]
        self.expanded_author_list: List[List[str]] = process_authors(self.author_list)

    def __str__(self):
        authors = ", ".join(self.author_list)
        s = f"{authors} ({self.year}). {self.title} {self.journal_name} {self.doi}"
        return s


@dataclass
class Result:
    submission: Submission = field(default=None)
    article: Article = field(default=None)


class ResultDict(UserDict):

    def __init__(
        self,
        result: Result,
        field_label_map: List[Tuple[str, str]] = [
            ('submission.manuscript_nm', 'manuscript_nm'),
            ('submission.editor', 'editor'),
            ('submission.decision', 'decision'),
            ('article.journal_abbr', 'journal'),
            ('article.citations', 'citations'),
            ('submission.title', "original_title"),
            ('article.title', 'retrieved_title'),
            ('submission.author_list', 'original_authors'),
            ('article.author_list', 'retrieved_authors'),
            ('article.doi', 'doi'),
            ('article.pmid', 'pmid'),
            ('article.year', 'pub_year'),
            ('article.month', 'pub_month'),
            ('article.abstract', 'retrieved_abstract'),
            ('article.strategy', 'retrieval_strategy'),
            ('article.title_similarity_score', 'title_score'),
            ('article.author_overlap_score', 'author_score'),
        ]
    ):
        d = {
            'submission': dataclasses.asdict(result.submission) if result.submission is not None else {},
            'article': dataclasses.asdict(result.article) if result.article is not None else {},
        }
        od = OrderedDict()
        for field_name, label in field_label_map:
            obj, f = field_name.split('.')
            od[label] = d[obj].get(f, None)
        self.data = od

    @property
    def cols(self):
        return list(self.keys())


class Analysis(UserList):
    def __init__(self, results: List[Result] = [], field_label_map: List[Tuple[str, str]] = []):
        self.data = [ResultDict(r) for r in results]
        if results:
            self.cols = self.data[0] if results else []
        else:
            self.cols = []
