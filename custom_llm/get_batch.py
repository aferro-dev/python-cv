import torch


def get_batch(*, data: torch.Tensor, block_size: int, batch_size: int, device="cpu"):
    if len(data) <= block_size:
        raise ValueError("data must contain more tokens than block_size")
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i : i + block_size] for i in ix])
    y = torch.stack([data[i + 1 : i + block_size + 1] for i in ix])
    x, y = x.to(device), y.to(device)
    return x, y
