#!/usr/bin/env python3

import json


PDF_STARTS = [
    9,14,16,18,21,22,23,26,28,30,33,35,36,37,40,42,44,45,48,50,
    51,54,58,60,63,65,66,69,71,73,74,78,79,80,83,85,87,90,92,
    94,95,98,100,102,105,107,109,110,115,117,118,120,122,124,
    125,128,130,133,135,139,140,143,147,149,150,154,155,158,
    161,162,164,165,166,167,170,172,174,177,181,182,186,187,
    189,192,193,195,196,199,201,203,206,208,209,210,213,214,
    216,217,221,223,224,227,228,230,233,235,237,238,241,244,
    245,248,249,251,252,255,257,259,261,265,267,268,272,273,
    274,275,279,281,282,285,288,291,294,295,296,299,300,303,
    304,307,308,312,313,314,316,318,320,321,324,327,329,330,
    331,333,334,337,338,340,342,344,346,347,349,351,353,355,
    358,359,360,362,365,366,368,370,371,373,377,380,381,383,
    384,387,391,394,397,398,399,402,405,408,409,411,412,415,
    416,418,421,424,425,426,428,431,434,436,438,439,441,443,
    445,448,450,452,453,456,458,460,461,462,465,466,467,471,
    474,477,479,480,481,484,486,487,491,493,494
]


INPUT = "petete_articles.json"
OUTPUT = "petete_page_map.json"


def main():

    with open(INPUT, encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Articles in JSON : {len(articles)}")
    print(f"PDF starts given : {len(PDF_STARTS)}")

    if len(articles) != len(PDF_STARTS):
        raise SystemExit(
            "ERROR: number of articles and PDF starts do not match."
        )

    result = []

    for i, article in enumerate(articles):

        pdf_start = PDF_STARTS[i]

        if i + 1 < len(PDF_STARTS):
            pdf_end = PDF_STARTS[i + 1] - 1
        else:
            pdf_end = 494

        entry = {
            "article_id": article["article_id"],
            "title": article["title"],

            "editorial_start": article["start_page"],
            "editorial_end": article["end_page"],

            "pdf_start": pdf_start,
            "pdf_end": pdf_end,
        }

        result.append(entry)

    # --------------------------------------------------------
    # Sanity checks
    # --------------------------------------------------------

    for i in range(len(result) - 1):

        current = result[i]
        next_article = result[i + 1]

        if current["pdf_end"] >= next_article["pdf_start"]:
            raise SystemExit(
                f"ERROR: overlap between articles "
                f"{current['article_id']} and "
                f"{next_article['article_id']}"
            )

    if result[0]["pdf_start"] != 9:
        raise SystemExit("ERROR: first article does not start at PDF page 9.")

    if result[-1]["pdf_end"] != 494:
        raise SystemExit("ERROR: last article does not end at PDF page 494.")

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("Page map created successfully.")
    print(f"Articles : {len(result)}")
    print(f"First    : PDF {result[0]['pdf_start']}")
    print(f"Last     : PDF {result[-1]['pdf_end']}")
    print(f"Output   : {OUTPUT}")


if __name__ == "__main__":
    main()
