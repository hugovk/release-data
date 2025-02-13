import re
import sys
from bs4 import BeautifulSoup
from common import endoflife
from datetime import datetime, timezone
from liquid import Template

"""Fetch versions with their dates from a cgit repository, such as
https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git.

Ideally we would want to use the git repository directly, but cgit repositories
do not support partial clone so we cannot.
"""

METHOD = 'cgit'
# Same as used in Ruby (update.rb)
DEFAULT_TAG_TEMPLATE = (
    "{{major}}{% if minor %}.{{minor}}{% if patch %}.{{patch}}{%if tiny %}.{{tiny}}{%endif%}{%endif%}{%endif%}"
)
DEFAULT_VERSION_REGEX = (
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.?(?P<patch>\d+)?\.?(?P<tiny>\d+)?$"
)


# Parse date with format 2023-05-01 08:32:34 +0900 and convert to UTC
def parse_date(d):
    return (
        datetime.strptime(d, "%Y-%m-%d %H:%M:%S %z")
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%d")
    )


def make_bs_request(url):
    response = endoflife.fetch_url(url + '/refs/tags')
    return BeautifulSoup(response, features="html5lib")


def fetch_releases(url, regex, template):
    releases = {}

    soup = make_bs_request(url)
    l_template = Template(template)

    for table in soup.find_all("table", class_="list"):
        for row in table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) == 4:
                version_text = columns[0].text.strip()
                datetime_td = columns[3].find_next("span")
                datetime_text = datetime_td.attrs["title"] if datetime_td else None
                if datetime_text:
                    matches = re.match(regex.strip(), version_text)
                    if matches:
                        match_data = matches.groupdict()
                        version_string = l_template.render(**match_data)
                        date = parse_date(datetime_text)
                        print(f"{version_string} : {date}")
                        releases[version_string] = date

    return releases


def update_product(product_name, configs):
    versions = {}

    for config in configs:
        t = config.get("template", DEFAULT_TAG_TEMPLATE)
        regex = config.get("regex", DEFAULT_VERSION_REGEX)
        versions = versions | fetch_releases(config[METHOD], regex, t)

    endoflife.write_releases(product_name, versions)


p_filter = sys.argv[1] if len(sys.argv) > 1 else None
for product, configs in endoflife.list_products(METHOD, p_filter).items():
    print(f"::group::{product}")
    update_product(product, configs)
    print("::endgroup::")
