"""Tests voor LLM-gebaseerde gebrektype detectie."""

import pytest
from unittest.mock import AsyncMock, patch
import anyio

from tekstherkenning_ark.models.gebrek import (
    Gebrek,
    Scheur,
    GrondVoerendGat,
    LokaalVerdwenenMetselwerk,
    BuikInWand,
    Scheefstand,
    OnderloopsheidschermBeschadigd,
)
from tekstherkenning_ark.llm.gebrek_classificatie import GebrekTypeDetectieLLM
from tekstherkenning_ark.enums import NietBeschikbaar


class TestGebrekTypeDetectie:
    """Test suite voor gebrektype detectie met LLM."""

    def test_grondvoerend_gat_detectie(self):
        """Test detectie van grondvoerend gat via LLM."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB1",
                omschrijving="Grondvoerend gat achter het metselwerk, 30x40x50 cm",
                figuurnummer="1",
            )

            # Mock de LLM type detectie
            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=True,
                    is_buik_of_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                # Mock de attribuut extractie
                with patch(
                    "tekstherkenning_ark.models.gebrek.GrondVoerendGatLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_extract:
                    from tekstherkenning_ark.llm.gebrek_classificatie import GrondVoerendGatLLM

                    mock_extract.return_value = GrondVoerendGatLLM(
                        afstand_van_startrak_m=NietBeschikbaar.LEEG,
                        breedte_cm=30,
                        hoogte_cm=40,
                        diepte_cm=50,
                    )

                    result = await Gebrek.classify_gebrek(gebrek)
                    assert isinstance(result, GrondVoerendGat)
                    assert result.breedte_cm == 30

        anyio.run(run_test)

    def test_verdwenen_metselwerk_detectie(self):
        """Test detectie van verdwenen metselwerk via LLM (zonder 'grondvoerend')."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB2",
                omschrijving="Metselwerk ontbreekt ter plaatse, gat van 20x30 cm",
                figuurnummer="2",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=True,
                    is_buik_of_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                with patch(
                    "tekstherkenning_ark.models.gebrek.LokaalVerdwenenMetselwerkLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_extract:
                    from tekstherkenning_ark.llm.gebrek_classificatie import LokaalVerdwenenMetselwerkLLM

                    mock_extract.return_value = LokaalVerdwenenMetselwerkLLM(
                        afstand_van_startrak_m=NietBeschikbaar.LEEG,
                        breedte_cm=20,
                        hoogte_cm=30,
                        diepte_cm=NietBeschikbaar.LEEG,
                    )

                    result = await Gebrek.classify_gebrek(gebrek)
                    assert isinstance(result, LokaalVerdwenenMetselwerk)
                    assert result.breedte_cm == 20

        anyio.run(run_test)

    def test_buik_in_wand_detectie(self):
        """Test detectie van buik in wand via LLM."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB3",
                omschrijving="Wand vertoont een buik met uitbuiging van 5 cm",
                figuurnummer="3",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=False,
                    is_buik_of_scheefstand=True,
                    is_onderloopsheidscherm=False,
                )

                with patch(
                    "tekstherkenning_ark.models.gebrek.BuikInWandLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_extract:
                    from tekstherkenning_ark.llm.gebrek_classificatie import BuikInWandLLM

                    mock_extract.return_value = BuikInWandLLM(
                        afstand_van_startrak_m=NietBeschikbaar.LEEG,
                        uitbuiking_cm=5,
                    )

                    result = await Gebrek.classify_gebrek(gebrek)
                    assert isinstance(result, BuikInWand)
                    assert result.uitbuiking_cm == 5

        anyio.run(run_test)

    def test_scheefstand_detectie(self):
        """Test detectie van scheefstand via LLM (zonder 'buik')."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB4",
                omschrijving="Wand wijkt af naar het water, scheefstand waarneembaar",
                figuurnummer="4",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=False,
                    is_buik_of_scheefstand=True,
                    is_onderloopsheidscherm=False,
                )

                with patch(
                    "tekstherkenning_ark.models.gebrek.ScheefstandLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_extract:
                    from tekstherkenning_ark.llm.gebrek_classificatie import ScheefstandLLM

                    mock_extract.return_value = ScheefstandLLM(
                        afstand_van_startrak_m=NietBeschikbaar.LEEG,
                        hoek_graden=NietBeschikbaar.LEEG,
                    )

                    result = await Gebrek.classify_gebrek(gebrek)
                    assert isinstance(result, Scheefstand)

        anyio.run(run_test)

    def test_scheur_heeft_prioriteit(self):
        """Test dat scheur detectie voorrang heeft boven andere types."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB5",
                omschrijving="Scheur in metselwerk met SW 2mm",
                figuurnummer="5",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                # Simuleer dat zowel scheur als ander type gedetecteerd worden
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=True,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=False,
                    is_buik_of_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                with patch(
                    "tekstherkenning_ark.models.gebrek.ScheurMetselwerkLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_extract:
                    from tekstherkenning_ark.llm.gebrek_classificatie import ScheurMetselwerkLLM

                    mock_extract.return_value = ScheurMetselwerkLLM(
                        afstand_van_startrak_m=NietBeschikbaar.LEEG,
                        lengte_cm=NietBeschikbaar.LEEG,
                        scheurwijdte_mm=2.0,
                        afstand_van_waterlijn_cm=NietBeschikbaar.LEEG,
                        afstand_van_deksloof_cm=NietBeschikbaar.LEEG,
                        is_inprikbaar=NietBeschikbaar.LEEG,
                        orientatie=NietBeschikbaar.LEEG,
                    )

                    result = await Gebrek.classify_gebrek(gebrek)
                    # Scheur moet worden gedetecteerd
                    assert "Scheur" in result.__class__.__name__

        anyio.run(run_test)

    def test_niet_algemeen_gebrek_wordt_niet_geclassificeerd(self):
        """Test dat niet-algemene gebreken niet worden geclassificeerd."""

        async def run_test():
            gebrek = Gebrek(
                codering="SP1",  # Geen algemeen gebrek (geen GB prefix)
                omschrijving="Wand wijkt af naar het water",
                figuurnummer="6",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=False,
                    is_buik_of_scheefstand=True,
                    is_onderloopsheidscherm=False,
                )

                result = await Gebrek.classify_gebrek(gebrek)
                # Moet het originele Gebrek blijven omdat codering niet algemeen is
                assert type(result) == Gebrek
                assert result.codering == "SP1"

        anyio.run(run_test)

    def test_geen_gebrektype_gedetecteerd(self):
        """Test dat gebrek onveranderd blijft als geen type gedetecteerd wordt."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB10",
                omschrijving="Onbekend gebrek",
                figuurnummer="7",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat_of_verdwenen_metselwerk=False,
                    is_buik_of_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                result = await Gebrek.classify_gebrek(gebrek)
                assert type(result) == Gebrek
                assert result.codering == "GB10"

        anyio.run(run_test)
