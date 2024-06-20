# Copyright (c) 2024 LOLML GmbH (https://lolml.com/), Julian Wergieluk, George Whelan
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from aiewf import AIEWF, convert_dataframe_to_csv, convert_dataframe_to_excel

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
"""
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


def main() -> None:
    st.title(APP_TITLE)
    st.logo("lolml.png", link="https://lolml.com/")
    st.markdown(APP_DESC)

    db = get_db()

    # st.header("Stats")
    # col0, col1 = st.columns(2)
    # col0.metric("Events", db.num_events)
    # col1.metric("Presenters", db.num_presenters)

    st.subheader("Filters")

    st.caption("Empty filter will select all avaiable data")

    selected_tracks = st.multiselect("Track", db.tracks)
    selected_dates = st.multiselect("Date", db.dates)
    selected_rooms = st.multiselect("Room", db.event_rooms)
    selected_companies = st.multiselect("Company", db.companies)

    st.subheader("Event data")

    event_df = db.event_df
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
        selected_companies_str = "-".join(selected_companies)
        event_base_name += f"_companies_{selected_companies_str}"

    if event_df.empty:
        st.warning("No data found with the selected filters")
    else:
        st.dataframe(event_df, hide_index=True, use_container_width=True)
        display_df_download_buttons(event_df, event_base_name)

    show_presenters = bool(os.getenv("SHOW_PRESENTERS", False))
    show_companies = bool(os.getenv("SHOW_COMPANIES", False))

    if show_presenters:
        st.header("Presenters")
        st.dataframe(db.presenter_df, hide_index=True, use_container_width=True)

    if show_companies:
        st.header("Companies")
        st.dataframe(db.company_df, hide_index=True, use_container_width=True)

    st.markdown(COPYRIGHT_LINE)
    st.write("Legal Notice")
    st.caption(LEGAL_NOTICE)


if __name__ == "__main__":
    main()
