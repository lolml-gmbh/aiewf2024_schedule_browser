# Copyright (c) 2024 [LOLML GmbH](https://lolml.com/), Julian Wergieluk, George Whelan
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
Copyright (c) 2024 [LOLML GmbH](https://lolml.com/), Julian Wergieluk, George Whelan
"""
st.set_page_config(page_title=APP_TITLE, page_icon=":euro:")


@st.cache_data()
def get_db() -> AIEWF:
    return AIEWF()


def main() -> None:
    st.title(APP_TITLE)
    st.logo('lolml.png')
    st.markdown(APP_DESC)

    db = get_db()
    st.dataframe(db.event_df)

    st.markdown(COPYRIGHT_LINE)
    st.caption(LEGAL_NOTICE)


if __name__ == "__main__":
    main()
