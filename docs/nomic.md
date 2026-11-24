# Nomic-workflows draaien

Het model [`Nomic`](../src/tekstherkenning_ark/models/nomic.py) draait workflow **ARK WF1 – Extract duikrapport**
op een rapport dat al in het Nomic-project staat. Het downloadt alle tabellen als CSV en slaat de metadata van de
run op. Het inlezen van deze CSV's in de overige datamodellen valt buiten dit model.

## Configuratie

Zet de volgende variabelen in `.env` (zie `.env.example`):

| Variabele             | Betekenis                                              |
| --------------------- | ------------------------------------------------------ |
| `NOMIC_ENDPOINT`      | Basis-URL van het Nomic-platform, bijv. `https://<domein>.nomic.ai` |
| `NOMIC_API_KEY`       | API-key met scopes `developer:agent` en `developer:files` |
| `NOMIC_PROJECT_ID`    | ID van het Nomic-project                               |
| `NOMIC_EXTRACT_WF_ID` | ID van WF1 (extractie duikrapport)                     |
| `NOMIC_ANALYSE_WF_ID` | ID van WF2 (nog niet gebruikt)                         |

## Gebruik

```python
import asyncio

from tekstherkenning_ark.models import Nomic

nomic = asyncio.run(Nomic.from_parsed_pdf("HEG0801_Houtmonstername&VisueleInspectie_V1.1_20220311.pdf"))
print(nomic.csv_paths, nomic.total_cost_usd, nomic.platform_link)
```

- De bestandsnaam moet **exact** (inclusief extensie) één keer voorkomen in Nomic; anders volgt een fout.
- Een run duurt meestal enkele minuten; de standaard-timeout is 30 minuten (`timeout_s`).
- Op Windows gebruikt de standaardclient de vertrouwde systeemcertificaten voor TLS-verificatie.
- `Nomic.from_pdf` en `Nomic.from_rak_id` zijn placeholders en nog niet geïmplementeerd.

## Output

Per run wordt een map aangemaakt: `data/nomic/{YYMMDD-HHMM}-WF1-{bestandsnaam[:20]}/` met:

- één CSV per tabel-artifact, vernoemd naar de artifactnaam;
- `metadata.json` met o.a. gebruikt model, kosten en tokens per model, het gesprek (prompt en antwoord),
  workflowversie en -instructies (alleen met bewerkrechten op de workflow), tijden en een link naar de run.

Als de workflow eindigt met `failed` of `stopped`, wordt `metadata.json` wel opgeslagen en volgt een
`NomicWorkflowFailed`-fout.

Algemene namen in de Python-interface en nieuwe metadata zijn Engels, bijvoorbeeld `filename`,
`output_folder`, `messages`, `costs` en `csv_paths`. Domeintermen en de door Nomic geleverde tabelnamen
blijven Nederlands. Eerder opgeslagen metadata met Nederlandse veldnamen wordt niet gewijzigd.
