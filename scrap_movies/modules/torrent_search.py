import sys
import requests
import urllib.parse

sys.path.append("..")

from scrap_movies.utils import threads, sort_by_match
from scrap_movies.data import TypeQuery, TypeTorrent, ModelTorrent
from modules.sources import YtsMx, YtsMovie, X1337, KickAss, TDownloadInfo, PirateBay

from rich import print

banned_terms = (
    "hdcam",
    "hd cam",
    "cam rip",
    "camrip",
    "sd rip",
    "sdrip",
    "dvdrip",
    "dvd rip",
    "hdts",
    "s print",
    "hq cam",
    "hqcam",
    "qrip",
    "qrips",
)


class TorrentSearch:
    def __init__(self, category="movies"):
        _YtsMx = YtsMx()
        _YtsMovie = YtsMovie()
        _X1337 = X1337()
        _KickAss = KickAss()
        _PirateBay = PirateBay()
        _TDownloadInfo = TDownloadInfo()

        self.models = {
            # YTS
            _YtsMx.host: _YtsMx,
            _YtsMovie.host: _YtsMovie,
            # NON YTS
            _X1337.host: _X1337,
            _KickAss.host: _KickAss,
            _PirateBay.host: _PirateBay,
            # _TDownloadInfo.host: _TDownloadInfo,  # download not working
        }

        self.banned_terms = banned_terms

        self.category = category

        self.search_results: list[TypeQuery] = []

    def search(self, text):
        print(11111)

        def task(i):
            try:
                print("searching: ", i)
                model: TorrentSearch = self.models[i]
                model.category = self.category

                r = model.search(text)
                print(i, len(r))
                self.search_results.extend(r)
            except requests.exceptions.ReadTimeout:
                print("timeout: ", i)
                ...
            except requests.exceptions.ConnectionError:
                print("connection error: ", i)
                ...
            except IndexError:
                print("index error: ", i)
                ...
            except Exception as e:
                print(f"error: {e} - {i}")
                ...

        threads(task, data=self.models.keys(), max_workers=10)

        self.search_results = list(set(self.search_results))
        return self.search_results

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        ModelTorrent.describe(self=ModelTorrent, selected=selected)  # type: ignore

        url = selected.url
        host = "https://" + urllib.parse.urlparse(url).hostname
        if host in self.models:
            try:
                self.host = host
                return self.models[host].describe(selected)
            except requests.exceptions.ReadTimeout:
                return []
        else:
            print(host)
            raise ValueError(f"Invalid URL: {url}")

    def sort(
        self,
        query: str,
        obj_arg: str | None = None,
        min_seeds: int = 5,
        min_peers: int = 5,
    ):
        if len(self.search_results) == 0:
            return []

        search_results = [
            i
            for i in self.search_results
            if (
                (i.seeds.isnumeric() and i.peers.isnumeric())
                and int(i.seeds) > min_seeds
                and int(i.peers) > min_peers
            )
            or i.seeds == ""
        ]
        return sort_by_match(query, search_results, obj_arg, self.banned_terms)