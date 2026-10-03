#!/usr/bin/env python3

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mingpt.model import GPT
from petete_dataset import load_text


CHECKPOINT = Path("petete_checkpoint.pt")
TEST_FILE = Path("petete_test.txt")

ARTICLE_IDS = [3, 10, 30, 53, 61]
TEST_ARTICLE_IDS = [
    3, 10, 30, 53, 61, 82, 106, 107, 110, 111, 112, 116,
    127, 141, 146, 154, 170, 185, 188, 191, 194, 196, 207
]

BLOCK_SIZE = 256
PROMPT_CHARS = 64
GENERATE_CHARS = 300

TEMPERATURES = [0.5, 0.8]

SEPARATOR = "\n\n<|END_ARTICLE|>\n\n"


def encode(text, stoi):
    return [stoi[ch] for ch in text if ch in stoi]


def decode(ids, itos):
    return "".join(itos[i] for i in ids)


@torch.no_grad()
def generate(model, prompt, stoi, itos, temperature):

    ids = encode(prompt, stoi)

    for _ in range(GENERATE_CHARS):

        context = ids[-BLOCK_SIZE:]

        x = torch.tensor(
            [context],
            dtype=torch.long,
        )

        logits, _ = model(x)

        logits = logits[:, -1, :]
        logits = logits / temperature

        probs = torch.softmax(logits, dim=-1)

        next_id = torch.multinomial(
            probs,
            num_samples=1,
        ).item()

        ids.append(next_id)

    return decode(ids, itos)


def main():

    print("=" * 70)
    print("TINY IRIS — PETETE TEST COMPLETION")
    print("=" * 70)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    checkpoint = torch.load(
        CHECKPOINT,
        map_location=device,
        weights_only=False,
    )

    stoi = checkpoint["stoi"]

    itos = {
        int(k): v
        for k, v in checkpoint["itos"].items()
    }

    model_config = checkpoint["model_config"]

    model = GPT(model_config)

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    test_text = load_text(TEST_FILE)

    articles = test_text.split("<|END_ARTICLE|>")
    articles = [article.strip() for article in articles]

    print()
    print(f"Device       : {device}")
    print(f"Parameters   : {sum(p.numel() for p in model.parameters()):,}")
    print(f"Test articles: {len(articles)}")
    print(f"Article IDs  : {ARTICLE_IDS}")
    print()

    for article_id in ARTICLE_IDS:

        article_index = TEST_ARTICLE_IDS.index(article_id)
        article = articles[article_index]

        prompt = article[:PROMPT_CHARS]

        real_continuation = article[
            PROMPT_CHARS:
            PROMPT_CHARS + GENERATE_CHARS
        ]

        print()
        print("=" * 70)
        print(f"ARTICLE {article_id}")
        print("=" * 70)

        print()
        print(">>> PROMPT")
        print(prompt)

        print()
        print(">>> REAL CONTINUATION")
        print(real_continuation)

        for temperature in TEMPERATURES:

            generated = generate(
                model,
                prompt,
                stoi,
                itos,
                temperature,
            )

            generated_continuation = generated[
                PROMPT_CHARS:
            ]

            print()
            print("-" * 70)
            print(
                f">>> MODEL — TEMPERATURE {temperature}"
            )
            print("-" * 70)
            print(generated_continuation)

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
