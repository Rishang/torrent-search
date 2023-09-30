import re
import urllib.parse


from bs4 import BeautifulSoup
from lxml.etree import _Element

from scrap_movies.data import ModelTorrent, TypeQuery, TypeTorrent
from scrap_movies.utils import log

"""
YTS sources
"""

sources = {
    "yts": "https://yts.mx",  # www.yts.nz
    "ytsmovie": "https://ytstvmovies.me",
    "1337x": "https://1337x.to",
    "kickass": "https://kattracker.com",
    "piratebay": "https://thepiratebay0.org",
    "torrentdownload": "https://www.torrentdownload.info",
}


class YtsMx(ModelTorrent):
    def __init__(self, host=sources["yts"]) -> None:
        super().__init__()
        self.host = host
        self.available_categories["movies"] = "ajax/search"

    def pre_search(self, query: str) -> list[TypeQuery]:
        endpoint = self.__search_url__(query)

        try:
            response = self.request(
                endpoint,
                params={
                    "query": query,
                },
                timeout=20,
            )

            self.search_results = response.json()["data"]
        except KeyError as e:
            log.error(e)
            return []

        data = []
        for i in self.search_results:
            data.append(
                TypeQuery(
                    host=self.host,
                    url=i["url"],
                    title=i["title"] + " " + i["year"] + " #YTS",
                    img=i["img"],
                )
            )
        return data

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        page = self.find_dom_jspath(
            selected.url,
            "div.modal-torrent",
        )

        data = []
        for i in page:
            size = i.select_one("p:nth-child(5)").text
            quality = i.select_one(".modal-quality").text
            magnet_url = i.select_one(".magnet-download").attrs["href"]
            # print(size, quality, magnet_url)

            data.append(
                TypeTorrent(
                    title=selected.title,
                    url=magnet_url,
                    size_bytes=size,
                    # date_uploaded=i["date_uploaded"],
                    quality=quality,
                    is_magent=True,
                )
            )
        return data


class YtsMovie(ModelTorrent):
    def __init__(self, host=sources["ytsmovie"]) -> None:
        super().__init__()
        self.host = host
        self.available_categories["movies"] = "?s={query}"
        self.available_categories["tv"] = "?s={query}"

    def pre_search(self, query: str) -> list[TypeQuery]:
        search_result: list[_Element] = self.find_dom_xpath(
            url=self.__search_url__(query),
            xpath='//*[@id="main"]/div/div[2]/div/div[2]',
        )

        if len(search_result) == 0:
            return []

        data = []
        for c, i in enumerate(search_result[0]):
            try:
                # find a href
                _a = i[0]
                url = _a.attrib["href"]

                try:
                    title = _a.attrib.get("oldtitle") + " - " + _a[0].text + " #YTS"
                except:
                    title = _a.attrib.get("oldtitle")

                data.append(TypeQuery(host=self.host, url=url, title=title))

            except IndexError:
                continue

        return data

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        super().describe(selected)
        dom = self.get_dom(selected.url)

        container: list[_Element] = dom.xpath('//*[@id="lnk list-downloads"]/div[2]')[0]
        title = selected.title

        data = [
            TypeTorrent(
                title=title,
                size_bytes="",
                url=i.attrib["href"],
                quality=i[2].text,
                is_magent=False,
            )
            for i in container
            if i.attrib.get("href")
        ]
        return data


"""
Non - YTS sources
"""


class X1337(ModelTorrent):
    def __init__(self, host=sources["1337x"]) -> None:
        super().__init__()
        self.host = host
        self.available_categories["movies"] = "category-search/{query}/Movies/1/"
        self.available_categories["tv"] = "category-search/{query}/TV/1/"

    def pre_search(self, query: str) -> list[TypeQuery]:
        search_result: list[_Element] = self.find_dom_xpath(
            url=self.__search_url__(query),
            xpath="/html/body/main/div/div/div/div[2]/div[1]/table/tbody",
        )

        if len(search_result) == 0:
            log.error(f"IndexError: {query} | {search_result}")
            return []

        data = []
        for i in search_result[0]:
            title = i.xpath("td[1]/a[2]")[0].text

            url = urllib.parse.urljoin(
                self.host, i.xpath("td[1]/a[2]")[0].attrib["href"]
            )
            seeds = i.xpath("td[2]")[0].text
            peers = i.xpath("td[3]")[0].text
            size = i.xpath("td[5]")[0].text
            data.append(
                TypeQuery(self.host, url, title, size=size, seeds=seeds, peers=peers)
            )

        return data

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        dom = self.get_dom(selected.url)
        size = dom.xpath("/html/body/main/div/div/div/div[2]/div[1]/ul[2]/li[4]/span")[
            0
        ].text
        magnet_url = dom.xpath(
            "/html/body/main/div/div/div/div[2]/div[1]/ul[1]/li[1]/a"
        )[0].attrib["href"]

        return [
            TypeTorrent(
                title=selected.title,
                url=magnet_url,
                size_bytes=size,
                is_magent=True,
            )
        ]


class KickAss(ModelTorrent):
    def __init__(self, host=sources["kickass"]) -> None:
        super().__init__()
        self.host = host
        self.available_categories["movies"] = "usearch/{query}%20category:movies/"
        self.available_categories["tv"] = "usearch/{query}%20category:tv/"

    def pre_search(self, query: str) -> list[TypeQuery]:
        search_results = self.find_dom_xpath(
            url=self.__search_url__(query),
            xpath='//*[@id="torrent_latest_torrents"]',
        )

        if not len(search_results) > 0:
            log.error(f"IndexError: {query}")
            return []

        data = []
        for i in search_results:
            a = i.xpath("td[1]/div[2]/div/a")
            title = a[0].text
            url = a[0].attrib["href"]
            size = i.xpath("td[2]")[0].text
            seeds = i.xpath("td[4]")[0].text
            peers = i.xpath("td[5]")[0].text
            magnet_url = i.xpath("td[1]/div[1]/a[2]")[0].attrib["href"]
            obj = TypeQuery(
                host=self.host,
                url=url,
                title=title,
                size=size,
                seeds=seeds,
                peers=peers,
            )
            obj.magnet_url = magnet_url  # type: ignore

            data.append(obj)

        # d=sort_by_match(query, queries=data, obj_arg='title', ratio=0.3)
        # data might get grabage so only taking 5 outputs
        return data[:40]

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        super().describe(selected)

        magnet_url = selected.magnet_url  # type: ignore
        return [
            TypeTorrent(
                title=selected.title,
                url=magnet_url,
                size_bytes=selected.size,
                is_magent=True,
            )
        ]


class TDownloadInfo(ModelTorrent):
    def __init__(self, host=sources["torrentdownload"]) -> None:
        super().__init__()
        self.host = host
        self.available_categories["movies"] = "feed?q={query}"
        self.available_categories["tv"] = "feed?q={query}"

    def pre_search(self, query: str) -> list[TypeQuery]:
        # using RSS feed for query
        response = self.request(url=self.__search_url__(query))
        soup = BeautifulSoup(response.content, "lxml-xml")
        items = soup.find_all("item")
        data = []

        for item in items:
            title = item.find("title").text
            url = item.find("link").text
            description = item.find("description").text
            size = description.split("Seeds")[0].replace("Size:", "")
            seeds = description.split("Peers")[0].split("Seeds:")[1].replace(",", "")
            data.append(
                TypeQuery(host=self.host, url=url, title=title, size=size, seeds=seeds)
            )

        return data

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        webpage = self.request(selected.url)
        soup = BeautifulSoup(webpage.content, "html.parser")
        download_bocks = soup.find_all("a", attrs={"class": "tosa"})

        for i in download_bocks:
            d_link: str = i.attrs["href"].strip()
            if d_link.startswith("magnet:?"):
                return [
                    TypeTorrent(
                        title=selected.title,
                        url=d_link,
                        size_bytes=selected.size,
                        is_magent=True,
                    )
                ]
        return []


class PirateBay(ModelTorrent):
    def __init__(self, host=sources["piratebay"]) -> None:
        super().__init__()
        self.host = host
        self.available_categories["movies"] = "search/{query}"
        self.available_categories["tv"] = "search/{query}"

    def pre_search(self, query: str) -> list[TypeQuery]:
        search_results = self.find_dom_jspath(self.__search_url__(query), "tr")[1:]

        data = []
        for item in search_results:
            try:
                category = " - ".join(
                    [i.text.strip() for i in item.select("td.vertTh > center > a")]
                ).lower()
                _a = item.select_one("td div a")
                title = _a.text
            except:
                continue
            url = _a.attrs["href"]
            magnet_url = item.select_one("td:nth-child(2) > a:nth-child(2)").attrs[
                "href"
            ]
            seeds = item.select_one("td:nth-child(3)").text
            peers = item.select_one("td:nth-child(4)").text

            _detail = item.select_one("td:nth-child(2) > font").text
            size = _detail.split("Size")[1].split(",")[0].replace("\xa0", " ")

            obj = TypeQuery(
                host=self.host,
                url=url,
                title=title,
                size=size,
                seeds=seeds,
                peers=peers,
            )
            obj.magnet_url = magnet_url  # type: ignore

            if (
                category in ["video - hd - movies", "video - movies"]
                and self.category == "movies"
            ):
                data.append(obj)
                # print(category, title)
            elif (
                category in ["video - hd - tv shows", "video - tv shows"]
                and self.category == "tv"
            ):
                # print(category, title)
                data.append(obj)

        return data

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        return [
            TypeTorrent(
                title=selected.title,
                url=selected.magnet_url,  # type: ignore
                size_bytes=selected.size,
                is_magent=True,
            )
        ]
