# Lokale PDF-structuurextractie

`SmartDocument.from_pdf()` gebruikt PyMuPDF 2.1 en de geintegreerde `Document.to_json()`-API.
Het afzonderlijke `pymupdf4llm`-compatibiliteitspakket en de Azure Document Intelligence SDK zijn niet nodig.
Azure OpenAI blijft uitsluitend verantwoordelijk voor de latere domeinclassificatie.

## Invoer en OCR

- De PDF moet bestaande selecteerbare tekst bevatten. Een bestaande OCR-tekstlaag telt als bestaande tekst.
- `use_ocr=False` is expliciet ingesteld; ook pixeltekst binnen afbeeldingen wordt nooit herkend.
- Versleutelde, beschadigde PDF's en documenten zonder native tekst geven een duidelijke `ValueError`.
- Beeldpagina's binnen een document met native tekst blijven zonder nieuwe OCR.
- Layoutanalyse en figuurrendering kosten nog steeds rekenwerk. Er wordt geen vaste snelheidswinst beloofd.

## Extractieroute

1. Lees bronbytes en bereken de SHA256-vingerafdruk.
2. Gebruik een geldige bron-/configuratiegebonden JSON-cache indien beschikbaar.
3. Normaliseer paginarotatie en kopieer native tekstregels en `Page.find_tables(use_layout=False)`-cellen.
4. Gebruik JSON-layout voor elementvolgorde, koprollen en volledige gedetecteerde figuurgebieden.
5. Koppel paragrafen, tabellen en PNG's aan secties via een canonieke elementregistratie.

Native tabellen worden voor de layoutanalyse gekopieerd: layoutnabewerking kan anders meetwaarden of
native extractie-instellingen beinvloeden. Celtekst, lege cellen, rij-/kolomspans en brongebieden blijven bewaard.
De domeinprojectie combineert compatible native meetsegmenten; onverenigbare koppen geven een fout in plaats
van stil rijen weg te laten. Historische referentiefixtures zijn expliciet gemarkeerd en gebruiken hun oude celindeling.

## Structuur en Figuren

`sections` blijft een vlakke lijst met expliciete `id`, `kopniveau` en `ouder_id`.
`element_ids` bewaart de gemengde sectievolgorde; `elementen` bevat iedere paragraaf, tabel of afbeelding eenmaal.
`BronLocatie` bevat het op een gebaseerde paginanummer en de bbox in punten vanaf linksboven.
Nummering, bijlagen en exact gematchte PDF-bookmarks sturen de hierarchie.

PNG's bevatten het volledige gedetecteerde figuurgebied, inclusief raster-, vector- en samengestelde inhoud,
op 150 DPI. Selecteerbare figuurlabels blijven daarnaast paragrafen. Een eenduidig nabij bijschrift wordt via
`bijschrift_id` gekoppeld; er wordt geen pixeltekst naar nieuwe paragrafen omgezet.

Beperkingen: figuurgebieden en ongenummerde koprollen zijn afhankelijk van PyMuPDF-layoutdetectie.
Een ongenummerde kop zonder exacte bookmark krijgt voorlopig niveau 1; ambigue bijschriften blijven ongekoppeld.

## Verplaatsbare Export

```python
from pathlib import Path
from tekstherkenning_ark.document.smart_document import SmartDocument

document = SmartDocument.from_pdf(Path("data/duikrapporten/rapport.pdf"))
manifest = document.exporteer_structuur(Path("data/structuur_exports/rapport"))
```

De exportmap bevat `structuur.json` en `afbeeldingen/*.png` met relatieve paden. Verplaats de hele map.
De JSON bewaart bronhash, extractieconfiguratie, pagina-afmetingen, bookmarks, sectierelaties, elementvolgorde,
ruwe cellen en figuurverwijzingen. Iedere PNG heeft een volledige SHA256-inhoudshash.
Het manifest wordt pas na assetcontrole gepubliceerd. De bestaande Rak-JSON- en Excel-export veranderen niet.

## Caches

Documentcaches staan onder `data/.cache/pymupdf_extractie/<documentvingerafdruk>/`.
De sleutel omvat broninhoud, schema- en extractorversie, PyMuPDF-versie, OCR-/tekstopties, native tabelmodus en DPI.
De gebruikte configuratie blijft in het document bewaard, onafhankelijk van latere instellingen.
Gelijke inhoud onder een andere naam kan dezelfde extractiecache gebruiken; het resultaat heeft de huidige bronnaam.

Een cachehit controleert schema, identiteit, elementverwijzingen, hierarchie, bundelrelatieve paden en PNG-inhoud.
Bij ontbrekende/beschadigde assets volgt lokale herextractie. Cachehits openen geen PDF en renderen niet opnieuw.
`SmartDocument.from_pdf(..., use_cache=False)` omzeilt lezen, maar schrijft wel een nieuw gecontroleerd resultaat.
Tijdelijke renderbestanden worden opgeruimd; bestaande oude Azure-caches blijven onaangeroerd en worden genegeerd.
Nieuwe Rak-caches gebruiken de documentvingerafdruk. CLI `--no-cache` omzeilt alleen de Rak-cache, niet document-/LLM-caches.

## Omgeving en Licentie

Gebruik Python 3.13 en uv. De lockfile legt de geteste PyMuPDF-release vast.
Voor alleen PDF-extractie zijn geen Azure-credentials of netwerkverbinding nodig.
PyMuPDF wordt aangeboden onder AGPL of commerciele licentie; deze keuze is voor dit project goedgekeurd.
Controleer de voorwaarden bij distributie. De repositorylicentie wordt hierdoor niet gewijzigd.