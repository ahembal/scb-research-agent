from fastapi import FastAPI
from research_agent.agent import answer_question, select_table
from research_agent.schema import (
    QuestionRequest,
    AnswerResponse,
    TableSearchResponse,
    TableMetadataResponse,
    TableQueryRequest,
)
from research_agent.scb_metadata import search_tables, get_table_metadata
from research_agent.metadata_parser import parse_table_dimensions
from research_agent.scb_query_builder import build_scb_query
from research_agent.result_parser import map_selection_to_labels
import httpx

app = FastAPI(title="Public Data Research Agent")


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AnswerResponse)
def ask(q: QuestionRequest):
    result = answer_question(q.question)
    return {
        "question": q.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "notes": result["notes"],
        "next_action": result.get("next_action"),
    }


@app.get("/agent/select_table/{table_id}", response_model=AnswerResponse)
def agent_select_table(table_id: str):
    result = select_table(table_id)
    return {
        "question": "",
        "answer": result["answer"],
        "sources": result["sources"],
        "notes": result["notes"],
        "next_action": result.get("next_action"),
    }


@app.post("/tables/search", response_model=TableSearchResponse)
async def tables_search(q: QuestionRequest):
    result = await search_tables(q.question)
    return {
        "question": q.question,
        "tables": result.get("tables", [])
    }


@app.get("/tables/{table_id}/metadata", response_model=TableMetadataResponse)
async def table_metadata(table_id: str):
    metadata = await get_table_metadata(table_id)
    dimensions = parse_table_dimensions(metadata)

    return {
        "table_id": table_id,
        "label": metadata.get("label"),
        "dimensions": dimensions
    }


@app.post("/tables/{table_id}/query")
async def query_table(table_id: str, req: TableQueryRequest):
    data_url = f"https://statistikdatabasen.scb.se/api/v2/tables/{table_id}/data?lang=sv"
    payload = build_scb_query(req.selection)

    async with httpx.AsyncClient() as client:
        response = await client.post(data_url, json=payload)
        response.raise_for_status()
        result = response.json()

    return {
        "table_id": table_id,
        "label": result.get("label"),
        "selection": req.selection,
        "selection_labels": map_selection_to_labels(result, req.selection),
        "values": result.get("value", []),
        "dimension_labels": {
            dim_id: dim_data.get("label")
            for dim_id, dim_data in result.get("dimension", {}).items()
        },
    }
