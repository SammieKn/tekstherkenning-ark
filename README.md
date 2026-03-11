# Tekstherkenning ARK

## Wat doet deze tool?

Deze tool ondersteunt het ARK-proces (Amsterdamse Risicobeoordeling Kademuren) van de Gemeente Amsterdam door duikinspecties automatisch te transformeren naar gestructureerde data. Duikinspectierapporten van Nebest worden ingelezen en omgezet naar een standaard datastructuur die direct gebruikt kan worden in de [ARK-tool](https://github.com/ic144/ark-automatiseren).

De tool automatiseert het handmatige werk van het invoeren van gegevens uit duikinspectierapporten, waardoor fouten worden verminderd en tijd wordt bespaard.

## Gebruik

### Command-line interface

De tool kan worden gebruikt via de command-line om duikinspectierapporten te verwerken:

```bash
uv run tekstherkenning-ark -i <input_pdf_path> [-o <output_directory>]
```

**Parameters:**
- `-i`, `--input`: Pad naar het input PDF bestand (verplicht)
- `-o`, `--output`: Output directory voor het JSON bestand (optioneel, default: huidige directory)
- `--no-cache`: Gebruik geen cache voor Azure Document Intelligence (optioneel)

**Voorbeelden:**

```bash
# Verwerk een rapport en sla op in huidige directory
uv run tekstherkenning-ark -i data/duikrapporten/HEG0201_Houtmonstername.pdf

# Verwerk een rapport en sla op in specifieke directory
uv run tekstherkenning-ark -i data/duikrapporten/HEG0201_Houtmonstername.pdf -o data/json_exports

# Verwerk zonder cache te gebruiken
uv run tekstherkenning-ark -i data/duikrapporten/HEG0201_Houtmonstername.pdf -o output --no-cache
```

De output wordt automatisch opgeslagen met een bestandsnaam gebaseerd op de rakcode (bijv. `HEG0201`) en een timestamp in het formaat: `{rakcode}_{YYMMDD_HHMM}.json`

**Belangrijke punten:**
- Het PDF bestand moet een geldige rakcode bevatten (bijv. HEG0201, AMS0601)
- PDF's met "boorweestand" in de bestandsnaam worden automatisch afgewezen, aangezien dit type rapport niet wordt ondersteund
- De output directory wordt automatisch aangemaakt als deze nog niet bestaat

## Samenwerken

### Branching strategie
- **main** - stabiele releases
- **develop** - development branch voor nieuwe features
- **feature branches** - voor nieuwe functionaliteit (gebruik `kebab-case` voor branch namen, bijvoorbeeld `feature/nieuwe-parser`)

### Workflow
1. Maak een feature branch vanaf `develop`
2. Ontwikkel en test je feature
3. Maak een pull request naar `develop`
4. Na review en goedkeuring: merge naar `develop`
5. Releases worden gedaan van `develop` naar `main`

### Code standaarden
- Voertaal: Nederlands (documentatie en comments)
- Python code volgens PEP8
- Gebruik `kebab-case` voor branch naming

### Contact
Voor vragen over de ontwikkeling:
- Sammie Knoppert - sammie.knoppert@arcadis.com
- Matthias Tavasszy - matthias.tavasszy@witteveenbos.com

## Project informatie
- **Opdrachtgever:** Gemeente Amsterdam
- **Doel:** Ondersteuning ARK-proces voor kademuren

## Documentatie
Zie [docs/uitleg_velden_ark.md](docs/uitleg_velden_ark.md) voor uitleg over de mapping tussen duikrapporten en ARK-velden.

