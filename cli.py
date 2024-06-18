import click
import pandas as pd

from aiewf import AIEWF

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 25)
pd.set_option("display.width", 250)


@click.group()
def cli():
    """CLI"""


@cli.command("get-schedule")
def cmd_main():
    db = AIEWF()
    pass


if __name__ == "__main__":
    cli()
