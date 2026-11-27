import torch

from .biagram_model import BiagramLanguageModel
from .constants import BATCH_SIZE, BLOCK_SIZE, EVAL_ITERS
from .get_batch import get_batch


@torch.no_grad()
def estimate_loss(model: BiagramLanguageModel, data: torch.Tensor) -> float:
    was_training = model.training
    model.eval()
    losses = []
    try:
        for _ in range(EVAL_ITERS):
            xb, yb = get_batch(
                data=data,
                batch_size=BATCH_SIZE,
                block_size=BLOCK_SIZE,
                device=next(model.parameters()).device,
            )
            _, loss = model(xb, yb)
            losses.append(loss.item())
    finally:
        model.train(was_training)
    return sum(losses) / len(losses)
