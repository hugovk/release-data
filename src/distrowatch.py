import re
import sys
from bs4 import BeautifulSoup
from common import endoflife
from liquid import Template

METHOD = 'distrowatch'
DEFAULT_TAG_TEMPLATE = (  # Same as used in Ruby (update.rb)
    "{{major}}{% if minor %}.{{minor}}{% if patch %}.{{patch}}{%endif%}{%endif%}"
)


def get_versions_from_headline(regex, headline, template):
    if not isinstance(regex, list):
        regex = [regex]
    for r in regex:
        matches = re.match(r.strip(), headline)
        if matches:
            match_data = matches.groupdict()
            version_string = template.render(**match_data)
            return version_string.split("\n")

    return {}


def fetch_releases(distrowatch_id, regex, template):
    releases = {}
    l_template = Template(template)
    url = f"https://distrowatch.com/index.php?distribution={distrowatch_id}"
    response = endoflife.fetch_url(url)
    soup = BeautifulSoup(response, features="html5lib")
    for table in soup.select("td.News1>table.News"):
        headline = table.select_one("td.NewsHeadline a[href]").get_text().strip()
        date = table.select_one("td.NewsDate").get_text()
        for v in get_versions_from_headline(regex, headline, l_template):
            print(f"{v}: {date}")
            releases[v] = date
    return releases


def update_product(product_name, configs):
    versions = {}

    for config in configs:
        t = config.get("template", DEFAULT_TAG_TEMPLATE)
        if "regex" in config:
            regex = config["regex"]
            versions = versions | fetch_releases(config[METHOD], regex, t)

    endoflife.write_releases(product_name, versions)


p_filter = sys.argv[1] if len(sys.argv) > 1 else None
for product, configs in endoflife.list_products(METHOD, p_filter).items():
    print(f"::group::{product}")
    update_product(product, configs)
    print("::endgroup::")
