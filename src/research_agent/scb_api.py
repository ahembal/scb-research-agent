import httpx
from research_agent.config import SCB_API_BASE_URL

async def fetch_table(table_path: str):
    url = f"{SCB_API_BASE_URL}/{table_path}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()
