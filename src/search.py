
from lxml.etree import fromstring, Element, ParseError
from typing import List
import requests

from .utils import process_authors
from . import logger


class PMCArticle:

    def __init__(self, a: Element):
        self.pmid: str = a.findtext('./pmid', '')
        self.pub_type: str = a.findtext('.//pubType', '').lower()
        if self.pub_type == 'preprint':
            self.journal_name: str = a.findtext('.//publisher', '')
        else:
            self.journal_name: str = a.findtext('./journalInfo/journal/title', '')
        self.year: str = a.findtext('./journalInfo/yearOfPublication', '')
        self.month: str = a.findtext('./journalInfo/monthOfPublication', '')
        self.title: str = a.findtext('./title', '')
        self.doi: str = a.findtext('./doi', '')
        self.abstract: str = a.findtext('./abstractText', '')
        self.author_list: List[str] = [au.text for au in a.findall('./authorList/author/lastName')]
        self.expanded_author_list: List[List[str]] = process_authors(self.author_list)

    def __str__(self):
        authors = ", ".join(self.author_list)
        s = f"{authors} ({self.year}). {self.title} {self.journal_name} {self.doi}"
        return s


class PMCService:

    REST_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST'

    def __init__(self, min_date: int = 1970, max_date: int = 3000, include_preprint: bool = False):
        self.start = str(min_date)
        self.end = str(max_date)
        self.include_preprint = include_preprint

    def search_by_author(self, author_list: List[List[str]]) -> List[PMCArticle]:
        if author_list:
            # consider alternatives of same name and use OR construct
            or_statements = []
            for alternatives in author_list:
                statement = " OR ".join([f'AUTH:"{au}"' for au in alternatives])
                or_statements.append(f"({statement})")
            and_names = ' AND '.join(or_statements)
            query = f"{and_names} AND PUB_YEAR:[{self.start} TO {self.end}]"
            PMCArticle_list = self._search(query)
        else:
            PMCArticle_list = []
        return PMCArticle_list

    def search_by_title(self, title: str) -> List[PMCArticle]:
        if title:
            query = f'TITLE:{title} AND PUB_YEAR:[{self.start} TO {self.end}]'
            PMCArticle_list = self._search(query)
        else:
            PMCArticle_list = []
        return PMCArticle_list

    def _search(self, query: str) -> List[PMCArticle]:
        params = {"query": query, "resultType": "core", "pageSize": "5"}
        logger.debug(f"search_PMC with {params}")
        PMCArticle_list = []
        response = requests.post(self.REST_URL, data=params)
        if response.status_code == 200:
            try:
                xml = fromstring(response.content)
                # tree_fetched = parse(xml)
                PMCArticles = xml.xpath('.//result')
                PMCArticle_list = [PMCArticle(a) for a in PMCArticles]
                PMCArticle_list = [a for a in PMCArticle_list if a.pub_type != 'preprint']
                logger.debug(f"{len(PMCArticle_list)} results found.")
            except ParseError:
                logger.error(f"XML parse error with: {params}")
        else:
            logger.error(f"failed query ({response.status_code}) with: {params}")
        return PMCArticle_list


def self_test():
    s = PMCService()
    by_author = s.search_by_author([["Lemberger"], ["Liechti"]])
    print(str(by_author[0]))
    by_title = s.search_by_title("SourceData: a semantic platform for curating and searching figures")
    print(str(by_title[0]))
    print(by_title[0].expanded_author_list)
    empty_author = s.search_by_author([])
    print(str(empty_author))


if __name__ == "__main__":
    self_test()
