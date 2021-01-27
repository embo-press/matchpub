
from lxml.etree import fromstring, Element, ParseError
from typing import List, Set, Union
import requests
import re
from .utils import normalize


class Article:

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
        self.expanded_author_set: Set[str] = Article.process_authors(self.author_list)

    def __str__(self):
        authors = ", ".join(self.author_list)
        s = f"{authors} ({self.year}). {self.title} {self.journal_name} {self.doi}"
        return s

    @staticmethod
    def process_authors(authors: Union[str, List[str]]) -> List[str]:
        if isinstance(authors, str):
            authors = [authors]
        authors = Article.split_composed_names(authors)  # needs to be done first since hyphens would be removed by normalization
        authors = [normalize(au) for au in authors]  # tremove punctuation including hyphens
        authors = [re.sub(r"^(van der |vander |van den |vanden |van |von |de |de la |del |della |dell')", r'', au) for au in authors]  # particles
        authors = [re.sub(r"^(mac|mc) ", r"\1", au) for au in authors]  # mc intosh mc mahon
        authors = set(authors)  # unique normalized names
        return authors

    @staticmethod
    def split_composed_names(authors: List[str]):
        expanded_author_list = []
        for last_name in authors:
            sub_names = last_name.split('-')
            expanded_author_list.extend(sub_names)
        return expanded_author_list


class PMCService:

    REST_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST'

    def __init__(self, min_date=1970, max_date=3000, include_preprint=False):
        self.start = str(min_date)
        self.end = str(max_date)
        self.include_preprint = include_preprint

    def search_by_author(self, author_list: List[List[str]]) -> List[Article]:
        if author_list:
            # consider alternatives of same name and use OR construct
            or_statements = []
            for alternatives in author_list:
                statement = " OR ".join([f'AUTH:"{au}"' for au in alternatives])
                or_statements.append(f"({statement})")
            and_names = ' AND '.join(or_statements)
            query = f"{and_names} AND PUB_YEAR:[{self.start} TO {self.end}]"
            article_list = self._search(query)
        else:
            article_list = []
        return article_list

    def search_by_title(self, title: str) -> List[Article]:
        if title:
            # need to clean up title from : otherwise PMC REST API chokes!
            query = f'TITLE:"{normalize(title)}" AND PUB_YEAR:[{self.start} TO {self.end}]'
            article_list = self._search(query)
        else:
            article_list = []
        return article_list

    def _search(self, query: str) -> List[Article]:
        params = {"query": query, "resultType": "core"}
        print("2. search_PMC with", params)
        article_list = []
        response = requests.post(self.REST_URL, data=params)
        if response.status_code == 200:
            print("3. query successful!")
            try:
                xml = fromstring(response.content)
                # tree_fetched = parse(xml)
                articles = xml.xpath('.//result')
                article_list = [Article(a) for a in articles]
                article_list = [a for a in article_list if a.pub_type != 'preprint']
                print(len(article_list), "results found.")
            except ParseError:
                print("XML parse error with: {params}")
        else:
            print("failed query ({response.status_code}) with: {params}")
        return article_list


def self_test():
    s = PMCService()
    by_author = s.search_by_author([["Lemberger"], ["Liechti"]])
    print(str(by_author[0]))
    by_title = s.search_by_title("SourceData: a semantic platform for curating and searching figures")
    print(str(by_title[0]))
    print(by_title[0].expanded_author_set)
    empty_author = s.search_by_author([])
    print(str(empty_author))


if __name__ == "__main__":
    self_test()
