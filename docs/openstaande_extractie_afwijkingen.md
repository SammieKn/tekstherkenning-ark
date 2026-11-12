# Openstaande extractie-afwijkingen

Dit document registreert bevindingen voor vervolgonderzoek. Het maakt geen afwijkende bronwaarden acceptabel en verandert geen testverwachtingen.

## Open: procesvolgorde-afhankelijke celtekst

De ruwe tabelvergelijking vindt negen tekstverschillen in de autorisatietabel `p1-t0` op pagina 1: nulgebaseerde rijen 1-3 en kolommen 1-3. Het patroon is gelijk voor de twee geteste rapporten:

- Kolom 1: initialen en punten worden anders gegroepeerd; de bronvariant bevat ook een extra puntregel.
- Kolom 2: de broncellen hebben een statuswoord zonder tussenliggende spatie; de extractiecellen hebben die spatie.
- Kolom 3: de broncellen voegen dag en maand aaneen; de extractiecellen scheiden ze met een spatie.

Alle negen verschillen blijven ongelijk na witruimtenormalisatie. Namen en letterlijke celwaarden staan hier bewust niet uitgeschreven. In de tweede-rapport-runs kwamen de overige 75 HEG0201-tabellen en 61 KZG1002-tabellen exact overeen.

De nieuwe [celvergelijker](../scripts/vergelijk_native_tabelcellen.py) toont de werkelijke bron- en extractiewaarden lokaal. De uitvoer kan persoonsgegevens bevatten; deel of commit die niet zonder controle. De vergelijker gebruikt een tijdelijke cache en herstelt de bestaande cache-instelling.

```powershell
uv run --no-sync --offline python -m scripts.vergelijk_native_tabelcellen "data/duikrapporten/HEG0201_Houtmonstername&VisueleInspectie_V1.1_20220504.pdf" "data/duikrapporten/KZG1002_Houtmonstername&VisueleInspectie_V1.1_20220207.pdf"
```

Waargenomen runs met PyMuPDF 2.1:

| Procesvolgorde | Eerste PDF | Tweede PDF |
|---|---:|---:|
| HEG0201, KZG1002 | 0 verschillen | 9 verschillen in `p1-t0` |
| KZG1002, HEG0201 | 0 verschillen | 9 verschillen in `p1-t0` |
| KZG1002 alleen, vers proces | 0 verschillen | n.v.t. |

De afwijking is dus niet specifiek voor KZG1002 of voor HEG0201 als voorganger. Ze treedt in deze proeven op bij het tweede rapport in hetzelfde proces. Ook de diagnostische optie `--bron-via-byte-stream` gaf negen verschillen; alleen het verschil tussen pad-openen en stream-openen verklaart het niet.

De corpusassertion in [test_smart_document.py](../tests/test_smart_document.py#L781) blijft exact en is niet versoepeld. In `DocumentTabel.from_pymupdf()` wordt de tekst rechtstreeks uit `Table.extract()` gekopieerd; `_lees_layout()` verplaatst de tabel alleen naar de leesvolgorde. Er zijn geen expliciete PyMuPDF-globale tekstinstellingen in de repository gevonden. De observaties wijzen daarom op procesafhankelijke verschillen tussen PyMuPDF-extracties, maar bewijzen nog geen interne oorzaak.

Vervolgonderzoek: vergelijk `Page.find_tables(use_layout=False).tables[0].extract()` direct in het tweede rapport vóór en na de eerste `SmartDocument.from_pdf()`-aanroep. Herhaal daarna met alleen `Document.to_json()` als voorganger en met het tweede rapport twee keer achter elkaar. Leg PyMuPDF-versie en exacte matrices vast in een afgeschermde lokale sessie. De celassertion niet normaliseren of overslaan.

De corpuscontrole en vergelijker zijn optioneel. De volledige corpuscontrole is:

```powershell
uv run --no-sync --offline python -m pytest -q --tb=short --show-capture=no --pdf-corpus
```

## Eerder gevonden en gecorrigeerd

- KZG0202 pagina 59: een kortere rechterrand van een cel werd ten onrechte als rasterlijn geteld. Celspans worden nu afgeleid van celstartankers; de extractieversie is verhoogd.
- KZG1002 pagina 36: zes paalrijen vielen onder de meerderheid-ID-drempel, ondanks een bevestigde meetkop. De meetkop bevestigt nu het segmenttype.
- OVW0101 pagina 18: acht paalrijen betroffen dezelfde drempelkwestie; een gerichte broncontrole bevestigde behoud.
- HEG0201 had correcte tabelvervolgen zonder herhaalde kop. De onafhankelijke corpuscontrole telt zulke records nu mee via de voorafgaande bevestigde, aangrenzende meettabel.

Gerichte corpusproeven na deze correcties slaagden voor HEG0201 en OVW0101; de volledige KZG1002-proef blijft hierboven genoteerd. De standaard regressieset slaagt. Zie [testdocumentatie](testing.md) voor de corpusoptie en haar scope.

## Laatst bekende validatie

```text
uv run --no-sync --offline python -m pytest -q --tb=short --show-capture=no
249 passed, 12 skipped, 1 bestaande PytestCollectionWarning
```

De 12 skips zijn de optionele lokale corpuscontroles; de afwijking hierboven blijft dus apart zichtbaar. Externe netwerkverbindingen, OCR en echte Azure OpenAI-clients zijn in de tests geblokkeerd. Er zijn geen bestaande caches verwijderd.
