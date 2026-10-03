#!/usr/bin/env python3

import sys
import time
from pathlib import Path

import torch

# ---------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mingpt.model import GPT
from mingpt.trainer import Trainer

from petete_dataset import (
    load_text,
    build_vocab,
    PeteteDataset,
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

TRAIN_FILE = Path("petete_train.txt")
TEST_FILE = Path("petete_test.txt")

CHECKPOINT_FILE = Path("petete_checkpoint.pt")

BLOCK_SIZE = 256
BATCH_SIZE = 16
MAX_ITERS = 10000

# Same learning rate as our previous Tiny Iris experiment.
LEARNING_RATE = 1e-3

PRINT_EVERY = 100


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("TINY IRIS — PETETE TRAINING")
    print("=" * 70)

    # -----------------------------------------------------------------
    # Device
    # -----------------------------------------------------------------

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Device       : {device}")
    print(f"Block size   : {BLOCK_SIZE}")
    print(f"Batch size   : {BATCH_SIZE}")
    print(f"Max iters    : {MAX_ITERS}")
    print(f"Print every  : {PRINT_EVERY}")

    # -----------------------------------------------------------------
    # Load corpus
    # -----------------------------------------------------------------

    train_text = load_text(TRAIN_FILE)
    test_text = load_text(TEST_FILE)

    print()
    print(f"Train chars  : {len(train_text):,}")
    print(f"Test chars   : {len(test_text):,}")

    # IMPORTANT:
    # Build vocabulary ONLY from training data.
    stoi, itos = build_vocab(train_text)
    vocab_size = len(stoi)

    print(f"Vocabulary   : {vocab_size}")

    # -----------------------------------------------------------------
    # Dataset
    # -----------------------------------------------------------------

    train_dataset = PeteteDataset(
        train_text,
        stoi,
        block_size=BLOCK_SIZE,
    )

    test_dataset = PeteteDataset(
        test_text,
        stoi,
        block_size=BLOCK_SIZE,
    )

    print()
    print(f"Train samples: {len(train_dataset):,}")
    print(f"Test samples : {len(test_dataset):,}")

    # -----------------------------------------------------------------
    # GPT-Nano configuration
    # -----------------------------------------------------------------

    model_config = GPT.get_default_config()

    # We specify the architecture explicitly.
    model_config.model_type = None

    model_config.n_layer = 4
    model_config.n_head = 4
    model_config.n_embd = 128

    model_config.vocab_size = vocab_size
    model_config.block_size = BLOCK_SIZE

    # -----------------------------------------------------------------
    # Model
    # -----------------------------------------------------------------

    model = GPT(model_config)

    parameters = sum(
        p.numel()
        for p in model.parameters()
    )

    print()
    print("Model:")
    print(f"Parameters   : {parameters:,}")

    # -----------------------------------------------------------------
    # Trainer configuration
    # -----------------------------------------------------------------

    trainer_config = Trainer.get_default_config()

    trainer_config.device = device
    trainer_config.num_workers = 0

    trainer_config.max_iters = MAX_ITERS
    trainer_config.batch_size = BATCH_SIZE
    trainer_config.learning_rate = LEARNING_RATE

    print()
    print("Training configuration:")
    print(f"Learning rate: {trainer_config.learning_rate}")
    print(f"Weight decay : {trainer_config.weight_decay}")
    print(f"Grad clip    : {trainer_config.grad_norm_clip}")

    # -----------------------------------------------------------------
    # Trainer
    # -----------------------------------------------------------------

    trainer = Trainer(
        trainer_config,
        model,
        train_dataset,
    )

    # -----------------------------------------------------------------
    # Progress reporting
    # -----------------------------------------------------------------

    progress = {
        "last_time": time.time(),
        "last_iter": 0,
    }

    def print_progress(trainer):

        if trainer.iter_num % PRINT_EVERY != 0:
            return

        now = time.time()

        elapsed = now - progress["last_time"]
        iterations = trainer.iter_num - progress["last_iter"]

        if iterations > 0:
            iter_per_sec = iterations / elapsed
        else:
            iter_per_sec = 0.0

        print(
            f"iter {trainer.iter_num:5d} | "
            f"loss {trainer.loss.item():.4f} | "
            f"{iter_per_sec:6.1f} iter/s"
        )

        progress["last_time"] = now
        progress["last_iter"] = trainer.iter_num

    trainer.set_callback(
        "on_batch_end",
        print_progress,
    )

    # -----------------------------------------------------------------
    # Training
    # -----------------------------------------------------------------

    print()
    print("Starting training...")
    print()

    start_time = time.time()

    trainer.run()

    total_time = time.time() - start_time

    # -----------------------------------------------------------------
    # Save checkpoint
    # -----------------------------------------------------------------

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "model_config": model_config,
        "vocab_size": vocab_size,
        "stoi": stoi,
        "itos": itos,
        "block_size": BLOCK_SIZE,
        "train_chars": len(train_text),
        "test_chars": len(test_text),
        "iterations": MAX_ITERS,
        "learning_rate": LEARNING_RATE,
        "final_loss": trainer.loss.item(),
    }

    torch.save(
        checkpoint,
        CHECKPOINT_FILE,
    )

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------

    print()
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print(f"Iterations   : {MAX_ITERS:,}")
    print(f"Final loss   : {trainer.loss.item():.4f}")
    print(f"Total time   : {total_time:.1f}s")

    if total_time > 0:
        print(
            f"Iterations/s : "
            f"{MAX_ITERS / total_time:.1f}"
        )

    print(f"Checkpoint   : {CHECKPOINT_FILE}")


if __name__ == "__main__":
    main()
