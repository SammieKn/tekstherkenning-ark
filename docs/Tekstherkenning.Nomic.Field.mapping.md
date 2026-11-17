# ARK WF1 – Field dictionary

Output specification for the **ARK WF1 – Extract duikrapport** workflow. Create an Excel workbook with the
sheet names, column names, column order, values and relationships described below.

## Workbook structure

Create these sheets in this order:

1. `document`
2. `rakken`
3. `rakdelen`
4. `bovenbouw`
5. `onderbouw`
6. `houtmonsters` (optional)
7. `palen`
8. `kespen`
9. `boorweerstandsmetingen` (optional)
10. `toestandsbepalingen`
11. `onverwachte_resultaten`
12. `gebreken`
13. One `gebreken_<type>` sheet for each defect type present

Include `document` and the non-optional sheets even when they have no rows; an empty sheet has no column headers.
Include `houtmonsters` and `boorweerstandsmetingen` only when the corresponding table is present in the report;
otherwise omit that sheet. Only include a defect-type sheet when at least one row of that type is present.
Sheet names have a maximum length of 30 characters. Put column headers in the first row and do not add an
index column.

Rows follow the order of the reports and items within them. Do not sort, deduplicate, or add identifiers.
`rak_id` refers to `rakken.raknaam`; `rakdeel_id` is the construction label. The combination of these values
identifies a rakdeel within a rak. Keys in the section headings refer only to columns in that section's table.

### Values and columns

- Column origin is `PDF` by default: read or extract the value directly from the report. Notes marked
  `[Linked]` values connect rows or identify their location in the workbook; `[Classified]` values are categories assigned from report content;
- Use the listed column order. For `gebreken`, include the union of defect fields in first-appearance order.
  Leave cells empty for fields that do not apply to a row.
- A column with no scalar values in any row is omitted. Do not expand lists or nested records into columns.
- If a value is not found in the report, leave its cell empty. Do not guess, infer, or insert a placeholder.
  Fill derived values only when their calculation is specified and the required inputs are available.
  Preserve `0` and `False` when they are actual values.
- Replace newlines in text with spaces and remove characters that cannot be stored in an Excel cell.
- Use the exact enum cell text shown in this document, not a shortened label.

|Value|Excel cell text|
|---|---|
|Upper-structure material `Metselwerk`|`MateriaalBovenbouw.METSELWERK`|
|Upper-structure material `Basalt`|`MateriaalBovenbouw.BASALT`|
|Upper-structure material `Beton+Metselwerk`|`MateriaalBovenbouw.BETON_METSELWERK`|
|Upper-structure material `Beton+Basalt`|`MateriaalBovenbouw.BETON_BASALT`|
|Upper-structure material `Beton`|`MateriaalBovenbouw.BETON`|
|Lower-structure materials `Hout`, `Staal`, `Beton`|`MateriaalOnderbouw.HOUT`, `MateriaalOnderbouw.STAAL`, `MateriaalOnderbouw.BETON`|
|Foundation materials `Hout`, `Staal`, `Beton`|`MateriaalFundering.HOUT`, `MateriaalFundering.STAAL`, `MateriaalFundering.BETON`|
|Batter direction `PNV`, `PNA`, `LR`|`SchoorStand.POSITIEF`, `SchoorStand.NEGATIEF`, `SchoorStand.NEUTRAAL`|
|Connection status `G`, `S`, `NM`|`AansluitingStatus.GOED`, `AansluitingStatus.SLECHT`, `AansluitingStatus.NIET_MEETBAAR`|
|Explicitly stated status `NM` or `NVT`|`NietBeschikbaar.NIET_MEETBAAR` or `NietBeschikbaar.NIET_VAN_TOEPASSING`|

Only use `NM` or `NVT` when that status is stated in the report or is explicitly defined for the field.
For `toestandsbepalingen.aangetast`, write those statuses as `NM` or `NVT`; leave unreported values empty.
Write booleans as Excel booleans.

## C1. `document`: 1 row, key `<raknaam>`

One row per report.

|Column|Type / unit|Values / notes|
|---|---|---|
|raknaam|string|Rak code, e.g. `ABC1234`|
|objectnaam|string|Descriptive name, such as a street or quay name|
|bedrijf|enum|`Nebest`, `Wals`, `Overig`|
|rapport_type|enum|`houtmonster`, `boorweerstandsmeting`, `visuele_inspectie`, `overig`; [Classified] from report contents|
|template|enum|`wals`, `nebest_bwm`, `nebest_hm`, `overig`; [Classified] from report layout|
|template_versie|enum|Nebest: `klassiek` or `2024`; Wals and overig: `""`; [Classified] from report layout|
|rapportnummer|string|Report number, if present|
|versie|string|Version as printed in the report|
|rapportdatum|date|Report date|
|inspectiedatum|string|Date or `YYYY-MM-DD/YYYY-MM-DD` range|
|totale_lengte_m|number, m|Total length of the rak|
|jaar_van_aanleg_tekst|string|As printed; may list several years|
|stadsdeel|string|District|
|aantal_rakdelen|integer|Number of rakdelen in the report; [Computed] by counting the rakdelen|
|secties|string|`onderdeel: p.x-y; …` using PDF page numbers; [Computed] summary of report sections|
|opmerkingen|string|Notable information about the report|
|bron|string|Citation to the report location|
|pagina|integer|PDF page number, not printed page number|

## C2. `rakken`: 1 row per rak, key `<raknaam>`

One row per rak.

|Column|Type / unit|Values / notes|
|---|---|---|
|opmerkingen|string|Remarks about the rak|
|raknaam|string|Rak code; referenced as `rak_id` in the other sheets|
|totale_lengte_m|number, m / empty|Total length of the rak, if stated|
|aantal_rakdelen|integer|Number of rakdelen in the rak|

## C3. `rakdelen`: key `<rak_id>|<rakdeel_id>`

One row per rakdeel.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Reference to `rakken.raknaam`; [Linked]|
|opmerkingen|string|Remarks about the rakdeel|
|rakdeel_id|string|Construction label, e.g. `Constructie A`|
|omschrijving|string|Full construction description|
|lengte_m_omschrijving|number, m / empty|Length stated in the description|
|bouwjaar|integer / empty|Construction year, if available|


## C4. `bovenbouw`: key `<rak_id>|<rakdeel_id>`

One row per rakdeel.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference; [Linked]|
|opmerkingen|string|Remarks about the upper structure|
|materiaal|enum / empty|Upper-structure material; use the exact enum cell text above|
|bovenkant_deksteen_cm_tov_nap|number, cm / empty|Top of coping relative to NAP|

Associate a crack with a `Scheefstand` or `BuikInWand` when their codings match or the crack's numeric
distance falls within the defect's start and end distances.

## C5. `onderbouw`: key `<rak_id>|<rakdeel_id>`

One row per rakdeel.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference; [Linked]|
|opmerkingen|string|Remarks about the lower structure|
|vloer|empty, conditional|Include as an empty column only when a rakdeel has no floor; do not place floor details here; [Linked]|
|onderloopsheidscherm|empty, conditional|Include as an empty column only when a rakdeel has no underseepage screen; do not place its details here; [Linked]|
|materiaal|enum / empty|Lower-structure material|
|materiaal_fundering|enum / empty|Foundation material|

The `vloer` and `onderloopsheidscherm` columns contain no nested details. Include each only if it is empty for
at least one row; omit it if every row has that component. Leave percentages empty when their denominator is zero.

## C6. `houtmonsters` (optional): key `<rak_id>|<codering>`

Include this sheet only if the report contains a houtmonster table. One row per houtmonster. Use `unassigned`
for `rakdeel_id` when the houtmonster is not assigned to a rakdeel.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference or `unassigned`; [Linked]|
|opmerkingen|string|Remarks about the houtmonster|
|codering|string|Houtmonster coding as printed|
|rak_code|string|Rak code associated with the houtmonster|
|paal_nummer|string|Pile number|
|houtmonster_code|string|e.g. `HM12345`|
|diameter_paal_ter_hoogte_houtmonster_mm|integer, mm / empty|Pile diameter at sample height|
|hoogte_onder_nap_cm|integer, cm / empty|Height below NAP; use the stated value and sign|
|hoogte_tov_onderzijde_fundering_cm|integer, cm / empty|Height relative to the underside of the foundation|
|is_wankant_aanwezig|bool / empty|Whether waney edge is present|
|datum_monstername|string / empty|Date as printed|
|is_aangetast|bool / empty|Whether the houtmonster is affected, if stated|
|stichtingjaar|integer / empty|Foundation year, if stated|

## C7. `palen`: key `<rak_id>|<rakdeel_id>|<paal_nummer>`

One row per pile assigned to a rakdeel.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference; [Linked]|
|opmerkingen|string|Remarks about the pile|
|paal_nummer|string|Pile ID in the form `P<x>.<y>`|
|diameter_haaks|integer, mm / empty|Diameter perpendicular to the wall|
|diameter_parallel|integer, mm / empty|Diameter parallel to the wall|
|diameter_gemiddeld|integer, mm / empty|Average diameter, if stated|
|hoh_afstand_cm|integer, cm / empty|Centre-to-centre distance|
|hoh_paalnummer|string|Pile to which the centre-to-centre distance is measured|
|schoor_graden|integer, ° / empty|Batter angle|
|schoor_richting|enum / empty|Direction: `PNV`, `PNA`, or `LR`; use the exact enum cell text above|
|afstand_frontwand_cm|integer, cm / empty|Distance to the front wall|
|is_scheefstand|bool / empty|Whether scheefstand is present|
|is_paalbreuk|bool / empty|Whether paalbreuk is present|
|is_aantasting|bool / empty|Whether aantasting is present|
|aansluiting_status|enum / empty|Connection condition: `G`, `S`, or `NM`; use the exact enum cell text above|
|positionering_aansluiting_cm|string / empty|Connection position as stated|

For `afstand_van_startrak_cm`, begin each rakdeel at its length in centimetres. Advance the distance by
`hoh_afstand_cm` along the first pile row, following the pile order in the table. Leave it empty when the
rakdeel length or the required distance is not found.

## C8. `kespen`: key `<rak_id>|<rakdeel_id>|<kesp_nummer>`

One row per kesp. Use `unassigned` for `rakdeel_id` when a kesp is not assigned to a rakdeel.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference or `unassigned`; [Linked]|
|opmerkingen|string|Remarks about the kesp|
|kesp_nummer|string|Kesp ID in the form `K<nr>`|
|hoogte_cm|integer, cm / empty|Kesp height|
|breedte_cm|integer, cm / empty|Kesp width|
|hoek_tov_lengte_as_graden|integer, ° / empty|Angle to the wall's length axis|
|lengte_uitstekend_deel_cm|integer, cm / empty|Length of the projecting part|
|mate_inknijping_cm|integer, cm / empty|Amount of indentation|
|indrukking_paal_in_kesp|bool / empty|Whether a pile has indented the kesp|
|is_opsluitklos_aanwezig|bool / empty|Whether an opsluitklos is present|
|is_opsluitklos_aangetast|bool / empty|Whether the opsluitklos is affected|
|is_vervormd|bool / empty|Whether the kesp is deformed|
|is_aangetast|bool / empty|Whether the kesp is affected|

## C9. `boorweerstandsmetingen` (optional): key `<rakdeel_id>|<codering>`

Include this sheet only if the report contains a boorweerstandsmeting table. One row per measurement.

|Column|Type / unit|Values / notes|
|---|---|---|
|rakdeel_id|string|Rakdeel reference; [Linked]|
|codering|string|Measurement coding, e.g. `ABC1234/Constructie A/P1.1/BM`|
|rak_code|string|Rak code|
|paal_nummer|string|Pile number|
|bma_nummer|string|Measurement number|
|diameter_paal_mm|integer, mm|Pile diameter|
|hoogte_onder_nap_cm|integer, cm|Height below NAP; positive means below NAP|
|hoogte_tov_onderzijde_fundering_cm|integer, cm|Height relative to underside of foundation|
|datum_meting|date|Measurement date|
|resultaat_tekst|string|Measurement result, such as affected zone or sound-wood depth; empty if none|
|bron|string|Citation to the report location|
|pagina|integer|PDF page number, not printed page number|
|bron_rij|string|Source row, with cells joined by `|`|

## C10. `toestandsbepalingen`: key `<rak_id>|<rakdeel_id>|<model_pad>|<onderdeel>`

One row per condition item.

|Column|Type|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference; [Linked]|
|model_pad|string|Path to the item, e.g. `bovenbouw`, `onderbouw`, `onderbouw/vloer`, or `rakdeel`; [Linked]|
|onderdeel|string|Name of the construction component|
|aangetast|bool / text / empty|Boolean, `NM`, `NVT`, empty|

## C11. `gebreken` : key `<rak_id>|<rakdeel_id>|<model_pad>|<codering>|<gebrek_type>`

One row per defect. Keep duplicate codings when more than one defect type is present; do not add a row number
to the coding.
The first four columns are `rak_id`, `rakdeel_id`, `model_pad`, and `gebrek_type`. Follow these with the
applicable defect fields below. The sheet's columns are the union of fields present in its rows, in the order
they first occur. Leave fields that do not apply to a row empty.

|Column|Type / unit|Values / notes|
|---|---|---|
|rak_id|string|Rak reference; [Linked]|
|rakdeel_id|string|Rakdeel reference; [Linked]|
|model_pad|string|Path to the item with the defect; [Linked]|
|gebrek_type|string|Defect type, as listed below; [Classified]|
|codering|string|Defect coding|
|omschrijving|string|Full defect description|
|figuurnummer|string / empty|Figure or photo reference|
|Type-specific fields|varies|Use the fields and order specified for the defect type|
