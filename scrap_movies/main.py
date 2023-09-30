import os

import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import radiolist_dialog
from rich import print

from modules.torrent_search import TorrentSearch, TypeQuery
from scrap_movies.utils import (
    GoogleSuggestionCompleter,
    open_magnet_link,
)

import sys

CATEGORY = sys.argv[1] if len(sys.argv) > 1 else "movies"

TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)


def query() -> str:
    session: PromptSession = PromptSession(completer=GoogleSuggestionCompleter())

    text = session.prompt("Search for: ")

    print(f"Your Query: {text}")
    return text


def main():
    text = query()
    # text = "rrr"
    ts = TorrentSearch(category=CATEGORY)

    ts.search(text)
    x = []
    with open("x.json", "w") as f:
        for i in ts.search_results:
            a = i.__dict__
            a["id"] = i.__hash__()
            x.append(a)
        import json

        f.write(json.dumps(x))

    sorted_results: list[TypeQuery] = ts.sort(  # type: ignore
        text,
        obj_arg="title",
        min_seeds=5,
        min_peers=5,
        # ratio=0.01,
        # strict=False,
    )[0:20]

    if len(sorted_results) == 0:
        print("No results found")
        return

    values = [(i, f"{i.seeds} - {i.peers} - {i._title_clean}") for i in sorted_results]

    selected = radiolist_dialog(
        title=f"Torrents for: '{text}'",
        text="Which torrent do you want to download",
        values=values,
    ).run()

    if not selected:
        return

    torrents = ts.describe(selected)

    if isinstance(torrents, list) and len(torrents) > 1:
        torrent = radiolist_dialog(
            title="Torrents",
            text="Which torrent do you want to download",
            values=[(i, i.quality) for i in torrents],
        ).run()

        if torrent == None:
            return
    else:
        torrent = torrents[0]

    if torrent.is_magent:
        print(f"[green]Opening magnet link for : {torrent.title}[/green]")
        open_magnet_link(torrent.url)
    else:
        with open(f"{TMP_DIR}/{torrent.title.replace(' ','-')}.torrent", "wb") as f:
            d = requests.get(torrent.url).content
            print(f"Saved torrent: {f.name}")
            f.write(d)


if __name__ == "__main__":
    main()
