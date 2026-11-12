# Testbenadering

Dit document beschrijft de testbenadering en -structuur van het tekstherkenning-ark project.

Alle Python- en testcommando's lopen via uv. Gebruik voor de bestaande omgeving
`uv run --no-sync --offline python -m pytest`; dit installeert of synchroniseert niets.
De session-fixtures blokkeren externe netwerkverbindingen, OCR en echte Azure OpenAI-clients.
Alleen lokale loopbacksockets voor de Windows-eventloop zijn toegestaan.
LLM-antwoorden worden naar een tijdelijke sessiecache gekopieerd; referentiefixtures worden nooit overschreven.

## Lokale PDF-extractie

[test_smart_document.py](../tests/test_smart_document.py) controleert native tekst/cellen, hoofdstukhierarchie,
gemengde leesvolgorde, PNG-figuren, selecteerbare labels zonder pixel-OCR, rotatie en foutmeldingen.
Exporttests verplaatsen de volledige JSON-/PNG-bundel en controleren celspans, referenties en assetintegriteit.
Cachetests behandelen wijzigingen in bron, parser, PyMuPDF en DPI, ontbrekende/beschadigde PNG's en cachehits
zonder PDF-opening. Een vers proces blokkeert alle Azure-imports en leest de eigen fixture.

De relatief dure corpusproef is optioneel en gebruikt uitsluitend lokale PDF's:

```powershell
uv run --no-sync --offline python -m pytest tests/test_smart_document.py --pdf-corpus -k native_corpus -q -s
```

Deze proef vergelijkt alle ruwe tabelcellen exact met native broncellen die voor layoutanalyse zijn vastgelegd,
en palen-/kesprecords met bronmeetkoppen. Paalverwijzingen in houtmonsters/tekeningen zijn geen meetrecords.
Dit is een broncontrole, geen garantie op correcte LLM-classificatie of volledige visuele figuurdetectie.
De standaardset slaat deze corpusgevallen over; kleinere echte rapportselecties blijven wel onderdeel van die set.
Een bekende, procesvolgorde-afhankelijke celafwijking in KZG1002 staat met reproductiecommando's beschreven in
[openstaande extractie-afwijkingen](openstaande_extractie_afwijkingen.md); de exacte celassertion blijft actief.

## Teststructuur

Het project gebruikt pytest als testframework. Alle tests bevinden zich in de `tests/` directory:

```
tests/
├── conftest.py                              # Test fixtures en configuratie
├── data/                                    # Test data
│   ├── mock_rak_with_gebreken.py           # Mock data met gebreken
│   ├── mock_rak_with_onverwachte_resultaten.py  # Mock data met onverwachte resultaten
│   ├── mock_rak_with_scheuren.py           # Mock data met scheuren
│   └── KZG0202_Houtmonstername&.../        # Gesanitizeerde duikrapport data
├── scripts/                                 # Test utility scripts
│   └── create_kzg_0202_test_data.py        # Script om KZG0202 testdata te genereren
└── test_*.py                                # Test modules
```

## Soorten Tests

### Unit Tests

Unit tests testen individuele modellen en hun functionaliteit in isolatie. Deze tests gebruiken **mock data** die gedefinieerd is in de `tests/data/` directory.

**Voorbeelden van unit tests:**

- **[test_paal.py](../tests/test_paal.py)** - Test Paal model parsing en validatie
- **[test_gebrek.py](../tests/test_gebrek.py)** - Test Gebrek model instantiatie
- **[test_rakdeel.py](../tests/test_rakdeel.py)** - Test Rakdeel model en berekeningen
- **[test_rak_base_model.py](../tests/test_rak_base_model.py)** - Test basis model functionaliteit
- **[test_rak_base_model_integration.py](../tests/test_rak_base_model_integration.py)** - Test OnverwachtResultaat integratie

**Mock data:**

Mock data wordt aangemaakt via functies in de `tests/data/` directory:

- `create_mock_rak_with_gebreken()` - Maakt een Rak object met gebreken op verschillende niveaus
- `create_mock_rak_with_onverwachte_resultaten()` - Maakt een Rak object met OnverwachtResultaat instances
- `create_mock_rak_with_scheuren()` - Maakt een Rak object voor het testen van scheurberekeningen

Deze mock data is volledig handmatig geconstrueerd en bevat geen gevoelige informatie.

### Integration Tests - KZG0202 Duikrapport

De integration tests gebruiken een **gesanitizeerd duikrapport** om de volledige parsing pipeline te testen met realistische data. Deze tests gebruiken het KZG0202 duikrapport.
**Gesanitizeerd houdt in dan alleen de benodigde info overblijft en persoons- en gevoelige informatie verwijdert zijn**.

**Locatie:** `tests/data/KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325/`

**Belangrijkste test:** [test_rak.py](../tests/test_rak.py) met fixture `kzg0202_rak`

**Wat wordt getest:**

```python
def test_kzg0202(kzg0202_rak: Rak):
    """Verify correct number of rakdelen parsed"""
    assert len(kzg0202_rak.rakdelen) == 10

def test_kzg0202_nul_onverwacht(kzg0202_rak: Rak):
    """Verify no unexpected results in parsed data"""
    assert len(kzg0202_rak.alle_onverwachte_resultaten) == 0

def test_kzg0202_gebreken(kzg0202_rak: Rak):
    """Verify correct number of gebreken parsed"""
    assert len(kzg0202_rak.alle_gebreken) == 79

def test_kzg0202_raknaam(kzg0202_rak: Rak):
    """Verify correct raknaam parsed"""
    assert kzg0202_rak.raknaam == "KZG0202"
```

**Waarom KZG0202 tests belangrijk zijn:**

1. **Realistische data** - Test met echte (gesanitizeerde) duikrapport structuur
2. **Domeinregressie** - Test historische referentiewaarden van eigen SmartDocument-typen naar Rak; aparte PDF-tests toetsen extractie
3. **LLM caching** - LLM resultaten worden gecached, waardoor tests snel en deterministisch zijn
4. **Regressie detectie** - Wijzigingen in models die parsing beïnvloeden worden direct gedetecteerd

## KZG0202 Test Data - Sanitization & Caching

### Wat is gesanitizeerde data?

Het originele KZG0202 duikrapport bevat gevoelige informatie en is te groot voor gebruik in tests. Daarom wordt het document **gesanitizeerd**:

1. **Alleen relevante secties** - Alleen secties met meettabellen en constructie-informatie worden behouden
2. **Handmatige privacycontrole** - Relevante secties selecteren is geen garantie dat alle gevoelige tekst is verwijderd
3. **Compacte opslag** - Het SmartDocument wordt opgeslagen als pickle file

**Actieve fixture:** `KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_smart_document_lokaal.pkl`.
Deze bevat uitsluitend eigen paragrafen, cellen en sectieverwijzingen, geen Azure SDK-objecten.
De historische tekst en celwaarden zijn ongewijzigd gemigreerd, zodat bestaande LLM-cachekeys geldig blijven.
Historische tabellen hebben expliciet `herkomst="historische_fixture"`; ze worden niet als PyMuPDF-raster behandeld.
De oude gesanitizeerde pickle blijft uitsluitend als archief bestaan en wordt niet door tests geladen.

### Wat is LLM caching?

Tijdens het aanmaken van een `Rak` object worden LLM calls gedaan voor:

- Gebrek type detectie
- Rakdeel omschrijving parsing
- Scheur classificatie
- Buik-in-wand detectie
- Scheefstand detectie
- etc.

Deze LLM calls zijn **kostbaar en traag**. Om tests snel en deterministisch te maken, worden alle LLM resultaten **gecached als pickle files** in de test data directory.

**Voorbeeld cache files:**

```
gebrektypedetectiellm_<hash>.pkl
rakdeelomschrijving_<hash>.pkl
scheurhoutllm_<hash>.pkl
scheurmetselwerkllm_<hash>.pkl
buikinwandllm_<hash>.pkl
```

Tijdens tests worden kopieen van deze antwoorden gebruikt. Een cachemiss faalt hard; er volgt geen echte call.

## Test Data Updaten - Wanneer en Hoe?

### Wanneer moet je de test data updaten?

Beoordeel of de KZG0202-referentiedata moet worden bijgewerkt wanneer:

1. **Model wijzigingen** - Je wijzigt veldnamen, types of validatie in Pydantic models (Rak, Rakdeel, Paal, Gebrek, etc.)
2. **LLM prompt wijzigingen** - Je wijzigt LLM prompts voor gebrek detectie, rakdeel parsing, etc.
3. **Parsing logica wijzigingen** - Je wijzigt hoe tabellen of teksten worden geparsed in SmartDocument of model classes
4. **Nieuwe features** - Je voegt nieuwe velden toe aan models die data uit het duikrapport extraheren

**Let op:** Als je alleen unit test mock data wijzigt, hoef je de KZG0202 data **NIET** te regenereren.

### Hoe update je de KZG0202 test data?

#### Stap 1: Zorg dat het originele duikrapport beschikbaar is

Het script verwacht het originele PDF in:

```
data/duikrapporten/KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325.pdf
```

Als dit bestand niet beschikbaar is, vraag het aan een teamlid of projectbeheerder.

#### Stap 2: Run het lokale fixture-script

Voer het volgende commando uit vanuit de project root:

```powershell
uv run --no-sync --offline python tests/scripts/create_kzg_0202_test_data.py
```

**Wat doet dit script?**

1. **Laadt het originele PDF** - Van `data/duikrapporten/`
2. **Maakt SmartDocument** - Leest de PDF lokaal met PyMuPDF zonder OCR
3. **Selecteert secties** - Behoudt relevante secties en een consistente, onafhankelijke elementregistratie
4. **Slaat een eigen fixture op** - Geen LLM-calls en geen verwijdering van bestaande caches
5. **Weigert overschrijven** - Alleen bewust met `--overschrijven` kan de eigen documentfixture vervangen worden

Laat privacy en bronwaarden handmatig controleren voordat nieuwe fixtures worden gedeeld.
Nieuwe native omschrijvingen kunnen andere teksthashes hebben; bestaande LLM-antwoorden zijn dan niet automatisch passend.
Mock ontbrekende classificaties of curateer expliciet goedgekeurde testantwoorden. Deze tool regenereert ze niet automatisch.
`--migreer-historisch` is uitsluitend voor de eenmalige, reeds uitgevoerde conversie in een oude SDK-omgeving.

#### Stap 3: Verifieer de resultaten

1. Run de tests om te controleren of alles werkt:

```powershell
uv run --no-sync --offline python -m pytest tests/test_rak.py -v
```

2. **Controleer afwijkingen tegen de bron** - Verander assertions alleen bij aantoonbaar gecorrigeerde bronwaarden:

```python
# Pas een verwacht aantal alleen aan nadat de betrokken bronrecords zijn gecontroleerd.
def test_kzg0202_gebreken(kzg0202_rak: Rak):
    aantal_gebreken_tot = len(kzg0202_rak.alle_gebreken)
    assert aantal_gebreken_tot == 80, f"Expected 80 gebreken, got {aantal_gebreken_tot}"
```

#### Stap 4: Commit de changes

De gegenereerde pickle files moeten worden gecommit naar Git:

```powershell
git add tests/data/KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325/
git commit -m "Update KZG0202 test data na model wijziging"
```

## Test Fixtures

Test fixtures worden gedefinieerd in [conftest.py](../tests/conftest.py) en zijn beschikbaar voor alle tests.

**Belangrijkste fixtures:**

| Fixture | Scope | Omschrijving |
|---------|-------|--------------|
| `kzg0202_rak` | session | Volledige Rak object van KZG0202 duikrapport |
| `kzg0202_smart_document` | session | SDK-vrije historische referentie in eigen documenttypen |
| `paal_tables` | session | StructuredTable met paal meettabel data |
| `mock_rak_with_gebreken` | function | Mock Rak met gebreken op verschillende niveaus |
| `mock_rak_with_onverwachte_resultaten` | function | Mock Rak met OnverwachtResultaat instances |
| `mock_rak_with_scheuren` | function | Mock Rak voor scheur berekeningen |
| `mock_rakdeel` | function | Enkel Rakdeel uit mock_rak_with_gebreken |
| `mock_palen` | function | Lijst van Paal objecten uit mock_rak_with_gebreken |

**Session scope fixtures** worden één keer per test sessie aangemaakt en hergebruikt voor snelheid.

**Function scope fixtures** worden opnieuw aangemaakt voor elke test functie voor isolatie.

## Tests Runnen

### Alle tests runnen

```powershell
uv run --no-sync --offline python -m pytest
```

### Specifieke test module runnen

```powershell
uv run --no-sync --offline python -m pytest tests/test_rak.py
```

### Specifieke test functie runnen

```powershell
uv run --no-sync --offline python -m pytest tests/test_rak.py::test_kzg0202_gebreken -v
```

### Tests met verbose output

```powershell
uv run --no-sync --offline python -m pytest -v
```

### Tests met output van print statements

```powershell
uv run --no-sync --offline python -m pytest -s
```

## Best Practices

### Do's ✅

- **Schrijf tests voor nieuwe features** - Elke nieuwe feature moet unit tests hebben
- **Update KZG0202 tests bij model wijzigingen** - Regenereer test data wanneer models wijzigen
- **Gebruik mock data voor unit tests** - Geen echte PDF parsing in unit tests
- **Test edge cases** - Test niet alleen happy path, maar ook foutafhandeling
- **Gebruik descriptieve test namen** - Test naam moet duidelijk maken wat er getest wordt

### Dont's ❌

- **Geen echte LLM calls in tests** - Gebruik altijd caching voor snelheid en kosten
- **Geen gevoelige data in tests** - Sanitizeer altijd test data
- **Geen automatische LLM-hergeneratie** - Gebruik expliciete mocks of gecureerde, goedgekeurde antwoorden
- **Niet tests skippen zonder reden** - Als een test faalt, fix de oorzaak

## Troubleshooting

### Test faalt met een ontbrekende eigen documentfixture

**Oorzaak:** De KZG0202 test data is niet aanwezig.

**Oplossing:** Herstel de meegeleverde eigen fixture uit versiebeheer; regenereer historische testantwoorden niet stilzwijgend.

### Test faalt met "AssertionError: Expected X gebreken, got Y"

**Oorzaak:** De parsing logica of het model is gewijzigd, waardoor meer/minder gebreken worden gedetecteerd.

**Oplossing:** 

1. Verifieer of de wijziging intentioneel is
2. Vergelijk de betrokken records en waarden met de bron-PDF voordat je assertions wijzigt
3. Commit de wijziging

### Tests zijn traag

**Oorzaak:** Lokale layoutanalyse en figuurrendering van echte PDF's kosten rekenwerk. Een ontbrekende LLM-cache faalt juist direct.

**Oplossing:** Gebruik gerichte tests; activeer de volledige corpusproef alleen bewust met `--pdf-corpus`.

### Import errors in tests

**Oorzaak:** Python path is niet correct geconfigureerd.

**Oplossing:** Zorg dat je pytest runt vanuit de project root directory.

## Contact

Bij vragen over de testbenadering:

- Sammie Knoppert - sammie.knoppert@arcadis.com
- Matthias Tavasszy - matthias.tavasszy@witteveenbos.com
