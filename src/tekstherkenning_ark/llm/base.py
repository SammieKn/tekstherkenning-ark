"""Base class voor LLM classificatie modellen."""

from __future__ import annotations

from typing import ClassVar, Self

from pydantic import BaseModel

from tekstherkenning_ark.llm.llm import AzureOpenAILLM


class LLMClassificeerbaar(BaseModel):
    """Generieke base class voor modellen die via LLM geclassificeerd worden.

    Subclasses dienen `_systeem_prompt` als ClassVar te definiëren met een
    specifieke prompt voor het betreffende model.

    Attributes
    ----------
    Geen standaard attributen - subclasses definiëren hun eigen velden.
    """

    _systeem_prompt: ClassVar[str]

    @classmethod
    def classificeer_omschrijving(cls, omschrijving: str) -> Self:
        """Classificeer een omschrijving naar een instantie van dit model via Azure OpenAI.

        Parameters
        ----------
        omschrijving : str
            De omschrijving tekst om te classificeren.

        Returns
        -------
        Self
            Een instantie van het betreffende model met geëxtraheerde waarden.

        Raises
        ------
        ValueError
            Als de LLM geen geldig resultaat retourneert.
        """
        llm = AzureOpenAILLM()

        response = llm.client.beta.chat.completions.parse(
            model=llm.model,
            messages=[
                {"role": "system", "content": cls._systeem_prompt},
                {"role": "user", "content": f"Classificeer de volgende omschrijving:\n\n{omschrijving}"},
            ],
            response_format=cls,
            temperature=0,
        )

        parsed_result = response.choices[0].message.parsed
        if parsed_result is None:
            raise ValueError("Kon de omschrijving niet classificeren: geen resultaat ontvangen van LLM")

        return parsed_result
