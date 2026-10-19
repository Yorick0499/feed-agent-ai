import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import hashlib
from database import save_article


def rss_sniff():
    url = "https://www.polsatnews.pl/rss/wszystkie.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:157.0) Gecko/20100101 Firefox/157.0"
    }

    try:
        response = requests.get(url=url, headers=headers, timeout=15)
        response.raise_for_status()

    except requests.exceptions.HTTPError as error:
        print(f"Wystąpił błąd HTTP: {error}")
        response = None

    except requests.exceptions.RequestException as error:
        print(f"Błąd sieciowy: {error}")
        response = None

    if response:
        try:
            xml_content = response.content
            root = ET.fromstring(xml_content)

        except ET.ParseError as error:
            print(f"Błąd parsowania: {error}")
            root = None

        if root is not None:
            for item in root.findall(".//item"):
                title = item.find("title")
                desc = item.find("description")
                link = item.find("link")
                pub_date = item.find("pubDate")

                title = title.text if title is not None else "Brak tytułu"
                desc = desc.text if desc is not None else ""
                link = link.text if link is not None else ""
                if pub_date is not None and pub_date.text is not None:
                    pub_date = (
                        datetime.strftime(
                            datetime.strptime(
                                str(pub_date.text), "%a, %d %b %Y %H:%M:%S %z"
                            ),
                            "%d-%m-%Y %H:%M",
                        )
                        if pub_date is not None
                        else ""
                    )
                else:
                    pub_date = ""
                raw_id = (
                    str(title) + "_" + str(desc) + "_" + str(link) + "_" + str(pub_date)
                )
                hash_id = hashlib.md5(raw_id.encode("utf-8")).hexdigest()

                article = {
                    "hash_id": hash_id,
                    "title": title,
                    "description": desc,
                    "link": link,
                    "pub_date": pub_date,
                }

                save_article(article)


if __name__ == "__main__":
    rss_sniff()
    print("Pobieranie RSS zakończone.")
