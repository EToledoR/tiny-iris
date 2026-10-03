#!/usr/bin/env python3

from pathlib import Path
import json

import torch
from torch.utils.data import Dataset


TRAIN_FILE = Path("petete_train.txt")
TEST_FILE = Path("petete_test.txt")

OUTPUT_DIR = Path("petete_vocab")


class PeteteDataset(Dataset):
    def __init__(
        self,
        text,
        stoi,
        block_size=64,
    ):
        self.text = text
        self.stoi = stoi
        self.block_size = block_size

        # Convertimos todo el corpus a IDs una sola vez.
        self.data = torch.tensor(
            [stoi[c] for c in text],
            dtype=torch.long,
        )

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]

        return x, y


def load_text(path):
    return path.read_text(encoding="utf-8")


def build_vocab(text):
    chars = sorted(set(text))

    stoi = {
        ch: i
        for i, ch in enumerate(chars)
    }

    itos = {
        i: ch
        for ch, i in stoi.items()
    }

    return stoi, itos


def encode(text, stoi):
    return [stoi[c] for c in text]


def decode(ids, itos):
    return "".join(itos[i] for i in ids)


def main():
    print("Loading Petete corpus...")

    train_text = load_text(TRAIN_FILE)
    test_text = load_text(TEST_FILE)

    print(f"Train characters: {len(train_text):,}")
    print(f"Test characters : {len(test_text):,}")

    # IMPORTANT:
    # vocabulary is built ONLY from the training corpus.
    stoi, itos = build_vocab(train_text)

    print(f"Vocabulary size : {len(stoi)}")
    print()

    print("Characters:")
    print(repr("".join(stoi.keys())))

    # Check that test does not contain unknown characters.
    unknown = sorted(
        set(test_text) - set(stoi.keys())
    )

    if unknown:
        print()
        print("WARNING: test contains unknown characters:")
        print(repr(unknown))
        raise ValueError(
            "Test vocabulary contains characters absent from training."
        )

    OUTPUT_DIR.mkdir(exist_ok=True)

    vocab = {
        "stoi": stoi,
        "itos": {
            str(k): v
            for k, v in itos.items()
        },
    }

    with (OUTPUT_DIR / "vocab.json").open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            vocab,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Vocabulary saved to: {OUTPUT_DIR / 'vocab.json'}")

    # Quick sanity check
    sample = train_text[:200]

    encoded = encode(sample, stoi)
    decoded = decode(encoded, itos)

    assert decoded == sample

    print()
    print("Encode/decode test: OK")
    print()
    print("Sample:")
    print(decoded[:200])

    # Dataset objects
    train_dataset = PeteteDataset(
        train_text,
        stoi,
        block_size=64,
    )

    test_dataset = PeteteDataset(
        test_text,
        stoi,
        block_size=64,
    )

    print()
    print("Dataset:")
    print(f"Train samples: {len(train_dataset):,}")
    print(f"Test samples : {len(test_dataset):,}")

    x, y = train_dataset[0]

    print()
    print("First sample:")
    print("x:", x[:20].tolist())
    print("y:", y[:20].tolist())

    print()
    print("Decoded x:")
    print(decode(x.tolist(), itos))

    print()
    print("Decoded y:")
    print(decode(y.tolist(), itos))


if __name__ == "__main__":
    main()
