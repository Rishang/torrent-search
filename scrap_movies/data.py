import re
import time
import urllib.parse
from typing import final

import requests
from lxml import etree
import bs4.element
from bs4 import BeautifulSoup

from scrap_movies.utils import requests_session, clean_query, log

headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en;q=0.9",
    "dnt": "1",
    "sec-ch-ua": '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TypeQuery:
    host: str
    url: str
    title: str
    img: Optional[str] = field(default_factory=str)
    size: Optional[str] = field(default_factory=str)
    seeds: Optional[str] = field(default_factory=str)
    peers: Optional[str] = field(default_factory=str)

    # _ztype: Optional[list] = field(default_factory=list)

    # filter out the ... from the title
    def __eq__(self, __value) -> bool:
        return isinstance(self.title, str) and self.title == __value.title

    def __hash__(self) -> int:
        return hash(self.title)

    def __post_init__(self):
        self.title = self.title.strip()
        self._title_clean = clean_query(self.title).title()

        self.size = self.size.strip()
        self.seeds = self.seeds.strip()
        self.peers = self.peers.strip()

        # if not self.seeds.isnumeric():
        #     self.seeds = ""
        # if not self.peers.isnumeric():
        #     self.peers = ""

        if self.url.startswith("/"):
            self.url = self.host + self.url


@dataclass
class TypeTorrent:
    title: str
    url: str
    size_bytes: str
    date_uploaded: Optional[str] = field(default="")
    quality: Optional[str] = field(default="")
    is_magent: Optional[bool] = field(default=False)

    def __post_init__(self):
        self.size_bytes = self.size_bytes.strip()
        self.date_uploaded = self.date_uploaded.strip()
        self.quality = self.quality.strip()

        if self.is_magent:
            url = re.search(
                r"magnet:\?xt=urn:btih:.*", urllib.parse.unquote(self.url)
            ).group(0)
            self.url = urllib.parse.quote(url, safe=":/?&=")


class ModelTorrent:
    def __init__(self) -> None:
        self.headers = headers
        self.host = ""
        self.selected: TypeQuery | None = None

        self.category = "movie"
        self.available_categories: dict[str, str | None] = {"movie": None, "tv": None}

    def request(self, url, headers=headers, timeout=15, retry=5, params={}):
        for _ in range(retry):
            try:
                response = requests_session.get(
                    url, headers=headers, timeout=timeout, params=params
                )
                return response
            except requests.exceptions.ConnectionError:
                log.error(f"Connection Error: {url}")
                time.sleep(5)
                # return self.request(url=url)
                continue

        # return response

    @final
    def search(self, query: str) -> list[TypeQuery]:
        query = urllib.parse.quote_plus(query)
        result = self.pre_search(query=query)

        if len(result) != 0:
            if not isinstance(result, list):
                raise TypeError(f"Expected list, got {type(result)} instead")
            if not isinstance(result[0], TypeQuery):
                raise TypeError(f"Expected TypeQuery, got {type(result[0])} instead")

        return result

    def pre_search(self, query: str) -> list[TypeQuery]:
        return []

    def __search_url__(self, query):
        if self.available_categories.get(self.category) == None:
            raise Exception(f"Category not found: {self.category}")
        return f"{self.host}/{self.available_categories[self.category].format(query=query)}"

    def get_dom(self, url, _etree: bool = True, parser="html.parser") -> etree._Element:
        webpage = self.request(url, headers=self.headers, timeout=15, retry=10)
        soup = BeautifulSoup(webpage.content, parser)
        if _etree:
            dom = etree.HTML(str(soup))
            return dom
        else:
            return soup

    def find_dom_xpath(self, url, xpath) -> etree._Element:
        dom = self.get_dom(url)
        search_result_xpath = etree.XPath(xpath)
        result = search_result_xpath(dom)
        return result

    def find_dom_jspath(self, url, jspath) -> list[bs4.element.Tag]:
        dom: BeautifulSoup = self.get_dom(url, _etree=False)
        return dom.css.select(jspath)

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        if isinstance(selected, TypeQuery):
            self.selected = selected
        else:
            raise TypeError(f"Expected TypeQuery, got {type(selected)} instead")
        return []
