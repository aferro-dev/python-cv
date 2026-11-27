import torch
import torch.nn as nn

from custom_llm.constants import DROPOUT, EMBEDDING_SIZE, NUM_HEADS

from .attention_head import AttentionHead
from .feed_forward import FeedForward


class TransformerBlock(nn.Module):
    def __init__(
        self,
    ):
        super().__init__()
        self.attention_heads = nn.ModuleList([AttentionHead() for _ in range(NUM_HEADS)])
        self.feed_forward = FeedForward()
        self.layer_norm_1 = nn.LayerNorm(EMBEDDING_SIZE)
        self.layer_norm_2 = nn.LayerNorm(EMBEDDING_SIZE)

        self.dropout = nn.Dropout(p=DROPOUT)

    def forward(self, tokens):

        normalized_tokens = self.layer_norm_1(tokens)
        context = tokens + self.dropout(
            torch.cat(
                [head(normalized_tokens) for head in self.attention_heads],
                dim=-1,
            )
        )
        droped_context = self.feed_forward(self.layer_norm_2(context))
        context = context + droped_context
        return context
