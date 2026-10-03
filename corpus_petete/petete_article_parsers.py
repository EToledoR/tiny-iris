#!/usr/bin/env python3

import argparse
import json
import re


PAGE_RE = re.compile(r"(?<![\d/])(\d{1,3})\s*$")
WEIRD_PAGE_RE = re.compile(r"([0-9]+/[0-9]+)\s*$")


IGNORE_TITLES = [
    "Editorial P.T.T. S.A.",
    "PRODUCCIONES GARCÍA FERRÉ",
]


def clean_line(line):
    return re.sub(r"\s+", " ", line).strip()


def should_ignore(title):
    return any(title.startswith(prefix) for prefix in IGNORE_TITLES)


def parse_index(path):
    entries = []

    pending_lines = []
    pending_source_lines = []

    with open(path, encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):

            line = clean_line(raw_line)

            if not line:
                continue

            # Ignore the index heading.
            if line.upper() == "ÍNDICE":
                continue

            pending_lines.append(line)
            pending_source_lines.append(line_number)

            # ---------------------------------------------------------
            # Normal page number at the end of the entry
            # ---------------------------------------------------------
            match = PAGE_RE.search(line)

            if match:
                page = int(match.group(1))

                title = line[:match.start()].strip()
                title = " ".join(pending_lines[:-1] + [title])

                if should_ignore(title):
                    pending_lines = []
                    pending_source_lines = []
                    continue

                entries.append({
                    "title": title,
                    "start_page": page,
                    "source_lines": pending_source_lines.copy(),
                    "status": "ok",
                })

                pending_lines = []
                pending_source_lines = []
                continue

            # ---------------------------------------------------------
            # OCR'd page number, e.g. "1/6"
            # ---------------------------------------------------------
            weird = WEIRD_PAGE_RE.search(line)

            if weird:
                title = line[:weird.start()].strip()
                title = " ".join(pending_lines[:-1] + [title])

                if should_ignore(title):
                    pending_lines = []
                    pending_source_lines = []
                    continue

                entries.append({
                    "title": title,
                    "start_page": None,
                    "page_raw": weird.group(1),
                    "source_lines": pending_source_lines.copy(),
                    "status": "review",
                })

                pending_lines = []
                pending_source_lines = []

    return entries


def main():
    parser = argparse.ArgumentParser(
        description="Extract Petete article entries from the index."
    )

    parser.add_argument(
        "input",
        help="TXT extracted from the index pages"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="petete_index.json"
    )

    args = parser.parse_args()

    entries = parse_index(args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(
            entries,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Entries: {len(entries)}")
    print(f"Output:  {args.output}")
    print()

    for i, entry in enumerate(entries, 1):
        page = entry.get("start_page")

        if page is None:
            page = entry.get("page_raw", "?")

        print(
            f"{i:3d}  "
            f"p.{str(page):>3}  "
            f"{entry['title']}"
        )


if __name__ == "__main__":
    main()
