"""Caricamento lazy, una volta per processo. Installare l'extra `local`."""

from threading import Lock
from typing import Any


class InferenceEngine:
    def __init__(self, model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct"):
        self.model_id = model_id
        self.model: Any = None
        self.tokenizer: Any = None
        self.lock = Lock()

    def generate(self, prompt: str, max_new_tokens: int = 100) -> str:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # Il lock protegge anche il caricamento e l'uso concorrente del modello.
        with self.lock:
            if self.model is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
                self.model = (
                    AutoModelForCausalLM.from_pretrained(
                        self.model_id,
                        dtype="auto",
                    )
                    .to(device)
                    .eval()
                )
            messages = [{"role": "user", "content": prompt}]
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=4096).to(
                self.model.device
            )
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            return self.tokenizer.decode(
                outputs[0, inputs.input_ids.shape[1] :], skip_special_tokens=True
            )


def generate(prompt: str = "Explain what a neural network is.") -> str:
    return InferenceEngine().generate(prompt)
