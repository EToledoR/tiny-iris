import torch

from mingpt.model import GPT
from tiny_dataset import TinyDataset


# ------------------------------------------------------------
# Dataset
# ------------------------------------------------------------

with open("data/tiny.txt", "r") as f:
    text = f.read()

dataset = TinyDataset(text, block_size=32)


# ------------------------------------------------------------
# Model
# ------------------------------------------------------------

config = GPT.get_default_config()
config.model_type = "gpt-nano"
config.vocab_size = dataset.get_vocab_size()
config.block_size = dataset.get_block_size()

model = GPT(config)

print()
print("Model:")
print(model)
print()


# ------------------------------------------------------------
# Optimizer
# ------------------------------------------------------------

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3
)


# ------------------------------------------------------------
# Training
# ------------------------------------------------------------

model.train()

batch_size = 16

for step in range(50000):

    # Pick a random batch of training examples
    indices = torch.randint(len(dataset), (batch_size,))

    x = torch.stack([dataset[i][0] for i in indices])
    y = torch.stack([dataset[i][1] for i in indices])

    # Forward pass
    logits, loss = model(x, y)

    # Backward pass
    optimizer.zero_grad(set_to_none=True)
    loss.backward()

    # Update weights
    optimizer.step()

    if step % 500 == 0:
        print(f"step {step:5d} | loss {loss.item():.4f}")

# ------------------------------------------------------------
# Generate
# ------------------------------------------------------------

model.eval()

prompt = "Iris"

x = torch.tensor(
    [[dataset.stoi[ch] for ch in prompt]],
    dtype=torch.long
)

y = model.generate(
    x,
    100,
    temperature=0.8,
    do_sample=True,
    top_k=5
)

result = "".join(
    dataset.itos[int(i)]
    for i in y[0]
)

print()
print("Generated:")
print(result)

torch.save(model.state_dict(), "tiny_iris_char.pt")
print("\nModel saved to tiny_iris_char.pt")
