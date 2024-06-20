from aiewf import AIEWF, convert_df_dict_to_excel


def dump_data(output_path: str = "aiewf_schedule.xlsx"):
    db = AIEWF()

    d = {"events": db.event_df, "presenters": db.presenter_df, "companies": db.company_df}
    buffer = convert_df_dict_to_excel(d)
    with open(output_path, "wb") as f:
        f.write(buffer)


if __name__ == "__main__":
    dump_data()
