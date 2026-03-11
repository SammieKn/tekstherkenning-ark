"""Centrale stijlconstanten voor alle Plotly-visualisaties.

Kleuren zijn gebaseerd op het bedrijfskleurenpalet:
  Heritage (oranje)       #e4610f  — primair
  Confidence (zwart)      #1d1d1d  — primair
  Wisdom (wit)            #ffffff  — primair
  Collaboration (roze)    #9c266e  — secundair
  Client Success (geel)   #f1b434  — secundair
  Sustainability (teal)   #007377  — secundair
  Integrity (blauw)       #326295  — secundair
"""

KLEUREN: dict[str, str] = {
    # Scheuren: Heritage (oranje) → donkerder tint → lichtere tint
    "Scheur": "#e4610f",
    "ScheurMetselwerk": "#b34a0a",
    "ScheurHout": "#f1884a",
    # Buik / Scheefstand: Integrity (blauw) tints
    "BuikInWand": "#326295",
    "Scheefstand": "#1d1d1d",
    # Overige gebreken: secundaire kleuren
    "GrondVoerendGat": "#f1b434",
    "LokaalVerdwenenMetselwerk": "#9c266e",
    "OnderloopsheidschermBeschadigd": "#007377",
    # Status / kesp
    "kesp_aangetast": "#9c266e",
    "waar": "#007377",
    "onwaar": "#e4610f",
    "onbekend": "#1d1d1d",
    "fallback": "#326295",
}

LETTERTYPE: dict = {
    "family": "Arial, sans-serif",
    "size": 13,
    "color": "#1d1d1d",
}

MARGES: dict = {
    "l": 60,
    "r": 30,
    "t": 60,
    "b": 60,
}

ACHTERGROND_KLEUR: str = "#f8f9fa"

FIGUUR_BREEDTE: int = 1100
FIGUUR_HOOGTE: int = 500
