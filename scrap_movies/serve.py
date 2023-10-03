import streamlit as st
import streamlit.components.v1 as components
from modules.torrent_search import TorrentSearch, sort_by_seeds_and_peers
from streamlit_searchbox import st_searchbox

from scrap_movies.data import TypeQuery
from scrap_movies.utils import get_google_suggestions, log

st.set_page_config(layout="wide", page_title="Torrent Hunt 🦊", page_icon="🐌")


def search(searchterm: str) -> list:
    return get_google_suggestions(searchterm) if searchterm else []


"""Search for a **Movie** 🎥 or **TV** show 📺 to Download"""
sr_col1, sr_col2 = st.columns([5, 1])
with sr_col1:
    selected_value = st_searchbox(
        search,
        key="wiki_searchbox",
    )


# with sr_col2:
#     search_button = st.button("Search")

show_all = st.checkbox("Show all results")

ts = TorrentSearch(
    category=st.radio("**Select category**", ["Movie", "TV"], horizontal=True).lower()
)


def highlight_words(text: str, words: list[str]) -> str:
    text_words = text.split(" ")
    for word in words:
        for l in range(len(text_words)):
            tw_title = text_words[l].title()
            w_title = word.title()
            if tw_title == w_title:
                text_words[
                    l
                ] = f'<span style="color:#cc7f27;font-weight: bold">{w_title}</span>'
            elif text_words[l] == word:
                text_words[
                    l
                ] = f'<span style="color:#cc7f27;font-weight: bold">{word}</span>'

    return " ".join(text_words)


if search_result := selected_value:
    with st.spinner("Wait for it... ⏳"):
        results_all = ts.search(selected_value)
        st.write(
            f"Results for: **{selected_value}** - Total results: {len(ts.search_results)}"
        )

        col_ratios = (1, 10, 1, 2, 2)
        col0, col1, col2, col3, col4 = st.columns(col_ratios)
        col0.write("<b>No.</b>", unsafe_allow_html=True)
        col1.write("<b>Title</b>", unsafe_allow_html=True)
        col2.write("<b>📦</b>", unsafe_allow_html=True)
        col3.write("<b>🌱 / 🐌</b>", unsafe_allow_html=True)
        col4.write("<b>Magnet</b>", unsafe_allow_html=True)

        results: list[TypeQuery] = ts.sort(
            selected_value,
            obj_arg="title",
        )

        if show_all:
            results = results_all
        else:
            # results = results[:15]
            results = sort_by_seeds_and_peers(results[:15])

        for c, i in enumerate(results):
            _d = st.container()
            r0, r1, r2, r3, r4 = _d.columns(col_ratios)
            log.debug(f"Title {i.title}")
            r0.write(
                f'<span style="color:#f59542;font-weight: bold">{c+1}.</span>',
                unsafe_allow_html=True,
            )
            title = highlight_words(i._title_clean, selected_value.split(" "))
            if "#YTS" in i.title:
                r1.write(
                    f'<b style="color:#83fcd6">{title} ✅</b>',
                    unsafe_allow_html=True,
                )
            else:
                r1.write(
                    f'<b style="color:#f5cc5d">{title.replace("5 1","5.1")}</b>',
                    unsafe_allow_html=True,
                )

            if isinstance(i.size, str) and i.size != "":
                r2.write(
                    f'<span style="color:#c795fc">{i.size}</span>',
                    unsafe_allow_html=True,
                )
            else:
                r2.text("N/A")

            if isinstance(i.seeds, str) and i.seeds != "":
                r3.write(
                    f'<span style="color:#95fc9e">{i.seeds}/{i.peers}</span>',
                    unsafe_allow_html=True,
                )
            else:
                r3.text("N/A")

            _d.write("\n")
            if r4.button("Open", key=i.title, type="primary"):
                data = ts.describe(i)
                log.info("Opening: magnet ")
                components.html(
                    f"""
                    <script>
                        console.log("{data[0].url}");
                        window.open("{data[0].url}", "_blank");
                    </script>
                    """,
                    height=0,
                    width=0
                    # , unsafe_allow_html=True
                )
            # webbrowser.open(data[0].url)
