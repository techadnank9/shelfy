import chromadb
from openai import AsyncOpenAI
from app.config import settings
from app.models.schemas import Product

_chroma = chromadb.Client()
_collection = _chroma.get_or_create_collection("products")
_openai = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_products(products: list[Product]) -> None:
    if not products:
        return
    texts = [f"{p.name} {p.category} {p.brand_tier} {p.sku}" for p in products]
    response = await _openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    embeddings = [item.embedding for item in response.data]
    _collection.upsert(
        ids=[p.sku for p in products],
        embeddings=embeddings,
        metadatas=[p.model_dump() for p in products],
        documents=texts,
    )


async def search_similar(query: str, top_k: int = 5) -> list[dict]:
    response = await _openai.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
    )
    query_embedding = response.data[0].embedding
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    return results["metadatas"][0] if results["metadatas"] else []
