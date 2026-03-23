# src/research_agent/metadata_parser.py
"""
Parses raw SCB table metadata into a clean, ordered list of dimensions.

The raw metadata from the SCB API uses a non-obvious structure where dimension
order is stored separately from dimension details. This module handles that
and returns a flat, ordered list ready for use by the agent and prompts.
"""


def parse_table_dimensions(metadata: dict) -> list[dict]:
    """
    Extract and order dimension information from raw SCB table metadata.

    Returns a list of dicts, one per dimension, in the order SCB defines them:
      {
        "id": "Region",
        "label": "Region",
        "values": [
          {"code": "00", "label": "Whole country"},
          {"code": "01", "label": "Stockholm county"},
          ...
        ]
      }
    """
    dimensions = metadata.get("dimension", {})
    ordered_ids = metadata.get("id", [])

    parsed = []

    for dim_id in ordered_ids:
        dim = dimensions.get(dim_id, {})
        category = dim.get("category", {})
        labels = category.get("label", {})

        values = [
            {"code": code, "label": label}
            for code, label in labels.items()
        ]

        parsed.append({
            "id": dim_id,
            "label": dim.get("label", dim_id),
            "values": values,
        })

    return parsed
