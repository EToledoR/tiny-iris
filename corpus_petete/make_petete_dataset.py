#!/usr/bin/env python3

import json
import random
from pathlib import Path


INPUT = Path("petete_raw.jsonl")
TRAIN_OUTPUT = Path("petete_train.txt")
TEST_OUTPUT = Path("petete_test.txt")

SEED = 42
TEST_FRACTION = 0.10

ARTICLE_SEPARATOR = "\n\n<|END_ARTICLE|>\n\n"


def load_articles():
    articles = []

    with INPUT.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                articles.append(json.loads(line))

    return articles


def article_text(article):
    return article["text"].strip()


def main():
    print(f"Loading: {INPUT}")

    articles = load_articles()

    print(f"Articles loaded: {len(articles)}")

    # Important:
    # split by ARTICLE, not by characters.
    rng = random.Random(SEED)
    shuffled = articles[:]
    rng.shuffle(shuffled)

    test_size = round(len(shuffled) * TEST_FRACTION)

    test_articles = shuffled[:test_size]
    train_articles = shuffled[test_size:]

    # Put them back in original Petete order.
    train_articles.sort(key=lambda a: a["article_id"])
    test_articles.sort(key=lambda a: a["article_id"])

    train_text = ARTICLE_SEPARATOR.join(
        article_text(article)
        for article in train_articles
        if article_text(article)
    )

    test_text = ARTICLE_SEPARATOR.join(
        article_text(article)
        for article in test_articles
        if article_text(article)
    )

    TRAIN_OUTPUT.write_text(train_text + "\n", encoding="utf-8")
    TEST_OUTPUT.write_text(test_text + "\n", encoding="utf-8")

    print()
    print("Dataset created.")
    print()
    print(f"Train articles : {len(train_articles)}")
    print(f"Test articles  : {len(test_articles)}")
    print(f"Train chars    : {len(train_text):,}")
    print(f"Test chars     : {len(test_text):,}")
    print()
    print(f"Train output   : {TRAIN_OUTPUT}")
    print(f"Test output    : {TEST_OUTPUT}")
    print()
    print("Test article IDs:")
    print([a["article_id"] for a in test_articles])


if __name__ == "__main__":
    main()
