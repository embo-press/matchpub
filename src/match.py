import numpy as np
from lxml.etree import Element
import spacy
from typing import List, Tuple, Callable, Union

from .utils import process_authors, flat_unique_set, normalize
from .models import Article
from . import logger

# do this before in Dockerfile: python -m spacy download en_core_web_lg
nlp = spacy.load('en_core_web_lg')


def match_by_title(candidates: List[Article], submitted_title: str, threshold: float = 0.85) -> Article:
    """Given a list of candidate articles, find the one that has the highest similartiy score for the title.

    Args:
        candidates (List[Article]): the list of candidate submissions.
        submitted_title (str): the title of the submitted paper we are trying to match.
        threshold (float): the threshold above which the similartiy score between titles should be.

    Returns:
        (Article): the best retrieved article.
    """
    match = _match(candidates, submitted_title, max_title_similarity, threshold)
    return match


def match_by_author(candidates: List[Article], submitting_authors: List[List[str]], threshold: float = 0.80) -> Article:
    """Given a list of candidate articles, find the one that has the maximal overlap of author names.

    Args:
        candidates (List[Article]): the list of candidate Articles.
        submitting_authors (List[List[str]]): the set of unique author last names.
        threshold (float): the threshold above which the similartiy score between titles should be.

    Returns:
        (Article): the best retrieved article.
    """
    match = _match(candidates, submitting_authors, max_author_overlap, threshold)
    return match


def _match(
    candidates: List[Article],
    submitted_feature: Union[str, List[List[str]]],
    similarity_funct: Callable,
    threshold: float
) -> Tuple[Article, bool]:
    """Given a list of candidate articles, finds the one with the best similartiy score.

    Args:
        candidates (List[Article]): the list of candidate Articles.
        submitted_feature (Union[str, List[List[str]]]): eith the title or the authors of the submission we are trying to match.
        best_similarity_funct (Callable): a function taking the candidates and the submitted feature as args and returning the best matching paper and its score.
        threshold (float): the threshold above which the similartiy score between titles should be.

    Returns:
        (Article): the best retrieved article.
        (bool): whether the similarity score is above threshold and the match successful
    """
    match, score = similarity_funct(candidates, submitted_feature)
    logger.debug(f"best match : '{match.title}' {match.author_list}.  Score {score:.2f} ({similarity_funct.__name__})")
    match.score = score
    if (score > threshold):
        success = True
    else:
        success = False
        logger.debug(f"DISCARDED with score {match.score:.2f} < {threshold}")
    return match, success


def max_title_similarity(candidates: List[Article], title: str = '') -> Tuple[Article, float]:
    score_list = [similarity(title, Article.title) for Article in candidates]
    idx = np.array(score_list).argmax()
    return candidates[idx], score_list[idx]


def similarity(s1: str, s2: str) -> float:
    n1 = nlp(normalize(s1))
    n2 = nlp(normalize(s2))
    score = n1.similarity(n2)
    return score


def max_author_overlap(candidates: List[Article], authors: List[List[str]] = [[]]) -> Tuple[Article, float]:
    num_authors = len(authors)
    unique_names = flat_unique_set(authors)
    overlap_list = [len(unique_names & flat_unique_set(a.expanded_author_list)) for a in candidates]
    idx = np.array(overlap_list).argmax()
    score = overlap_list[idx] / num_authors
    return candidates[idx], score


def self_test():
    Article_1 = Article(Element('nothing'))
    Article_1.author_list = ['Roguet', 'Nielsen', 'van der Parasite']
    Article_1.expanded_author_list = process_authors(Article_1.author_list)
    Article_1.title = "This is a different title or what!"
    Article_2 = Article(Element('nothing'))
    Article_2.author_list = ['Nobody', 'Somebody', 'Roguet-Simson']
    Article_2.expanded_author_list = process_authors(Article_1.author_list)
    Article_2.title = "This is my title: or what?"

    by_title = match_by_title([Article_1, Article_2], "This is my title: or what?", [["roguet"], ["jens-nielsen", "jens", "nielsen", "nielsen-jens"]])
    print(by_title)

    by_author = match_by_author([Article_1, Article_2], "This is my title: or what?", [["roguet"], ["jens-nielsen", "jens", "nielsen", "nielsen-jens"], ["parasite"]])
    print(by_author)


if __name__ == "__main__":
    self_test()
