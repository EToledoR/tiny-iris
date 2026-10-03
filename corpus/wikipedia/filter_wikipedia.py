from pathlib import Path
import json
import shutil


BASE_DIR = Path(__file__).parent

ARTICLES_DIR = BASE_DIR / "articles"
METADATA_FILE = BASE_DIR / "metadata.jsonl"

FILTERED_DIR = BASE_DIR / "filtered"
FILTERED_ARTICLES_DIR = FILTERED_DIR / "articles"
FILTERED_METADATA_FILE = FILTERED_DIR / "metadata.jsonl"


# ------------------------------------------------------------
# Articles to exclude
# ------------------------------------------------------------

BOTANICAL_TITLES = {
    "Aquifoliaceae",
    "Sapindaceae",
    "Apiaceae",
    "Araucariaceae",
    "Alismataceae",
    "Araceae",
    "Aegilops",
    "Agrostis",
    "Andropogon",
    "Arundo",
    "Amphipogon",
    "Arctagrostis",
    "Annonaceae",
    "Brassicaceae",
    "Bombacaceae",
    "Buxaceae",
    "Butomaceae",
    "Betulaceae",
    "Brachypodium",
    "Bromus",
    "Bouteloua",
    "Cistaceae",
    "Crassulaceae",
    "Commelinaceae",
    "Castanea henryi",
    "Castanea seguinii",
    "Castanea ozarkensis",
    "Grossulariaceae",
}


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    FILTERED_ARTICLES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove a previous filtered dataset,
    # but NEVER touch the original articles.
    for path in FILTERED_ARTICLES_DIR.glob("*.txt"):
        path.unlink()

    if FILTERED_METADATA_FILE.exists():
        FILTERED_METADATA_FILE.unlink()

    kept = 0
    excluded = 0
    kept_chars = 0
    excluded_chars = 0

    with (
        METADATA_FILE.open(
            encoding="utf-8"
        ) as source_metadata,
        FILTERED_METADATA_FILE.open(
            "w",
            encoding="utf-8"
        ) as output_metadata,
    ):

        for line in source_metadata:

            item = json.loads(line)

            title = item["title"]

            # Find the actual filename from metadata.
            matches = list(
                ARTICLES_DIR.glob(
                    f"{item['id']}_*.txt"
                )
            )

            if not matches:
                print(
                    f"WARNING: file not found "
                    f"for {title}"
                )
                continue

            source_file = matches[0]

            if title in BOTANICAL_TITLES:

                item["exclude"] = True
                item["exclude_reason"] = (
                    "botanical_taxonomy"
                )

                excluded += 1
                excluded_chars += item["chars"]

                continue

            destination = (
                FILTERED_ARTICLES_DIR
                / source_file.name
            )

            shutil.copy2(
                source_file,
                destination,
            )

            item["exclude"] = False

            output_metadata.write(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
                + "\n"
            )

            kept += 1
            kept_chars += item["chars"]

    print()
    print("=" * 60)
    print("Wikipedia filtering complete")
    print("=" * 60)

    print()
    print("KEPT")
    print(f"Articles:   {kept}")
    print(f"Characters: {kept_chars:,}")

    print()
    print("EXCLUDED")
    print(f"Articles:   {excluded}")
    print(f"Characters: {excluded_chars:,}")

    print()
    print("TOTAL")
    print(
        f"Articles:   "
        f"{kept + excluded}"
    )
    print(
        f"Characters: "
        f"{kept_chars + excluded_chars:,}"
    )

    print()
    print(
        f"Filtered articles: "
        f"{FILTERED_ARTICLES_DIR}"
    )

    print(
        f"Filtered metadata: "
        f"{FILTERED_METADATA_FILE}"
    )


if __name__ == "__main__":
    main()
