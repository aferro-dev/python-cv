import torch
import torch.nn as nn
from torch.nn import functional as F

from custom_llm.constants import BLOCK_SIZE, EMBEDDING_SIZE, NUM_LAYERS

from .transformer_block import TransformerBlock


class BiagramLanguageModel(nn.Module):
    def __init__(self, vocab_size):

        super().__init__()
        self.block_size = BLOCK_SIZE
        self.token_embedding_table = nn.Embedding(vocab_size, EMBEDDING_SIZE)
        self.positional_embedding = nn.Embedding(BLOCK_SIZE, EMBEDDING_SIZE, NUM_LAYERS)
        self.transformer_blocks = nn.ModuleList([TransformerBlock() for _ in range(NUM_LAYERS)])
        self.linear = nn.Linear(EMBEDDING_SIZE, vocab_size)

    def forward(self, idx, targets=None):

        tokens = self.token_embedding_table(idx) + self.positional_embedding(
            torch.arange(idx.shape[1], device=idx.device)
        )
        context = tokens

        for block in self.transformer_blocks:
            context = block(context)

        logits = self.linear(context)
        if targets is None:
            loss = None
        else:
            B, T, C = logits.shape
            logits = logits.view(B * T, C)
            targets = targets.view(B * T)
            loss = F.cross_entropy(logits, targets)
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens):
        for _ in range(max_new_tokens):
            logits, loss = self(idx[:, -self.block_size :])
            logits = logits[:, -1, :]
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx
