# src/research_agent/prompts.py
"""
LLM prompt templates for each step of the assisted agent pipeline.

Design principle: prompts ask Claude to rank and explain, never to decide silently.
Every prompt produces output that is shown to the user before any action is taken.

Response language always matches the language of the user's question.
"""


def table_ranking_prompt(question: str, candidates: list[dict]) -> str:
    """
    Ask Claude to rank SCB table candidates by relevance and provide
    a one-line reason for each, so the user can make an informed choice.

    Returns a prompt expecting a JSON array of objects with id and reason.
    """
    candidates_text = "\n".join(
        f"- ID: {c['id']} | Label: {c['label']}"
        for c in candidates
    )
    return f"""You are a data analyst with expertise in Swedish public statistics.

A user has asked the following question:
"{question}"

The following SCB (Statistics Sweden) tables were found:
{candidates_text}

Your task: rank these tables by relevance to the question and provide a short
reason for each explaining why it is or is not a good match.

Rules:
- Reply with ONLY a valid JSON array, no explanation outside the JSON.
- Each item must have: "id" (string) and "reason" (string, max 15 words).
- Order by relevance, most relevant first.
- Include all candidates in the output.

Example output:
[
  {{"id": "TAB001", "reason": "Directly matches population by region and year filter"}},
  {{"id": "TAB002", "reason": "Similar but lacks regional breakdown"}}
]

JSON:"""


def dimension_suggestion_prompt(question: str, dimensions: list[dict]) -> str:
    """
    Ask Claude to suggest dimension values that best match the user's question,
    with a short reason for each suggestion.

    Returns a prompt expecting a JSON array of dimension suggestion objects.
    """
    dims_text = ""
    for dim in dimensions:
        values_text = ", ".join(
            f"{v['code']} ({v['label']})" for v in dim["values"][:40]
        )
        dims_text += f"\nDimension ID: {dim['id']} | Label: {dim['label']}\nAvailable values: {values_text}\n"

    return f"""You are a data analyst with expertise in Swedish public statistics.

A user has asked the following question:
"{question}"

The selected SCB table has these dimensions and available values:
{dims_text}

Your task: for each dimension, suggest the value codes that best answer the question,
and provide a short reason explaining your suggestion.

Rules:
- Reply with ONLY a valid JSON array, no explanation outside the JSON.
- Each item must have:
    "dimension_id": the dimension ID string
    "suggested_codes": list of value code strings
    "reason": short explanation, max 15 words
- If the question implies a total or all values, suggest the aggregate code if available.
- If the question asks about a specific region, year, or sex, suggest that specific value.
- Do not invent codes — only use codes listed above.

Example output:
[
  {{"dimension_id": "Region", "suggested_codes": ["01"], "reason": "Question asks about Stockholm county"}},
  {{"dimension_id": "Kon", "suggested_codes": ["1", "2"], "reason": "Question does not filter by sex, include both"}},
  {{"dimension_id": "Tid", "suggested_codes": ["2024"], "reason": "Question asks about 2024"}}
]

JSON:"""


def answer_generation_prompt(
    question: str,
    table_label: str,
    selection_labels: dict,
    values: list,
    dimension_labels: dict,
) -> str:
    """
    Ask Claude to generate a clear natural language answer from raw SCB data.

    The answer language must match the language of the question.
    The answer must be grounded only in the provided data — no invented facts.
    """
    data_summary = []
    for dim_id, items in selection_labels.items():
        label = dimension_labels.get(dim_id, dim_id)
        codes = ", ".join(i["label"] for i in items)
        data_summary.append(f"  {label}: {codes}")

    data_text = "\n".join(data_summary)
    values_text = ", ".join(str(v) for v in values)

    return f"""You are a research assistant that answers questions using Swedish public statistics.

The user asked:
"{question}"

Data was retrieved from the SCB table: "{table_label}"

Selected dimensions:
{data_text}

Retrieved values:
{values_text}

Your task: write a clear, concise answer to the user's question based solely on this data.

Rules:
- Respond in the same language as the question.
- Be factual and precise — use exact numbers from the data.
- Mention the source table name.
- If multiple values are returned, summarise them clearly.
- Do not use data or knowledge beyond what is provided above.
- Keep the answer to 2-4 sentences.

Answer:"""


def keyword_extraction_prompt(question: str) -> str:
    """
    Ask Claude to extract short SCB-friendly search keywords from a
    natural language question.

    The SCB search API works best with 1-3 short keywords, not full sentences.
    Returns a prompt expecting a single line of space-separated keywords.
    """
    return f"""You are helping search a statistical database.

A user asked:
"{question}"

Extract 2-4 short search keywords from this question that would find relevant
statistical tables. Focus on the topic, not the question structure.

Rules:
- Reply with ONLY the keywords on a single line, space-separated
- No punctuation, no explanation
- Use English keywords
- Examples:
    "What was the population of Sweden in 2024?" → population Sweden
    "How many females lived in Stockholm in 2023?" → population region sex
    "What is the average age in Gothenburg?" → average age region

Keywords:"""
