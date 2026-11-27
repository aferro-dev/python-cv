import torch
import torch.nn as nn
from torch.nn import functional as F

from custom_llm.constants import DROPOUT, EMBEDDING_SIZE, HEAD_SIZE


class AttentionHead(nn.Module):
    def __init__(self):
        super().__init__()

        self.query = nn.Linear(EMBEDDING_SIZE, HEAD_SIZE)
        self.key = nn.Linear(EMBEDDING_SIZE, HEAD_SIZE)
        self.value = nn.Linear(EMBEDDING_SIZE, HEAD_SIZE)
        self.dropout = nn.Dropout(p=DROPOUT)

    def forward(self, tokens):

        query = self.query(tokens)
        key = self.key(tokens)
        value = self.value(tokens)
        attention_scores = (query @ key.transpose(-2, -1)) / key.shape[-1] ** 0.5
        mask = torch.tril(torch.ones_like(attention_scores)) == 0
        attention_scores = attention_scores.masked_fill(mask, float("-inf"))

        attention_weights = F.softmax(attention_scores, dim=-1)

        return self.dropout(attention_weights) @ value
