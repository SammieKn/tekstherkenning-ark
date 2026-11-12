# Reviewgids: extractie-afwijkingen

## Doel

Gebruik deze gids om de bekende verschillen tussen ruwe PyMuPDF-tabelcellen en de door `SmartDocument` vastgelegde cellen te beoordelen. De vergelijker toont celtekst op stdout; die kan persoonsgegevens bevatten. Deel of commit die uitvoer niet zonder controle.

De eerdere registratie en validatiecontext staan in [openstaande_extractie_afwijkingen.md](openstaande_extractie_afwijkingen.md).

## Bekende open afwijking

In de tweede PDF die in een proces wordt verwerkt, verschillen negen cellen van de autorisatietabel `p1-t0` op pagina 1: nulgebaseerde rijen 1-3 en kolommen 1-3. In de eerste PDF zijn er nul celverschillen. Dit patroon is waargenomen voor HEG0201 gevolgd door KZG1002 én voor de omgekeerde volgorde. KZG1002 geïsoleerd in een vers proces gaf nul verschillen.

De verschillen zijn inhoudelijk zichtbaar in de tekstpresentatie: initialen/punten en regelafbreking in kolom 1, een spatie in een statuswoord in kolom 2, en spatiëring tussen dag en maand in kolom 3. Geen van de negen paren wordt gelijk door witruimtenormalisatie. In de runs waarin een rapport als tweede werd verwerkt, kwamen de overige 75 HEG0201-tabellen en 61 KZG1002-tabellen exact overeen.

De exacte waarden zijn bewust niet in dit document opgenomen. Gebruik de vergelijker voor lokale inspectie; zie [openstaande_extractie_afwijkingen.md](openstaande_extractie_afwijkingen.md) voor de waargenomen runresultaten en werkhypothese.

## Wat de test vergelijkt

In [test_smart_document.py](../tests/test_smart_document.py#L709) bouwt de corpuscontrole eerst `brontabellen` met `Page.find_tables(use_layout=False)` en `Table.extract()`. Daarna opent de test dezelfde PDF via `SmartDocument.from_pdf()` en bouwt `geextraheerd` uit de `DocumentTabel.matrix`-waarden.

De exacte vergelijking staat op [regel 781](../tests/test_smart_document.py#L781). Bij een fout toont de assertion tabel-, rij- en kolomcoördinaten plus een boolean die aangeeft of whitespace-normalisatie de tekst gelijk zou maken. De assertion toont de celtekst zelf niet.

| Vergelijkingspunt | Referentie | Extractie |
|---|---|---|
| Tabel | `brontabellen["p1-t0"]` | `geextraheerd["p1-t0"]` |
| Cellen | rijen 1-3, kolommen 1-3 | dezelfde posities |
| Resultaat | ruwe PyMuPDF-tekst | opgeslagen `DocumentTabel.matrix`-tekst |

## Reviewstappen

1. Toon de werkelijke verschillen met de vergelijker. Dit commando gebruikt dezelfde rapportvolgorde als de eerste waarneming; de uitvoer kan persoonsgegevens bevatten:

   ```powershell
   uv run --no-sync --offline python -m scripts.vergelijk_native_tabelcellen "data/duikrapporten/HEG0201_Houtmonstername&VisueleInspectie_V1.1_20220504.pdf" "data/duikrapporten/KZG1002_Houtmonstername&VisueleInspectie_V1.1_20220207.pdf"
   ```

2. Keer de volgorde om. De waargenomen uitkomst was opnieuw nul verschillen voor het eerste rapport en negen voor het tweede:

   ```powershell
   uv run --no-sync --offline python -m scripts.vergelijk_native_tabelcellen "data/duikrapporten/KZG1002_Houtmonstername&VisueleInspectie_V1.1_20220207.pdf" "data/duikrapporten/HEG0201_Houtmonstername&VisueleInspectie_V1.1_20220504.pdf"
   ```

3. Vergelijk KZG1002 geïsoleerd in een vers proces. De bekende uitkomst is nul verschillen:

   ```powershell
   uv run --no-sync --offline python -m scripts.vergelijk_native_tabelcellen "data/duikrapporten/KZG1002_Houtmonstername&VisueleInspectie_V1.1_20220207.pdf"
   ```

4. Gebruik zo nodig `--bron-via-byte-stream` om ook de referentie-PDF als bytesstream te openen. De huidige proef gaf daarmee nog steeds negen verschillen, dus het openmechanisme alleen verklaart de anomalie niet.

5. Bij een gecombineerde fout: zet een breakpoint bij de assertion op regel 781 en vergelijk `brontabellen["p1-t0"]` met `geextraheerd["p1-t0"]`. Leg lokaal vast of het verschil in inhoud, regeleinden, celpositie of rastervorm zit. Schrijf gevoelige celtekst niet naar testoutput.

6. Volg de referentieroute vanaf `get_text("dict", sort=True)` en `find_tables(use_layout=False)` in de corpuscontrole. Volg daarna de extractieroute vanaf `SmartDocument.from_pdf()` in [smart_document.py](../src/tekstherkenning_ark/document/smart_document.py#L474).

7. Controleer in [structured_table.py](../src/tekstherkenning_ark/document/structured_table.py#L81) hoe `DocumentTabel.from_pymupdf()` `Table.extract()` omzet naar cellen. Deze conversie kopieert de tekst; `_lees_layout()` verandert de celinhoud niet.

8. Vervolg de isolatie door `Table.extract()` voor het tweede rapport vóór en na één eerdere `SmartDocument.from_pdf()`-aanroep te vergelijken. Test daarna of alleen `Document.to_json()` de uitkomst beïnvloedt. Noteer per run de PyMuPDF-versie, rapportvolgorde en verschillen.

## Werkhypothese

De huidige feiten wijzen op een PyMuPDF-/MuPDF-procestoestand die de tabeltekst van de tweede PDF beïnvloedt. De fout treedt met beide rapporten op als tweede document, blijft bestaan wanneer de bron ook als bytesstream wordt geopend en betreft tekst die rechtstreeks uit `Table.extract()` wordt gekopieerd. Er is geen expliciete globale PyMuPDF-tekstinstelling in de repository gevonden. De exacte interne oorzaak is nog onbekend; bovenstaande aanvullende probes moeten dat onderscheid maken.

Verander de assertion niet in whitespace-normalisatie, sla de tabel niet over en versoepel de vergelijking niet om de fout groen te maken.

## Eerder gevonden verschillen die zijn gecorrigeerd

- **KZG0202, pagina 59:** een kortere rechterrand leidde tot een onjuiste kolomspan. De celstartankers bepalen nu het raster. De regressietest staat in [test_smart_document.py](../tests/test_smart_document.py#L460).
- **KZG1002, pagina 36 en OVW0101, pagina 18:** meetrijen vielen weg door een lage ID-dichtheid, ondanks een expliciete meetkop. De native meettabelverwerking behoudt zulke segmenten; zie [structured_table.py](../src/tekstherkenning_ark/document/structured_table.py#L312).
- **HEG0201:** de corpuscontrole telt bevestigde koploze tabelvervolgen mee. Dit betreft de onafhankelijke broncontrole en verklaart de KZG1002-celafwijking niet.

## Huidige status

De standaard regressieset slaagde eerder met 249 geslaagde tests en 12 overgeslagen optionele corpusgevallen. De geïsoleerde KZG1002-proef slaagde ook. De gecombineerde corpusafwijking blijft open; beschouw de volledige corpuscontrole daarom niet als groen.
