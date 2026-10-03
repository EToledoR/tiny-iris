import json
import random

INPUT = "petete_raw.jsonl"

with open(INPUT, encoding="utf-8") as f:
    articles = [json.loads(line) for line in f]

# Algunos artículos representativos:
ids = [1, 2, 10, 50, 137]

for article_id in ids:
    article = next(a for a in articles if a["article_id"] == article_id)

    print("=" * 80)
    print(f"ARTICLE {article['article_id']}")
    print(article["title"])
    print(
        f"PDF {article['pdf_start']}–{article['pdf_end']} | "
        f"Editorial {article['editorial_start']}–{article['editorial_end']}"
    )
    print("=" * 80)

    print(article["text"][:5000])
    print()
