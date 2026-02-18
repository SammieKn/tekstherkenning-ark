# LLM-gebaseerde Gebrektype Detectie

## Overzicht

Deze documentatie beschrijft de implementatie van LLM-gebaseerde detectie van gebrektype(n) voor verbeterde classificatie van gebreken in kademuren.

## Probleem

De originele implementatie gebruikte eenvoudige keyword matching voor het detecteren van gebrektypes. Dit werkte niet goed voor bepaalde types:

- **GrondVoerendGat** en **LokaalVerdwenenMetselwerk**: Vaak werden gaten in metselwerk niet goed herkend door beperkte synonym lijst
- **BuikInWand** en **Scheefstand**: Afwijkingen van verticale stand werden niet goed gedetecteerd als ze niet exact de woorden "buik" of "scheefstand" bevatten

## Oplossing

### 1. Nieuw LLM Model: `GebrekTypeDetectieLLM`

Een nieuwe LLM classifier die automatisch detecteert welke type(n) gebrek(en) aanwezig zijn in een omschrijving.

**Kenmerken:**
- Gebruikt Azure OpenAI voor intelligente text analyse
- Kan meerdere gebrektypes in één omschrijving detecteren
- Bevat gedetailleerde instructies voor elk gebrektype
- Boolean velden voor elk type:
  - `is_scheur`
  - `is_grondvoerend_gat_of_verdwenen_metselwerk`
  - `is_buik_of_scheefstand`
  - `is_onderloopsheidscherm`

### 2. Fallback Logica

**Voor GrondVoerendGat / LokaalVerdwenenMetselwerk:**
1. LLM detecteert eerst of het een gat of ontbrekend metselwerk is
2. Als "grondvoerend" in de omschrijving staat → `GrondVoerendGat`
3. Anders → `LokaalVerdwenenMetselwerk`

**Voor BuikInWand / Scheefstand:**
1. LLM detecteert eerst of het een afwijking van verticaal is
2. Als "buik" of "uitbuiging" in de omschrijving staat → `BuikInWand`
3. Anders → `Scheefstand`

### 3. Bijgewerkte Classificatie Flow

```
Gebrek Omschrijving
    ↓
GebrekTypeDetectieLLM (bepaal type)
    ↓
Prioriteit 1: Is het een Scheur?
    → Ja: Verder classificeren naar ScheurHout/ScheurMetselwerk/Scheur
    
Prioriteit 2: Is het GrondVoerendGat of LokaalVerdwenenMetselwerk?
    → Ja: Check "grondvoerend" keyword voor specifiek type
    
Prioriteit 3: Is het BuikInWand of Scheefstand?
    → Ja: Check "buik"/"uitbuiging" keywords voor specifiek type
    
Prioriteit 4: Is het Onderloopsheidscherm?
    → Ja: Return OnderloopsheidschermBeschadigd
    
Anders: Return originele Gebrek (niet geclassificeerd)
```

## Voordelen

1. **Betere Detectie**: LLM begrijpt context en synoniemen beter dan keyword matching
2. **Flexibiliteit**: Gemakkelijk uit te breiden met nieuwe gebrektypes
3. **Robuustheid**: Werkt met verschillende formuleringen van dezelfde gebrektypes
4. **Performance**: Resultaten worden gecached om herhaalde LLM calls te voorkomen
5. **Backward Compatibility**: Bestaande tests blijven werken (101/101 tests slagen)

## Gebruik

De classificatie gebeurt automatisch bij het verwerken van gebreken:

```python
from tekstherkenning_ark.models.gebrek import Gebrek

# Maak een gebrek instantie
gebrek = Gebrek(
    codering="GB1",
    omschrijving="Metselwerk ontbreekt, gat van 30x40 cm",
    figuurnummer="1"
)

# Classificeer naar specifiek type (async)
geclassificeerd_gebrek = await Gebrek.classify_gebrek(gebrek)
# Result: LokaalVerdwenenMetselwerk met breedte_cm=30, hoogte_cm=40
```

## Testen

7 nieuwe tests in `tests/test_gebrek_type_detectie.py` valideren:
- ✅ Detectie van grondvoerend gat
- ✅ Detectie van verdwenen metselwerk (zonder "grondvoerend")
- ✅ Detectie van buik in wand
- ✅ Detectie van scheefstand (zonder "buik")
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
- **API Calls**: Per gebrek 1-2 LLM calls (1 voor type detectie, 1 voor attribuut extractie)

## Toekomstige Uitbreidingen

Mogelijke verbeteringen:
1. Fine-tuning van het LLM model met testset data
2. Toevoegen van meer gebrektypes aan de type detectie
3. Feedback loop om detectie nauwkeurigheid te verbeteren
4. Monitoring van classificatie accuratesse
