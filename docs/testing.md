# Testbenadering

Dit document beschrijft de testbenadering en -structuur van het tekstherkenning-ark project.

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
    assert len(kzg0202_rak.alle_gebreken) == 78

def test_kzg0202_raknaam(kzg0202_rak: Rak):
    """Verify correct raknaam parsed"""
    assert kzg0202_rak.raknaam == "KZG0202"
```

**Waarom KZG0202 tests belangrijk zijn:**

1. **Realistische data** - Test met echte (gesanitizeerde) duikrapport structuur
2. **End-to-end validatie** - Test de volledige parsing pipeline van PDF → SmartDocument → Rak
3. **LLM caching** - LLM resultaten worden gecached, waardoor tests snel en deterministisch zijn
4. **Regressie detectie** - Wijzigingen in models die parsing beïnvloeden worden direct gedetecteerd

## KZG0202 Test Data - Sanitization & Caching

### Wat is gesanitizeerde data?

Het originele KZG0202 duikrapport bevat gevoelige informatie en is te groot voor gebruik in tests. Daarom wordt het document **gesanitizeerd**:

1. **Alleen relevante secties** - Alleen secties met meettabellen en constructie-informatie worden behouden
2. **Geen gevoelige data** - Azure Document Intelligence `analyze_result` wordt verwijderd
3. **Compacte opslag** - Het SmartDocument wordt opgeslagen als pickle file

**Resultaat:** `KZG0202_Houtmonstername&VisueleInspectie_V1.2_20220325_smart_document_sanitized.pkl`

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

Tijdens tests worden deze cached resultaten gebruikt in plaats van echte LLM calls te doen.

## Test Data Updaten - Wanneer en Hoe?

### Wanneer moet je de test data updaten?

Je moet de KZG0202 test data **regenereren** wanneer:

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

#### Stap 2: Run het regeneratie script

Voer het volgende commando uit vanuit de project root:

```powershell
python tests\scripts\create_kzg_0202_test_data.py
```

**Wat doet dit script?**

1. **Laadt het originele PDF** - Van `data/duikrapporten/`
2. **Maakt SmartDocument** - Parsed het document met Azure Document Intelligence (gebruikt cache indien beschikbaar)
3. **Sanitizeert het document** - Behoudt alleen relevante secties, verwijdert gevoelige data
4. **Cleared oude LLM cache** - Verwijdert alle bestaande LLM cache files
5. **Genereert nieuwe LLM cache** - Maakt een Rak object en cached alle LLM calls
6. **Slaat resultaten op** - Schrijft gesanitizeerd SmartDocument + LLM caches naar `tests/data/KZG0202.../`

#### Stap 3: Verifieer de resultaten

1. Run de tests om te controleren of alles werkt:

```powershell
pytest tests/test_rak.py -v
```

2. **Controleer de test assertions** - Als de verwachte aantallen zijn veranderd (bijv. aantal gebreken, rakdelen), update de assertions in de tests:

```python
# Voorbeeld: als het aantal gebreken is gewijzigd van 78 naar 80
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
| `paal_tables` | session | DocumentTable met paal meettabel data |
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
pytest
```

### Specifieke test module runnen

```powershell
pytest tests/test_rak.py
```

### Specifieke test functie runnen

```powershell
pytest tests/test_rak.py::test_kzg0202_gebreken -v
```

### Tests met verbose output

```powershell
pytest -v
```

### Tests met output van print statements

```powershell
pytest -s
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
- **Niet handmatig LLM cache files aanmaken** - Gebruik altijd het regeneratie script
- **Niet tests skippen zonder reden** - Als een test faalt, fix de oorzaak

## Troubleshooting

### Test faalt met "FileNotFoundError: KZG0202_smart_document_sanitized.pkl"

**Oorzaak:** De KZG0202 test data is niet aanwezig.

**Oplossing:** Run het regeneratie script (zie "Hoe update je de KZG0202 test data?")

### Test faalt met "AssertionError: Expected X gebreken, got Y"

**Oorzaak:** De parsing logica of het model is gewijzigd, waardoor meer/minder gebreken worden gedetecteerd.

**Oplossing:** 

1. Verifieer of de wijziging intentioneel is
2. Update de test assertion naar het nieuwe verwachte aantal
3. Commit de wijziging

### Tests zijn traag

**Oorzaak:** LLM cache is niet aanwezig en er worden echte LLM calls gedaan.

**Oplossing:** Regenereer de KZG0202 test data om de LLM cache te vullen.

### Import errors in tests

**Oorzaak:** Python path is niet correct geconfigureerd.

**Oplossing:** Zorg dat je pytest runt vanuit de project root directory.

## Contact

Bij vragen over de testbenadering:

- Sammie Knoppert - sammie.knoppert@arcadis.com
- Matthias Tavasszy - matthias.tavasszy@witteveenbos.com
