#!/usr/bin/env python3

import json

INPUT = "petete_page_map.json"

with open(INPUT, encoding="utf-8") as f:
    pages = json.load(f)

print(f"Articles: {len(pages)}")

errors = []

# 1. Número de artículos
if len(pages) != 233:
    errors.append(f"Expected 233 articles, got {len(pages)}")

# 2. IDs consecutivos
for i, article in enumerate(pages, start=1):
    if article["article_id"] != i:
        errors.append(
            f"Article {i}: expected ID {i}, got {article['article_id']}"
        )

# 3. Starts crecientes
for current, nxt in zip(pages, pages[1:]):
    if current["pdf_start"] >= nxt["pdf_start"]:
        errors.append(
            f"Bad order: article {current['article_id']} "
            f"starts at {current['pdf_start']}, "
            f"next starts at {nxt['pdf_start']}"
        )

# 4. End = siguiente start - 1
for current, nxt in zip(pages, pages[1:]):
    expected_end = nxt["pdf_start"] - 1
    if current["pdf_end"] != expected_end:
        errors.append(
            f"Article {current['article_id']}: "
            f"pdf_end={current['pdf_end']}, "
            f"expected {expected_end}"
        )

# 5. Extremos conocidos
if pages[0]["pdf_start"] != 9:
    errors.append("First article does not start at PDF page 9")

if pages[-1]["pdf_end"] != 494:
    errors.append("Last article does not end at PDF page 494")

# Resultado
if errors:
    print("\nERRORS:")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("INTEGRITY CHECK PASSED")
print(f"PDF coverage: {pages[0]['pdf_start']}–{pages[-1]['pdf_end']}")
print("No overlaps")
print("Starts strictly increasing")
print("Ends match next article start")
