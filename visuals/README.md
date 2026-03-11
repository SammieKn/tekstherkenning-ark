# Rakdeel Visualiseerder

Plotly-gebaseerde visualisatiemodule voor geëxporteerde `Rak`-objecten uit het ARK-formulier.

## Mapstructuur

```
visuals/
├── README.md                    ← dit bestand
├── rakdeelvisualiseerder.py     ← klasse RakdeelVisualiseerder + laad/sla-op functies + interne hulpfuncties
├── stijl.py                     ← centrale stijlconstanten (kleuren, lettertypen, marges)
└── output/                      ← map voor opgeslagen figuren (gitignore)
```

---

## Datamodel (samenvatting)

De visualiseerder werkt op `Rakdeel`-niveau. Een `Rakdeel` bevat:

- `rakdeel_id: str` — unieke naam (bijv. `"Constructie A"`)
- `lengte_m: float | None` — lengte van het rakdeel in meters
- `bovenbouw: Bovenbouw`
  - `gebreken: list[Gebrek]` — bevat subklassen: `Scheur`, `ScheurMetselwerk`, `BuikInWand`, `Scheefstand`, `GrondVoerendGat`, `LokaalVerdwenenMetselwerk`, `OnderloopsheidschermBeschadigd`
  - Elke `Scheur` heeft: `afstand_van_startrak_m`, `lengte_cm`, `scheurwijdte_mm`
  - Elke `BuikInWand`/`Scheefstand` heeft een start- en eindafstand
- `onderbouw: Onderbouw`
  - `palen: list[Paal]` — elk met: `is_paalbreuk`, `is_aantasting`, `aansluiting_status` (`JuisteAansluiting` / `OnvoldoendeAansluiting` / `OnverwachtResultaat`), `schoor_graden`, `is_scheefstand`, `n_scheuren`
  - `kespen: list[Kesp]` — elk met: `is_vervormd`, `is_aangetast`, `is_opsluitklos_aanwezig`, `is_opsluitklos_aangetast`

Velden met de waarde `NietBeschikbaar` of `OnverwachtResultaat` worden behandeld als ontbrekend en overgeslagen in berekeningen en visualisaties.

---

## Bestandsbeschrijvingen

### `stijl.py`

Bevat **alle** stijlconstanten als Python-dictionaries en constanten. Niets anders.

Inhoud:
- `KLEUREN: dict[str, str]` — kleur per gebrektype (bijv. `"Scheur": "#e63946"`, `"BuikInWand": "#457b9d"`, enz.)
- `LETTERTYPE: dict` — standaard Plotly `font`-dict
- `MARGES: dict` — standaard `margin`-dict voor alle figuren
- `ACHTERGROND_KLEUR: str`
- `FIGUUR_BREEDTE: int`, `FIGUUR_HOOGTE: int`

### `rakdeelvisualiseerder.py`

#### Laad-functie (module-niveau)

```python
def laad_rak_uit_json(json_pad: str | Path) -> Rak:
    """Laad een Rak-object uit een JSON-exportbestand."""
```

Gebruik: `Rak.model_validate_json(Path(json_pad).read_text())`.

#### Sla-op-functie (module-niveau)

```python
def sla_figuren_op(figuren: dict[str, go.Figure], uitvoer_map: str | Path) -> None:
    """Sla alle figuren op als HTML-bestanden in uitvoer_map."""
```

Slaat elke figuur op als `{sleutel}.html` via `fig.write_html(...)`.

#### Klasse `RakdeelVisualiseerder`

```python
class RakdeelVisualiseerder:
    def __init__(self, rakdeel: Rakdeel) -> None:
        ...

    @property
    def alle_figuren(self) -> dict[str, go.Figure]:
        """Geeft alle figuren terug als dict met een beschrijvende sleutel."""
```

De `alle_figuren`-property roept alle onderstaande methoden aan en bundelt ze in één dict.

---

## Figuren

Alle methoden retourneren een `go.Figure` en accepteren geen argumenten buiten `self`.

### 1. `gebreken_per_type_barchart() -> go.Figure`

**Type:** Staafdiagram  
**Bron:** `rakdeel.bovenbouw.gebreken`  
**X-as:** gebrektype (klasse-naam: `Scheur`, `BuikInWand`, enz.)  
**Y-as:** aantal gebreken  
**Kleur:** per staaf uit `stijl.KLEUREN`; onbekende typen krijgen een fallback-kleur  
**Titel:** `"Gebreken per type — {rakdeel_id}"`

### 2. `scheur_lengte_vs_wijdte_scatter() -> go.Figure`

**Type:** Scatterplot  
**Bron:** alle `Scheur`-gebreken in `rakdeel.bovenbouw.gebreken` (inclusief `ScheurMetselwerk`)  
**X-as:** `lengte_cm` (skipna: sla `NietBeschikbaar` over)  
**Y-as:** `scheurwijdte_mm` (skipna)  
**Tooltip:** `codering`, `omschrijving`, `afstand_van_startrak_m`  
**Titel:** `"Scheurlengte vs. scheurwijdte — {rakdeel_id}"`

### 3. `scheur_en_kesp_langs_rak() -> go.Figure`

**Type:** Gecombineerd scatter/strip-diagram met gedeelde X-as  
**Bron:** bovenbouw-scheuren + `rakdeel.onderbouw.kespen`  
**X-as:** afstand langs het rak in meters (0 t/m `lengte_m`)  
**Y-as (positief, boven nul):** `Scheur`-gebreken — één punt per scheur op `afstand_van_startrak_m`  
**Y-as (negatief, onder nul):** `Kesp`-gebreken — één punt per kesp waarvan `is_aangetast == True`; de X-positie wordt afgeleid uit de volgorde van de kespen en de cumulatieve paalafstanden (`hoh_afstand_cm`)  
**Kleur:** scheuren en kespen elk een eigen vaste kleur uit `stijl.KLEUREN`  
**Referentielijn:** horizontale lijn op y=0  
**Titel:** `"Scheuren (boven) en aangetaste kespen (onder) langs rak — {rakdeel_id}"`

### 4. `gebrek_locaties_langs_rak() -> go.Figure`

**Type:** Scatter met meerdere sporen (één spoor per gebrektype)  
**Bron:** `rakdeel.bovenbouw.gebreken`  
**X-as:** afstand langs het rak in meters (`afstand_van_startrak_m` voor puntgebreken; `start_*_van_startrak_m`/`eind_*_van_startrak_m` voor vlaksgebreken als `BuikInWand` en `Scheefstand` — teken als horizontale lijn)  
**Y-as:** gebrektype (categorische labels)  
**Kleur:** per gebrektype uit `stijl.KLEUREN`  
**Titel:** `"Gebreklocaties langs rak — {rakdeel_id}"`  
**Noot:** gebreken zonder locatieveld (`figuurnummer` of `afstand_van_startrak_m`) worden weggelaten

### 5. `paal_status_barchart() -> go.Figure`

**Type:** Gegroepeerd staafdiagram  
**Bron:** `rakdeel.onderbouw.palen`  
**Groepen (X-as):** `is_paalbreuk`, `is_aantasting`, `is_juiste_aansluiting`  
  - `is_juiste_aansluiting` = `True` als `aansluiting_status is AansluitingStatus.GOED`, anders `False`  
  - Velden met `NietBeschikbaar` of `OnverwachtResultaat` worden als `None` geteld in een aparte balk `"Onbekend"`  
**Y-as:** aantal palen  
**Kleuren:** `True` → groen, `False` → rood, `None/onbekend` → grijs  
**Titel:** `"Paalstatus — {rakdeel_id}"`

### 6. `kesp_status_barchart() -> go.Figure`

**Type:** Gegroepeerd staafdiagram  
**Bron:** `rakdeel.onderbouw.kespen`  
**Groepen (X-as):** `is_vervormd`, `is_aangetast`  
  - Velden met `NietBeschikbaar` of `OnverwachtResultaat` worden als `None` geteld in een aparte balk `"Onbekend"`  
**Y-as:** aantal kespen  
**Kleuren:** `True` → oranje, `False` → groen, `None/onbekend` → grijs  
**Titel:** `"Kespstatus — {rakdeel_id}"`

---

## Gebruik

```python
from pathlib import Path
from visuals.rakdeelvisualiseerder import laad_rak_uit_json, sla_figuren_op, RakdeelVisualiseerder

rak = laad_rak_uit_json("data/json_exports/KZG0202_260304_1431.json")

for rakdeel in rak.rakdelen:
    vis = RakdeelVisualiseerder(rakdeel)
    sla_figuren_op(vis.alle_figuren, uitvoer_map=f"visuals/output/{rakdeel.rakdeel_id}")
```

---

## Algemene regels

- Alle figuren worden op `Rakdeel`-niveau gemaakt; de klasse ontvangt één `Rakdeel`-instantie.
- Alle stijlkeuzes staan uitsluitend in `stijl.py`; `rakdeelvisualiseerder.py` importeert alleen van daar.
- Gebruik `isinstance(waarde, (int, float))` om `NietBeschikbaar` en `OnverwachtResultaat` te filteren.
- Gebruik DRY: generieke hulpfuncties voor terugkerende handelingen (bijv. een puntlijst ophalen, figuurlayout toepassen) als module-niveau functies in `rakdeelvisualiseerder.py`.
