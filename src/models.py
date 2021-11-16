from dataclasses import dataclass, field, InitVar
import dataclasses
from collections import OrderedDict, UserDict, UserList
from typing import List, Tuple, Union
import re

from lxml.etree import Element
import pandas as pd

from .decision import normalize_decision
from .utils import process_authors, last_name, normalize, normalize_date


@dataclass
class Paper:
    """Base class for a paper holding title, author list and an expanded author list names, useful when running search.

    Fields:
        title (str): the title.
        abstract (str): abstract.
        author_list (List[str]): the list of authors' *last names*
        expanded_author_list (List[List[str]]): the list of authors last name, each names being expanded to alternatives when necessary (eg composed names)
    """
    title: str = field(default='')
    abstract: str = field(default='')
    author_list: List[str] = field(default_factory=list)
    expanded_author_list: List[List[str]] = field(default_factory=list)


# TODO: some class to centralize key_index in description, rows extracted from Excel and attributes of Paper

@dataclass
class Submission(Paper):
    """A Submission as extracted from an eJP report parsed into a pandas DataFrame.
    Includes editorial information in addition to fields inherited from Paper.

    Args:
        row (pd.Series): the pandas row parsed from the eJP report row.

    Fields:
        title (str): the title.
        abstract (str): abstract.
        author_list (List[str]): the list of authors' *last names*
        expanded_author_list (List[List[str]]): the list of authors last name, each names being expanded to alternatives when necessary (eg composed names)
        manuscript_nm (str): the manuscript number internal to the editorial system.
        editor (str): the handling editor.
        decision (str): the editorial decision associated with this manuscirpt number.
        sub_date (str): submission date
        min_time_to_secure_rev (int): time to secure first reviewers in days.
        avg_time_to_secure_rev (float): average time to secure all reviewers.
        referee_number (int): number of referees who returned a report.
        ping_reply (str): the reply to an offer(or 'ping') to transfer the manuscript to another journal
    """
    manuscript_nm: str = field(default='')
    editor: str = field(default='')
    journal_decision: str = field(default='')
    decision: str = field(default='')
    sub_date: str = field(default='')
    min_time_to_secure_rev: int = field(default=None)
    avg_time_to_secure_rev: float = field(default=None)
    referee_number: int = field(default=None)
    ping_response: str = field(default='')

    row: InitVar[pd.Series] = None

    def __post_init__(self, row: pd.Series):
        self.manuscript_nm: str = row['manuscript_nm']
        self.editor: str = row.get('editor', 'editor name not available')
        self.journal_decision: str = row['journal_decision']
        self.decision: str = normalize_decision(self.journal_decision)
        self.sub_date: str = normalize_date(str(row['sub_date']))  # normalize date to ISO format with date only
        self.min_time_to_secure_rev = row.get('min_time_to_secure_rev', 0)
        self.avg_time_to_secure_rev = row.get('avg_time_to_secure_rev', 0)
        self.referee_number = row.get('referee_number', 0)
        self.ping_response = row.get('ping_response', '')
        self.title: str = normalize(row['title'], do=['ctrl'])  # remove control characters that are invariably toxic
        self.abstract: str = normalize(row.get('abstract', 'abstract not available'))  # rare illegal character can block pd.ExcelWriter
        self.author_list: List[str] = self.split_author_list(row['authors'])
        self.expanded_author_list: List[List[str]] = process_authors(self.author_list)

    @staticmethod
    def split_author_list(content: str) -> List[str]:
        """Splits the single string into author last names.
        Assumes that the names are comma separated with first name first and last name last, with no intervening commas.
        Cleans it up from 'decoration' added by eJP and removes duplicates, removes double spaces, non breaking spaces or empty entries.
        Last names are exctracted to INCLUDE a particle (de, von, saint, etc...)
        The names are NOT yet normalized at this stage.

        Args:
            content (str): the author list as single string.

        Returns:
           (List[str]): the list with unique last names.
        """
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
class EuropePMCArticle(Paper):
    """A published article retrieved from EuropePMC. Might become a specialize class later if we re-introduce PubMed as search engine.
    It assumes that EuropePMC results are returned in XML format using ResultType=Core
    In addition to the fields inherited from Paper, it contains publishing information such as doi, journal names etc...

    Args:
        xml (Element): the XML Element parsed from the results returned by EuropePMC.

    Fields:
        title (str): the title.
        abstract (str): abstract.
        author_list (List[str]): the list of authors' *last names*
        expanded_author_list (List[List[str]]): the list of authors last name, each names being expanded to alternatives when necessary (eg composed names)
        doi (str): the DOI of the published paper.
        pmid (str): the PMID identifier in PubMed.
        pub_type (str): whether a preprint, journal article, letter, book
        pub_date (str): date of publishing
        journal_name (str): the full-length journal title.
        journal_abbr (str): the abbreviated journal title as it appears in PubMed.
        abstract (str): the abstract.
        citations (int): the citation number obtained from Scopus.
        author_overlap_score (float): the degree of overalp of authors with the matching submission.
        title_similarty_score (float): the similarity of the title with the title of the matching submission.
        preprint_published_doi (str): for preprint only; the doi of the journal paper if already published.
    """
    doi: str = field(default='')
    pmid: str = field(default='')
    pub_type: List[str] = field(default_factory=list)
    is_preprint: bool = field(default=None)
    preprint_published_doi: float = field(default=None)
    pub_date: str = field(default='')
    journal_name: str = field(default='')
    journal_abbr: str = field(default='')
    citations: int = field(default=None)
    strategy: str = field(default='')
    author_overlap_score: float = field(default=None)
    title_similarity_score: float = field(default=None)

    xml: InitVar[Element] = None

    def __post_init__(self, xml: Element):
        self.pmid = xml.findtext('./pmid', '')
        self.pub_type = [t.text.lower() for t in xml.findall('.//pubTypeList/pubType', [])]
        # might be better to use  <source>PPR</source
        # if 'preprint' in self.pub_type:
        if xml.findtext('./source') == "PPR":
            self.journal_name = xml.findtext('.//publisher', '')
            self.journal_abbr = self.journal_name
            self.is_preprint = True
        else:
            self.journal_name = xml.findtext('./journalInfo/journal/title', '')
            self.journal_abbr = xml.findtext('./journalInfo/journal/medlineAbbreviation', '')
            self.is_preprint = False
        self.pub_date = normalize_date(xml.findtext('./firstPublicationDate'))  # normalize date format to ISO date only
        self.doi = xml.findtext('./doi', '')
        self.abstract = xml.findtext('./abstractText', '')

        self.title = xml.findtext('./title', '')
        self.author_list = [au.text for au in xml.findall('./authorList/author/lastName')]
        self.expanded_author_list = process_authors(self.author_list)

    def __str__(self):
        authors = ", ".join(self.author_list)
        s = f"{authors} ({self.year}). {self.title} {self.journal_name} {self.doi}"
        return s


@dataclass
class PubMedArticle(Paper):
    """A published article retrieved from PubMed.
    It assumes that PubMed results are returned in XML format using ResultType=Core
    In addition to the fields inherited from Paper, it contains publishing information such as doi, journal names etc...

    Args:
        xml (Element): the XML Element parsed from the results returned by PubMed.

    Fields:
        title (str): the title.
        abstract (str): abstract.
        author_list (List[str]): the list of authors' *last names*
        expanded_author_list (List[List[str]]): the list of authors last name, each names being expanded to alternatives when necessary (eg composed names)
        doi (str): the DOI of the published paper.
        pmid (str): the PMID identifier in PubMed.
        pub_type (str): whether a preprint, journal article, letter, book
        pub_date (str): date of publishing
        journal_name (str): the full-length journal title.
        journal_abbr (str): the abbreviated journal title as it appears in PubMed.
        abstract (str): the abstract.
        citations (int): the citation number obtained from Scopus.
        author_overlap_score (float): the degree of overalp of authors with the matching submission.
        title_similarty_score (float): the similarity of the title with the title of the matching submission.
        preprint_published_doi (str): for preprint only; the doi of the journal paper if already published.
    """
    doi: str = field(default='')
    pmid: str = field(default='')
    pub_type: List[str] = field(default_factory=list)
    is_preprint: bool = field(default=None)
    preprint_published_doi: float = field(default=None)
    pub_date: str = field(default='')
    journal_name: str = field(default='')
    journal_abbr: str = field(default='')
    citations: int = field(default=None)
    strategy: str = field(default='')
    author_overlap_score: float = field(default=None)
    title_similarity_score: float = field(default=None)

    xml: InitVar[Element] = None

    def __post_init__(self, xml: Element):
        medline_citation = xml.find('MedlineCitation')
        article = medline_citation.find('Article')
        self.pmid = medline_citation.findtext('PMID', '')
        self.pub_type = [t.text.lower() for t in article.findall('PublicationTypeList/PublicationType', [])]
        self.is_preprint = 'preprint' in self.pub_type
        self.journal_name = article.findtext('Journal/Title', '')
        self.journal_abbr = article.findtext('Journal/ISOAbbreviation', '')
        date = medline_citation.xpath('ArticleDate | DateRevised')
        if date:
            date = date[0]
        else:
            import pdb; pdb.set_trace()
        year = date.findtext('Year', '')
        month = date.findtext('Month', '')
        day = date.findtext('Day', '')
        self.pub_date = '-'.join([year, month, day])   # iso format
        self.doi = article.findtext('ELocationID[@EIdType="doi"]', '')
        self.abstract = article.findtext('Abstract', '')
        self.title = article.findtext('ArticleTitle', '')
        self.author_list = [au.text for au in article.findall('AuthorList/Author/LastName')]
        self.expanded_author_list = process_authors(self.author_list)

    def __str__(self):
        authors = ", ".join(self.author_list)
        s = f"{authors} ({self.year}). {self.title} {self.journal_name} {self.doi}"
        return s


@dataclass
class Result:
    """The matched article and submission resulting from the search and matching algorithm.

    Fields:
        submission (Submission): the submitted mansucript.
        article (Article): the matching published article.
    """
    submission: Submission = field(default=None)
    article: Union[PubMedArticle, EuropePMCArticle] = field(default=None)


class ResultDict(UserDict):
    """Maps the fields of matching Article and Submission to the ordered sequence of headers or columns
    names that are used when saving results in Excel files or processing the data in pandas DataFrame.
    Dataclass fields are mapped to dictionary keys. To allow reordering of fields from Article and Submissions, fields
    are encoded with the convention: (<submission|article>.<field_name>, <my_header_name>)

    Args:
        result (Result): the result to be mapped.
        field_label_map (List[Tuple[str, str]]): the list of ordered field names (using the convention (<submission|article>.<field_name>).
    """
    def __init__(
        self,
        result: Result,
        field_label_map: List[Tuple[str, str]]
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
        """The ordered list of header or column names."""
        return list(self.keys())


class Analysis(UserList):
    """A list of results ready to be ingested by pandas DataFrame constructor.
    The names and order of the columns can be provided in field_lable_map.
    DaArticle and Submission fields are mapped to the respective desired column/header names.
    Column/header names MUST be unique.
    To allow arbitray reordering of fields from Article and Submissions, fields
    are encoded in Tuples with the convention: (<submission|article>.<field_name>, <my_header_name>)

    Args:
        results (List[Result])
        field_label_map (List[List[Tuple]])): the mapping between Article and Submission fields with the desired column/header names.
    """
    def __init__(
        self,
        results: List[Result] = [],
        field_label_map: List[Tuple[str, str]] = [
            ('submission.manuscript_nm', 'manuscript_nm'),
            ('submission.sub_date', 'sub_date'),
            ('submission.editor', 'editor'),
            ('submission.journal_decision', 'journal_decision'),
            ('submission.decision', 'decision'),
            ('article.journal_abbr', 'journal'),
            ('article.citations', 'citations'),
            ('submission.title', "original_title"),
            ('article.title', 'retrieved_title'),
            ('submission.author_list', 'original_authors'),
            ('article.author_list', 'retrieved_authors'),
            ('article.doi', 'doi'),
            ('article.pmid', 'pmid'),
            ('article.pub_date', 'pub_date'),
            ('submission.abstract', 'original_abstract'),
            ('article.abstract', 'retrieved_abstract'),
            ('article.strategy', 'retrieval_strategy'),
            ('article.title_similarity_score', 'title_score'),
            ('article.author_overlap_score', 'author_score'),
            ('submission.min_time_to_secure_rev', 'min_time_to_secure_rev'),
            ('submission.avg_time_to_secure_rev', 'avg_time_to_secure_rev'),
            ('submission.referee_number', 'referee_number'),
            ('submission.ping_response', 'ping_response'),
            ('article.pub_type', 'publication_type'),
            ('article.preprint_published_doi', 'preprint_published_doi'),
            ('article.is_preprint', 'is_preprint')
        ]
    ):
        self.data = [ResultDict(r, field_label_map) for r in results]
        if results:
            self.cols = self.data[0] if results else []
        else:
            self.cols = []
