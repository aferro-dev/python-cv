"""Baseline lessicale locale: chunk sovrapposti e ranking BM25, senza download."""

import math
import re
from collections import Counter

from app.db import Document
from app.schemas import Source


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


def retrieve(documents: list[Document], question: str, top_k: int) -> list[Source]:
    chunks = [
        (doc, doc.content[start : start + 1000])
        for doc in documents
        for start in range(0, len(doc.content), 800)
    ]
    if not chunks:
        return []
    tokens = [tokenize(chunk) for _, chunk in chunks]
    average = sum(map(len, tokens)) / len(tokens) or 1
    query = set(tokenize(question))
    frequencies = {term: sum(term in row for row in tokens) for term in query}
    results = []
    for (doc, chunk), row in zip(chunks, tokens, strict=True):
        counts = Counter(row)
        score = 0.0
        for term in query:
            frequency = counts[term]
            inverse = math.log(
                1 + (len(chunks) - frequencies[term] + 0.5) / (frequencies[term] + 0.5)
            )
            score += (
                inverse * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * len(row) / average))
            )
        if score > 0:
            results.append(Source(document_id=doc.id, title=doc.title, excerpt=chunk, score=score))
    return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]
