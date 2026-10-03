#!/usr/bin/env python3

import sys
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mingpt.model import GPT


CHECKPOINT = Path("petete_checkpoint.pt")

BLOCK_SIZE = 256


def generate(model, context, stoi, itos, max_new_tokens=300, temperature=0.8):

    model.eval()

    device = next(model.parameters()).device

    ids = [
        stoi[c]
        for c in context
        if c in stoi
    ]

    x = torch.tensor(
        [ids],
        dtype=torch.long,
        device=device,
    )

    with torch.no_grad():

        for _ in range(max_new_tokens):

            # Only keep the last block_size characters.
            x_cond = x[:, -BLOCK_SIZE:]

            logits, _ = model(x_cond)

            logits = logits[:, -1, :]
            logits = logits / temperature

            probabilities = F.softmax(
                logits,
                dim=-1,
            )

            next_token = torch.multinomial(
                probabilities,
                num_samples=1,
            )

            x = torch.cat(
                (x, next_token),
                dim=1,
            )

    generated_ids = x[0].tolist()

    return "".join(
        itos[i]
        for i in generated_ids
    )


def main():

    print("=" * 70)
    print("TINY IRIS — PETETE GENERATION")
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

    print()
    print(f"Device     : {device}")
    print(f"Parameters : {sum(p.numel() for p in model.parameters()):,}")
    print(f"Train loss : {checkpoint['final_loss']:.4f}")

    prompts = [
        "El cerebro",
        "Los animales",
        "El cacao",
        "La Tierra",
    ]

    temperatures = [0.5, 0.8, 1.0]

    for temperature in temperatures:

        print()
        print("=" * 70)
        print(f"TEMPERATURE {temperature}")
        print("=" * 70)

        for prompt in prompts:

            print()
            print(f">>> {prompt}")
            print()

            text = generate(
                model,
                prompt,
                stoi,
                itos,
                max_new_tokens=300,
                temperature=temperature,
            )

            print(text)


if __name__ == "__main__":
    main()
