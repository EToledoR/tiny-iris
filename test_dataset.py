from tiny_dataset import TinyDataset


with open("data/tiny.txt", "r") as f:
    text = f.read()

dataset = TinyDataset(text, block_size=32)

print("vocab size:", dataset.get_vocab_size())
print("block size:", dataset.get_block_size())
print("dataset length:", len(dataset))

x, y = dataset[0]

print("x:", x)
print("y:", y)

print("decoded x:", "".join(dataset.itos[int(i)] for i in x))
print("decoded y:", "".join(dataset.itos[int(i)] for i in y))
