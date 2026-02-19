# LLM-gebaseerde Gebrektype Detectie

## Overzicht

Deze documentatie beschrijft de implementatie van LLM-gebaseerde detectie van gebrektype(n) voor verbeterde classificatie van gebreken in kademuren.

## Probleem

De originele implementatie gebruikte eenvoudige keyword matching voor het detecteren van gebrektypes. Dit werkte niet goed voor bepaalde types:

- **GrondVoerendGat** en **LokaalVerdwenenMetselwerk**: Vaak werden gaten in metselwerk niet goed herkend door beperkte synonym lijst. Het verschil tussen grondvoerende en niet-grondvoerende gaten was moeilijk te bepalen met simpele keywords.
- **BuikInWand** en **Scheefstand**: Afwijkingen van verticale stand werden niet goed gedetecteerd als ze niet exact de woorden "buik" of "scheefstand" bevatten. Het onderscheid tussen een uitbuiging (buik) en scheefstand vereist contextbegrip.

## Oplossing

### 1. Nieuw LLM Model: `GebrekTypeDetectieLLM`

Een nieuwe LLM classifier die automatisch detecteert welke type(n) gebrek(en) aanwezig zijn in een omschrijving, **inclusief de nuance tussen gerelateerde types**.

**Kenmerken:**
- Gebruikt Azure OpenAI voor intelligente text analyse
- Kan meerdere gebrektypes in één omschrijving detecteren
- Bevat gedetailleerde instructies voor elk gebrektype met nadruk op de verschillen
- Boolean velden voor elk specifiek type:
  - `is_scheur`
  - `is_grondvoerend_gat` - LLM bepaalt of het gat grondvoerend is
  - `is_verdwenen_metselwerk` - LLM bepaalt of het ontbrekend metselwerk zonder grondvoerende werking is
  - `is_buik_in_wand` - LLM bepaalt of het een uitbuiging is
  - `is_scheefstand` - LLM bepaalt of het scheefstand zonder uitbuiging is
  - `is_onderloopsheidscherm`

### 2. LLM-Gedreven Classificatie (Geen Keyword Fallback)

**Voor GrondVoerendGat vs LokaalVerdwenenMetselwerk:**
- LLM analyseert de omschrijving en bepaalt of het gat grondvoerend is of simpelweg ontbrekend metselwerk
- Geen keyword-gebaseerde fallback meer - de LLM maakt het onderscheid
- LLM kijkt naar context zoals "grondvoerend", maar ook naar beschrijvingen van grondstroming

**Voor BuikInWand vs Scheefstand:**
- LLM analyseert de omschrijving en bepaalt of het een uitbuiging (buik) of scheefstand is
- Geen keyword-gebaseerde fallback meer - de LLM maakt het onderscheid
- LLM begrijpt het verschil tussen convexe uitbuiging en afwijking van verticaal

### 3. Bijgewerkte Classificatie Flow

```
Gebrek Omschrijving
    ↓
GebrekTypeDetectieLLM (bepaal exact type met LLM)
    ↓
Prioriteit 1: Is het een Scheur?
    → Ja: Verder classificeren naar ScheurHout/ScheurMetselwerk/Scheur
    
Prioriteit 2: Is het GrondVoerendGat? (door LLM bepaald)
    → Ja: Classificeer naar GrondVoerendGat
    
Prioriteit 3: Is het LokaalVerdwenenMetselwerk? (door LLM bepaald)
    → Ja: Classificeer naar LokaalVerdwenenMetselwerk
    
Prioriteit 4: Is het BuikInWand? (door LLM bepaald)
    → Ja: Classificeer naar BuikInWand
    
Prioriteit 5: Is het Scheefstand? (door LLM bepaald)
    → Ja: Classificeer naar Scheefstand
    
Prioriteit 6: Is het Onderloopsheidscherm?
    → Ja: Return OnderloopsheidschermBeschadigd
    
Anders: Return originele Gebrek (niet geclassificeerd)
```

## Voordelen

1. **Betere Nuance-Detectie**: LLM begrijpt het verschil tussen grondvoerend gat en verdwenen metselwerk, en tussen buik en scheefstand
2. **Contextbegrip**: LLM analyseert de volledige beschrijving, niet alleen keywords
3. **Flexibiliteit**: Gemakkelijk uit te breiden met nieuwe gebrektypes
4. **Robuustheid**: Werkt met verschillende formuleringen van dezelfde gebrektypes
5. **Performance**: Resultaten worden gecached om herhaalde LLM calls te voorkomen
6. **Backward Compatibility**: Bestaande tests blijven werken (101/101 tests slagen)

## System Prompt Details

De LLM krijgt gedetailleerde instructies om onderscheid te maken:

**GrondVoerendGat vs LokaalVerdwenenMetselwerk:**
- Grondvoerend gat: Een gat waar grond doorheen stroomt of kan stromen
- Verdwenen metselwerk: Ontbrekend metselwerk ZONDER expliciete vermelding van grondvoerende werking

**BuikInWand vs Scheefstand:**
- Buik in wand: Een uitbuiging of convexe vorm naar buiten toe
- Scheefstand: Afwijking van verticaal ZONDER duidelijke buik

## Gebruik

De classificatie gebeurt automatisch bij het verwerken van gebreken:

```python
from tekstherkenning_ark.models.gebrek import Gebrek

# Voorbeeld 1: Grondvoerend gat
gebrek1 = Gebrek(
    codering="GB1",
    omschrijving="Grondvoerend gat achter metselwerk, grond stroomt erdoor",
    figuurnummer="1"
)
result1 = await Gebrek.classify_gebrek(gebrek1)
# Result: GrondVoerendGat (LLM herkent grondvoerende werking)

# Voorbeeld 2: Verdwenen metselwerk
gebrek2 = Gebrek(
    codering="GB2",
    omschrijving="Metselwerk ontbreekt lokaal, gat van 30x40 cm",
    figuurnummer="2"
)
result2 = await Gebrek.classify_gebrek(gebrek2)
# Result: LokaalVerdwenenMetselwerk (LLM ziet geen grondvoerende werking)

# Voorbeeld 3: Buik in wand
gebrek3 = Gebrek(
    codering="GB3",
    omschrijving="Wand buigt uit met buik van 5 cm",
    figuurnummer="3"
)
result3 = await Gebrek.classify_gebrek(gebrek3)
# Result: BuikInWand (LLM herkent uitbuiging)

# Voorbeeld 4: Scheefstand
gebrek4 = Gebrek(
    codering="GB4",
    omschrijving="Wand staat niet verticaal, wijkt af naar water",
    figuurnummer="4"
)
result4 = await Gebrek.classify_gebrek(gebrek4)
# Result: Scheefstand (LLM herkent scheefstand zonder buik)
```

## Testen

7 tests in `tests/test_gebrek_type_detectie.py` valideren:
- ✅ Detectie van grondvoerend gat (LLM-gebaseerd)
- ✅ Detectie van verdwenen metselwerk (LLM-gebaseerd, zonder grondvoerend)
- ✅ Detectie van buik in wand (LLM-gebaseerd)
- ✅ Detectie van scheefstand (LLM-gebaseerd, zonder buik)
- ✅ Prioriteit van scheur detectie
- ✅ Filtering van niet-algemene gebreken
- ✅ Correcte afhandeling van onbekende gebrektypes

## Configuratie

De LLM gebruikt dezelfde Azure OpenAI configuratie als bestaande classifiers:

```bash
AZURE_OPENAI_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_VERSION=<api-version>
AZURE_MODEL_NAME=<model-name>
```

## Prestaties

- **Caching**: Resultaten worden lokaal gecached op basis van MD5 hash van de omschrijving
- **Parallel Processing**: Meerdere gebreken worden parallel geclassificeerd via `asyncio.gather()`
- **API Calls**: Per gebrek 2 LLM calls (1 voor type detectie, 1 voor attribuut extractie)

## Verschil met Vorige Implementatie

**Voorheen (keyword fallback):**
```python
# LLM detecteerde gecombineerde categorie
if type_detectie.is_grondvoerend_gat_of_verdwenen_metselwerk:
    # Keyword fallback bepaalde specifiek type
    if "grondvoerend" in omschrijving:
        return GrondVoerendGat
    else:
        return LokaalVerdwenenMetselwerk
```

**Nu (LLM bepaalt nuance):**
```python
# LLM bepaalt direct het specifieke type
if type_detectie.is_grondvoerend_gat:
    return GrondVoerendGat
    
if type_detectie.is_verdwenen_metselwerk:
    return LokaalVerdwenenMetselwerk
```

Dit betekent dat de LLM nu de volledige verantwoordelijkheid heeft voor het onderscheid maken tussen gerelateerde gebrektypes, wat resulteert in betere classificatie bij edge cases.

## Toekomstige Uitbreidingen

Mogelijke verbeteringen:
1. Fine-tuning van het LLM model met testset data voor nog betere nuance-detectie
2. Toevoegen van meer gebrektypes aan de type detectie
3. Feedback loop om detectie nauwkeurigheid te verbeteren
4. Monitoring van classificatie accuratesse per gebrektype
5. A/B testing tussen LLM-classificatie en keyword-classificatie voor validatie
