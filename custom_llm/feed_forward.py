import torch.nn as nn
from torch.nn import functional as F

from custom_llm.constants import DROPOUT, EMBEDDING_SIZE, HIDDEN_SIZE


class FeedForward(nn.Module):
    def __init__(self):
        super().__init__()
        self.input = nn.Linear(EMBEDDING_SIZE, HIDDEN_SIZE)
        self.ouput = nn.Linear(HIDDEN_SIZE, EMBEDDING_SIZE)
        self.dropout = nn.Dropout(p=DROPOUT)

    def forward(self, context):
        features = self.input(context)
        relu_features = F.relu(features)
        output = self.ouput(relu_features)
        droped_output = self.dropout(output)
        return droped_output
