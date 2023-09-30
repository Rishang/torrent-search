import re
import time
import difflib
import platform
import subprocess
import string
from urllib import parse
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

import requests
from rapidfuzz import fuzz
from prompt_toolkit.completion import Completer, Completion
from rich import print as pprint

requests_session = requests.Session()

import logging
import os
from rich.logging import RichHandler


def _logger(flag: str = "", format: str = ""):
    if format == "" or format == None:
        format = "%(levelname)s|%(name)s| %(message)s"

    # message
    logger = logging.getLogger(__name__)

    if os.environ.get(flag) != None:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # # create formatter
    # # add formatter to ch
    # formatter = logging.Formatter(format)
    # ch.setFormatter(formatter)

    # # add ch to logger
    # logger.addHandler(ch)
    handler = RichHandler()
    logger.addHandler(handler)
    return logger


# message
# export LOG_LEVEL=true
log = _logger("LOG_LEVEL")


def timing_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # Get the current time
        result = f(*args, **kwargs)  # Call the function
        end_time = time.perf_counter()  # Get the current time again
        execution_time = end_time - start_time  # Calculate the difference
        pprint(f"[yellow]Execution time: {execution_time:.4f} seconds[/yellow]")
        return result  # Return the result of the function

    return wrapper


# Precompute translation table
translator = str.maketrans(
    string.punctuation + string.whitespace,
    " " * len(string.punctuation + string.whitespace),
)


def clean_query(value: str):
    """Clean up the query string using the precomputed translation table."""
    return " ".join(value.lower().translate(translator).split())


# def ratio(query_words: list, item_words: list):
#     """Calculate the match ratio for a single query."""
#     w_pass = 0


#     for index, word in enumerate(query_words):
#         match_ratio = fuzz.ratio(item_words[index], word) / 100
#         if match_ratio > 0.5:
#             w_pass += 1

#     if w_pass == len(query_words):
#         return True
#     else:
#         return False


# def match_score(
#     input_query: str, query, obj_arg: str = None, banned_terms=[], strict: bool = False
# ):
#     """Calculate the match score for a single query."""
#     query_str = str(getattr(query, obj_arg)) if obj_arg else str(query)
#     query_str = clean_query(query_str)

#     if strict:
#         if not ratio(
#             query_words=input_query.split(" "), item_words=query_str.split(" ")
#         ):
#             return 0.0

#     if any(term in query_str for term in banned_terms):
#         match_ratio = 0.0
#     else:
#         match_ratio = fuzz.ratio(input_query.lower(), query_str) / 100

#     return match_ratio


# @timing_decorator
# def sort_by_match(
#     input_query: str,
#     queries,
#     obj_arg: str | None = None,
#     ratio: float = 0.0,
#     strict: bool = False,
#     banned_terms: tuple = (),
# ):
#     input_query = clean_query(input_query)

#     """Sort a list of queries based on their similarity to a given input query."""
#     # Precompute match scores for each query
#     match_scores = {
#         i: match_score(
#             input_query,
#             query,
#             obj_arg,
#             banned_terms=banned_terms,
#             strict=strict,
#         )
#         for i, query in enumerate(queries)
#     }

#     # Filter out queries that don't meet the specified ratio threshold
#     queries = [query for i, query in enumerate(queries) if match_scores[i] >= ratio]

#     # pprint(queries)
#     # Sort the remaining queries based on their precomputed match scores
#     return sorted(
#         queries, key=lambda query: match_scores[queries.index(query)], reverse=True
#     )


def calculate_relevance(
    item, keywords, obj_arg: str | None = None, banned_terms: tuple = ()
):
    if obj_arg:
        _item = getattr(item, obj_arg)
        item_param = clean_query(_item)
    else:
        item_param = clean_query(item)

    if any(term in item_param for term in banned_terms):
        return 0.0

    keyword_count = sum(
        1
        for keyword in keywords
        if re.search(rf"\b{re.escape(keyword.lower())}\b", item_param)
    )

    return keyword_count


def sort_by_match(
    query: str, items, obj_arg: str | None = None, banned_terms: tuple = ()
):
    keywords = query.split(" ")

    # Create a dictionary to store item-relevance pairs
    item_relevance_dict = {}

    for item in items:
        relevance = calculate_relevance(item, keywords, obj_arg, banned_terms)
        if relevance > 0:
            item_relevance_dict[item] = relevance

    # Sort the items based on relevance (exact word matches)
    sorted_items = sorted(
        item_relevance_dict.keys(),
        key=lambda x: item_relevance_dict[x],
        reverse=True,
    )

    return sorted_items


def get_google_suggestions(query):
    q = requests_session.get(
        f"http://suggestqueries.google.com/complete/search?client=chrome&q={query}"
    ).json()[1]
    return q


def open_magnet_link(magnet_link):
    """Open magnet link in the default torrent client."""
    os_type = platform.system().lower()

    if os_type == "windows":
        # For Windows, assuming the torrent client is qBittorrent
        command = f"start qbittorrent '{magnet_link}'"
    elif os_type == "darwin":
        # For macOS, assuming the torrent client is Transmission
        command = f"open -a Transmission '{magnet_link}'"
    else:
        # For Linux, assuming the torrent client is Deluge
        command = f"xdg-open '{magnet_link}'"

    process = subprocess.Popen(command, shell=True)
    process.communicate()


class GoogleSuggestionCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.text_before_cursor
        if not word:
            return

        suggestions = get_google_suggestions(word)
        for sugg in suggestions:
            yield Completion(sugg, start_position=-len(word))


def threads(funct, data, max_workers=5, return_result: bool = True):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future = executor.map(funct, data)
        if return_result == True:
            for i in future:
                results.append(i)
    return results
