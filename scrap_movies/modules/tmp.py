from sources import TDownloadInfo, X1337, KickAss, YtsMx, PirateBay
from rich import print
from scrap_movies.utils import open_magnet_link

# t = TDownloadInfo()
t = YtsMx()
# t.category = "
x = t.search("ted")
print(len(x))
print(t.describe(x[0]))


# x = t.find_dom_jspath(
#     "https://www.yts.mx/movies/the-social-network-2010",
#     "div.modal-torrent",
# )

# # div:nth-child(1) > p:nth-child(5)"

# for i in x:
#     size = i.select_one("p:nth-child(5)").text
#     quality = i.select_one(".modal-quality").text
#     magnet_url = i.select_one(".magnet-download").attrs["href"]
#     print(size, quality, magnet_url)
