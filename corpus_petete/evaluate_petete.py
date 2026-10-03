#!/usr/bin/env python3

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mingpt.model import GPT
from petete_dataset import load_text, build_vocab, PeteteDataset


CHECKPOINT = Path("petete_checkpoint.pt")
TEST_FILE = Path("petete_test.txt")

BLOCK_SIZE = 256


def main():

    print("=" * 70)
    print("TINY IRIS — PETETE EVALUATION")
    print("=" * 70)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    checkpoint = torch.load(
        CHECKPOINT,
        map_location=device,
        weights_only=False,
    )

    test_text = load_text(TEST_FILE)

    # Reconstruct the vocabulary used during training.
    stoi = checkpoint["stoi"]
    itos = checkpoint["itos"]

    vocab_size = checkpoint["vocab_size"]

    # JSON turns integer keys into strings.
    itos = {
        int(k): v
        for k, v in itos.items()
    }

    dataset = PeteteDataset(
        test_text,
        stoi,
        block_size=BLOCK_SIZE,
    )

    model_config = checkpoint["model_config"]

    model = GPT(model_config)
    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    losses = []

    # Evaluate a fixed number of random samples.
    # This is enough for a first sanity check.
    num_batches = 200
    batch_size = 16

    print()
    print(f"Device       : {device}")
    print(f"Test samples : {len(dataset):,}")
    print(f"Vocabulary   : {vocab_size}")
    print(f"Evaluating   : {num_batches} batches")
    print()

    with torch.no_grad():

        for i in range(num_batches):

            indices = torch.randint(
                0,
                len(dataset),
                (batch_size,),
            )

            x = torch.stack(
                [dataset[j][0] for j in indices]
            ).to(device)

            y = torch.stack(
                [dataset[j][1] for j in indices]
            ).to(device)

            _, loss = model(x, y)

            losses.append(loss.item())

    test_loss = sum(losses) / len(losses)

    print("=" * 70)
    print("EVALUATION")
    print("=" * 70)

    print(f"Train loss   : {checkpoint['final_loss']:.4f}")
    print(f"Test loss    : {test_loss:.4f}")
    print(
        f"Difference   : "
        f"{test_loss - checkpoint['final_loss']:+.4f}"
    )


if __name__ == "__main__":
    main()
