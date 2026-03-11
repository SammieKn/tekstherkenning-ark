"""Visualiseerder voor rakdelen op basis van JSON-exportbestanden.

Heeft geen afhankelijkheid van het tekstherkenning_ark-pakket; werkt
uitsluitend met de dict-structuur die door json.loads() wordt teruggegeven.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import plotly.graph_objects as go

import visuals.stijl as stijl

# Gebrektypen die als 'scheur' worden behandeld
SCHEUR_TYPEN = {"Scheur", "ScheurMetselwerk", "ScheurHout"}


# ---------------------------------------------------------------------------
# Module-niveau hulpfuncties
# ---------------------------------------------------------------------------


def laad_rak_uit_json(json_pad: str | Path) -> dict:
    """Laad een rak-dict uit een JSON-exportbestand.

    Parameters
    ----------
    json_pad : str | Path
        Pad naar het JSON-exportbestand.

    Returns
    -------
    dict
        De gedeserialiseerde rak als Python-dict.
    """
    return json.loads(Path(json_pad).read_text(encoding="utf-8"))


def sla_figuren_op(figuren: dict[str, go.Figure], uitvoer_map: str | Path) -> None:
    """Sla alle figuren op als HTML-bestanden in uitvoer_map.

    Parameters
    ----------
    figuren : dict[str, go.Figure]
        Dict van figuren met een beschrijvende sleutel als bestandsnaam.
    uitvoer_map : str | Path
        Map waarin de HTML-bestanden worden opgeslagen. Wordt aangemaakt als
        die nog niet bestaat.
    """
    uitvoer_map = Path(uitvoer_map)
    uitvoer_map.mkdir(parents=True, exist_ok=True)
    for naam, fig in figuren.items():
        fig.write_html(uitvoer_map / f"{naam}.html")


def _is_geldig(waarde: object) -> bool:
    """Geef True als waarde een bruikbaar getal of bool is.

    Strings (NVT, NM, "") en dicts (OnverwachtResultaat) geven False.
    """
    return isinstance(waarde, (int, float, bool))


def _pas_layout_toe(fig: go.Figure, titel: str) -> go.Figure:
    """Pas de standaard stijl toe op een figuur.

    Parameters
    ----------
    fig : go.Figure
        De figuur waarop de layout wordt toegepast.
    titel : str
        Titel van de figuur.

    Returns
    -------
    go.Figure
        De figuur met toegepaste layout.
    """
    fig.update_layout(
        title=titel,
        font=stijl.LETTERTYPE,
        margin=stijl.MARGES,
        paper_bgcolor=stijl.ACHTERGROND_KLEUR,
        plot_bgcolor=stijl.ACHTERGROND_KLEUR,
        width=stijl.FIGUUR_BREEDTE,
        height=stijl.FIGUUR_HOOGTE,
    )
    return fig


def _kleur_voor_type(gebrek_type_naam: str) -> str:
    """Geef de kleur voor een gebrektype op basis van stijl.KLEUREN."""
    return stijl.KLEUREN.get(gebrek_type_naam, stijl.KLEUREN["fallback"])


def _bereken_kesp_posities(kespen: list[dict], palen: list[dict]) -> list[float | None]:
    """Leid de X-positie (meter langs rak) af voor elke kesp.

    Sorteert de palen van rij 1 op paal_nummer_main en berekent de cumulatieve
    hoh_afstand_cm. De kesp met kesp_nummer_main K wordt geplaatst op de
    cumulatieve afstand van de K-de paal in rij 1.

    Parameters
    ----------
    kespen : list[dict]
        Lijst van kespen om posities voor te berekenen.
    palen : list[dict]
        Alle palen van de onderbouw.

    Returns
    -------
    list[float | None]
        Een positie per kesp in meters; None als de positie niet bepaald kan worden.
    """
    rij1_palen = sorted(
        [p for p in palen if p.get("paalrij_nummer") == 1 and _is_geldig(p.get("hoh_afstand_cm"))],
        key=lambda p: p.get("paal_nummer_main") or 0,
    )

    cumulatief: list[float] = []
    som = 0.0
    for paal in rij1_palen:
        som += paal["hoh_afstand_cm"] / 100
        cumulatief.append(som)

    posities: list[float | None] = []
    for kesp in kespen:
        idx = (kesp.get("kesp_nummer_main") or 1) - 1
        if 0 <= idx < len(cumulatief):
            posities.append(cumulatief[idx])
        else:
            posities.append(None)
    return posities


# ---------------------------------------------------------------------------
# Klasse
# ---------------------------------------------------------------------------


class RakdeelVisualiseerder:
    """Maakt Plotly-figuren voor een enkel rakdeel.

    Parameters
    ----------
    rakdeel : dict
        Het te visualiseren rakdeel als geparsed JSON-dict.
    """

    def __init__(self, rakdeel: dict) -> None:
        self._rakdeel = rakdeel

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def alle_figuren(self) -> dict[str, go.Figure]:
        """Geeft alle figuren terug als dict met een beschrijvende sleutel.

        Returns
        -------
        dict[str, go.Figure]
            Sleutels zijn bestandsvriendelijke namen; waarden zijn de figuren.
        """
        return {
            "gebreken_per_type": self.gebreken_per_type_barchart(),
            "scheur_lengte_vs_wijdte": self.scheur_lengte_vs_wijdte_scatter(),
            "scheur_en_kesp_langs_rak": self.scheur_en_kesp_langs_rak(),
            "gebrek_locaties_langs_rak": self.gebrek_locaties_langs_rak(),
            "paal_status": self.paal_status_barchart(),
            "kesp_status": self.kesp_status_barchart(),
        }

    # ------------------------------------------------------------------
    # Figuurmethoden
    # ------------------------------------------------------------------

    def gebreken_per_type_barchart(self) -> go.Figure:
        """Staafdiagram met het aantal gebreken per gebrektype in de bovenbouw.

        Returns
        -------
        go.Figure
            Plotly-figuur met één staaf per gebrektype.
        """
        gebreken = self._rakdeel.get("bovenbouw", {}).get("gebreken", [])
        tellingen: Counter[str] = Counter(g.get("gebrek_type", "Onbekend") for g in gebreken)

        typen = list(tellingen.keys())
        aantallen = list(tellingen.values())
        kleuren = [_kleur_voor_type(t) for t in typen]

        fig = go.Figure(
            go.Bar(
                x=typen,
                y=aantallen,
                marker_color=kleuren,
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        )
        fig.update_layout(xaxis_title="Gebrektype", yaxis_title="Aantal")
        return _pas_layout_toe(fig, f"Gebreken per type — {self._rakdeel.get('rakdeel_id', '')}")

    def scheur_lengte_vs_wijdte_scatter(self) -> go.Figure:
        """Scatterplot van scheurlengte (X) vs. scheurwijdte (Y) voor scheuren in de bovenbouw.

        Scheuren waarbij lengte_cm of scheurwijdte_mm ontbreekt worden overgeslagen.

        Returns
        -------
        go.Figure
            Plotly-figuur met één punt per scheur.
        """
        gebreken = self._rakdeel.get("bovenbouw", {}).get("gebreken", [])
        scheuren = [g for g in gebreken if g.get("gebrek_type") in SCHEUR_TYPEN]
        geldig = [
            s
            for s in scheuren
            if _is_geldig(s.get("lengte_cm")) and _is_geldig(s.get("scheurwijdte_mm"))
        ]

        x_waarden = [s["lengte_cm"] for s in geldig]
        y_waarden = [s["scheurwijdte_mm"] for s in geldig]
        hover = [
            f"{s.get('codering', '')}<br>{s.get('omschrijving', '')}<br>Afstand: {s.get('afstand_van_startrak_m')} m"
            for s in geldig
        ]

        fig = go.Figure(
            go.Scatter(
                x=x_waarden,
                y=y_waarden,
                mode="markers",
                marker=dict(color=_kleur_voor_type("Scheur"), size=8),
                text=hover,
                hovertemplate="%{text}<extra></extra>",
            )
        )
        fig.update_layout(xaxis_title="Scheurlengte (cm)", yaxis_title="Scheurwijdte (mm)")
        return _pas_layout_toe(
            fig, f"Scheurlengte vs. scheurwijdte — {self._rakdeel.get('rakdeel_id', '')}"
        )

    def scheur_en_kesp_langs_rak(self) -> go.Figure:
        """Gecombineerd diagram met scheuren (boven nul) en aangetaste kespen (onder nul) langs het rak.

        Scheuren worden geplot op afstand_van_startrak_m op y=1.
        Aangetaste kespen worden geplot op hun berekende positie op y=-1.
        Een horizontale referentielijn op y=0 scheidt beide.

        Returns
        -------
        go.Figure
            Plotly-figuur met twee sporen en een referentielijn.
        """
        gebreken = self._rakdeel.get("bovenbouw", {}).get("gebreken", [])
        scheuren = [g for g in gebreken if g.get("gebrek_type") in SCHEUR_TYPEN]
        scheur_x = [
            s["afstand_van_startrak_m"]
            for s in scheuren
            if _is_geldig(s.get("afstand_van_startrak_m"))
        ]

        onderbouw = self._rakdeel.get("onderbouw", {})
        kespen = onderbouw.get("kespen", [])
        palen = onderbouw.get("palen", [])
        posities = _bereken_kesp_posities(kespen, palen)
        aangetaste_kesp_x = [
            pos
            for kesp, pos in zip(kespen, posities)
            if kesp.get("is_aangetast") is True and pos is not None
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=scheur_x,
                y=[1] * len(scheur_x),
                mode="markers",
                name="Scheur",
                marker=dict(color=_kleur_voor_type("Scheur"), size=10, symbol="diamond"),
                hovertemplate="Afstand: %{x} m<extra>Scheur</extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=aangetaste_kesp_x,
                y=[-1] * len(aangetaste_kesp_x),
                mode="markers",
                name="Aangetaste kesp",
                marker=dict(color=stijl.KLEUREN["kesp_aangetast"], size=10, symbol="triangle-down"),
                hovertemplate="Positie: %{x} m<extra>Aangetaste kesp</extra>",
            )
        )

        fig.add_hline(y=0, line_color="#333333", line_dash="dash", line_width=1)
        fig.update_layout(
            xaxis_title="Afstand langs rak (m)",
            yaxis=dict(tickvals=[-1, 1], ticktext=["Aangetaste kesp", "Scheur"]),
        )
        return _pas_layout_toe(
            fig,
            f"Scheuren (boven) en aangetaste kespen (onder) langs rak — {self._rakdeel.get('rakdeel_id', '')}",
        )

    def gebrek_locaties_langs_rak(self) -> go.Figure:
        """Diagram met de locaties van alle typen gebreken langs het rak.

        Puntgebreken worden als marker geplot op afstand_van_startrak_m.
        Vlaksgebreken (BuikInWand, Scheefstand) worden als horizontale lijn
        van start- tot eindafstand getekend.
        Gebreken zonder geldige locatie worden overgeslagen.

        Returns
        -------
        go.Figure
            Plotly-figuur met één spoor per gebrektype.
        """
        gebreken = self._rakdeel.get("bovenbouw", {}).get("gebreken", [])
        sporen_per_type: dict[str, list[dict]] = {}
        for gebrek in gebreken:
            naam = gebrek.get("gebrek_type", "Onbekend")
            sporen_per_type.setdefault(naam, []).append(gebrek)

        fig = go.Figure()

        for type_naam, type_gebreken in sporen_per_type.items():
            kleur = _kleur_voor_type(type_naam)

            for gebrek in type_gebreken:
                if gebrek.get("gebrek_type") == "BuikInWand":
                    start = gebrek.get("start_buik_van_startrak_m")
                    eind = gebrek.get("eind_buik_van_startrak_m")
                    if _is_geldig(start) and _is_geldig(eind):
                        fig.add_trace(
                            go.Scatter(
                                x=[start, eind],
                                y=[type_naam, type_naam],
                                mode="lines",
                                line=dict(color=kleur, width=6),
                                name=type_naam,
                                legendgroup=type_naam,
                                showlegend=False,
                                hovertemplate=f"{gebrek.get('codering', '')}: {start}–{eind} m<extra>{type_naam}</extra>",
                            )
                        )
                elif gebrek.get("gebrek_type") == "Scheefstand":
                    start = gebrek.get("start_scheefstand_van_startrak_m")
                    eind = gebrek.get("eind_scheefstand_van_startrak_m")
                    if _is_geldig(start) and _is_geldig(eind):
                        fig.add_trace(
                            go.Scatter(
                                x=[start, eind],
                                y=[type_naam, type_naam],
                                mode="lines",
                                line=dict(color=kleur, width=6),
                                name=type_naam,
                                legendgroup=type_naam,
                                showlegend=False,
                                hovertemplate=f"{gebrek.get('codering', '')}: {start}–{eind} m<extra>{type_naam}</extra>",
                            )
                        )
                else:
                    afstand = gebrek.get("afstand_van_startrak_m")
                    if _is_geldig(afstand):
                        fig.add_trace(
                            go.Scatter(
                                x=[afstand],
                                y=[type_naam],
                                mode="markers",
                                marker=dict(color=kleur, size=10),
                                name=type_naam,
                                legendgroup=type_naam,
                                showlegend=False,
                                hovertemplate=f"{gebrek.get('codering', '')}: %{{x}} m<extra>{type_naam}</extra>",
                            )
                        )

        # Voeg één legenda-entry per type toe
        for type_naam in sporen_per_type:
            kleur = _kleur_voor_type(type_naam)
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(color=kleur, size=10),
                    name=type_naam,
                    legendgroup=type_naam,
                )
            )

        fig.update_layout(
            xaxis_title="Afstand langs rak (m)",
            yaxis_title="Gebrektype",
            showlegend=True,
        )
        return _pas_layout_toe(fig, f"Gebreklocaties langs rak — {self._rakdeel.get('rakdeel_id', '')}")

    def paal_status_barchart(self) -> go.Figure:
        """Gegroepeerd staafdiagram met de verdeling van paalstatussen.

        Telt per attribuut (is_paalbreuk, is_aantasting, is_juiste_aansluiting)
        het aantal palen met waarde True, False, of onbekend.

        Returns
        -------
        go.Figure
            Plotly-figuur met drie gekleurde sporen (waar, onwaar, onbekend).
        """
        palen = self._rakdeel.get("onderbouw", {}).get("palen", [])
        kolommen = ["is_paalbreuk", "is_aantasting", "is_juiste_aansluiting"]

        def _aansluiting_waarde(paal: dict) -> bool | None:
            status = paal.get("aansluiting_status")
            if isinstance(status, dict):
                return None
            if status == "G":
                return True
            if status == "NM":
                return None
            return False

        def _waarde_voor(paal: dict, kolom: str) -> bool | None:
            if kolom == "is_juiste_aansluiting":
                return _aansluiting_waarde(paal)
            waarde = paal.get(kolom)
            if isinstance(waarde, dict) or waarde is None:
                return None
            return bool(waarde) if isinstance(waarde, bool) else None

        waar = [sum(1 for p in palen if _waarde_voor(p, k) is True) for k in kolommen]
        onwaar = [sum(1 for p in palen if _waarde_voor(p, k) is False) for k in kolommen]
        onbekend = [sum(1 for p in palen if _waarde_voor(p, k) is None) for k in kolommen]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Ja", x=kolommen, y=waar, marker_color=stijl.KLEUREN["waar"]))
        fig.add_trace(go.Bar(name="Nee", x=kolommen, y=onwaar, marker_color=stijl.KLEUREN["onwaar"]))
        fig.add_trace(go.Bar(name="Onbekend", x=kolommen, y=onbekend, marker_color=stijl.KLEUREN["onbekend"]))

        fig.update_layout(barmode="group", xaxis_title="Attribuut", yaxis_title="Aantal palen")
        return _pas_layout_toe(fig, f"Paalstatus — {self._rakdeel.get('rakdeel_id', '')}")

    def kesp_status_barchart(self) -> go.Figure:
        """Gegroepeerd staafdiagram met de verdeling van kespstatussen.

        Telt per attribuut (is_vervormd, is_aangetast) het aantal kespen met
        waarde True, False, of onbekend (None).

        Returns
        -------
        go.Figure
            Plotly-figuur met drie gekleurde sporen (waar, onwaar, onbekend).
        """
        kespen = self._rakdeel.get("onderbouw", {}).get("kespen", [])
        kolommen = ["is_vervormd", "is_aangetast"]

        def _kesp_waarde(kesp: dict, kolom: str) -> bool | None:
            waarde = kesp.get(kolom)
            if isinstance(waarde, dict) or waarde is None:
                return None
            return bool(waarde) if isinstance(waarde, bool) else None

        waar = [sum(1 for k in kespen if _kesp_waarde(k, kolom) is True) for kolom in kolommen]
        onwaar = [sum(1 for k in kespen if _kesp_waarde(k, kolom) is False) for kolom in kolommen]
        onbekend = [sum(1 for k in kespen if _kesp_waarde(k, kolom) is None) for kolom in kolommen]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Ja", x=kolommen, y=waar, marker_color=stijl.KLEUREN["waar"]))
        fig.add_trace(go.Bar(name="Nee", x=kolommen, y=onwaar, marker_color=stijl.KLEUREN["onwaar"]))
        fig.add_trace(go.Bar(name="Onbekend", x=kolommen, y=onbekend, marker_color=stijl.KLEUREN["onbekend"]))

        fig.update_layout(barmode="group", xaxis_title="Attribuut", yaxis_title="Aantal kespen")
        return _pas_layout_toe(fig, f"Kespstatus — {self._rakdeel.get('rakdeel_id', '')}")
