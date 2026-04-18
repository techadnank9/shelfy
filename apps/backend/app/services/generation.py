import json
import anthropic
from app.config import settings
from app.models.schemas import Planogram, StoreFormat
from app.repositories.planogram import SupabasePlanogramRepository
from app.repositories.brand import SupabaseBrandRepository, SupabaseSalesRepository
from app.services.embeddings import search_similar

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# Injected at app startup via main.py lifespan
planogram_repo: SupabasePlanogramRepository = None  # type: ignore
brand_repo: SupabaseBrandRepository = None           # type: ignore
sales_repo: SupabaseSalesRepository = None           # type: ignore

TOOLS = [
    {
        "name": "get_brand_guidelines",
        "description": "Get parsed brand guidelines including placement rules and brand hierarchy.",
        "input_schema": {
            "type": "object",
            "properties": {"brand_id": {"type": "string"}},
            "required": ["brand_id"],
        },
    },
    {
        "name": "get_product_catalog",
        "description": "Get all products for a brand in a given category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "category": {"type": "string"},
            },
            "required": ["brand_id", "category"],
        },
    },
    {
        "name": "get_store_sales_data",
        "description": "Get sales data for all products in a specific store format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "store_format": {"type": "string", "enum": ["SMALL", "MEDIUM", "LARGE"]},
            },
            "required": ["brand_id", "store_format"],
        },
    },
    {
        "name": "search_similar_products",
        "description": "Semantic search over product catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "submit_planogram",
        "description": "Submit the final generated planogram positions. Call this last.",
        "input_schema": {
            "type": "object",
            "properties": {
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "shelf_index": {"type": "integer"},
                            "column_index": {"type": "integer"},
                            "sku": {"type": "string"},
                            "facings": {"type": "integer"},
                            "rationale": {"type": "string"},
                        },
                        "required": ["shelf_index", "column_index", "sku", "facings", "rationale"],
                    },
                }
            },
            "required": ["positions"],
        },
    },
]

SYSTEM = """You are an expert visual merchandising AI for beauty retail brands.
Generate a store-specific planogram based on brand guidelines and sales performance data.

Rules:
- Eye level (shelf 1) = highest-selling hero products
- Shelf 0 (top) = new products and secondary items
- Shelf 2 (bottom) = bulkier secondary items
- Allocate more facings to higher-selling products
- Always call get_brand_guidelines, get_product_catalog, and get_store_sales_data before generating
- Call submit_planogram last with all shelf positions"""


async def _execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_brand_guidelines":
        result = await brand_repo.get_guidelines(tool_input["brand_id"])
        return json.dumps(result)

    if tool_name == "get_product_catalog":
        products = await brand_repo.get_product_catalog(
            tool_input["brand_id"], tool_input["category"]
        )
        return json.dumps([p.model_dump() for p in products])

    if tool_name == "get_store_sales_data":
        sales = await sales_repo.get_store_sales(
            tool_input["brand_id"], tool_input["store_format"]
        )
        return json.dumps([s.model_dump() for s in sales])

    if tool_name == "search_similar_products":
        results = await search_similar(tool_input["query"], tool_input.get("top_k", 5))
        return json.dumps(results)

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


async def run_generation_agent(brand_id: str, store_format: str) -> list[dict]:
    messages = [{
        "role": "user",
        "content": (
            f"Generate a planogram for brand_id={brand_id}, "
            f"store_format={store_format}. "
            "Use the available tools to gather all data, then call submit_planogram."
        ),
    }]

    while True:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        submitted_positions = None

        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "submit_planogram":
                submitted_positions = block.input["positions"]
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"status": "saved"}),
                })
            else:
                result = await _execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if submitted_positions is not None:
            return submitted_positions

        messages.append({"role": "user", "content": tool_results})

    return []


async def generate_planogram(brand_id: str, store_format: str) -> Planogram:
    positions = await run_generation_agent(brand_id, store_format)
    return await planogram_repo.save(brand_id, store_format, positions)
