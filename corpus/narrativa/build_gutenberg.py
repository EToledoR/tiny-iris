#!/usr/bin/env python3

"""
Tiny Iris — Gutenberg narrative corpus

Downloads selected Spanish-language Gutenberg books,
extracts individual stories, removes Gutenberg/editorial
front matter and back matter, and writes one TXT per story.
"""

from pathlib import Path
import re
import unicodedata
import urllib.request


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "sources"
STORY_DIR = BASE_DIR / "stories"


BOOKS = {
    "77759": {
        "author": "Miguel de Unamuno",
        "title": "El espejo de la muerte",
        "url": "https://www.gutenberg.org/cache/epub/77759/pg77759.txt",

        "stories": [
            "El espejo de la muerte",
            "La princesa doña Lambra",
            "La revolución de los hombres",
            "El héroe",
            "El semejante",
            "La locura del doctor Montarco",
            "Una visita al viejo poeta",
            "El sencillo don Rafael",
            "El amor de la doncella",
            "El diamante de Villasola",
            "La venda",
            "La flor en el jardín",
            "El misterio del barrio",
            "El caballero de la triste figura",
            "El canto del gallo",
            "La promesa",
            "El fin de la historia",
            "La redención",
            "El espejo",
            "El semejante",
            "La sobrina del cura",
            "La difunta",
            "El rey",
            "La pasión de la tierra",
            "La prueba",
            "La última mosca",
            "Y va de cuento",
        ],

        "frontmatter": {
            "El espejo de la muerte": {
                "keep_heading_lines": 1,
                "start_marker": "HISTORIA MUY VULGAR",
            }
        },

        "backmatter_markers": [
            "NOTAS:",
        ],
    },

    "69873": {
        "author": "Nilo María Fabra",
        "title": "Cuentos ilustrados",
        "url": "https://www.gutenberg.org/cache/epub/69873/pg69873.txt",

        "stories": [
            "El fin de Barcelona",
            "La guerra del porvenir",
            "La locura de la ciencia",
            "El futuro Madrid",
            "La catástrofe de Inglaterra",
            "El desastre de Cartagena",
            "El último día de Roma",
            "La guerra de 1914",
            "En el año 2000",
            "El triunfo de la democracia",
            "El mundo en el año 2000",
            "La paz universal",
            "El último hombre",
            "El sueño de un loco",
            "La vida en Marte",
            "El planeta Marte",
        ],

        "backmatter_markers": [
            "ÍNDICE",
        ],
    },

    "30053": {
        "author": "Armando Palacio Valdés",
        "title": "Los Puritanos, y otros cuentos",
        "url": "https://www.gutenberg.org/cache/epub/30053/pg30053.txt",

        # We deliberately skip the first story. Its heading is badly
        # OCR-corrupted in the Gutenberg edition and caused repeated
        # extraction problems. We can recover it later if we want.
        "start_line": 120,

        "stories": [
            "El pajaro en la nieve",
            "La confesión de un crimen",
            "El sueño de un reo de muerte",
            "Los puritanos",
        ],

        # These are the actual editorial note headings found in the
        # Gutenberg text. Each story must stop before its own notes.
        "story_note_markers": {
            "La confesión de un crimen":
                'NOTES FOR "LA CONFESION DE UN CRIMEN":',

            "El sueño de un reo de muerte":
                'NOTES FOR "EL SUE—O DE UN REO DE MUERTE":',

            "Los puritanos":
                'NOTES FOR "LOS PURITANOS":',
        },

        # Final book-level vocabulary. Useful as a final safety net.
        "backmatter_markers": [
            "VOCABULARY",
            "WORDS OF SIMILAR ORTHOGRAPHY",
        ],
    },
}


# ----------------------------------------------------------------------
# Text utilities
# ----------------------------------------------------------------------

def download_book(book_id, config):
    """
    Download the Gutenberg TXT source if it does not already exist.
    """
    path = SOURCE_DIR / f"{book_id}.txt"

    if path.exists():
        print(f"[OK] Source already exists: {path}")
        return path

    print(f"[DOWNLOAD] {config['title']}")
    print(f"           {config['url']}")

    urllib.request.urlretrieve(config["url"], path)

    print(f"[OK] Saved: {path}")
    return path


def clean_text(text):
    """
    Basic mechanical cleanup.

    We deliberately do not try to 'improve' the prose or repair OCR
    beyond a few safe normalisations.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove Gutenberg's soft line hyphen.
    text = text.replace("\u00ad", "")

    # Gutenberg sometimes uses form-feed.
    text = text.replace("\f", "\n")

    # Mechanical broken-line hyphen cleanup.
    text = re.sub(r"-\n(?=\w)", "", text)

    # Remove trailing whitespace.
    text = "\n".join(line.rstrip() for line in text.splitlines())

    # Collapse excessive blank lines.
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text.strip()


def remove_gutenberg_wrapper(text):
    """
    Remove Project Gutenberg boilerplate around the actual book.
    """
    lines = text.splitlines()

    start = 0
    end = len(lines)

    for i, line in enumerate(lines):
        if "*** START OF THE PROJECT GUTENBERG EBOOK" in line.upper():
            start = i + 1
            break

    for i in range(start, len(lines)):
        if "*** END OF THE PROJECT GUTENBERG EBOOK" in lines[i].upper():
            end = i
            break

    return lines[start:end]


# ----------------------------------------------------------------------
# Matching
# ----------------------------------------------------------------------

def normalize_for_matching(text):
    """
    Normalise headings for fuzzy-but-safe matching.

    This deals with:
      - accents
      - punctuation
      - Gutenberg/OCR quirks
      - common OCR corruption in the selected books
    """
    text = text.strip().lower()

    # Known OCR oddities in Palacio Valdés.
    text = text.replace("p¡jaro", "pajaro")
    text = text.replace("p jaro", "pajaro")
    text = text.replace("sue—o", "sueno")
    text = text.replace("sue o", "sueno")

    # D. / D / Don
    text = re.sub(r"\bd\.\s+", "don ", text)
    text = re.sub(r"\bd\s+", "don ", text)

    # Remove accents.
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    # Punctuation -> spaces.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_normalized_lines(lines):
    """
    Return (original_index, original_line, normalized_line).
    """
    result = []

    for i, line in enumerate(lines):
        normalized = normalize_for_matching(line)

        # Important: empty lines must never match an empty heading.
        if normalized:
            result.append((i, line, normalized))

    return result


def find_heading(lines, heading, start_line=0):
    """
    Find the first line matching a story heading after start_line.
    """
    target = normalize_for_matching(heading)

    for i in range(start_line, len(lines)):
        normalized = normalize_for_matching(lines[i])

        if not normalized:
            continue

        if normalized == target:
            return i

    return None


# ----------------------------------------------------------------------
# Story extraction
# ----------------------------------------------------------------------

def trim_story_frontmatter(text, config):
    """
    Remove known material between a story heading and its actual prose.
    """
    if not config:
        return text

    start_marker = config.get("start_marker")

    if not start_marker:
        return text

    lines = text.splitlines()
    target = normalize_for_matching(start_marker)

    for i, line in enumerate(lines):
        if normalize_for_matching(line) == target:
            keep_heading_lines = config.get("keep_heading_lines", 1)

            # Keep the heading itself plus the desired number of lines.
            cut = i

            if keep_heading_lines > 0:
                cut = max(0, i - keep_heading_lines + 1)

            return "\n".join(lines[cut:]).strip()

    return text


def trim_at_marker(text, markers):
    """
    Cut text at the first matching marker occurring at the beginning
    of a line.
    """
    if not markers:
        return text

    lines = text.splitlines()

    normalized_markers = [
        normalize_for_matching(marker)
        for marker in markers
    ]

    for i, line in enumerate(lines):
        normalized = normalize_for_matching(line)

        for marker in normalized_markers:
            if normalized.startswith(marker):
                return "\n".join(lines[:i]).strip()

    return text.strip()


def extract_stories(lines, config):
    """
    Extract configured stories from one book.
    """
    stories = config["stories"]
    start_line = config.get("start_line", 0)

    results = []

    # We deliberately skip problematic stories if explicitly listed.
    skip_stories = set(config.get("skip_stories", []))

    for story_index, story_title in enumerate(stories):

        if story_title in skip_stories:
            print(f"[SKIP] {story_title}")
            continue

        # We intentionally skip the first Palacio story.
        if (
            config["title"] == "Los Puritanos, y otros cuentos"
            and story_title == "El pajaro en la nieve"
        ):
            print(f"[SKIP] {story_title} (problematic Gutenberg heading)")
            continue

        heading_index = find_heading(
            lines,
            story_title,
            start_line=start_line,
        )

        if heading_index is None:
            print(f"[WARN] Heading not found: {story_title}")
            continue

        # Find next story heading.
        next_heading_index = len(lines)

        for later_title in stories[story_index + 1:]:
            if later_title in skip_stories:
                continue

            if (
                config["title"] == "Los Puritanos, y otros cuentos"
                and later_title == "El pajaro en la nieve"
            ):
                continue

            candidate = find_heading(
                lines,
                later_title,
                start_line=heading_index + 1,
            )

            if candidate is not None:
                next_heading_index = candidate
                break

        story_lines = lines[heading_index:next_heading_index]
        story_text = "\n".join(story_lines).strip()

        # --------------------------------------------------------------
        # Book-specific story notes
        # --------------------------------------------------------------

        story_note_markers = config.get("story_note_markers", {})

        if story_title in story_note_markers:
            marker = story_note_markers[story_title]
            story_text = trim_at_marker(
                story_text,
                [marker],
            )

        # --------------------------------------------------------------
        # Generic backmatter
        # --------------------------------------------------------------

        story_text = trim_at_marker(
            story_text,
            config.get("backmatter_markers", []),
        )

        # --------------------------------------------------------------
        # Frontmatter
        # --------------------------------------------------------------

        frontmatter_config = config.get(
            "frontmatter",
            {},
        ).get(story_title)

        story_text = trim_story_frontmatter(
            story_text,
            frontmatter_config,
        )

        story_text = story_text.strip()

        if not story_text:
            print(f"[WARN] Empty story: {story_title}")
            continue

        results.append({
            "index": story_index + 1,
            "title": story_title,
            "text": story_text,
            "start_line": heading_index,
            "end_line": next_heading_index - 1,
        })

        print(
            f"[OK] {story_index + 1:02d} "
            f"{story_title}: "
            f"{len(story_text):,} chars"
        )

        # Once we've found a real heading, don't search before it.
        start_line = heading_index + 1

    return results


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

def safe_filename(title):
    """
    Convert story title to a stable filesystem-friendly filename.
    """
    text = normalize_for_matching(title)

    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text,
    )

    text = text.strip("_")

    return text


def write_stories(book_id, config, stories):
    """
    Write individual story TXT files.
    """
    book_dir = STORY_DIR / book_id
    book_dir.mkdir(parents=True, exist_ok=True)

    for story in stories:
        filename = (
            f"{story['index']:02d}_"
            f"{safe_filename(story['title'])}.txt"
        )

        path = book_dir / filename

        path.write_text(
            story["text"] + "\n",
            encoding="utf-8",
        )

    print(
        f"[OK] Wrote {len(stories)} stories to "
        f"{book_dir}"
    )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    print()
    print("=" * 70)
    print("Tiny Iris — Gutenberg narrative corpus")
    print("=" * 70)
    print()

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    STORY_DIR.mkdir(parents=True, exist_ok=True)

    total_stories = 0
    total_chars = 0

    for book_id, config in BOOKS.items():

        print()
        print("-" * 70)
        print(f"{config['author']} — {config['title']}")
        print("-" * 70)

        source_path = download_book(
            book_id,
            config,
        )

        raw_text = source_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        raw_text = clean_text(raw_text)
        lines = remove_gutenberg_wrapper(raw_text)

        stories = extract_stories(
            lines,
            config,
        )

        write_stories(
            book_id,
            config,
            stories,
        )

        book_chars = sum(
            len(story["text"])
            for story in stories
        )

        print()
        print(
            f"[BOOK] {len(stories)} stories, "
            f"{book_chars:,} chars"
        )

        total_stories += len(stories)
        total_chars += book_chars

    print()
    print("=" * 70)
    print("TOTAL")
    print("=" * 70)
    print(f"Historias: {total_stories}")
    print(f"Caracteres: {total_chars:,}")
    print()


if __name__ == "__main__":
    main()
