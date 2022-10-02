import sys

from bs4 import BeautifulSoup
import requests


class CardPage:
    def __init__(self, index):
        response = requests.request("GET", f"https://netrunnerdb.com/en/card/{index}")
        self.soup = BeautifulSoup(response.content, "html.parser")

    def printings(self):
        tables = self.soup.find_all("div", class_="panel-body")
        printings_table = next(filter(has_printings, tables))
        return [tag.text.strip() for tag in printings_table.find_all("a")]

    def title(self):
        title = self.soup.find("span", class_="card-title").text
        title = title.replace("♦", "")
        return title.strip()

    def card_type(self):
        tag = self.soup.find("div", class_="card-type").find("strong")
        return tag.text.replace(":", "").lower()

    def is_identity(self):
        return self.card_type() == "identity"


def has_printings(tag):
    if thead := tag.find("thead"):
        return "printings" in thead.text.lower()
    else:
        return False


def get_pack_card_index(pack_code):
    """Get card indexes contained in the pack

    Parameters
    ----------
    pack_code : str
        Pack code

    Returns
    -------
    list of str
        Card indexes
    """
    response = requests.request("GET", f"https://netrunnerdb.com/en/set/{pack_code}")
    soup = BeautifulSoup(response.content, "html.parser")
    cards = soup.find_all("a", class_="card")
    return [card["data-index"] for card in cards]


def get_pack_data(pack_code):
    response = requests.request("GET", f"https://netrunnerdb.com/api/2.0/public/pack/{pack_code}")
    try:
        return response.json()["data"][0]
    except IndexError as exc:
        raise ValueError(f"no pack found with code '{pack_code}'") from exc


def get_pack_duplicates(pack_code):
    pack_data = get_pack_data(pack_code)
    pack_name = pack_data["name"]
    pack_name_set = {pack_name}
    card_indexes = get_pack_card_index(pack_code)

    duplicates = {}

    for index in card_indexes:
        card = CardPage(index)
        printings = card.printings()
        if len(printings) > 1:
            extra = set(printings) - pack_name_set
            duplicates[card.title()] = {
                "extra": extra,
                "is_id": card.is_identity(),
                "side": get_card_data(index)["side_code"]
            }

    return duplicates


def get_card_data(index):
    response = requests.request("GET", f"https://netrunnerdb.com/api/2.0/public/card/{index}")
    return response.json()["data"][0]


def print_pack_duplicates(pack_code):
    duplicates = get_pack_duplicates(pack_code)
    for title, data in sorted(duplicates.items(), key=lambda i: i[1]["side"]):
        if data["is_id"]:
            print(f"{title} (ID) - {data['side']}")
        else:
            print(f"{title} - {data['side']}")

        for extra in data["extra"]:
            print(f"    {extra}")
        print()


if __name__ == "__main__" and len(sys.argv) > 1:
    print_pack_duplicates(sys.argv[1])
