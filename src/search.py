
from typing import List
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from lxml.etree import fromstring, ParseError

from .models import Article
from . import logger


def requests_retry_session(
    retries=4,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """Creates a resilient session that will retry several times when a query fails.
    from  https://www.peterbe.com/plog/best-practice-with-retries-with-requests

    Usage:
        session_retry = self.requests_retry_session()
        session_retry.headers.update({
            "Accept": "application/json",
            "From": "thomas.lemberger@embo.org"
        })
        response = session_retry.post(url, data=params, timeout=30)
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class PMCService:

    REST_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST'
    HEADERS = {
        "From": "thomas.lemberger@embo.org",
        "Content-type": "application/x-www-form-urlencoded"
    }

    def __init__(self, min_date: int = 1970, max_date: int = 3000, include_preprint: bool = False):
        self.start = str(min_date)
        self.end = str(max_date)
        self.include_preprint = include_preprint
        self.retry_request = requests_retry_session()
        self.retry_request.headers.update(self.HEADERS)

    def search_by_author(self, author_list: List[List[str]]) -> List[Article]:
        if author_list:
            # consider alternatives of same name and use OR construct
            or_statements = []
            for alternatives in author_list:
                statement = " OR ".join([f'AUTH:"{au}"' for au in alternatives])
                or_statements.append(f"({statement})")
            and_names = ' AND '.join(or_statements)
            query = f"{and_names} AND PUB_YEAR:[{self.start} TO {self.end}]"
            Article_list = self._search(query)
        else:
            Article_list = []
        return Article_list

    def search_by_title(self, title: str) -> List[Article]:
        if title:
            query = f'TITLE:{title} AND PUB_YEAR:[{self.start} TO {self.end}]'
            Article_list = self._search(query)
        else:
            Article_list = []
        return Article_list

    def _search(self, query: str) -> List[Article]:
        params = {"query": query, "resultType": "core", "pageSize": "5"}
        logger.debug(f"search_PMC with {params}")
        Article_list = []
        response = self.retry_request.post(self.REST_URL, data=params, headers=self.HEADERS)
        if response.status_code == 200:
            try:
                xml = fromstring(response.content)
                # tree_fetched = parse(xml)
                Articles = xml.xpath('.//result')
                Article_list = [Article(xml=a) for a in Articles]
                Article_list = [a for a in Article_list if a.pub_type != 'preprint']
                logger.debug(f"{len(Article_list)} results found.")
            except ParseError:
                logger.error(f"XML parse error with: {params}")
        else:
            logger.error(f"failed query ({response.status_code}) with: {params}")
        return Article_list


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
