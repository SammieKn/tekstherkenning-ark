# Tekstherkenning ARK

## Wat doet deze tool?

Deze tool ondersteunt het ARK-proces (Amsterdamse Risicobeoordeling Kademuren) van de Gemeente Amsterdam door duikinspecties automatisch te transformeren naar gestructureerde data. Duikinspectierapporten van Nebest worden ingelezen en omgezet naar een standaard datastructuur die direct gebruikt kan worden in de [ARK-tool](https://github.com/ic144/ark-automatiseren).

De tool automatiseert het handmatige werk van het invoeren van gegevens uit duikinspectierapporten, waardoor fouten worden verminderd en tijd wordt bespaard.

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

