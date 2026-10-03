#!/usr/bin/env python3

import json
from html.parser import HTMLParser


PAGE_MAP = "petete_page_map.json"
BBOX_FILE = "petete_01_azul_bbox.html"
OUTPUT = "petete_articles_bbox.json"


class BBoxParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.pages = []

        self.current_page = None
        self.current_block = None
        self.current_line = None
        self.current_word = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "page":

            self.current_page = {
                "width": float(attrs["width"]),
                "height": float(attrs["height"]),
                "blocks": [],
            }

        elif tag == "block":

            if self.current_page is None:
                return

            self.current_block = {
                "x0": float(attrs["xmin"]),
                "y0": float(attrs["ymin"]),
                "x1": float(attrs["xmax"]),
                "y1": float(attrs["ymax"]),
                "lines": [],
            }

        elif tag == "line":

            if self.current_block is None:
                return

            self.current_line = {
                "x0": float(attrs["xmin"]),
                "y0": float(attrs["ymin"]),
                "x1": float(attrs["xmax"]),
                "y1": float(attrs["ymax"]),
                "words": [],
            }

        elif tag == "word":

            if self.current_line is None:
                return

            self.current_word = {
                "x0": float(attrs["xmin"]),
                "y0": float(attrs["ymin"]),
                "x1": float(attrs["xmax"]),
                "y1": float(attrs["ymax"]),
                "text": "",
            }

    def handle_data(self, data):

        if self.current_word is not None:
            self.current_word["text"] += data

    def handle_endtag(self, tag):

        if tag == "word":

            if self.current_word is not None:
                self.current_line["words"].append(
                    self.current_word
                )
                self.current_word = None

        elif tag == "line":

            if self.current_line is not None:
                self.current_block["lines"].append(
                    self.current_line
                )
                self.current_line = None

        elif tag == "block":

            if self.current_block is not None:
                self.current_page["blocks"].append(
                    self.current_block
                )
                self.current_block = None

        elif tag == "page":

            if self.current_page is not None:
                self.pages.append(
                    self.current_page
                )
                self.current_page = None


def load_bbox(path):

    parser = BBoxParser()

    with open(path, encoding="utf-8") as f:
        parser.feed(f.read())

    return parser.pages


def main():

    print("Loading page map...")
    with open(PAGE_MAP, encoding="utf-8") as f:
        page_map = json.load(f)

    print(f"Articles : {len(page_map)}")

    print("Loading BBOX...")
    bbox_pages = load_bbox(BBOX_FILE)

    print(f"PDF pages : {len(bbox_pages)}")

    # BBOX pages are stored zero-based in the Python list.
    # PDF page 1 is bbox_pages[0].
    def get_page(pdf_page):
        return bbox_pages[pdf_page - 1]

    result = []

    for article in page_map:

        pdf_start = article["pdf_start"]
        pdf_end = article["pdf_end"]

        pages = []

        for pdf_page in range(pdf_start, pdf_end + 1):

            page = get_page(pdf_page)

            pages.append({
                "pdf_page": pdf_page,
                "width": page["width"],
                "height": page["height"],
                "blocks": page["blocks"],
            })

        result.append({
            "article_id": article["article_id"],
            "title": article["title"],
            "editorial_start": article["editorial_start"],
            "editorial_end": article["editorial_end"],
            "pdf_start": pdf_start,
            "pdf_end": pdf_end,
            "pages": pages,
        })

    # Basic sanity checks

    if len(result) != len(page_map):
        raise SystemExit(
            "ERROR: output article count does not match page map."
        )

    for article in result:

        expected = (
            article["pdf_end"]
            - article["pdf_start"]
            + 1
        )

        actual = len(article["pages"])

        if actual != expected:
            raise SystemExit(
                f"ERROR: article {article['article_id']} "
                f"expected {expected} pages, got {actual}"
            )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("BBOX attachment completed successfully.")
    print(f"Articles : {len(result)}")
    print(
        f"PDF range: "
        f"{result[0]['pdf_start']}–"
        f"{result[-1]['pdf_end']}"
    )
    print(f"Output   : {OUTPUT}")


if __name__ == "__main__":
    main()
