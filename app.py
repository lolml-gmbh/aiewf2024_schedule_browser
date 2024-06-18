# Copyright (c) 2024 LOLML GmbH (https://lolml.com/), Julian Wergieluk, George Whelan
import io
import re

import pandas as pd
import streamlit as st

from aiewf import AIEWF

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

APP_TITLE = "AI Engineers World's Fair 2024 Schedule Browser"
APP_DESC = """
This is an UNOFFICIAL AI Engineer World's Fair schedule browser
"""
LEGAL_NOTICE = """
Legal Notice

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
st.set_page_config(page_title=APP_TITLE, page_icon=":rocket:")


@st.cache_data()
def get_db() -> AIEWF:
    return AIEWF()


def convert_dataframe_to_csv(df: pd.DataFrame, include_index: bool = False) -> str:
    buffer = io.StringIO()
    df.to_csv(buffer, index=include_index)
    return buffer.getvalue()


def convert_dataframe_to_excel(df: pd.DataFrame, include_index: bool = False) -> bytes:
    buffer = io.BytesIO()
    df.to_excel(buffer, index=include_index)
    return buffer.getvalue()


def clean_excel_sheet_name(input_str, sheet_index: int) -> str:
    cleaned_str = re.sub(r'[\/:*?"<>|]', "_", input_str)
    cleaned_str = re.sub(r'[\'"]', "", cleaned_str)
    cleaned_str = cleaned_str.strip()

    if len(cleaned_str) == 0:
        cleaned_str = f"Sheet{sheet_index}"
    elif len(cleaned_str) > 31:
        cleaned_str = cleaned_str[:31]

    return cleaned_str


def convert_df_dict_to_excel(dfs: dict[str, pd.DataFrame], adjust_col_width: bool = False) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        for i, (sheet_name, df) in enumerate(dfs.items()):
            sheet_name = clean_excel_sheet_name(sheet_name, i)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            if not adjust_col_width:
                continue
            worksheet = writer.sheets[sheet_name]
            for col_index, col in enumerate(df):
                max_len = (
                    max(
                        (
                            df[col].astype(str).map(len).max(),  # len of largest item
                            len(str(df[col].name)),  # len of column name/header
                        )
                    )
                    + 1
                )  # adding a little extra space
                worksheet.set_column(col_index, col_index, max_len)  # set column width
    return buffer.getvalue()


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

    st.header("Events")

    col0, col1 = st.columns(2)
    col0.metric("Events", db.num_events)
    col1.metric("Presenters", db.num_presenters)
    st.dataframe(db.event_df)
    display_df_download_buttons(db.event_df, "event_df")

    st.markdown(COPYRIGHT_LINE)
    st.caption(LEGAL_NOTICE)


if __name__ == "__main__":
    main()
