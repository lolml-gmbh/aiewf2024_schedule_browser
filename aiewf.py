# Copyright (c) 2024 [LOLML GmbH](https://lolml.com/), Julian Wergieluk, George Whelan
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup


class AIEWF:
    schedule_url = "https://www.ai.engineer/worldsfair/2024/schedule"

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
        except KeyError:
            raise ValueError("Data has an unexpected format")

        event_cols = [
            "title",
            "trackName",
            "presenters",
            "company",
            "about",
            "room",
            "since",
            "till",
        ]
        event_records = []
        self.presenter_dict = {}
        self.company_dict = {}
        for event in events:
            rec = {k: v for k, v in event.items() if k in event_cols}
            presenter_names = set()
            presenter_companies = set()
            for presenter in event["presenters"]:
                presenter_data = presenter["attributes"]
                presenter_names.add(presenter_data["name"].strip())
                self.presenter_dict[presenter["id"]] = presenter_data
                company_data = presenter_data["company"]["data"]
                company_id = company_data["id"]
                company_data = company_data["attributes"]
                presenter_companies.add(company_data["name"].strip())
                self.company_dict[company_id] = company_data
            rec["presenters"] = ", ".join(presenter_names)
            rec["company"] = ", ".join(presenter_companies)
            event_records.append(rec)

        self.event_df = pd.DataFrame.from_records(event_records, columns=event_cols)
        self.presenter_df = pd.DataFrame.from_records(
            list(self.presenter_dict.values()), columns=["name", "tagline", "about", "socialLinks"]
        )
        self.company_df = pd.DataFrame.from_records(
            list(self.company_dict.values()), columns=["name", "link", "socialLinks"]
        )
