#!/usr/bin/env python3

import argparse
import json


def main():
    parser = argparse.ArgumentParser(
        description="Check Petete article page ranges."
    )

    parser.add_argument(
        "articles",
        help="Path to petete_articles.json"
    )

    args = parser.parse_args()

    with open(args.articles, encoding="utf-8") as f:
        articles = json.load(f)

    errors = []

    if not articles:
        print("No articles found.")
        return

    # Primer artículo
    if articles[0]["start_page"] != 1:
        errors.append(
            f"First article starts at "
            f"{articles[0]['start_page']}, expected 1"
        )

    # Comprobar continuidad
    for previous, current in zip(articles, articles[1:]):
        expected = previous["end_page"] + 1

        if current["start_page"] != expected:
            errors.append(
                f"Gap/overlap between articles "
                f"{previous['article_id']} and "
                f"{current['article_id']}: "
                f"{previous['end_page']} -> "
                f"{current['start_page']} "
                f"(expected {expected})"
            )

    # Última página
    last_page = articles[-1]["end_page"]

    if last_page != 559:
        errors.append(
            f"Last article ends at {last_page}, expected 559"
        )

    if errors:
        print("INTEGRITY CHECK FAILED")
        print()

        for error in errors:
            print(f"  ERROR: {error}")

    else:
        print("INTEGRITY CHECK PASSED")
        print()
        print(f"Articles : {len(articles)}")
        print(f"Pages    : 1–{last_page}")
        print("Coverage : continuous")
        print("Overlap  : none")


if __name__ == "__main__":
    main()
