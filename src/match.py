import numpy as np
from lxml.etree import Element
import spacy
from typing import List, Tuple, Set
from .search import Article

# do this before: python -m spacy download en_core_web_sm
nlp = spacy.load('en_core_web_sm')


def best_match_by_title(candidates: List[Article], submitted_title: str, submitting_authors: Set[str], threshold: float = 0.5, max_diff: int = 3) -> Article:
    if candidates:
        best_match, score = similarity_best_match(submitted_title, candidates)
        pubmed_authors = best_match.author_list
        # in rare cases of community papers a search by author returns results, but only a collective naem is given and no specific author
        num_pubmed_au = len(pubmed_authors)
        num_sub_au = len(submitting_authors)
        if (score > threshold) and (num_pubmed_au > 0) and ((num_pubmed_au - num_sub_au) <= max_diff):
            return best_match
    return None


def best_match_by_author(candidates: List[Article], submitted_title: str, submitting_authors: Set[str], threshold: float = 0.5) -> Article:
    if candidates:
        best_match = candidates[0]  # pmc returns results sorted by relevance
        score = similarity(best_match.title, submitted_title)
        authors_of_best_match = best_match.expanded_author_set  # process_authors(best_match.author_list)
        overlap = len(authors_of_best_match & submitting_authors)
        # at least one author should be in the submitting authors
        if overlap > 0 and score >= threshold:
            return best_match
    return None


def similarity_best_match(query: str, candidates: List[Article]) -> Tuple[Article, float]:
    score_list = [similarity(query, article.title) for article in candidates]
    idx = np.array(score_list).argmax()
    return candidates[idx], score_list[idx]


def similarity(s1: str, s2: str):
    n1 = nlp(s1)
    n2 = nlp(s2)
    score = n1.similarity(n2)
    return score


def self_test():
    article_1 = Article(Element('nothing'))
    article_1.author_list = ['Roguet', 'Nielsen', 'van der Parasite']
    article_1.expanded_author_set = article_1.process_authors(article_1.author_list)
    article_1.title = "This is a different title or what!"
    article_2 = Article(Element('nothing'))
    article_2.author_list = ['Nobody', 'Somebody', 'Roguet-Simson']
    article_2.expanded_author_set = article_2.process_authors(article_1.author_list)
    article_2.title = "This is my title: or what?"

    by_title = best_match_by_title([article_1, article_2], "This is my title: or what?", set({"roguet", "nielsen"}))
    print(by_title)

    by_author = best_match_by_author([article_1, article_2], "This is my title: or what?", set({"roguet", "nielsen", "parasite"}))
    print(by_author)

if __name__ == "__main__":
    self_test()
