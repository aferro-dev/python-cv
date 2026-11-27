"""Training esplicito: nessun file letto o training eseguito durante l'import."""

import argparse
from pathlib import Path

import torch

from .biagram_model import BiagramLanguageModel
from .constants import BATCH_SIZE, BLOCK_SIZE, EVAL_INTERVAL, LEARNING_RATE, MAX_ITERS
from .estimate_loss import estimate_loss
from .get_batch import get_batch


def main():
    parser = argparse.ArgumentParser(description="Addestra un piccolo Transformer character-level")
    parser.add_argument("input", type=Path, help="Corpus UTF-8")
    parser.add_argument("--steps", type=int, default=MAX_ITERS)
    parser.add_argument("--output", type=Path, default=Path("checkpoint.pt"))
    args = parser.parse_args()
    torch.manual_seed(1337)
    text = args.input.read_text(encoding="utf-8")
    chars = sorted(set(text))
    stoi = {char: index for index, char in enumerate(chars)}
    data = torch.tensor([stoi[char] for char in text], dtype=torch.long)
    split = int(0.9 * len(data))
    train_data, val_data = data[:split], data[split:]
    if min(len(train_data), len(val_data)) <= BLOCK_SIZE:
        parser.error(f"Il corpus deve fornire più di {BLOCK_SIZE} caratteri in ciascuno split")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = BiagramLanguageModel(len(chars)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    model.train()
    for step in range(args.steps):
        if step % EVAL_INTERVAL == 0:
            print(
                f"step={step} train={estimate_loss(model, train_data):.4f} "
                f"val={estimate_loss(model, val_data):.4f}"
            )
        xb, yb = get_batch(
            data=train_data, batch_size=BATCH_SIZE, block_size=BLOCK_SIZE, device=device
        )
        _, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    torch.save({"model": model.state_dict(), "chars": chars}, args.output)
    model.eval()
    output = model.generate(torch.zeros((1, 1), dtype=torch.long, device=device), 500)
    print("".join(chars[index] for index in output[0].tolist()))


if __name__ == "__main__":
    main()
