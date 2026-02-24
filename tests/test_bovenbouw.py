"""Tests voor het Bovenbouw model."""

from tekstherkenning_ark.models.bovenbouw import Bovenbouw
from tekstherkenning_ark.models.toestand_onderdeel import ToestandOnderdeel
from tekstherkenning_ark.models.gebrek import Gebrek


def get_mock_bovenbouw(has_gebrek: bool = False, has_toestand: bool = False) -> Bovenbouw:
    """Maak een Bovenbouw instance met optionele gebreken en toestand_onderdelen.

    Parameters
    ----------
    has_gebrek : bool
        Of er een gebrek met 'schuifhout' in de omschrijving moet worden toegevoegd.
    has_toestand : bool
        Of er een aangetast schuifhout toestand_onderdeel moet worden toegevoegd.

    Returns
    -------
    Bovenbouw
        Een Bovenbouw instance met de opgegeven kenmerken.
    """

    gebreken = []
    toestand_onderdelen = []
    if has_gebrek:
        gebreken = [Gebrek(codering="GS1", omschrijving="Beschadigd schuifhout", figuurnummer="F1")]
    if has_toestand:
        toestand_onderdelen = [ToestandOnderdeel(constructie_onderdeel="schuifhout", aangetast=True)]

    return Bovenbouw(gebreken=gebreken, toestand_onderdelen=toestand_onderdelen)


class TestIsSchuifhoutBeschadigd:
    """Tests voor de is_schuifhout_beschadigd property van Bovenbouw."""

    def test_niet_beschadigd_zonder_gebreken_en_toestand(self):
        """Test dat is_schuifhout_beschadigd False is als er geen gebreken en geen toestand_onderdelen zijn."""
        bovenbouw = get_mock_bovenbouw()

        assert bovenbouw.is_schuifhout_beschadigd is False

    def test_beschadigd_met_schuifhout_gebrek(self):
        """Test dat is_schuifhout_beschadigd True is als er een gebrek met 'schuifhout' in de omschrijving is."""
        bovenbouw = get_mock_bovenbouw(has_gebrek=True)

        assert bovenbouw.is_schuifhout_beschadigd is True

    def test_beschadigd_met_aangetast_toestand_onderdeel(self):
        """Test dat is_schuifhout_beschadigd True is als er een aangetast schuifhout toestand_onderdeel is."""
        bovenbouw = get_mock_bovenbouw(has_toestand=True)

        assert bovenbouw.is_schuifhout_beschadigd is True

    def test_niet_beschadigd_met_niet_aangetast_toestand_onderdeel(self):
        """Test dat is_schuifhout_beschadigd False is als het schuifhout toestand_onderdeel niet aangetast is."""
        bovenbouw = get_mock_bovenbouw(has_toestand=True)
        bovenbouw.toestand_onderdelen[0].aangetast = False

        assert bovenbouw.is_schuifhout_beschadigd is False

    def test_beschadigd_met_zowel_gebrek_als_toestand(self):
        """Test dat is_schuifhout_beschadigd True is als zowel gebreken als toestand_onderdelen aanwezig zijn."""
        bovenbouw = get_mock_bovenbouw(has_gebrek=True, has_toestand=True)

        assert bovenbouw.is_schuifhout_beschadigd is True

    def test_niet_beschadigd_met_ander_gebrek(self):
        """Test dat is_schuifhout_beschadigd False is als er een gebrek is zonder 'schuifhout' in de omschrijving."""
        bovenbouw = get_mock_bovenbouw()
        bovenbouw.gebreken.append(Gebrek(codering="GS3", omschrijving="Scheur in metselwerk", figuurnummer="F3"))

        assert bovenbouw.is_schuifhout_beschadigd is False

    def test_niet_beschadigd_met_ander_toestand_onderdeel(self):
        """Test dat is_schuifhout_beschadigd False is bij aangetast toestand_onderdeel zonder 'schuifhout'."""
        bovenbouw = get_mock_bovenbouw()
        bovenbouw.toestand_onderdelen.append(ToestandOnderdeel(constructie_onderdeel="metselwerk", aangetast=True))

        assert bovenbouw.is_schuifhout_beschadigd is False
