#!/usr/bin/env python3

import json
import sys


INPUT = "petete_articles_bbox.json"


def block_words(block):
    return sum(
        len(line["words"])
        for line in block["lines"]
    )


def block_lines(block):
    return len(block["lines"])


def print_page(article, page):

    blocks = page["blocks"]

    print("=" * 90)
    print(
        f"ARTICLE {article['article_id']}: "
        f"{article['title']}"
    )
    print(
        f"PDF PAGE {page['pdf_page']}   "
        f"{page['width']:.0f} x {page['height']:.0f}"
    )
    print(
        f"Blocks: {len(blocks)}"
    )
    print("=" * 90)
    print()

    # Sort by horizontal position.
    blocks_sorted = sorted(
        enumerate(blocks, start=1),
        key=lambda item: (
            item[1]["x0"],
            item[1]["y0"]
        )
    )

    print(
        f"{'ID':>3} "
        f"{'X0':>5} "
        f"{'X1':>5} "
        f"{'WIDTH':>6} "
        f"{'Y0':>5} "
        f"{'Y1':>5} "
        f"{'LINES':>5} "
        f"{'WORDS':>5}"
    )

    print("-" * 90)

    for block_id, block in blocks_sorted:

        width = (
            block["x1"]
            - block["x0"]
        )

        print(
            f"{block_id:3d} "
            f"{block['x0']:5.0f} "
            f"{block['x1']:5.0f} "
            f"{width:6.0f} "
            f"{block['y0']:5.0f} "
            f"{block['y1']:5.0f} "
            f"{block_lines(block):5d} "
            f"{block_words(block):5d}"
        )

    print()

    # --------------------------------------------------------------
    # Rough horizontal occupancy map
    # --------------------------------------------------------------

    print("HORIZONTAL MAP")
    print()

    width = page["width"]
    scale = 80

    for block_id, block in blocks_sorted:

        start = int(
            block["x0"] / width * scale
        )

        end = int(
            block["x1"] / width * scale
        )

        start = max(0, min(scale - 1, start))
        end = max(start + 1, min(scale, end))

        line = [" "] * scale

        for i in range(start, end):
            line[i] = "#"

        visual = "".join(line)

        print(
            f"{block_id:02d} |{visual}|"
        )

    print()

    # --------------------------------------------------------------
    # X boundaries
    # --------------------------------------------------------------

    print("X BOUNDARIES")
    print()

    boundaries = []

    for _, block in blocks_sorted:

        boundaries.append(block["x0"])
        boundaries.append(block["x1"])

    boundaries.sort()

    for x in boundaries:

        print(
            f"{x:7.1f}",
            end=" "
        )

    print()
    print()


def find_page(articles, pdf_page):

    for article in articles:

        for page in article["pages"]:

            if page["pdf_page"] == pdf_page:

                return article, page

    return None, None


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python3 inspect_columns.py PDF_PAGE"
        )

        print(
            "Example:"
        )

        print(
            "  python3 inspect_columns.py 11"
        )

        raise SystemExit(1)

    try:
        pdf_page = int(sys.argv[1])

    except ValueError:

        raise SystemExit(
            "PDF page must be an integer."
        )

    with open(INPUT, encoding="utf-8") as f:
        articles = json.load(f)

    article, page = find_page(
        articles,
        pdf_page
    )

    if page is None:

        raise SystemExit(
            f"PDF page {pdf_page} not found."
        )

    print_page(
        article,
        page
    )


if __name__ == "__main__":
    main()
