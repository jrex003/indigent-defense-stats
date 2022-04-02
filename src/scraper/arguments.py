import argparse
from datetime import date, timedelta, datetime

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-start_date",
    "-s",
    type=lambda d: datetime.strptime(d, "%Y-%m-%d"),
    default=str(date.today() - timedelta(days=30)),
    help="The day to start scraping, default today - 30 days. YYYY-mm-dd",
)
argparser.add_argument(
    "-end_date",
    "-e",
    type=lambda d: datetime.strptime(d, "%Y-%m-%d"),
    default=str(date.today()),
    help="The day to end scraping, default today. YYYY-mm-dd",
)
argparser.add_argument(
    "-county",
    "-c",
    type=str,
    default="hays",
    help="The name of the county, the main page for their Odyssey install will be grabbed from resources/text_county_data.csv",
)
argparser.add_argument(
    "-ms_wait",
    "-w",
    type=int,
    default=200,
    help="Number of ms to wait between requests.",
)
argparser.add_argument(
    "-judicial_officers",
    "-j",
    nargs="*",
    type=str,
    default=[],
    help="Judicial Officers to scrape. For example, -j 'mr. something' 'Rob, Albert'. By default, it will scrape all JOs.",
)
argparser.add_argument(
    "-location",
    "-l",
    type=str,
    default="All Courts",
    help="'Select a location' select box on the main page. Usually 'All Courts' will work.",
)
argparser.add_argument(
    "-overwrite",
    "-o",
    action="store_true",
    help="Switch to overwrite cached case html, use this when updating your data from a small date range to grab new information.",
)
argparser.add_argument(
    "-log",
    type=str,
    default="INFO",
    help="Set the level to log at.",
)
argparser.description = "Scrape data for list of judicial officers in date range."
args = argparser.parse_args()
