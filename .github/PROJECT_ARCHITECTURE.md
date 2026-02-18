# Tekstherkenning ARK - Project Architectuur

> **Landingspagina** voor het begrijpen van de werking en architectuur van dit project.

## 📋 Inhoudsopgave

- [Overzicht](#overzicht)
- [Doel van de Tool](#doel-van-de-tool)
- [Architectuur Diagram](#architectuur-diagram)
- [Kerncomponenten](#kerncomponenten)
- [Datamodel](#datamodel)
- [Procesflow](#procesflow)
- [Technologieën](#technologieën)
- [Mappenstructuur](#mappenstructuur)
- [Configuratie](#configuratie)

---

## Overzicht

De **Tekstherkenning ARK** tool is ontwikkeld ter ondersteuning van het ARK-proces (Amsterdamse Risicobeoordeling Kademuren) van de Gemeente Amsterdam. Het project automatiseert de transformatie van duikinspectierapporten naar gestructureerde data die direct kan worden gebruikt in de [ARK-tool](https://github.com/ic144/ark-automatiseren).

### Belangrijkste functies

- **PDF-analyse**: Automatisch inlezen en parsen van duikinspectierapporten (Nebest)
- **Datastructurering**: Omzetten van tekstuele informatie naar gestandaardiseerde datamodellen
- **LLM-classificatie**: Intelligente extractie van constructie-eigenschappen via Azure OpenAI
- **Caching**: Efficiënte opslag van tussenresultaten voor herhaaldelijk gebruik

---

## Doel van de Tool

Het handmatig invoeren van gegevens uit duikinspectierapporten is tijdrovend en foutgevoelig. Deze tool automatiseert dit proces door:

1. **Duikrapporten te analyseren** met Azure Document Intelligence
2. **Relevante data te extraheren** zoals paalmetingen, gebreken en constructie-eigenschappen
3. **Gestructureerde output te genereren** die direct bruikbaar is in de ARK-tool

---

## Architectuur Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TEKSTHERKENNING ARK                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │  PDF Input   │────▶│              SmartDocument                       │   │
│  │ (Duikrapport)│     │  ┌─────────────────────────────────────────┐    │   │
│  └──────────────┘     │  │   Azure Document Intelligence SDK       │    │   │
│                       │  │   - Paragraphs                          │    │   │
│                       │  │   - Tables                              │    │   │
│                       │  │   - Sections                            │    │   │
│                       │  └─────────────────────────────────────────┘    │   │
│                       │                    │                             │   │
│                       │                    ▼                             │   │
│                       │  ┌─────────────────────────────────────────┐    │   │
│                       │  │   Sectie Parser                         │    │   │
│                       │  │   - RakdeelSectie                       │    │   │
│                       │  │   - Meettabellen                        │    │   │
│                       │  └─────────────────────────────────────────┘    │   │
│                       └─────────────────────────────────────────────────┘   │
│                                           │                                  │
│                                           ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Datamodellen (Pydantic)                        │   │
│  │  ┌─────────┐   ┌──────────┐   ┌────────┐   ┌─────────┐   ┌────────┐  │   │
│  │  │   Rak   │──▶│ Rakdeel  │──▶│ Paal   │   │  Kesp   │   │Gebrek  │  │   │
│  │  └─────────┘   └──────────┘   └────────┘   └─────────┘   └────────┘  │   │
│  │                     │                                                 │   │
│  │                     ▼                                                 │   │
│  │              ┌─────────────┐    ┌─────────────┐                       │   │
│  │              │  Bovenbouw  │    │  Onderbouw  │                       │   │
│  │              └─────────────┘    └─────────────┘                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                           │                                  │
│                                           ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         LLM Classificatie                             │   │
│  │  ┌───────────────────────┐    ┌───────────────────────────────────┐  │   │
│  │  │   AzureOpenAILLM      │    │   LLMClassifier (Base)            │  │   │
│  │  │   - GPT-4.1           │    │   - RakdeelOmschrijving           │  │   │
│  │  │   - Structured Output │    │   - GebrekClassificatie           │  │   │
│  │  └───────────────────────┘    └───────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                           │                                  │
│                                           ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Output (Gestructureerde Data)                    │   │
│  │                      - ARK-tool compatibel formaat                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Kerncomponenten

### 1. SmartDocument (`smart_document.py`)

Het centrale component voor documentanalyse. Verantwoordelijk voor:

- **PDF-analyse** via Azure Document Intelligence
- **Sectie-parsing**: Splitst het document op in logische secties (Introductie, Constructies, Bijlagen)
- **Tabel-toewijzing**: Koppelt tabellen aan de juiste secties op basis van offset
- **Caching**: Slaat resultaten op voor hergebruik

```python
# Voorbeeld gebruik
doc = SmartDocument.from_pdf(pdf_path, use_cache=True)
rakdeel_secties = doc.get_rakdeel_secties()
paal_tabellen = doc.get_meettabel_fundering_paal()
```

**Belangrijke classes:**
| Class | Beschrijving |
|-------|--------------|
| `SmartDocument` | Hoofdclass voor document parsing |
| `Sectie` | Een sectie met titel, paragrafen en tabellen |
| `RakdeelSectie` | Specifieke sectie voor een rakdeel met constructie info |

---

### 2. Datamodellen (`models/`)

Gestructureerde Pydantic modellen die de ARK-datastructuur representeren:

| Model | Beschrijving | Bron in duikrapport |
|-------|--------------|---------------------|
| `Rak` | Hoogste niveau, bevat meerdere rakdelen | Rapporttitel, H2.2.1 |
| `Rakdeel` | Een constructiedeel van een rak | Paragraaf 5.x |
| `Bovenbouw` | Eigenschappen bovenbouw (metselwerk, scheuren) | H5.3.3, gebrekentabel |
| `Onderbouw` | Eigenschappen onderbouw (palen, kespen, vloer) | Bijlage 3 |
| `Paal` | Funderingspaal met meetgegevens | Meettabel fundering |
| `Kesp` | Horizontale balk tussen palen | Meettabel fundering |
| `Gebrek` | Geconstateerd gebrek met codering | Gebrekentabel H5.3.3 |
| `Houtmonster` | Monster voor houtonderzoek | Bijlage 1 & 2 |

**Hiërarchie:**
```
Rak
├── Rakdeel
│   ├── Bovenbouw
│   │   └── Metselwerk
│   ├── Onderbouw
│   │   ├── Paal[]
│   │   │   ├── Houtmonster[]
│   │   │   └── Gebrek[]
│   │   ├── Kesp[]
│   │   ├── Vloer
│   │   └── Onderloopsheidscherm
│   └── Gebrek[]
```

---

### 3. LLM Classificatie (`llm/`)

Intelligente extractie van constructie-eigenschappen via Azure OpenAI:

| Component | Beschrijving |
|-----------|--------------|
| `AzureOpenAILLM` | Wrapper voor Azure OpenAI API met tokenberekening |
| `LLMClassifier` | Generieke base class voor gestructureerde LLM output |
| `RakdeelOmschrijving` | Extraheert materiaal, bouwjaar, lengtes uit tekst |
| `GebrekClassificatie` | Classificeert gebreken naar specifieke types |

**Werking LLMClassifier:**
1. Ontvangt een tekstuele omschrijving
2. Stuurt deze naar Azure OpenAI met een systeem-prompt
3. Ontvangt gestructureerde output (Pydantic model)
4. Cached het resultaat voor hergebruik

```python
# Voorbeeld
omschrijving = RakdeelOmschrijving.classificeer_omschrijving(tekst)
print(omschrijving.materiaal_bovenbouw)  # MateriaalBovenbouw.METSELWERK
```

---

### 4. Utilities (`utils.py`)

Hulpfuncties voor dataverwerking:

| Functie | Beschrijving |
|---------|--------------|
| `get_table_content()` | Converteert DocumentTable naar list[list[str]] |
| `parse_ja_nee()` | Parseert Ja/Nee strings naar booleans |
| `clean_paal_id()` | Corrigeert veelvoorkomende fouten in paal-IDs |
| `contains_paal_id()` | Controleert of een string een paal-ID patroon bevat |

---

## Datamodel

### Enumeraties (`enums.py`)

| Enum | Waarden | Gebruik |
|------|---------|---------|
| `MateriaalFundering` | HOUT, STAAL, BETON | Type funderingsmateriaal |
| `MateriaalOnderbouw` | HOUT, STAAL, BETON | Type onderbouw |
| `MateriaalBovenbouw` | METSELWERK, BASALT, BETON, etc. | Type bovenbouw |
| `MateriaalVloer` | ONBEKEND, HOUT, BETON | Type vloer |
| `SchoorStand` | POSITIEF (PNV), NEGATIEF (PNA), NEUTRAAL (LR) | Schoorrichting paal |
| `AansluitingStatus` | GOED (G), SLECHT (S), NIET_MEETBAAR (NM) | Status paal-kesp aansluiting |
| `NietBeschikbaar` | NVT, NM, LEEG | Ontbrekende waarden |

---

## Procesflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROCESFLOW                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. INPUT                                                                │
│     └── PDF Duikrapport (Nebest formaat)                                │
│                                                                          │
│  2. DOCUMENT ANALYSE (Azure Document Intelligence)                       │
│     ├── Tekst extractie (paragraphs)                                    │
│     ├── Tabel extractie (tables)                                        │
│     └── Structuur herkenning (sections)                                 │
│                                                                          │
│  3. SECTIE PARSING (SmartDocument)                                       │
│     ├── Identificeer secties op basis van headings                      │
│     ├── Wijs tabellen toe aan secties (offset-based)                    │
│     └── Extraheer RakdeelSecties                                        │
│                                                                          │
│  4. TABEL PARSING                                                        │
│     ├── Meettabel Palen → Paal objecten                                 │
│     ├── Meettabel Kespen → Kesp objecten                                │
│     ├── Meettabel Houtmonsters → Houtmonster objecten                   │
│     └── Gebrekentabel → Gebrek objecten                                 │
│                                                                          │
│  5. LLM CLASSIFICATIE                                                    │
│     ├── Constructie-omschrijving → RakdeelOmschrijving                  │
│     │   └── Materialen, lengtes, bouwjaar extractie                     │
│     └── Gebrek-omschrijving → Specifieke gebrektypen                    │
│         └── Scheuren, buiken, scheefstand classificatie                 │
│                                                                          │
│  6. MODEL COMPOSITIE                                                     │
│     ├── Combineer palen met houtmonsters                                │
│     ├── Bouw Onderbouw (palen, kespen, vloer)                           │
│     ├── Bouw Bovenbouw (materiaal, gebreken)                            │
│     ├── Bouw Rakdeel (bovenbouw, onderbouw, gebreken)                   │
│     └── Bouw Rak (rakdelen, metadata)                                   │
│                                                                          │
│  7. OUTPUT                                                               │
│     └── Gestructureerd Rak object (ARK-tool compatibel)                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technologieën

| Technologie | Versie | Gebruik |
|-------------|--------|---------|
| **Python** | ≥3.13 | Programmeertaal |
| **Pydantic** | ≥2.12.5 | Data validatie en modellen |
| **Azure Document Intelligence** | ≥1.0.0 | PDF-analyse en OCR |
| **Azure OpenAI** | via openai ≥2.15.0 | LLM classificatie |
| **tiktoken** | ≥0.12.0 | Token telling voor LLM |
| **pandas** | ≥3.0.0 | Data manipulatie |
| **python-dotenv** | ≥1.0.0 | Environment variabelen |

---

## Mappenstructuur

```
tekstherkenning-ark/
├── .github/
│   ├── copilot-instructions.md     # Copilot coding standards
│   └── PROJECT_ARCHITECTURE.md     # Dit document
├── data/                           # Testdata en cache
│   ├── .cache/                     # Gecachte analyse resultaten
│   └── *.pdf / *.json              # Duikinspectierapporten
├── docs/                           # Documentatie
│   ├── data_analyse.md             # Analyse notities
│   ├── datamodel.mermaid           # Datamodel diagram
│   ├── gebruik_doc_intelligence.md # Doc Intelligence handleiding
│   └── uitleg_velden_ark.md        # ARK velden mapping
├── src/tekstherkenning_ark/        # Broncode
│   ├── __init__.py
│   ├── constants.py                # Pad constanten
│   ├── enums.py                    # Enumeratie definities
│   ├── smart_document.py           # Document parser
│   ├── utils.py                    # Hulpfuncties
│   ├── llm/                        # LLM classificatie
│   │   ├── azureopenaillm.py       # Azure OpenAI wrapper
│   │   ├── llmclassifier.py        # Base classifier class
│   │   ├── rakdeel_omschrijving.py # Rakdeel classificatie
│   │   └── gebrek_classificatie.py # Gebrek classificatie
│   └── models/                     # Pydantic datamodellen
│       ├── rak.py                  # Rak model
│       ├── rakdeel.py              # Rakdeel model
│       ├── paal.py                 # Paal model
│       ├── kesp.py                 # Kesp model
│       ├── gebrek.py               # Gebrek model
│       ├── bovenbouw.py            # Bovenbouw model
│       ├── onderbouw.py            # Onderbouw model
│       └── ...                     # Overige modellen
├── tests/                          # Unit tests
├── main.py                         # Entry point
├── pyproject.toml                  # Project configuratie
└── README.md                       # Project overzicht
```

---

## Configuratie

### Environment Variabelen (`.env`)

```bash
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=<your-key>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_KEY=<your-key>
DEPLOYMENT_NAME_GPT41=gpt-41
```

### Caching

Resultaten worden gecached in `data/.cache/`:
- `*_docai_result.pkl` - Azure Document Intelligence resultaten
- `rak_*.pkl` - Volledige Rak objecten
- `rakdeelomschrijving_*.pkl` - LLM classificatie resultaten

---

## Gerelateerde Documentatie

- [README.md](../README.md) - Project overzicht en samenwerking
- [uitleg_velden_ark.md](../docs/uitleg_velden_ark.md) - Mapping duikrapport → ARK velden
- [data_analyse.md](../docs/data_analyse.md) - Data analyse notities
- [gebruik_doc_intelligence.md](../docs/gebruik_doc_intelligence.md) - Document Intelligence handleiding

---

## Contact

| Naam | Email | Organisatie |
|------|-------|-------------|
| Sammie Knoppert | sammie.knoppert@arcadis.com | Arcadis |
| Matthias Tavasszy | matthias.tavasszy@witteveenbos.com | Witteveen+Bos |

**Opdrachtgever:** Gemeente Amsterdam
