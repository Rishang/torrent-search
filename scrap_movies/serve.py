import streamlit as st
import streamlit.components.v1 as components
from modules.torrent_search import TorrentSearch
from streamlit_searchbox import st_searchbox

from scrap_movies.data import TypeQuery
from scrap_movies.utils import get_google_suggestions

st.set_page_config(layout="wide", page_title="Torrent Hunt 🦊")


def search(searchterm: str) -> list:
    return get_google_suggestions(searchterm) if searchterm else []


"""Search for a **Movie** 🎥 or **TV** show 📺"""
sr_col1, sr_col2 = st.columns([5, 1])
with sr_col1:
    selected_value = st_searchbox(
        search,
        key="wiki_searchbox",
    )


with sr_col2:
    search_button = st.button("Search")

# selected_value = "jailer"

show_all = st.checkbox("Show all results")

ts = TorrentSearch(
    category=st.radio("**Select category**", ["Movies", "TV"], horizontal=True).lower()
)


def highlight_words(text: str, words: list[str]) -> str:
    for word in words:
        text = text.replace(
            word.title(),
            f'<span style="color:#cc7f27;font-weight: bold">{word.title()}</span>',
        )
        text = text.replace(
            word, f'<span style="color:#cc7f27;font-weight: bold">{word}</span>'
        )

    return text


def show_results(results: list[TypeQuery]):
    for c, i in enumerate(results):
        _d = st.container()
        col0, col1, col2, col3, col4 = _d.columns(col_ratios)
        col0.write(
            f'<span style="color:#f59542;font-weight: bold">{c+1}.</span>',
            unsafe_allow_html=True,
        )
        title = highlight_words(i._title_clean, selected_value.split(" "))
        if "#YTS" in i.title:
            col1.write(
                f'<b style="color:#83fcd6">{title} ✅</b>',
                unsafe_allow_html=True,
            )
        else:
            col1.write(
                f'<b style="color:#f5cc5d">{title.replace("5 1","5.1")}</b>',
                unsafe_allow_html=True,
            )

        if isinstance(i.size, str) and i.size != "":
            col2.write(
                f'<span style="color:#c795fc">{i.size}</span>',
                unsafe_allow_html=True,
            )
        else:
            col2.text("N/A")

        if isinstance(i.seeds, str) and i.seeds != "":
            col3.write(
                f'<span style="color:#95fc9e">{i.seeds}/{i.peers}</span>',
                unsafe_allow_html=True,
            )
        else:
            col3.text("N/A")

        _d.write("\n")
        if col4.button("Open", key=i.title, type="primary"):
            st.session_state["item"] = i.url
            data = ts.describe(i)
            # print(data[0].url)
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


if search_button:
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
        show_results(results_all)
    else:
        results = results[:10]
        show_results(results)
