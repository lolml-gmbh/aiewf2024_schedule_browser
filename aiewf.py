# Copyright (c) 2024 LOLML GmbH (https://lolml.com/), Julian Wergieluk, George Whelan
import io
import json
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


def fix_social_link(link: str) -> str:
    if not link:
        return ""
    link = str(link).strip()
    if " " in link:
        return link
    if link.startswith("http://") or link.startswith("https://"):
        return link
    return f"https://{link}"


class AIEWF:
    schedule_url = "https://www.ai.engineer/worldsfair/2024/schedule"
    event_base_url = "https://www.ai.engineer/worldsfair/2024/schedule/"

    def __init__(self):
        session = requests.Session()
        response = session.get(self.schedule_url)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "lxml")
        for script_block in soup.find_all("script", id="__NEXT_DATA__"):
            json_str = script_block.text
            break
        else:
            raise ValueError("No data found")

        data = json.loads(json_str)
        try:
            events = data["props"]["pageProps"]["schedule"]["events"]
        except KeyError as e:
            raise ValueError("Data has an unexpected format") from e

        event_cols = [
            "title",
            "trackName",
            "presenters",
            "company",
            "room",
            "since",
            "link",
            "about",
            "till",
            "slug",
        ]
        event_records = []
        self.presenter_dict = {}
        self.company_dict = {}
        for event in events:
            event_data = {k: v for k, v in event.items() if k in event_cols}
            if event_data["slug"]:
                event_data["link"] = self.event_base_url + event_data["slug"]
            del event_data["slug"]
            presenter_names = set()
            presenter_companies = set()
            for presenter in event["presenters"]:
                presenter_data = presenter["attributes"]
                presenter_data["socialLinks"] = fix_social_link(
                    presenter_data.get("socialLinks", "")
                )
                presenter_names.add(presenter_data["name"].strip())
                self.presenter_dict[presenter["id"]] = presenter_data
                company_data = presenter_data["company"]["data"]
                company_id = company_data["id"]
                company_data = company_data["attributes"]
                company_data["socialLinks"] = fix_social_link(company_data.get("socialLinks", ""))
                company_data["link"] = fix_social_link(company_data.get("link", ""))
                presenter_data["company"] = company_data["name"]
                presenter_companies.add(company_data["name"].strip())
                if company_id not in self.company_dict:
                    self.company_dict[company_id] = company_data
                self.presenter_dict[presenter["id"]] = presenter_data
            event_data["presenters"] = ", ".join(presenter_names)
            event_data["company"] = ", ".join(presenter_companies)
            event_records.append(event_data)

        event_cols.remove("slug")
        self.event_df = pd.DataFrame.from_records(event_records, columns=event_cols)
        self.event_df["since"] = pd.to_datetime(self.event_df["since"])
        self.event_df["till"] = pd.to_datetime(self.event_df["till"])
        self.event_df["date"] = self.event_df["since"].dt.date
        self.event_df["room"] = self.event_df["room"].fillna("Unknown")
        self.event_df["presenters"] = self.event_df["presenters"].fillna("NA")
        self.event_df["company"] = self.event_df["company"].fillna("NA")
        self.event_df["about"] = self.event_df["about"].fillna("")
        self.event_df.sort_values(by="since", inplace=True, ascending=True)
        self.presenter_df = pd.DataFrame.from_records(
            list(self.presenter_dict.values()),
            columns=["name", "tagline", "company", "socialLinks", "about"],
        )
        self.presenter_df.fillna("", inplace=True)
        self.company_df = pd.DataFrame.from_records(
            list(self.company_dict.values()), columns=["name", "link", "socialLinks"]
        )
        self.company_df.fillna("", inplace=True)

    @property
    def num_presenters(self) -> int:
        return len(self.presenter_df["name"].unique())

    @property
    def num_events(self) -> int:
        return len(self.event_df)

    @property
    def tracks(self) -> list[str]:
        return sorted(self.event_df["trackName"].unique().tolist())

    @property
    def companies(self) -> list[str]:
        return sorted(self.company_df["name"].unique().tolist())

    @property
    def event_rooms(self) -> list[str]:
        return sorted(self.event_df["room"].unique().tolist())

    @property
    def dates(self) -> list[str]:
        return sorted(self.event_df["date"].unique().tolist())


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
