#!/usr/bin/env python3

import json
import sys


INPUT = "petete_articles_bbox.json"


def classify_x(block, page_width):
    """
    Give a very rough spatial classification.

    This is deliberately descriptive, not an attempt
    to infer document structure.
    """

    center = (block["x0"] + block["x1"]) / 2

    if center < page_width * 0.35:
        return "LEFT"

    if center > page_width * 0.65:
        return "RIGHT"

    return "CENTER"


def block_text(block):
    """
    Reconstruct the OCR text of a block from its lines.

    We do not correct or modify OCR.
    """

    lines = []

    for line in block["lines"]:
        text = " ".join(
            word["text"]
            for word in line["words"]
        )

        text = text.strip()

        if text:
            lines.append(text)

    return "\n".join(lines)


def print_block(number, block, page_width):

    position = classify_x(block, page_width)

    print(
        f"BLOCK {number:02d} "
        f"[{position}] "
        f"bbox=("
        f"{block['x0']:.0f},"
        f"{block['y0']:.0f},"
        f"{block['x1']:.0f},"
        f"{block['y1']:.0f}"
        f") "
        f"lines={len(block['lines'])}"
    )

    print("-" * 70)

    text = block_text(block)

    if text:
        for line in text.splitlines():
            print(f"  {line}")
    else:
        print("  [NO TEXT]")

    print()


def find_page(articles, pdf_page):

    for article in articles:

        for page in article["pages"]:

            if page["pdf_page"] == pdf_page:
                return article, page

    return None, None


def print_page(article, page):

    print("=" * 80)
    print(
        f"ARTICLE {article['article_id']}: "
        f"{article['title']}"
    )
    print(
        f"PDF PAGE {page['pdf_page']}   "
        f"{page['width']:.0f} x {page['height']:.0f}"
    )
    print(
        f"Blocks: {len(page['blocks'])}"
    )
    print("=" * 80)
    print()

    # Sort only for visual inspection.
    # We are NOT modifying the stored data.
    blocks = sorted(
        page["blocks"],
        key=lambda b: (b["y0"], b["x0"])
    )

    for number, block in enumerate(blocks, start=1):

        print_block(
            number,
            block,
            page["width"]
        )


def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python3 inspect_layout.py PDF_PAGE"
        )

        print(
            "Example: python3 inspect_layout.py 11"
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
