import numpy as np
from lxml.etree import Element
import spacy
from typing import List, Tuple, Callable
from .utils import process_authors, flat_unique_set, normalize
from .search import PMCArticle
from . import logger

# do this before in Dockerfile: python -m spacy download en_core_web_lg
nlp = spacy.load('en_core_web_lg')


def best_match_by_title(*args, threshold: float = 0.85, **kwargs) -> PMCArticle:
    """Given a list of candidate articles, find the one that has the highest similartiy score for the title.

    Args:
        candidates (List[PMCArticle]): the list of candidate PMCArticles.
        submitted_title (str): the title of the submitted paper we are trying to match.
        submitting_authors (List[List[str]]): the set of unique author last names.
        threshold (float): the threshold above which the similartiy score between titles should be.
    """
    return _best_match(*args, max_title_similarity, **kwargs, threshold=threshold)


def best_match_by_author(*args, threshold: float = 0.80, **kwargs) -> PMCArticle:
    """Given a list of candidate articles, find the one that has the maximal overlap of author names.

    Args:
        candidates (List[PMCArticle]): the list of candidate PMCArticles.
        submitted_title (str): the title of the submitted paper we are trying to match.
        submitting_authors (List[List[str]]): the set of unique author last names.
        threshold (float): the threshold above which the similartiy score between titles should be.
    """
    return _best_match(*args, max_author_overlap, **kwargs, threshold=threshold)


def _best_match(
        candidates: List[PMCArticle],
        submitted_title: str,
        submitting_authors: List[List[str]],
        best_similarity_funct: Callable,
        threshold: float) -> PMCArticle:
    """Given a list of candidate articles, find the one that has the similartiy score.

    Args:
        candidates (List[PMCArticle]): the list of candidate PMCArticles.
        submitted_title (str): the title of the submitted paper we are trying to match.
        submitting_authors (List[List[str]]): the set of unique author last names.
        threshold (float): the threshold above which the similartiy score between titles should be.
        best_similarity_funct (Callable): a function returning the best matching paper and its score.
    """
    if candidates:
        best_match, score = best_similarity_funct(candidates, submitted_title, submitting_authors)
        logger.debug(f"looking for: '{submitted_title }' {submitting_authors    }.")
        logger.debug(f"best match : '{best_match.title}' {best_match.author_list}.  Score {score:.2f} ({best_similarity_funct.__name__})")
        if (score > threshold):
            return best_match
        logger.debug(f"DISCARDED with score {score:.2f} < {threshold}")
    return None


def max_title_similarity(candidates: List[PMCArticle], title: str = '', authors: List[List[str]] = [[]]) -> Tuple[PMCArticle, float]:
    score_list = [similarity(title, PMCArticle.title) for PMCArticle in candidates]
    idx = np.array(score_list).argmax()
    return candidates[idx], score_list[idx]


def similarity(s1: str, s2: str):
    n1 = nlp(normalize(s1))
    n2 = nlp(normalize(s2))
    score = n1.similarity(n2)
    return score


def max_author_overlap(candidates: List[PMCArticle], title: str = '', authors: List[List[str]] = [[]]) -> Tuple[PMCArticle, int]:
    num_authors = len(authors)
    unique_names = flat_unique_set(authors)
    overlap_list = [len(unique_names & flat_unique_set(a.expanded_author_list)) for a in candidates]
    idx = np.array(overlap_list).argmax()
    score = overlap_list[idx] / num_authors
    return candidates[idx], score


def self_test():
    PMCArticle_1 = PMCArticle(Element('nothing'))
    PMCArticle_1.author_list = ['Roguet', 'Nielsen', 'van der Parasite']
    PMCArticle_1.expanded_author_list = process_authors(PMCArticle_1.author_list)
    PMCArticle_1.title = "This is a different title or what!"
    PMCArticle_2 = PMCArticle(Element('nothing'))
    PMCArticle_2.author_list = ['Nobody', 'Somebody', 'Roguet-Simson']
    PMCArticle_2.expanded_author_list = process_authors(PMCArticle_1.author_list)
    PMCArticle_2.title = "This is my title: or what?"

    by_title = best_match_by_title([PMCArticle_1, PMCArticle_2], "This is my title: or what?", [["roguet"], ["jens-nielsen", "jens", "nielsen", "nielsen-jens"]])
    print(by_title)

    by_author = best_match_by_author([PMCArticle_1, PMCArticle_2], "This is my title: or what?", [["roguet"], ["jens-nielsen", "jens", "nielsen", "nielsen-jens"], ["parasite"]])
    print(by_author)

if __name__ == "__main__":
    self_test()
