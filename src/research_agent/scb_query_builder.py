# src/research_agent/scb_query_builder.py
"""
Builds SCB API query payloads from a dimension selection dict.

The SCB PxWebApi v2 expects a specific JSON structure for data queries.
This module handles that translation so the rest of the code can work
with plain Python dicts.
"""


def build_scb_query(selection: dict[str, list[str]]) -> dict:
    """
    Convert a selection dict into the SCB API query payload format.

    Input:
      {"Region": ["01"], "Kon": ["1", "2"], "Tid": ["2024"]}

    Output:
      {
        "Selection": [
          {"VariableCode": "Region", "ValueCodes": ["01"]},
          {"VariableCode": "Kon",    "ValueCodes": ["1", "2"]},
          {"VariableCode": "Tid",    "ValueCodes": ["2024"]}
        ]
      }
    """
    return {
        "Selection": [
            {
                "VariableCode": dimension,
                "ValueCodes": values
            }
            for dimension, values in selection.items()
        ]
    }
