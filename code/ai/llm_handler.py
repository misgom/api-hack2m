from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
from config.settings import Settings
import torch
from log.logger import get_logger

logger = get_logger("llm")

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
            f"Loading LLM model: {self.settings.LLM_MODEL} - quantization={self.settings.LLM_QUANTIZATION}, load_in_8bit={self.settings.LLM_LOAD_IN_8BIT}"
        )

        # Configure quantization
        quantization_config = None
        if self.settings.LLM_QUANTIZATION and self.settings.LLM_LOAD_IN_8BIT:
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True
            )

        try:
            # Load model with specified quantization
            self.model = AutoModelForCausalLM.from_pretrained(
                self.settings.LLM_MODEL,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.bfloat16 if quantization_config else None
            )
            logger.info(f"Model loaded successfully: {self.settings.LLM_MODEL}")
        except Exception as e:
            logger.exception("Error loading model", exc=e)
            raise

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.settings.LLM_MODEL)
            logger.info(f"Tokenizer loaded successfully: {self.settings.LLM_MODEL}")
        except Exception as e:
            logger.exception("Error loading tokenizer", exc=e)
            raise

    def generate(self, prompt: str, system_prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generate text based on the given prompt and system prompt.

        Args:
            prompt: User's input prompt
            system_prompt: System prompt for context
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated text
        """
        logger.info("Generating response from LLM")
        try:
            # Prepare messages in chat format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            """
            # Apply chat template
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize the formatted prompt
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)

            # Generate
            max_tokens = max_tokens or self.settings.LLM_MAX_TOKENS
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                pad_token_id=self.tokenizer.eos_token_id
            )"""
            pipe = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)

            outputs = pipe(messages,max_new_tokens=4096)
            response = outputs[0]["generated_text"][-1].get("content")

            # Clear CUDA cache after generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Decode and return
            # response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from the response
            # response = response.replace(formatted_prompt, "").strip()
            return response
        except Exception as e:
            logger.exception("Error generating response", exc=e)
            raise

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
        """Clean up resources when the handler is destroyed."""
        try:
            if self.model is not None:
                del self.model
                logger.info("Model unloaded successfully")
            if self.tokenizer is not None:
                del self.tokenizer
                logger.info("Tokenizer unloaded successfully")
        except Exception as e:
            logger.exception("Error during cleanup", exc=e)
