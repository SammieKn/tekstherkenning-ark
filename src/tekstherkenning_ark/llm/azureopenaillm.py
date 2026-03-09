"""
This module originates from Arcadis and is used to interact with the Azure OpenAI API.
"""

from openai import AsyncAzureOpenAI
from openai.types.completion_usage import CompletionUsage
from dotenv import load_dotenv
import os
import tiktoken
from tekstherkenning_ark.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class AzureOpenAILLM:

    def __init__(self, input_api_key: str | None = None, model_name: str | None = None):
        """
        Initialize an instance of the AzureOpenAILLM class. This class is used
        to interact with the Azure OpenAI API. The GTP-3.5 models we currently
        offer use the cl100k_base encoding. The GPT-4o model uses the
        o200k_base encoding instead.
        NOTE: Please update the api_version as you see fit.
        For more information on encodings tiktoken uses, see
        https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb.

        Parameters
        ----------
        input_api_key : str, optioneel
            De Azure OpenAI API key. Standaard wordt AZURE_OPENAI_KEY uit de
            environment variabelen gebruikt.
        model_name : str, optioneel
            De naam van het model deployment. Standaard wordt DEPLOYMENT_NAME_GPT41
            uit de environment variabelen gebruikt.

        Raises
        ------
        ValueError
            Als de benodigde API key of model naam niet beschikbaar is.
        """
        if input_api_key is None:
            input_api_key = os.environ.get("AZURE_OPENAI_KEY")
            if not input_api_key:
                raise ValueError("AZURE_OPENAI_KEY environment variabele is niet ingesteld.")

        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variabele is niet ingesteld.")

        azure_openai_version = os.environ.get("AZURE_OPENAI_API_VERSION")
        if not azure_openai_version:
            raise ValueError("AZURE_OPENAI_API_VERSION environment variabele is niet ingesteld.")

        azure_encoding_name = os.environ.get("AZURE_OPENAI_ENCODING_NAME")
        if not azure_encoding_name:
            raise ValueError("AZURE_OPENAI_ENCODING_NAME environment variabele is niet ingesteld.")

        azure_model_name = os.environ.get("AZURE_MODEL_NAME")
        if model_name is None and not azure_model_name:
            raise ValueError("AZURE_MODEL_NAME environment variabele is niet ingesteld.")

        self.model = azure_model_name or model_name

        self.client = AsyncAzureOpenAI(
            api_key=input_api_key,
            azure_endpoint=azure_endpoint,
            api_version=azure_openai_version,
        )
        self.encoding = tiktoken.get_encoding(azure_encoding_name)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - sluit de client netjes af."""
        await self.aclose()
        return False

    async def aclose(self):
        """Sluit de async client netjes af."""
        if self.client:
            await self.client.close()

    async def chat_completion(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0,
        system: str = "You are an OpenAI chatbot. You should use professional language and give brief replies where possible while retaining all context.",
        get_tokens: bool = False,
    ) -> str | None:
        """Function to create a chat completion request. Works by pushing
        request to the model with optional parameters. Reports the number
        of tokens used in the request as reported by the model resource if
        get_tokens is set to True."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},  # Describes the role the assistant should take.
                    {"role": "user", "content": prompt},  # The request that is send to the model.
                ],
                max_tokens=max_tokens,  # Max number of tokens available for the response. Has a hard cut-off when limit is reached.
                temperature=temperature,  # Defines the 'randomness' of the model, with higher numbers being more creative but less consistent.
            )

            if get_tokens:
                usage: CompletionUsage = response.usage
                usage_dict = usage.to_dict()
                logger.debug("==============================================")
                logger.debug("Token usage details:")
                for key, value in usage_dict.items():
                    logger.debug(f"{key}: {value}")
                logger.debug("==============================================")
        except Exception as e:
            logger.error(f"OpenAI error: {e}\nInput: {prompt}")
            return ""
        return response.choices[0].message.content

    async def validate_api_key(self) -> tuple[bool, str]:
        """Validate the API key with a minimal request."""

        logger.info("Validating Azure OpenAI API key...")

        test_prompt = "Hello, world!"
        response = await self.chat_completion(test_prompt)
        if not response is None and len(response) > 0 and not "error" in response.lower():
            return True, response
        return False, response

    def count_prompt_tokens(self, system: str, prompt: str) -> list[int]:
        """
        Tokenize the system and prompt text combo using tiktoken, print the
        length of the list of tokens (aka the number of tokens) and return the
        tokens themselves in case they are needed. The first 300 characters of
        the combined system text and prompt are provided to give context.
        NOTE 1. 3 tokens are added per message, system or user.
        """
        text = system + prompt
        tokens = self.encoding.encode(text)
        tokens_number = len(tokens)  # system and user prompts tokens
        tokens_number += 6  # 3 tokens per message (system and user)
        logger.debug(
            f"The number of tokens corresponding to the combined text '{text[0:300]}[...]' is: {tokens_number}."
        )
        return tokens
