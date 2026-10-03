import torch
from torch.utils.data import Dataset


class TinyDataset(Dataset):

    def __init__(self, data, block_size=64):
        self.block_size = block_size

        chars = sorted(list(set(data)))

        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}

        self.vocab_size = len(chars)
        self.data = data

        print(f"data has {len(data)} characters, {self.vocab_size} unique")

    def get_vocab_size(self):
        return self.vocab_size

    def get_block_size(self):
        return self.block_size

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        chunk = self.data[idx:idx + self.block_size + 1]

        dix = [self.stoi[ch] for ch in chunk]

        x = torch.tensor(dix[:-1], dtype=torch.long)
        y = torch.tensor(dix[1:], dtype=torch.long)

        return x, y
