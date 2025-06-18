import requests
import bs4
import argparse
import json

external = []
unknown = []
fuzzables = []


def extractor(soup, host):
    all_links = list()
    for link in soup.find_all("a", href=True):
        if link["href"].startswith("/"):
            if link["href"] not in all_links:
                all_links.append(host + link["href"])
        elif host in link["href"]:
            if link["href"] not in all_links:
                all_links.append(link["href"])
        elif "http://" in host:
            if (
                "https://" + host.split("http://")[1] in link["href"]
                and link["href"] not in all_links
            ):
                all_links.append(link["href"])
        elif (
            "http" not in link["href"]
            and "www" not in link["href"]
            and len(link["href"]) > 2
            and "#" not in link["href"]
        ):
            if link["href"] not in all_links:
                all_links.append(host + "/" + link["href"])
        elif len(link["href"]) > 6:
            external.append(link["href"])
        else:
            unknown.append(link["href"])
    return all_links + external + unknown


def fuzzable_extract(linklist):
    fuzzables = []
    for link in linklist:
        if "=" in link:
            fuzzables.append(link)
    return fuzzables


def xploit(link, host=None):
    if host is None:
        host = link
    res = requests.get(link, allow_redirects=True)
    soup = bs4.BeautifulSoup(res.text, "lxml")
    return extractor(soup, host)


def level2(linklist, host):
    final_list = list()
    for link in linklist:
        if not link.startswith("http"):
            continue
        for x in xploit(link, host):
            if x not in final_list:
                final_list.append(x)
                # print("Appended", x)
        if link not in final_list:
            final_list.append(link)
    return final_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--url",
        help="root url",
        dest="url",
    )
    parser.add_argument(
        "-d",
        "--deepcrawl",
        help="crawl deaply",
        dest="deepcrawl",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--fuzzable",
        help="extract fuzzable",
        dest="fuzzable",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--external",
        help="extract external",
        dest="external",
        action="store_true",
    )
    args = parser.parse_args()

    if args.url is None:
        return None
    if "http" not in args.url:
        args.url = "http://" + args.url

    results = {}

    if args.deepcrawl:
        links = level2(xploit(args.url), args.url)
    else:
        links = xploit(args.url)

    # Return links if not empty
    if len(links) > 0:
        results["links"] = links

    # Return fuzzable links if requested and not empty
    if args.fuzzable:
        fuzzable_links = fuzzable_extract(links) if len(links) > 0 else []
        if len(fuzzable_links) > 0:
            results["fuzzable"] = fuzzable_links

    # Return external links if requested and not empty
    if args.external:
        if len(external) > 0:
            results["external"] = external

    return results if results else None


if __name__ == "__main__":
    results = main()

    # Output as JSON
    if results:
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps({}))
