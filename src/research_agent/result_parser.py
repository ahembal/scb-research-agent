# src/research_agent/result_parser.py
"""
Maps dimension value codes back to human-readable labels in query results.

SCB returns numeric codes in query results (e.g. "01", "1").
This module uses the labels embedded in the result to produce a readable
summary of what was actually selected.
"""


def map_selection_to_labels(result: dict, selection: dict) -> dict:
    """
    Map dimension value codes to their human-readable labels.

    Uses the 'dimension' block in the SCB result, which contains label
    mappings for all returned dimensions.

    Input:
      result: raw SCB API response dict
      selection: {"Region": ["01"], "Kon": ["1"]}

    Output:
      {
        "Region": [{"code": "01", "label": "Stockholm county"}],
        "Kon":    [{"code": "1",  "label": "men"}]
      }
    """
    dimensions = result.get("dimension", {})
    mapped = {}

    for dim_id, codes in selection.items():
        dim = dimensions.get(dim_id, {})
        labels = dim.get("category", {}).get("label", {})

        mapped[dim_id] = [
            {
                "code": code,
                "label": labels.get(code, code)
            }
            for code in codes
        ]

    return mapped
