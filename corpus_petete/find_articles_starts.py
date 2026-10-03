#!/usr/bin/env python3

import argparse
import json
import re
import unicodedata
from difflib import SequenceMatcher
from html.parser import HTMLParser


# ------------------------------------------------------------
# BBOX parser
# ------------------------------------------------------------

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
                self.current_line["words"].append(self.current_word)
                self.current_word = None

        elif tag == "line":

            if self.current_line is not None:
                self.current_block["lines"].append(self.current_line)
                self.current_line = None

        elif tag == "block":

            if self.current_block is not None:
                self.current_page["blocks"].append(self.current_block)
                self.current_block = None

        elif tag == "page":

            if self.current_page is not None:
                self.pages.append(self.current_page)
                self.current_page = None


def load_bbox(path):

    parser = BBoxParser()

    with open(path, encoding="utf-8") as f:
        parser.feed(f.read())

    return parser.pages


# ------------------------------------------------------------
# Text helpers
# ------------------------------------------------------------

def normalize(text):

    text = text.lower()

    # Remove accents.
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    # OCR noise: keep letters/numbers/spaces.
    text = re.sub(r"[^a-z0-9ñ]+", " ", text)

    return " ".join(text.split())


def page_text(page):

    words = []

    for block in page["blocks"]:
        for line in block["lines"]:
            for word in line["words"]:
                text = word["text"].strip()

                if text:
                    words.append(text)

    return " ".join(words)


# ------------------------------------------------------------
# Similarity
# ------------------------------------------------------------

def similarity(title, text):

    title = normalize(title)
    text = normalize(text)

    if not title or not text:
        return 0.0

    # Exact occurrence is obviously excellent.
    if title in text:
        return 1.0

    # Search approximately around the expected title length.
    title_words = title.split()

    if not title_words:
        return 0.0

    n = len(title_words)

    words = text.split()

    if len(words) < n:
        return SequenceMatcher(None, title, text).ratio()

    best = 0.0

    # A little breathing room helps with OCR errors.
    for width in range(max(1, n - 2), n + 4):

        for i in range(len(words) - width + 1):

            candidate = " ".join(words[i:i + width])

            score = SequenceMatcher(
                None,
                title,
                candidate
            ).ratio()

            if score > best:
                best = score

    return best


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--index",
        default="petete_index.json"
    )

    parser.add_argument(
        "--bbox",
        default="petete_01_azul_bbox.html"
    )

    parser.add_argument(
        "--output",
        default="petete_page_map_candidates.json"
    )

    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of candidates per article"
    )

    args = parser.parse_args()

    print("Loading index...")
    with open(args.index, encoding="utf-8") as f:
        index = json.load(f)

    print("Loading BBOX...")
    pages = load_bbox(args.bbox)

    print(f"Index entries : {len(index)}")
    print(f"Physical pages: {len(pages)}")

    print("Extracting page text...")

    page_texts = []

    for physical_page, page in enumerate(pages, start=1):

        text = page_text(page)

        page_texts.append({
            "physical_page": physical_page,
            "text": text,
        })

    results = []

    # --------------------------------------------------------
    # Search titles.
    # --------------------------------------------------------

    for article_number, article in enumerate(index, start=1):

        title = article["title"]

        candidates = []

        for page in page_texts:

            text = page["text"]

            if not text.strip():
                continue

            score = similarity(title, text[:3000])

            candidates.append({
                "physical_page": page["physical_page"],
                "score": round(score, 4),
            })

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        candidates = candidates[:args.top]

        result = {
            "index_number": article_number,
            "title": title,
            "editorial_page": article.get("start_page"),
            "candidates": candidates,
        }

        results.append(result)

        best = candidates[0] if candidates else None

        if best:
            print(
                f"{article_number:3d} "
                f"{best['physical_page']:3d} "
                f"{best['score']:.3f} "
                f"{title}"
            )

    # --------------------------------------------------------
    # Save candidates.
    # --------------------------------------------------------

    with open(args.output, "w", encoding="utf-8") as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(f"Written: {args.output}")


if __name__ == "__main__":
    main()
