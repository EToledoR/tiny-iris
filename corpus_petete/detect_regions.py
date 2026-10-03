#!/usr/bin/env python3

import json
import sys


INPUT = "petete_articles_bbox.json"


# ---------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------

def horizontal_overlap(a, b):
    """
    Horizontal intersection between two bounding boxes.
    """

    left = max(a["x0"], b["x0"])
    right = min(a["x1"], b["x1"])

    return max(0, right - left)


def vertical_overlap(a, b):
    """
    Vertical intersection between two bounding boxes.
    """

    top = max(a["y0"], b["y0"])
    bottom = min(a["y1"], b["y1"])

    return max(0, bottom - top)


def horizontal_gap(a, b):
    """
    Horizontal distance between two boxes.
    """

    if a["x1"] < b["x0"]:
        return b["x0"] - a["x1"]

    if b["x1"] < a["x0"]:
        return a["x0"] - b["x1"]

    return 0


def vertical_gap(a, b):
    """
    Vertical distance between two boxes.
    """

    if a["y1"] < b["y0"]:
        return b["y0"] - a["y1"]

    if b["y1"] < a["y0"]:
        return a["y0"] - b["y1"]

    return 0


def block_height(block):
    return block["y1"] - block["y0"]


def block_width(block):
    return block["x1"] - block["x0"]


def block_line_count(block):
    return len(block["lines"])


# ---------------------------------------------------------------------
# Block relationships
# ---------------------------------------------------------------------

def blocks_are_related(a, b):
    """
    Conservative spatial relationship test.

    This is deliberately NOT a reading-order algorithm.

    We consider two blocks related when:

    1. They overlap horizontally and are vertically close, OR
    2. They overlap vertically and are horizontally close.

    The thresholds are deliberately generous enough to expose
    candidate regions without trying to solve the whole layout.
    """

    h_overlap = horizontal_overlap(a, b)
    v_overlap = vertical_overlap(a, b)

    h_gap = horizontal_gap(a, b)
    v_gap = vertical_gap(a, b)

    # Case 1:
    # Same general column, nearby vertically.
    if h_overlap > 0 and v_gap <= 80:
        return True

    # Case 2:
    # Same horizontal band, nearby horizontally.
    if v_overlap > 0 and h_gap <= 80:
        return True

    return False


# ---------------------------------------------------------------------
# Region construction
# ---------------------------------------------------------------------

def find_regions(blocks):
    """
    Build connected groups of spatially related blocks.

    This is essentially a graph:

        block A ---- block B
                    |
                    block C

    All connected blocks become one candidate region.

    The result is only a geometric grouping.
    """

    n = len(blocks)

    neighbours = [
        set()
        for _ in range(n)
    ]

    for i in range(n):

        for j in range(i + 1, n):

            if blocks_are_related(
                blocks[i],
                blocks[j]
            ):

                neighbours[i].add(j)
                neighbours[j].add(i)

    visited = set()
    regions = []

    for start in range(n):

        if start in visited:
            continue

        stack = [start]
        visited.add(start)

        members = []

        while stack:

            current = stack.pop()
            members.append(current)

            for neighbour in neighbours[current]:

                if neighbour not in visited:

                    visited.add(neighbour)
                    stack.append(neighbour)

        regions.append(
            sorted(members)
        )

    return regions


# ---------------------------------------------------------------------
# Region statistics
# ---------------------------------------------------------------------

def region_bbox(blocks, indices):

    selected = [
        blocks[i]
        for i in indices
    ]

    return {
        "x0": min(b["x0"] for b in selected),
        "y0": min(b["y0"] for b in selected),
        "x1": max(b["x1"] for b in selected),
        "y1": max(b["y1"] for b in selected),
    }


def region_stats(blocks, indices):

    selected = [
        blocks[i]
        for i in indices
    ]

    bbox = region_bbox(
        blocks,
        indices
    )

    lines = sum(
        block_line_count(b)
        for b in selected
    )

    words = sum(
        len(line["words"])
        for b in selected
        for line in b["lines"]
    )

    return {
        "bbox": bbox,
        "blocks": len(selected),
        "lines": lines,
        "words": words,
    }


# ---------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------

def print_region(
    number,
    blocks,
    indices
):

    stats = region_stats(
        blocks,
        indices
    )

    bbox = stats["bbox"]

    print(
        f"REGION {number:02d} "
        f"blocks={stats['blocks']} "
        f"lines={stats['lines']} "
        f"words={stats['words']}"
    )

    print(
        f"  bbox=("
        f"{bbox['x0']:.0f}, "
        f"{bbox['y0']:.0f}, "
        f"{bbox['x1']:.0f}, "
        f"{bbox['y1']:.0f}"
        f")"
    )

    print(
        f"  block IDs: "
        f"{', '.join(str(i + 1) for i in indices)}"
    )

    print()


# ---------------------------------------------------------------------
# Page lookup
# ---------------------------------------------------------------------

def find_page(articles, pdf_page):

    for article in articles:

        for page in article["pages"]:

            if page["pdf_page"] == pdf_page:

                return article, page

    return None, None


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    if len(sys.argv) != 2:

        print(
            "Usage: python3 detect_regions.py PDF_PAGE"
        )

        print(
            "Example:"
        )

        print(
            "  python3 detect_regions.py 11"
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

    blocks = page["blocks"]

    regions = find_regions(
        blocks
    )

    print("=" * 80)

    print(
        f"ARTICLE {article['article_id']}: "
        f"{article['title']}"
    )

    print(
        f"PDF PAGE {pdf_page} "
        f"{page['width']:.0f} x "
        f"{page['height']:.0f}"
    )

    print(
        f"Blocks : {len(blocks)}"
    )

    print(
        f"Regions: {len(regions)}"
    )

    print("=" * 80)
    print()

    # Sort regions by their top-left position.
    region_data = []

    for indices in regions:

        bbox = region_bbox(
            blocks,
            indices
        )

        region_data.append(
            (bbox["y0"], bbox["x0"], indices)
        )

    region_data.sort(
        key=lambda x: (x[0], x[1])
    )

    for number, (_, _, indices) in enumerate(
        region_data,
        start=1
    ):

        print_region(
            number,
            blocks,
            indices
        )


if __name__ == "__main__":
    main()
