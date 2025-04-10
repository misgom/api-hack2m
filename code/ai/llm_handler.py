from typing import List, Dict, Any, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from config.settings import Settings
import torch
import os
from log.logger import logger

class LLMHandler:
    _instance = None
    _initialized = False

    def __new__(cls, settings: Optional[Settings] = None):
        if cls._instance is None:
            if settings is None:
                raise ValueError("Settings must be provided for first initialization")
            cls._instance = super(LLMHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, settings: Optional[Settings] = None):
        if not self._initialized and settings is not None:
            self.settings = settings
            self.model = None
            self.tokenizer = None
            self._load_model()
            self._initialized = True

    def _load_model(self) -> None:
        """
        Load the LLM model with the specified quantization settings.
        """

        # Log model loading configuration
        logger.info(
            "Loading LLM model",
            model_path=self.settings.LLM_MODEL,
            quantization=self.settings.LLM_QUANTIZATION,
            load_in_8bit=self.settings.LLM_LOAD_IN_8BIT
        )

        # Configure quantization
        quantization_config = None
        if self.settings.LLM_QUANTIZATION and self.settings.LLM_LOAD_IN_8BIT:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True
            )

        # Load model with specified quantization
        self.model = AutoModelForCausalLM.from_pretrained(
            self.settings.LLM_MODEL,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16 if not quantization_config else None
        )

        self.tokenizer = AutoTokenizer.from_pretrained(self.settings.LLM_MODEL)

        # Clear CUDA cache after model loading
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("LLM model loaded successfully")

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generate text based on the given prompt.

        Args:
            prompt: Input text to generate from
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated text
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")

        # Generate
        max_tokens = max_tokens or self.settings.LLM_MAX_TOKENS
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            pad_token_id=self.tokenizer.eos_token_id
        )

        # Clear CUDA cache after generation
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Decode and return
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    @classmethod
    def get_instance(cls) -> 'LLMHandler':
        """
        Get the singleton instance of the LLM handler.

        Returns:
            LLMHandler instance
        """
        if cls._instance is None:
            raise RuntimeError("LLMHandler not initialized. Call LLMHandler(settings) first.")
        return cls._instance

    def __del__(self):
        """
        Cleanup resources when the handler is destroyed.
        """
        if self.model:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
