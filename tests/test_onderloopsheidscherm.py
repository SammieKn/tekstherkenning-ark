"""Tests voor het Onderloopsheidscherm model."""

from unittest.mock import MagicMock

from tekstherkenning_ark.models.onderloopsheidscherm import Onderloopsheidscherm
from tekstherkenning_ark.models.toestand_onderdeel import ToestandOnderdeel
from tekstherkenning_ark.models.gebrek import Gebrek
from tekstherkenning_ark.enums import NietBeschikbaar


# ==============================================================================
# Hulpfuncties
# ==============================================================================


def maak_mock_omschrijving(onderloopsheidscherm: bool | NietBeschikbaar) -> MagicMock:
    """Maak een mock RakdeelOmschrijving met het opgegeven onderloopsheidscherm veld.

    Parameters
    ----------
    onderloopsheidscherm : bool | NietBeschikbaar
        Waarde voor het onderloopsheidscherm veld.
    """
    mock = MagicMock()
    mock.onderloopsheidscherm = onderloopsheidscherm
    return mock


def maak_toestand_onderdeel(aangetast: bool) -> ToestandOnderdeel:
    """Maak een ToestandOnderdeel voor een onderloopsheidscherm.

    Parameters
    ----------
    aangetast : bool
        Indicatie of het onderdeel aangetast is.
    """
    return ToestandOnderdeel(
        constructie_onderdeel="onderloopsheidscherm",
        aangetast=aangetast,
    )


# ==============================================================================
# Tests voor from_rakdeel_omschrijving
# ==============================================================================


class TestFromRakdeelOmschrijving:
    """Tests voor Onderloopsheidscherm.from_rakdeel_omschrijving."""

    def test_onderloopsheidscherm_aanwezig(self):
        """Test dat een Onderloopsheidscherm wordt aangemaakt als het in de omschrijving voorkomt."""
        omschrijving = maak_mock_omschrijving(onderloopsheidscherm=True)

        result = Onderloopsheidscherm.from_rakdeel_omschrijving(omschrijving)

        assert isinstance(result, Onderloopsheidscherm)

    def test_onderloopsheidscherm_afwezig(self):
        """Test dat None wordt teruggegeven als het onderloopsheidscherm niet in de omschrijving voorkomt."""
        omschrijving = maak_mock_omschrijving(onderloopsheidscherm=False)

        result = Onderloopsheidscherm.from_rakdeel_omschrijving(omschrijving)

        assert result is None

    def test_onderloopsheidscherm_niet_beschikbaar(self):
        """Test dat None wordt teruggegeven als het onderloopsheidscherm niet beschikbaar is."""
        omschrijving = maak_mock_omschrijving(onderloopsheidscherm=NietBeschikbaar.LEEG)

        result = Onderloopsheidscherm.from_rakdeel_omschrijving(omschrijving)

        assert result is None

    def test_nieuw_object_heeft_lege_defaults(self):
        """Test dat het aangemaakte object lege standaardwaarden heeft."""
        omschrijving = maak_mock_omschrijving(onderloopsheidscherm=True)

        result = Onderloopsheidscherm.from_rakdeel_omschrijving(omschrijving)

        assert result.gebreken == []
        assert result.toestand_onderdelen == []
        assert result.is_meerdere_locaties is None


# ==============================================================================
# Tests voor is_beschadigd
# ==============================================================================


class TestIsBeschadigd:
    """Tests voor de is_beschadigd property van Onderloopsheidscherm."""

    def test_niet_beschadigd_zonder_gebreken_en_toestand(self):
        """Test dat is_beschadigd False is als er geen gebreken en geen toestand_onderdelen zijn."""
        scherm = Onderloopsheidscherm()

        assert scherm.is_beschadigd is False

    def test_beschadigd_met_gebrek(self):
        """Test dat is_beschadigd True is als er een gebrek aanwezig is."""
        scherm = Onderloopsheidscherm(
            gebreken=[Gebrek(codering="GS1", omschrijving="Schade aan scherm", figuurnummer="F1")]
        )

        assert scherm.is_beschadigd is True

    def test_beschadigd_met_aangetast_toestand_onderdeel(self):
        """Test dat is_beschadigd True is als er een aangetast toestand_onderdeel aanwezig is."""
        scherm = Onderloopsheidscherm(toestand_onderdelen=[maak_toestand_onderdeel(aangetast=True)])

        assert scherm.is_beschadigd is True

    def test_niet_beschadigd_met_niet_aangetast_toestand_onderdeel(self):
        """Test dat is_beschadigd False is als het toestand_onderdeel niet aangetast is."""
        scherm = Onderloopsheidscherm(toestand_onderdelen=[maak_toestand_onderdeel(aangetast=False)])

        assert scherm.is_beschadigd is False

    def test_beschadigd_met_zowel_gebrek_als_toestand(self):
        """Test dat is_beschadigd True is als zowel gebreken als toestand_onderdelen aanwezig zijn."""
        scherm = Onderloopsheidscherm(
            gebreken=[Gebrek(codering="GS1", omschrijving="Schade aan scherm", figuurnummer="F1")],
            toestand_onderdelen=[maak_toestand_onderdeel(aangetast=True)],
        )

        assert scherm.is_beschadigd is True
