#!/usr/bin/env python3

import json
import sys


INPUT = "petete_articles_bbox.json"


def words_from_page(page):
    words = []

    for block in page["blocks"]:
        for line in block["lines"]:
            for word in line["words"]:
                words.append(word)

    return words


def print_article(article):

    print("=" * 80)
    print(f"ARTICLE {article['article_id']}")
    print(article["title"])
    print(
        f"Editorial: {article['editorial_start']}"
        f"–{article['editorial_end']}"
    )
    print(
        f"PDF: {article['pdf_start']}"
        f"–{article['pdf_end']}"
    )
    print("=" * 80)

    for page in article["pages"]:

        words = words_from_page(page)

        print()
        print(
            f"PDF PAGE {page['pdf_page']}  "
            f"{page['width']} x {page['height']}  "
            f"blocks={len(page['blocks'])}  "
            f"words={len(words)}"
        )

        for block_no, block in enumerate(
            page["blocks"], start=1
        ):

            print(
                f"  BLOCK {block_no:02d} "
                f"bbox=("
                f"{block['x0']:.0f},"
                f"{block['y0']:.0f},"
                f"{block['x1']:.0f},"
                f"{block['y1']:.0f}"
                f") "
                f"lines={len(block['lines'])}"
            )

            for line_no, line in enumerate(
                block["lines"], start=1
            ):

                text = " ".join(
                    word["text"]
                    for word in line["words"]
                )

                print(
                    f"      L{line_no:02d} "
                    f"("
                    f"{line['x0']:.0f},"
                    f"{line['y0']:.0f}"
                    f") "
                    f"{text}"
                )


def main():

    article_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    with open(INPUT, encoding="utf-8") as f:
        articles = json.load(f)

    matches = [
        article
        for article in articles
        if article["article_id"] == article_id
    ]

    if not matches:
        raise SystemExit(
            f"Article {article_id} not found."
        )

    print_article(matches[0])


if __name__ == "__main__":
    main()
