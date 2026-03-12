# Functionele mapping: Duikrapport naar ARK-tool

Dit document beschrijft hoe relevante gegevens uit een duikrapport (bijvoorbeeld inspectie_rapport OAW0601) worden vertaald naar de datastructuur van de ARK-tool. Het is bedoeld als naslag voor ontwikkelaars die werken aan de automatisering van deze mapping.

---

## 1. Overzicht ARK-structuur

De ARK-tool (Amsterdamse Risicobeoordeling Kademuren) werkt met een vaste datastructuur per rakdeel. Elk rakdeel bevat velden voor algemene gegevens, constructie, fundering, gebreken en meetwaarden. De mapping is opgezet zodat zoveel mogelijk velden automatisch uit het duikrapport worden gevuld.

### Projectmapstructuur (voorbeeld)
```
AMS0101/
├── A/  # rakdeel
│   ├── Algemene rakdeelgegevens
│   ├── Basisinformatie
│   ├── Omgeving
│   ├── Bomen
│   ├── Constructie/
│   │   └── Waterbodem
│   └── Beoordeling onderbouw en fundering/
│       └── Meettabel houtmonsters
├── B/
│   ├── Algemene rakdeelgegevens
│   ├── Basisinformatie
│   ├── Omgeving
│   ├── Bomen
│   ├── Constructie/
│   │   └── Waterbodem
│   └── Beoordeling onderbouw en fundering/
│       └── Meettabel houtmonsters
...
...
```
---

## 2. Mappingtabel: ARK-velden en duikrapport

| ARK-veld                        | Herkomst in duikrapport / toelichting                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------------|
| **Rakcode**                     | Kopregel, bijv. `OAW0601/P1.21/GB` (OAW0601 = rak, P1.21 = paal/stramienlijn, GB = gebrek bovenbouw)   |
| **Rakdeel**                     | Sectie-indeling in rapport, bijv. "A" of "B"                                                          |
| **Algemene rakdeelgegevens**     | Hoofdstuk 2, metadata, samenvatting (lengte, leeftijd, locatie)                                       |
| **Basisinformatie**              | Metadata, evt. uit AIP of andere bronnen                                                              |
| **Omgeving**                    | Niet uit duikrapport, handmatig invullen                                                              |
| **Bomen**                       | Niet uit duikrapport, handmatig invullen                                                              |
| **Constructie**                 | Hoofdstuk "Constructie", waterbodemgegevens uit duikrapport, evt. multibeammetingen                   |
| **Waterbodem**                  | Resultaten duikinspectie, evt. multibeam-data                                                         |
| **Beoordeling onderbouw/fundering** | Hoofdstuk 5.3.1, meetresultaten, bijlage 3 meettabel fundering                                       |
| **Meettabel houtmonsters**       | Bijlage 3, eerste vijf kolommen direct uit rapport, rest wordt berekend                               |
| **Gebreken (GB)**               | Hoofdstuk 5.3.3, tekstuele opsomming gebreken, vaak per locatie                                       |
| **Scheuren, buik, scheefstand** | Tekstueel, vaak met locatie-aanduiding (afstand vanaf begin rak)                                      |
| **Onderloopsheidsscherm**        | Opmerking over beschadiging/kieren in tekst                                                           |

---

## 3. Functionele extractie en logica

### 3.1 Rakcode en paalnummer
- **Rakcode**: Direct uit kopregel, bijvoorbeeld `OAW0601/P1.21/GB`.
- **Paalnummer/stramienlijn**: `P1.21` betekent paal 1 op stramienlijn 21.

### 3.2 Gebreken en locatie
- **Gebrek bovenbouw (GB)**: Indien alleen 'GB' genoemd, betreft het een gebrek aan de bovenbouw.
- **Locatie scheur/buik/scheefstand**: Extractie uit tekst, bijvoorbeeld "scheur op 2,2 m vanaf begin rak" of "buik tussen 2,2 en 15 m".
- **Onderloopsheidsscherm**: Indien in tekst genoemd als "beschadigd/kierend", dan boolean veld op 'ja'.

### 3.3 Meettabellen en houtmonsters
- **Meetresultaten**: Bijlage 3 bevat tabellen met paalmetingen (bijv. diameter, aantasting, locatie).
- **Automatische berekening**: Eerste vijf kolommen worden uit het rapport gehaald, overige waarden (zoals resterende diameter, percentages) worden automatisch berekend door de ARK-tool.
- **Leeftijd paal**: Wordt automatisch afgeleid uit eerdere invoervelden.

### 3.4 Validatie en afhankelijkheden
- **Validatie**: Onbekende combinaties of ontbrekende verplichte velden geven foutmeldingen.
- **Afhankelijkheden**: Sommige velden worden alleen getoond of verplicht op basis van eerdere invoer (bijv. alleen houtmonsters bij houten fundering).

---

## 4. Praktische aandachtspunten uit beheerdersoverleg

- **Minder dubbele invoervelden**: Sinds versie 3.0 zijn dubbele velden verwijderd, afhankelijkheden toegevoegd.
- **Automatische typologie**: Typologie van constructie wordt automatisch bepaald uit invoervelden; onbekende combinaties geven foutmelding.
- **Handmatige aanvulling**: Velden als omgeving en bomen zijn niet uit het duikrapport te halen en moeten handmatig worden ingevuld.
- **Interpretatieverschillen**: Verschillen in interpretatie van duikrapporten blijven mogelijk; controle door constructeur blijft vereist.
- **Iteratief werken**: Project wordt in sprints uitgevoerd, met regelmatige evaluaties en bijsturing.
- **Viktor-app**: Werkt met controllers en klassen per veld; outputvelden tonen berekende waarden.

---

## 5. Voorbeeld mapping (concreet)

### Voorbeeld uit inspectie_rapport OAW0601

- **Rakcode:** OAW0601/P1.21/GB
- **Paalnummer:** P1.21
- **Gebrek bovenbouw:** Ja (indien alleen 'GB' genoemd)
- **Scheur:** "Scheur op 2,2 m vanaf begin rak" → locatie = 2,2 m
- **Buik:** "Buik tussen 2,2 en 15 m" → range = 2,2–15 m
- **Onderloopsheidsscherm:** "Onderloopsheidsscherm beschadigd/kierend" → ja
- **Meettabel fundering:** Zie bijlage 3, kolommen direct overnemen

--- 

## 6. Niet uit duikrapport te halen (handmatig invullen)
- Omgeving
- Bomen
- Sommige basisinformatie (bijv. beheerder, documentatie uit AIP)

---

## 7. Referenties
- inspectie_rapport OAW0601: bron voor alle technische en gebreken-data
- transcriptie_startoverleg_geert.docx: toelichting op keuzes, afhankelijkheden en interpretatie
- AIP (Amsterdam Inspectie Portaal): aanvullende bron voor metadata en basisinformatie

---

## 8. Samenvatting

Deze mapping maakt het mogelijk om relevante data uit een duikrapport automatisch te vertalen naar de ARK-tool. Automatische extractie is mogelijk voor de meeste technische velden; enkele contextvelden vereisen handmatige aanvulling. Let op afhankelijkheden en validatie conform ARK-app logica. Interpretatie door een constructeur blijft noodzakelijk voor de uiteindelijke beoordeling.