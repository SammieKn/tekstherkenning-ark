"""Tests voor LLM-gebaseerde gebrektype detectie."""

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
                    is_grondvoerend_gat=True,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=False,
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
                    assert len(result) == 1
                    assert isinstance(result[0], GrondVoerendGat)
                    assert result[0].breedte_cm == 30

        anyio.run(run_test)

    def test_verdwenen_metselwerk_detectie(self):
        """Test detectie van verdwenen metselwerk via LLM."""

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
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=True,
                    is_buik_in_wand=False,
                    is_scheefstand=False,
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
                    assert len(result) == 1
                    assert isinstance(result[0], LokaalVerdwenenMetselwerk)
                    assert result[0].breedte_cm == 20

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
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=True,
                    is_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                with patch(
                    "tekstherkenning_ark.models.gebrek.BuikInWandLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_extract:
                    from tekstherkenning_ark.llm.gebrek_classificatie import BuikInWandLLM

                    mock_extract.return_value = BuikInWandLLM(
                        start_buik_van_startrak_m_ingevuld=NietBeschikbaar.LEEG,
                        eind_buik_van_startrak_m_ingevuld=NietBeschikbaar.LEEG,
                        lengte_buik_m_ingevuld=NietBeschikbaar.LEEG,
                        uitbuiking_cm=5,
                    )

                    result = await Gebrek.classify_gebrek(gebrek)
                    assert len(result) == 1
                    assert isinstance(result[0], BuikInWand)
                    assert result[0].uitbuiking_cm == 5

        anyio.run(run_test)

    def test_scheefstand_detectie(self):
        """Test detectie van scheefstand via LLM."""

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
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=True,
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
                    assert len(result) == 1
                    assert isinstance(result[0], Scheefstand)

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
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=False,
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
                    assert any("Scheur" in g.__class__.__name__ for g in result)

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
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=True,
                    is_onderloopsheidscherm=False,
                )

                result = await Gebrek.classify_gebrek(gebrek)
                # Moet het originele Gebrek blijven omdat codering niet algemeen is
                assert len(result) == 1
                assert type(result[0]) == Gebrek
                assert result[0].codering == "SP1"

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
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                result = await Gebrek.classify_gebrek(gebrek)
                assert len(result) == 1
                assert type(result[0]) == Gebrek
                assert result[0].codering == "GB10"

        anyio.run(run_test)

    def test_onderloopsheidscherm_detectie(self):
        """Test detectie van beschadigd onderloopsheidscherm via LLM."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB8",
                omschrijving="Onderloopsheidscherm is beschadigd ter plaatse",
                figuurnummer="8",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=False,
                    is_grondvoerend_gat=False,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=False,
                    is_onderloopsheidscherm=True,
                )

                result = await Gebrek.classify_gebrek(gebrek)
                assert len(result) == 1
                assert isinstance(result[0], OnderloopsheidschermBeschadigd)
                assert result[0].is_beschadigd is True

        anyio.run(run_test)

    def test_meerdere_gebreken_in_een_omschrijving(self):
        """Test dat meerdere gebrektypes in één omschrijving elk een apart object opleveren."""

        async def run_test():
            gebrek = Gebrek(
                codering="GB9",
                omschrijving="Grondvoerend gat van 20x30 cm achter de wand. Tevens een scheur van 50 cm met SW 3mm.",
                figuurnummer="9",
            )

            with patch.object(
                GebrekTypeDetectieLLM,
                "classificeer_omschrijving",
                new_callable=AsyncMock,
            ) as mock_type:
                mock_type.return_value = GebrekTypeDetectieLLM(
                    is_scheur=True,
                    is_grondvoerend_gat=True,
                    is_verdwenen_metselwerk=False,
                    is_buik_in_wand=False,
                    is_scheefstand=False,
                    is_onderloopsheidscherm=False,
                )

                with patch(
                    "tekstherkenning_ark.models.gebrek.ScheurLLM.classificeer_omschrijving",
                    new_callable=AsyncMock,
                ) as mock_scheur:
                    from tekstherkenning_ark.llm.gebrek_classificatie import ScheurLLM

                    mock_scheur.return_value = ScheurLLM(
                        afstand_van_startrak_m=NietBeschikbaar.LEEG,
                        lengte_cm=50,
                        scheurwijdte_mm=3.0,
                    )

                    with patch(
                        "tekstherkenning_ark.models.gebrek.GrondVoerendGatLLM.classificeer_omschrijving",
                        new_callable=AsyncMock,
                    ) as mock_gat:
                        from tekstherkenning_ark.llm.gebrek_classificatie import GrondVoerendGatLLM

                        mock_gat.return_value = GrondVoerendGatLLM(
                            afstand_van_startrak_m=NietBeschikbaar.LEEG,
                            breedte_cm=20,
                            hoogte_cm=30,
                            diepte_cm=NietBeschikbaar.LEEG,
                        )

                        result = await Gebrek.classify_gebrek(gebrek)

                        assert len(result) == 2
                        typen = {type(g) for g in result}
                        assert Scheur in typen
                        assert GrondVoerendGat in typen

                        scheur = next(g for g in result if isinstance(g, Scheur))
                        assert scheur.scheurwijdte_mm == 3.0

                        gat = next(g for g in result if isinstance(g, GrondVoerendGat))
                        assert gat.breedte_cm == 20

        anyio.run(run_test)
