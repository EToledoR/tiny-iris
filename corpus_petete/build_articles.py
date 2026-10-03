#!/usr/bin/env python3

import argparse
import json


def load_index(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_articles(entries, last_page):
    articles = []

    for i, entry in enumerate(entries):
        start_page = entry.get("start_page")

        if start_page is None:
            articles.append({
                "article_id": i + 1,
                "title": entry["title"],
                "start_page": None,
                "end_page": None,
                "pages": [],
                "status": "review",
            })
            continue

        # La siguiente entrada determina dónde termina este artículo.
        next_page = None

        for next_entry in entries[i + 1:]:
            if next_entry.get("start_page") is not None:
                next_page = next_entry["start_page"]
                break

        if next_page is not None:
            end_page = next_page - 1
        else:
            end_page = last_page

        pages = list(range(start_page, end_page + 1))

        articles.append({
            "article_id": i + 1,
            "title": entry["title"],
            "start_page": start_page,
            "end_page": end_page,
            "pages": pages,
            "status": entry.get("status", "ok"),
        })

    return articles


def main():
    parser = argparse.ArgumentParser(
        description="Build Petete articles from the cleaned index."
    )

    parser.add_argument(
        "index",
        help="Path to petete_index.json"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="petete_articles.json",
        help="Output JSON file"
    )

    parser.add_argument(
        "--last-page",
        type=int,
        default=559,
        help="Last page of the volume"
    )

    args = parser.parse_args()

    entries = load_index(args.index)

    articles = build_articles(
        entries,
        args.last_page,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(
            articles,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Index entries : {len(entries)}")
    print(f"Articles      : {len(articles)}")

    review = [
        article
        for article in articles
        if article["status"] == "review"
    ]

    print(f"Needs review  : {len(review)}")

    for article in review:
        print(
            f"  #{article['article_id']}: "
            f"{article['title']}"
        )


if __name__ == "__main__":
    main()
