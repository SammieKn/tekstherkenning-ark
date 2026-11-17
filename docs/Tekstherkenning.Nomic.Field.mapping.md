# ARK WF1 – Field dictionary

Reference for the **ARK WF1 – Extract duikrapport** workflow. Table names, column names, keys, units and enum values here are a contract with the `tekstherkenning-ark` code: do not rename or add columns. Value conventions and the change policy are in the workflow Instructions.

## Meta columns

Present on the tables indicated (code removes them before pydantic validation):

- `bron`: citation to the table block or page region the row sits in (not an estimated row region).
    
- `pagina`: integer page number of the PDF, not the printed page number.
    
- `bron_rij`: verbatim source row, cells joined with `|`, in left-to-right order including the header unit where the cell has none.
    

## C1. `document`: 1 row, key `document`

|   |   |   |
|---|---|---|
|Column|Type / unit|Values / notes|
|raknaam|string|Rak code as in the model, e.g. `ABC1234`. From the paspoort/object table. Fall back to the cover.|
|objectnaam|string|Descriptive name (street/quay name)|
|bedrijf|enum|`Nebest`, `Wals`, `Overig`|
|rapport_type|enum|`houtmonster`, `boorweerstandsmeting`, `visuele_inspectie`, `overig`|
|template|enum|`wals`, `nebest_bwm`, `nebest_hm`, `overig`. Matches the layout guide used.|
|template_versie|enum|Nebest: `klassiek` (appendices 1–4, "Figuur" captions) or `2024` (appendices A–D, "Foto" captions). Wals and overig: `""`.|
|rapportnummer|string||
|versie|string|Version as printed **in the document**|
|rapportdatum|date||
|inspectiedatum|string|Date or `YYYY-MM-DD/YYYY-MM-DD` range|
|totale_lengte_m|number, m|Total length of the rak|
|jaar_van_aanleg_tekst|string|As printed, may list several years|
|stadsdeel|string||
|aantal_rakdelen|integer|Number of rakdelen in the report|
|secties|string|`onderdeel: p.x-y; …` (PDF page numbers)|
|opmerkingen|string|Anything notable about the document|
|bron, pagina|meta||

## C2. `rakdelen`: key `rakdeel_id`

|   |   |   |
|---|---|---|
|Column|Type / unit|Notes|
|rakdeel_id|string|See Value conventions|
|rakdeel_label_origineel|verbatim|Label as printed|
|omschrijving|verbatim|Full description text|
|bouwjaar|integer|Only if explicitly given for this rakdeel (Wals grouping, Nebest paspoort per constructie). Otherwise `""`.|
|lengte_m|number, m|Only if explicitly given for this rakdeel. Otherwise `""`.|
|paal_bereik|string|Pile range covered, e.g. `P1.1 - P1.40`|
|figuur_paginas|string|Comma-separated PDF pages with cross-sections or drawings of this rakdeel (not opened)|
|rapport_aantal_palen|integer|Count stated by the report itself|
|rapport_aantal_kespen|integer|Count stated by the report itself|
|rapport_aantal_monsters|integer|HM or BWM taken, as stated by the report|
|rapport_aantal_scheefstand|integer|From the pile damage summary (BWM reports)|
|rapport_aantal_paalbreuk|integer|idem|
|rapport_aantal_aantasting|integer|idem|
|rapport_aantal_slechte_aansluiting|integer|idem|
|bron, pagina|meta||

## C3. `palen`: key `<rakdeel_id>|<paal_nummer>`

|   |   |   |   |
|---|---|---|---|
|Column|Type / unit|Model field|Notes|
|rakdeel_id|string|(grouping)||
|paal_nummer|string|`Paal.paal_nummer`|`P<rij>.<nr>`|
|diameter_haaks|integer, **mm**|`diameter_haaks`|Wals: cm × 10|
|diameter_parallel|integer, mm|`diameter_parallel`||
|diameter_gemiddeld|integer, mm|`diameter_gemiddeld`|Only if printed. Do not compute it.|
|hoh_afstand_cm|integer, cm|`hoh_afstand_cm`|Centre-to-centre distance along the wall|
|hoh_paalnummer|string|`hoh_paalnummer`|Pile the h.o.h. is measured to|
|schoor_graden|integer, °|`schoor_graden`||
|schoor_richting|enum|`schoor_richting`|`PNV`, `PNA`, `LR`, `NM`, `NVT`, `""`|
|schoor_richting_tekst|verbatim|(extra)|When the report uses other words|
|afstand_frontwand_cm|integer, cm|`afstand_frontwand_cm`|Nebest: as printed. Wals: Min → negative, Plus → positive.|
|is_scheefstand|bool/NM/NVT|`is_scheefstand`|Damage column "scheefstand"|
|is_paalbreuk|bool/NM/NVT|`is_paalbreuk`||
|is_aantasting|bool/NM/NVT|`is_aantasting`||
|aansluiting_status|enum|`aansluiting_status`|`G`, `S`, `NM`, `""`, only when the report uses these codes|
|aansluiting_tekst|verbatim|(extra)|Wals connection condition text, or any other vocabulary|
|positionering_aansluiting_cm|string|`positionering_aansluiting_cm`|As given|
|onderzocht|bool|(extra)|Nebest "Onderzocht" column|
|hoogte_onder_nap_cm|integer, cm, **positive = below NAP**|(extra)|If the pile table gives it (Wals)|
|omtrek_cm|integer, cm|(extra)|Wals|
|hoh_dwars_cm|integer, cm|(extra)|Wals h.o.h. across. If a second h.o.h. pair does not clearly mean "across", leave `""` (it stays in `bron_rij`).|
|opmerkingen|verbatim|`opmerkingen`|Remarks column, **excluding** constructie separator text|
|bron, pagina, bron_rij|meta|||

## C4. `kespen`: key `<rakdeel_id>|<kesp_nummer>`

|   |   |   |   |
|---|---|---|---|
|Column|Type / unit|Model field|Notes|
|rakdeel_id|string|||
|kesp_nummer|string|`kesp_nummer`|`K<nr>`|
|hoogte_cm|integer, cm|`hoogte_cm`|"Afmetingen → Hoogte"|
|breedte_cm|integer, cm|`breedte_cm`|"Afmetingen → Breedte". If the size is given as "20 x 25", it is hoogte x breedte unless the header says otherwise.|
|hoek_tov_lengte_as_graden|integer, °|`hoek_tov_lengte_as_graden`||
|lengte_uitstekend_deel_cm|integer, cm|`lengte_uitstekend_deel_cm`|Relative to the front of the front wall|
|mate_inknijping_cm|integer, cm|`mate_inknijping_cm`|Relative to the original state|
|indrukking_paal_in_kesp|bool/NM/NVT|`indrukking_paal_in_kesp`|Numbers instead of Ja/Nee: copy as printed, one bulk `opmaak_afwijkend` row|
|is_opsluitklos_aanwezig|bool/NM/NVT|`is_opsluitklos_aanwezig`|"Opsluitklos/schuifhout → Aanwezig?"|
|is_opsluitklos_aangetast|bool/NM/NVT|`is_opsluitklos_aangetast`||
|is_vervormd|bool/NM/NVT|`is_vervormd`|Damage column|
|is_aangetast|bool/NM/NVT|`is_aangetast`|Damage column|
|opmerkingen|verbatim|`opmerkingen`||
|bron, pagina, bron_rij|meta|||

## C5. `houtmonsters`: key `<codering>` (fallback `<rakdeel_id>|<paal_nummer>|<houtmonster_code>`)

|   |   |   |   |
|---|---|---|---|
|Column|Type / unit|Model field|Notes|
|rakdeel_id|string|||
|codering|string|`codering`|As printed with the ID conventions applied, e.g. `ABC1234/Constructie A/P1.16/HM`|
|rak_code|string|`rak_code`||
|paal_nummer|string|`paal_nummer`||
|houtmonster_code|string|`houtmonster_code`|e.g. `HM12345`|
|diameter_paal_ter_hoogte_houtmonster_mm|integer, mm|same|Wals: cm × 10|
|hoogte_onder_nap_cm|integer, cm, **positive = below NAP**|`hoogte_onder_nap_cm`|Normalise the sign. "−144" printed as "t.o.v. NAP" means 144 below NAP → `144`. Wals: underside NAP + sample height above underside → bulk `afgeleid`.|
|hoogte_tov_onderzijde_fundering_cm|integer, cm|`hoogte_tov_onderzijde_fundering_cm`|Nebest "Hoogte t.o.v. kesp/vloer"; Wals "monster t.o.v. onderzijde"|
|is_wankant_aanwezig|bool/NM/NVT|`is_wankant_aanwezig`|From the measurement table (leading)|
|datum_monstername|date|`datum_monstername`||
|is_aangetast|bool/NM/NVT|`is_aangetast`|From the HM card **text layer** or lab result, if printed|
|stichtingjaar|integer|`stichtingjaar`|From the HM card text layer / dendro result, if given. `0` or `-` → `""`|
|kaartlabel_tekst|verbatim|(extra)|Not read in this workflow: always `""`|
|bron, pagina, bron_rij|meta|||

## C6. `boorweerstandsmetingen`: key `<codering>`

|   |   |   |   |
|---|---|---|---|
|Column|Type / unit|Model field (new `Boorweerstandsmeting`)|Notes|
|rakdeel_id|string|||
|codering|string|`codering`|e.g. `ABC1234/Constructie A/P1.1/BM` with the label conventions applied|
|rak_code|string|`rak_code`||
|paal_nummer|string|`paal_nummer`||
|bma_nummer|string|`bma_nummer`|Measurement number|
|diameter_paal_mm|integer, mm|`diameter_paal_mm`||
|hoogte_onder_nap_cm|integer, cm, positive = below NAP|`hoogte_onder_nap_cm`|Same sign rule as houtmonsters|
|hoogte_tov_onderzijde_fundering_cm|integer, cm|`hoogte_tov_onderzijde_fundering_cm`|"t.o.v. kesp/vloer"|
|datum_meting|date|`datum_meting`||
|resultaat_tekst|verbatim|`resultaat_tekst`|Any per-measurement result printed (e.g. affected zone, sound-wood depth). `""` if none.|
|bron, pagina, bron_rij|meta|||

## C7. `gebreken`: key `<rakdeel_id>|<codering>` (append `|<n>` if a codering repeats)

|   |   |   |   |
|---|---|---|---|
|Column|Type / unit|Model field|Notes|
|rakdeel_id|string|||
|codering|string|`Gebrek.codering`|Nebest as printed with ID conventions applied (`GB3`, `ABC1234/P1.12/GB`). Wals cells joined with `/`.|
|codering_origineel|verbatim|(extra)||
|omschrijving|verbatim|`Gebrek.omschrijving`|Nebest: full text, lines joined. Wals: composed as described in the Instructions.|
|figuurnummer|string|`Gebrek.figuurnummer`|From the gebreken table's figure column: `Figuur 5.3` / `Foto 12` / `""`|
|element_type|enum|(extra)|`paal`, `kesp`, `schuifhout`, `vloer`, `metselwerk`, `onderloopsheidscherm`, `algemeen`, `overig`|
|locatie_bereik|string|(new) `Gebrek.locatie_bereik`|Wals range verbatim, e.g. `P1.10 t/m P1.26`. Empty for a single element.|
|afstand_referentie_m|number, m|(extra)|Wals "Ref. 09,45 mtr." if given in the table or caption text|
|bron, pagina|meta|||

## C8. `toestand`: key `<rakdeel_id>|<constructie_onderdeel>`

|   |   |   |   |
|---|---|---|---|
|Column|Type|Model field|Notes|
|rakdeel_id|string|||
|constructie_onderdeel|verbatim|`ToestandOnderdeel.constructie_onderdeel`|e.g. "Kespen", "Metselwerk", "Schuifhout P1.10 t/m P1.26"|
|aangetast|bool/NM/NVT|`ToestandOnderdeel.aangetast`|"Niet bereikbaar…" → `NM`|
|toelichting|verbatim|(extra)|Full cell text if it says more than Ja/Nee|
|bron, pagina, bron_rij|meta|||

## C9. `wijzigingen`: key `<tabel>|<rij_sleutel>|<veld>`

One row per change **rule**, not per affected row (see Bulk logging in the Instructions). One-off repairs get their own row.

|   |   |
|---|---|
|Column|Notes|
|tabel|Table name|
|rij_sleutel|Row key of the changed row, a key range (`<first key> - <last key>`), or `*` for all rows of the table|
|veld|Column name|
|origineel|Value as printed (verbatim), an example, or `""` if it was missing|
|nieuw|Value written, or the pattern applied|
|categorie|`reparatie`, `andere_bron`, `afgeleid`, `opmaak_afwijkend`|
|reden|One sentence with the evidence; for bulk rows include the number of rows affected|
|zekerheid|`hoog`, `middel`, `laag`|
|bron|Citation of the evidence (for `andere_bron`: the other source)|

## C10. `samenvatting`: key `<rakdeel_id>|<tabel>`

Generated by code in the validation step.

|   |   |
|---|---|
|Column|Notes|
|rakdeel_id|`""` for document-level rows|
|tabel|Table name|
|rijen_gevonden|integer|
|rijen_verwacht|integer or `""`|
|bron_verwacht|Where the expected number comes from, e.g. "tabel 4.1 p.8"|
|aantal_wijzigingen|integer: `wijzigingen` rows for this table and rakdeel|
|ontbrekende_items|e.g. `P1.17, P1.18`|
|status|`ok`, `afwijking`, `niet_te_controleren`|
|toelichting|Short template sentences; free text only for `afwijking`|