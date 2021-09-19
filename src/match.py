from typing import List, Tuple, Set, Callable, Union

import numpy as np
from lxml.etree import Element
import spacy

from .utils import process_authors, flat_unique_set, normalize
from .models import Paper
from . import logger

# do this before in Dockerfile: python -m spacy download en_core_web_lg
nlp = spacy.load('en_core_web_lg')


def match_by_title(candidates: List[Paper], submitting_authors: List[List[str]], submitted_title: str, auth_threshold: float = 0.50, title_threshold: float = 0.85) -> Tuple[Paper, bool]:
    """Given a list of candidate articles, find the one that has the highest similartiy score for the title.
    Validates the match to satisfy sufficient author overlap as well.

    Args:
        candidates (List[Paper]): the list of candidate submissions.
        submitted_title (str): the title of the submitted paper we are trying to match.
        threshold (float): the threshold above which the similartiy score between titles should be.

    Returns:
        (Article): the best retrieved article.
        (bool): whether the similarity score is above threshold and the match successful
    """
    match, success = _match(candidates, submitted_title, max_title_similarity, title_threshold)
    author_overlap_score = overlap_score(flat_unique_set(submitting_authors), len(submitting_authors), flat_unique_set(match.expanded_author_list))
    match.author_overlap_score = author_overlap_score
    validation = author_overlap_score >= auth_threshold
    success = success and validation
    return match, success


def match_by_author(candidates: List[Paper], submitting_authors: List[List[str]], submitted_title: str, auth_threshold: float = 0.50, title_threshold: float = 0.85) -> Tuple[Paper, bool]:
    """Given a list of candidate articles, find the one that has the maximal overlap of author names.
    Validates the match to satisty sufficient title simlilarity.

    Args:
        candidates (List[Paper]): the list of candidate Articles.
        submitting_authors (List[List[str]]): the set of unique author last names.
        threshold (float): the threshold above which the similartiy score between titles should be.

    Returns:
        (Article): the best retrieved article.
        (bool): whether a match could be found
    """
    match, success = _match(candidates, submitting_authors, max_author_overlap, auth_threshold)
    title_similarity_score = similarity(submitted_title, match.title)
    match.title_similarity_score = title_similarity_score
    validation = title_similarity_score >= title_threshold
    success = success and validation
    return match, success


def _match(
    candidates: List[Paper],
    submitted_feature: Union[str, List[List[str]]],
    similarity_funct: Callable,
    threshold: float
) -> Tuple[Paper, bool]:
    """Given a list of candidate articles, finds the one with the best similartiy score.

    Args:
        candidates (List[Paper]): the list of candidate Articles.
        submitted_feature (Union[str, List[List[str]]]): eith the title or the authors of the submission we are trying to match.
        best_similarity_funct (Callable): a function taking the candidates and the submitted feature as args and returning the best matching paper and its score.
        threshold (float): the threshold above which the similartiy score between titles should be.

    Returns:
        (Article): the best retrieved article.
        (bool): whether the similarity score is above threshold and the match successful
    """
    match, score = similarity_funct(candidates, submitted_feature)
    logger.debug(f"best match : '{match.title}' {match.author_list}.  Score {score:.2f} ({similarity_funct.__name__})")
    success = (score >= threshold)
    if not success:
        logger.debug(f"DISCARDED with primary score {score:.2f} < {threshold}")
    return match, success


def max_title_similarity(candidates: List[Paper], title: str = '') -> Tuple[Paper, float]:
    score_list = [similarity(title, Article.title) for Article in candidates]
    idx = np.array(score_list).argmax()
    match = candidates[idx]
    score = score_list[idx]
    match.title_similarity_score = score
    return match, score


def similarity(s1: str, s2: str) -> float:
    n1 = nlp(normalize(s1))
    n2 = nlp(normalize(s2))
    score = n1.similarity(n2)
    return score


def max_author_overlap(candidates: List[Paper], authors: List[List[str]] = [[]]) -> Tuple[Paper, float]:
    num_submitting_authors = len(authors)  # the actual number of submitting authors, not the expanded list
    flattened_unique_submitting_names = flat_unique_set(authors)
    flattened_unique_candidate_names = [flat_unique_set(a.expanded_author_list) for a in candidates]
    overlap_scores = [overlap_score(flattened_unique_submitting_names, num_submitting_authors, names) for names in flattened_unique_candidate_names]
    idx = np.array(overlap_scores).argmax()
    match = candidates[idx]
    score = overlap_scores[idx]
    match.author_overlap_score = score
    return match, score


def overlap_score(s1: Set[str], N: int, s2: Set[str]) -> float:
    # N is the length of the non-expanded list of author
    score = len(s1 & s2) / N
    return score


def self_test():
    Article_1 = Paper(Element('nothing'))
    Article_1.author_list = ['Roguet', 'Nielsen', 'van der Parasite']
    Article_1.expanded_author_list = process_authors(Article_1.author_list)
    Article_1.title = "This is a different title or what!"
    Article_2 = Paper(Element('nothing'))
    Article_2.author_list = ['Nobody', 'Somebody', 'Roguet-Simson']
    Article_2.expanded_author_list = process_authors(Article_1.author_list)
    Article_2.title = "This is my title: or what?"

    by_title = match_by_title([Article_1, Article_2], "This is my title: or what?", [["roguet"], ["jens-nielsen", "jens", "nielsen", "nielsen-jens"]])
    print(by_title)

    by_author = match_by_author([Article_1, Article_2], "This is my title: or what?", [["roguet"], ["jens-nielsen", "jens", "nielsen", "nielsen-jens"], ["parasite"]])
    print(by_author)


if __name__ == "__main__":
    self_test()
