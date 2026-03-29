# SCB Data & API

## What is SCB?

Statistics Sweden (SCB) is the Swedish government agency responsible for
producing official statistics. Their data covers population, economy, labour,
environment, and more.

All data is publicly available and free to use.

Official site: https://www.scb.se/en/
Statistical database: https://www.statistikdatabasen.scb.se/

## The API: PxWebApi v2

SCB provides a modern REST API called PxWebApi v2 that gives programmatic
access to the same tables available on their website.

Documentation: https://www.scb.se/en/services/open-data-api/api-for-the-statistical-database/

Base URL used in this project:
```
https://statistikdatabasen.scb.se/api/v2
```

## How the database is organised

The SCB database is a hierarchy:
```
Subject area
  └── Dataset
        └── Table
              └── Variables (dimensions)
                    └── Values
```

Example for population data:
```
Population and society
  └── Population
        └── Population by age and sex. Year 1860-2024
              ├── Region      → 00 (whole country), 01 (Stockholm), ...
              ├── Age         → 0, 1, 2, ... 100+, tot (total)
              ├── Sex         → 1 (men), 2 (women), 1+2 (total)
              └── Year        → 1860, 1861, ... 2024
```

## How a query works

Every query to SCB follows the same pattern:

1. **Search** for tables matching your topic
2. **Select** a table
3. **Fetch metadata** to see what dimensions and values exist
4. **Select values** for each dimension
5. **POST** the selection to the data endpoint
6. **Receive** the filtered dataset

Example dimension selection payload:
```json
{
  "Selection": [
    { "VariableCode": "Region", "ValueCodes": ["00"] },
    { "VariableCode": "Kon",    "ValueCodes": ["1", "2"] },
    { "VariableCode": "Tid",    "ValueCodes": ["2024"] }
  ]
}
```

## API limits

Be aware of these operational limits when building agents:

| Limit | Value |
|---|---|
| Max cells per extraction | 150,000 |
| Rate limit | ~30 requests per 10 seconds per IP |

This is why the agent always selects specific values rather than requesting
entire tables at once.

## Tables used in this project

This project focuses on population statistics as a well-structured starting point.

| Table topic | Dimensions |
|---|---|
| Population by age and sex | Region, Age, Sex, Year |
| Population per region | Region, Age, Sex, Year |
| Population per month | Region, Age, Sex, Month |
| Average age by region and sex | Region, Sex, Year |

## Why SCB works well for this project

- Data is public and free
- API is stable and well-documented
- Tables are well-structured with consistent dimension patterns
- Results are reliable and authoritative
- No authentication required

## Known limitations

### SCB search and Swedish characters

The SCB table search API matches on table titles and topics.
It does not reliably match on specific dimension values like region names.

In particular, Swedish place names with special characters (å, ä, ö) will
return zero results if typed in ASCII:

- `Ostergotland` → 0 results
- `Östergötland` → may work but users often type ASCII

**How this agent handles it:** the keyword extraction step intentionally
strips all specific place names, region names, and years from the search
query. These are handled later in the dimension selection step where Claude
picks the correct dimension value codes from the table metadata.

This means the search always uses generic topic keywords like
`population region` rather than `population Östergötland 2024`.
