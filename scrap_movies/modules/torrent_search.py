import requests
import urllib.parse

from scrap_movies.utils import threads, sort_by_match, log
from scrap_movies.data import TypeQuery, TypeTorrent, ModelTorrent
from modules.sources import YtsMx, YtsMovie, X1337, KickAss, TDownloadInfo, PirateBay

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
    def __init__(self, category="movie"):
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
            _TDownloadInfo.host: _TDownloadInfo,  # download not working
        }

        self.banned_terms = banned_terms

        self.category = category

        self.search_results: list[TypeQuery] = []
        self.ignore_query_terms = (
            "cast",
            "casts",
            "review",
            "reviews",
            "watch online",
            "watch online free",
            "imdb",
            "download",
        )

    def filter_query(self, query: str) -> str:
        """Remove unwanted terms from query"""
        for i in self.ignore_query_terms:
            query = query.replace(i, "")
        return query

    def search(self, text):
        def task(i):
            try:
                log.info(f"searching: {i}")
                model: TorrentSearch = self.models[i]
                model.category = self.category

                r = model.search(text)
                log.info(f"results: {i}, {len(r)}")
                self.search_results.extend(r)
            except requests.exceptions.ReadTimeout:
                log.error(f"timeout: {i}")
                ...
            except requests.exceptions.ConnectionError:
                log.error(f"connection error: {i}")
                ...
            except IndexError:
                log.error(f"index error: {i}")
                ...
            except Exception as e:
                log.error(f"error: {e} - {i}")
                ...

        threads(task, data=self.models.keys(), max_workers=10)

        self.search_results = list(set(self.search_results))
        return self.search_results

    def describe(self, selected: TypeQuery) -> list[TypeTorrent]:
        ModelTorrent.describe(self=ModelTorrent, selected=selected)  # type: ignore
        log.info(f"describe: {selected}")

        url = selected.url
        host = "https://" + urllib.parse.urlparse(url).hostname
        if host in self.models:
            try:
                self.host = host
                return self.models[host].describe(selected)
            except requests.exceptions.ReadTimeout:
                return []
        else:
            log.debug(host)
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
        matches: list[TypeQuery] = sort_by_match(
            query, search_results, obj_arg, self.banned_terms
        )

        return matches


# sort by seeds and peers
def sort_by_seeds_and_peers(matches: list[TypeQuery]):
    d = []
    n = []

    for i in matches:
        if i.seeds.isnumeric() and i.peers.isnumeric():
            d.append(i)
        elif "yts" in i._title_clean.lower():
            n.append(i)

    d = sorted(d, key=lambda x: (int(x.seeds), int(x.peers)), reverse=True)
    c = n + d
    # end of sort by seeds and peers
    return c
