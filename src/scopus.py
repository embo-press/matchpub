import requests
import argparse
from time import sleep
from . import logger, SCOPUS, API_KEY


# https://api.elsevier.com/content/search/scopus?query=all(gene)&apiKey=7f59af901d2d86f78a1fd60c1bf9426a
# https://dev.elsevier.com/tecdoc_cited_by_in_scopus.html
# check quotas
# https://dev.elsevier.com/api_key_settings.html
# https://dev.elsevier.com/apikey/manage


def citedby_count(pmid):
    sleep(0.33)  # 3 requests / sec max
    citation_count = None
    if pmid:
        params = {"apiKey": API_KEY, "query": f"PMID({str(pmid)})", "field": "citedby-count"}
        r = requests.post(SCOPUS, data=params)
        remaining_queries = r.headers.get('X-RateLimit-Remaining', 0)
        if int(remaining_queries) < 10_000:
            logger.error(f"more than half of queries consumed. Only {remaining_queries} left!")
            raise RuntimeError(f"quota half consumed. Remaining: {remaining_queries}.")
        elif r.status_code == 200:
            data = r.json()
            matches = int(data['search-results']['opensearch:totalResults'])
            if matches == 1:
                citation_count = int(data['search-results']['entry'][0]['citedby-count'])
        else:
            logger.error(f"Somethign went wrong ({r.status_code}) with {pmid}:\n{r.content}\n{r.headers}")
    return citation_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="searches SCOPUS for matching PMID and retuns citedby count")
    parser.add_argument('pmid', nargs="?", default="29088127", help="The pmid of the article to be searched for (test it with 16729048).")
    args = parser.parse_args()
    pmid = args.pmid
    print(citedby_count(pmid))
