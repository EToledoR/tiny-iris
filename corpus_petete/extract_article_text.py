#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path


INPUT = Path("petete_articles_bbox.json")
OUTPUT = Path("petete_raw.jsonl")


# Bloques con menos contenido que esto se consideran probablemente
# etiquetas, números de página, ruido gráfico, etc.
MIN_WORDS = 8
MIN_LINES = 2


def word_count(block):
    return sum(
        len(line.get("words", []))
        for line in block.get("lines", [])
    )


def line_count(block):
    return len(block.get("lines", []))


def block_text_raw(block):
    """Reconstruye exactamente el texto disponible en los BBOX."""
    lines = []

    for line in block.get("lines", []):
        words = [
            word.get("text", "").strip()
            for word in line.get("words", [])
        ]
        words = [w for w in words if w]
        if words:
            lines.append(" ".join(words))

    return "\n".join(lines)


def clean_line_breaks(text):
    """
    Limpieza puramente mecánica.

    Petete usa '¬' para indicar palabras partidas entre líneas:
        comu¬
        nicación

    Lo convertimos en:
        comunicación

    No corregimos ortografía ni OCR.
    """
    text = re.sub(r"¬\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return text.strip()


def block_is_candidate(block):
    words = word_count(block)
    lines = line_count(block)

    return words >= MIN_WORDS or lines >= MIN_LINES


def block_sort_key(block):
    """
    Orden pragmático para v0.1.

    Primero por posición horizontal (columna/zona),
    después verticalmente dentro de esa zona.

    No pretende reconstruir perfectamente el diseño editorial.
    """
    x0 = block["x0"]
    y0 = block["y0"]

    return (x0, y0)


def extract_article(article):
    blocks_for_text = []
    source_blocks = []

    for page in article["pages"]:
        pdf_page = page["pdf_page"]

        # Los bloques grandes primero, conservando su posición.
        candidates = [
            block
            for block in page.get("blocks", [])
            if block_is_candidate(block)
        ]

        candidates.sort(key=block_sort_key)

        for block in candidates:
            raw = block_text_raw(block)

            if not raw.strip():
                continue

            clean = clean_line_breaks(raw)

            blocks_for_text.append(clean)

            source_blocks.append({
                "pdf_page": pdf_page,
                "bbox": [
                    block["x0"],
                    block["y0"],
                    block["x1"],
                    block["y1"],
                ],
                "words": word_count(block),
                "lines": line_count(block),
                "text_raw": raw,
                "text": clean,
            })

    text_raw = "\n\n".join(
        block["text_raw"]
        for block in source_blocks
    )

    text = "\n\n".join(
        block["text"]
        for block in source_blocks
    )

    return text_raw, text, source_blocks


def main():
    if not INPUT.exists():
        print(f"ERROR: no existe {INPUT}")
        sys.exit(1)

    print(f"Loading: {INPUT}")

    with INPUT.open(encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Articles: {len(articles)}")
    print(f"MIN_WORDS: {MIN_WORDS}")
    print(f"MIN_LINES: {MIN_LINES}")
    print()

    total_words = 0
    total_blocks = 0

    with OUTPUT.open("w", encoding="utf-8") as out:

        for article in articles:
            text_raw, text, source_blocks = extract_article(article)

            article_words = sum(
                block["words"]
                for block in source_blocks
            )

            total_words += article_words
            total_blocks += len(source_blocks)

            record = {
                "article_id": article["article_id"],
                "title": article["title"],
                "editorial_start": article["editorial_start"],
                "editorial_end": article["editorial_end"],
                "pdf_start": article["pdf_start"],
                "pdf_end": article["pdf_end"],
                "text_raw": text_raw,
                "text": text,
                "source_blocks": source_blocks,
            }

            out.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

    print("Extraction completed.")
    print(f"Output      : {OUTPUT}")
    print(f"Articles    : {len(articles)}")
    print(f"Blocks      : {total_blocks}")
    print(f"Words       : {total_words}")


if __name__ == "__main__":
    main()
