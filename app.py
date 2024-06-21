# Copyright (c) 2024 LOLML GmbH (https://lolml.com/), Julian Wergieluk, George Whelan
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from aiewf import (
    AIEWF,
    convert_dataframe_to_csv,
    convert_dataframe_to_excel,
    convert_df_dict_to_excel,
)

load_dotenv()

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

APP_TITLE = "AI Engineers World's Fair 2024 Schedule Browser"
APP_DESC = """
This is an UNOFFICIAL [AI Engineer World's Fair](https://www.ai.engineer/worldsfair) schedule 
browser. The data is fetched from the 
[official website](https://www.ai.engineer/worldsfair/2024/schedule). 
"""
LEGAL_NOTICE = """
### Legal Notice

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
COPYRIGHT_LINE = """
App made by: [Julian Wergieluk](https://www.linkedin.com/in/julian-wergieluk/) + 
[George Whelan](https://www.linkedin.com/in/george-whelan-30582720/) = 
[LOLML GmbH](https://lolml.com/)

The source code is on [GitHub](https://github.com/lolml-gmbh/aiewf2024_schedule_browser)
"""
COL_FAV = "fav"
st.set_page_config(page_title=APP_TITLE, page_icon=":rocket:", layout="wide")


@st.cache_resource(show_spinner="Downloading data from ai.engineer ..")
def get_db() -> AIEWF:
    return AIEWF()


def display_df_download_buttons(df: pd.DataFrame, base_name: str, include_index: bool = False):
    col1, col2, _, _ = st.columns(4)
    file_name = f"{base_name}.xlsx"
    col1.download_button(
        label="Download as Excel",
        data=convert_dataframe_to_excel(df, include_index),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    file_name = f"{base_name}.csv"
    col2.download_button(
        label="Download as CSV",
        data=convert_dataframe_to_csv(df, include_index),
        file_name=file_name,
        mime="text/plain",
        key=file_name,
    )


FAV_EVENTS_FILE = "fav_events.txt"


class FavEvents:
    def __init__(self):
        self.event_ids: set[str] = set()
        self.modified = False
        self.load()

    def add(self, event_id: str) -> None:
        self.event_ids.add(event_id)
        self.modified = True

    def remove(self, event_id: str) -> None:
        self.event_ids.remove(event_id)
        self.modified = True

    def save(self) -> None:
        if not self.modified:
            return
        with open(FAV_EVENTS_FILE, "w") as f:
            f.write("\n".join(self.event_ids))

    def load(self) -> None:
        try:
            with open(FAV_EVENTS_FILE) as f:
                self.event_ids = set(f.read().splitlines())
        except FileNotFoundError:
            pass


def main() -> None:
    st.title(APP_TITLE)
    st.logo("lolml.png", link="https://lolml.com/")
    st.markdown(APP_DESC)

    enable_fav_events = bool(os.getenv("ENABLE_FAV_EVENTS", False))
    db = get_db()
    if st.session_state.get("event_df", None) is None:
        st.session_state.event_df = db.event_df.copy()
        event_df = st.session_state.event_df
        if enable_fav_events:
            event_df.insert(loc=0, column="fav", value=False)
            event_df[COL_FAV] = False
            st.session_state.fav_events = FavEvents()
            fav_events = st.session_state.fav_events
            event_df.loc[event_df["title"].isin(fav_events.event_ids), COL_FAV] = True

    event_df = st.session_state.event_df
    selected_tracks = st.sidebar.multiselect("Track", db.tracks)
    selected_dates = st.sidebar.multiselect("Date", db.dates)
    selected_rooms = st.sidebar.multiselect("Room", db.event_rooms)
    selected_companies = st.sidebar.multiselect("Company", db.companies)
    st.sidebar.caption(
        "Empty filter will select all available data. Multiple selections are supported."
    )

    st.header("Events")
    presenter_df = db.presenter_df
    company_df = db.company_df
    event_base_name = "event_df"
    if selected_tracks:
        event_df = event_df[event_df["trackName"].isin(selected_tracks)]
        selected_tracks_str = "-".join(selected_tracks)
        event_base_name += f"_tracks_{selected_tracks_str}"
    if selected_dates:
        event_df = event_df[event_df["date"].isin(selected_dates)]
        selected_dates_str = "-".join([f"{d:%d}" for d in selected_dates])
        event_base_name += f"_dates_{selected_dates_str}"
    if selected_rooms:
        event_df = event_df[event_df["room"].isin(selected_rooms)]
        selected_rooms_str = "-".join(selected_rooms)
        event_base_name += f"_rooms_{selected_rooms_str}"
    if selected_companies:
        event_df = event_df[event_df["company"].isin(selected_companies)]
        presenter_df = presenter_df[presenter_df["company"].isin(selected_companies)]
        company_df = company_df[company_df["name"].isin(selected_companies)]
        selected_companies_str = "-".join(selected_companies)
        event_base_name += f"_companies_{selected_companies_str}"

    column_config = {
        "link": st.column_config.LinkColumn("link"),
        "socialLinks": st.column_config.LinkColumn("socialLinks"),
    }
    if event_df.empty:
        st.warning("No data found with the selected filters")
    else:
        if enable_fav_events:
            non_editable_cols = list(event_df.columns)
            non_editable_cols.remove(COL_FAV)
            st.data_editor(
                event_df,
                hide_index=True,
                use_container_width=True,
                column_config=column_config,
                disabled=non_editable_cols,
            )
            fav_events = st.session_state.fav_events
            fav_event_titles = event_df[event_df[COL_FAV]]["title"].tolist()
            for fav_title in fav_event_titles:
                fav_events.add(fav_title)
            if fav_events.modified:
                fav_events.save()
        else:
            st.dataframe(
                event_df, hide_index=True, use_container_width=True, column_config=column_config
            )

        display_df_download_buttons(event_df, event_base_name)

    if bool(os.getenv("SHOW_PRESENTERS", False)):
        st.header("Presenters")
        if presenter_df.empty:
            st.warning("No data found with the selected filters")
        else:
            st.dataframe(
                presenter_df, hide_index=True, use_container_width=True, column_config=column_config
            )

    st.header("Companies")
    if company_df.empty:
        st.warning("No data found with the selected filters")
    else:
        st.dataframe(
            company_df, hide_index=True, use_container_width=True, column_config=column_config
        )

    df_dict = {"events": db.event_df, "presenters": db.presenter_df, "companies": db.company_df}
    now_str = pd.Timestamp.now().strftime("%Y-%m-%d-%H-%M-%S")
    st.download_button(
        label="Download all data as Excel",
        data=convert_df_dict_to_excel(df_dict),
        file_name=f"{now_str}-aiewf_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.caption("(Filters are not applied)")

    st.markdown(COPYRIGHT_LINE)
    st.caption(LEGAL_NOTICE)


if __name__ == "__main__":
    main()
