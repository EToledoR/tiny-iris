import time

import torch

from mingpt.model import GPT


def benchmark(model_type, steps=20):
    config = GPT.get_default_config()

    config.model_type = model_type
    config.vocab_size = 8192
    config.block_size = 128

    model = GPT(config)
    model.train()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=1e-3,
    )

    # Un batch pequeño para empezar.
    batch_size = 4
    sequence_length = config.block_size

    x = torch.randint(
        0,
        config.vocab_size,
        (batch_size, sequence_length),
    )

    y = torch.randint(
        0,
        config.vocab_size,
        (batch_size, sequence_length),
    )

    # Una iteración de calentamiento.
    logits, loss = model(x, y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    start = time.perf_counter()

    for _ in range(steps):
        logits, loss = model(x, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    elapsed = time.perf_counter() - start

    tokens = steps * batch_size * sequence_length

    print(f"\n{model_type}")
    print(f"Steps: {steps}")
    print(f"Time: {elapsed:.2f} s")
    print(f"Tokens: {tokens:,}")
    print(f"Tokens/s: {tokens / elapsed:.1f}")
    print(f"Final loss: {loss.item():.4f}")


if __name__ == "__main__":
    for model_type in [
        "gpt-nano",
        "gpt-micro",
        "gpt-mini",
    ]:
        benchmark(model_type)
