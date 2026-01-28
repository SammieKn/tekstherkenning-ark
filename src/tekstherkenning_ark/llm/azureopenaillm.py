"""
This module originates from Arcadis and is used to interact with the Azure OpenAI API.
"""

from openai import AzureOpenAI
from openai.types.completion_usage import CompletionUsage
from dotenv import load_dotenv
import os
import tiktoken

load_dotenv()


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

        if model_name is None:
            model_name = os.environ.get("DEPLOYMENT_NAME_GPT41")
            if not model_name:
                raise ValueError("DEPLOYMENT_NAME_GPT41 environment variabele is niet ingesteld.")

        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variabele is niet ingesteld.")

        self.model = model_name
        self.model_params = self.get_model_params(self.model)
        self.client = AzureOpenAI(
            api_key=input_api_key, azure_endpoint=azure_endpoint, api_version=self.model_params["api_version"]
        )
        self.encoding = tiktoken.get_encoding(self.model_params["encoding_name"])

    def get_model_params(self, model: str) -> dict[str, str]:
        """Get the model parameters for the Azure OpenAI API.
        Update as required."""
        model_params = {}
        if model == "arcadisgpt-gpt35-0125":
            model_params["api_version"] = "2023-05-15"
            model_params["encoding_name"] = "cl100k_base"
        elif model == "gpt-4o":
            model_params["api_version"] = "2024-06-01"
            model_params["encoding_name"] = "o200k_base"
        elif model == "gpt-41":
            model_params["api_version"] = "2024-06-01"
            model_params["encoding_name"] = "o200k_base"
        elif model == "gpt-41-mini":
            model_params["api_version"] = "2024-06-01"
            model_params["encoding_name"] = "o200k_base"
        elif model == "gpt-5":
            model_params["api_version"] = "2024-06-01"
            model_params["encoding_name"] = "o200k_base"
        elif model == "gpt-5-mini":
            model_params["api_version"] = "2024-06-01"
            model_params["encoding_name"] = "o200k_base"
        else:
            raise ValueError(f"Model name {model} is not supported.")
        return model_params

    def chat_completion(
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
            response = self.client.chat.completions.create(
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
                print("==============================================")
                print("Token usage details:")
                for key, value in usage_dict.items():
                    print(f"{key}: {value}")
                print("==============================================")
        except Exception as e:
            print(f"OpenAI error: {e}\nInput: {prompt}")
            return ""
        return response.choices[0].message.content

    def validate_api_key(self) -> tuple[bool, str]:
        """Validate the API key with a minimal request."""

        print("Validating Azure OpenAI API key...")

        test_prompt = "Hello, world!"
        response = self.chat_completion(test_prompt)
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
        print(
            f"The number of tokens corresponding to the combined text '{text[0:300]}[...]' is:", f" {tokens_number}."
        )
        return tokens
