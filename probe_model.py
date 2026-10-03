import torch

from mingpt.model import GPT


# Configuraciones que Karpathy ya incluyó en minGPT.
MODELS = [
    "gpt-nano",
    "gpt-micro",
    "gpt-mini",
]


def inspect_model(model_type):
    config = GPT.get_default_config()

    config.model_type = model_type
    config.vocab_size = 8192
    config.block_size = 128

    model = GPT(config)
    model.eval()

    # Contamos TODOS los parámetros, incluido lm_head.
    total_params = sum(
        p.numel() for p in model.parameters()
    )

    memory_mb = sum(
        p.numel() * p.element_size()
        for p in model.parameters()
    ) / (1024 ** 2)

    # Pequeña secuencia artificial de 16 tokens.
    tokens = torch.randint(
        low=0,
        high=config.vocab_size,
        size=(1, 16),
    )

    with torch.no_grad():
        logits, loss = model(tokens)

    print(f"\nModel: {model_type}")
    print(f"Parameters: {total_params:,}")
    print(f"Weight memory: {memory_mb:.2f} MiB")
    print(f"Input shape: {tuple(tokens.shape)}")
    print(f"Output shape: {tuple(logits.shape)}")
    print(f"Forward pass: OK")


if __name__ == "__main__":
    for model_type in MODELS:
        inspect_model(model_type)
