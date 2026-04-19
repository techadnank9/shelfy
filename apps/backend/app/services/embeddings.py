import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from app.models.schemas import Product

_ef = ONNXMiniLM_L6_V2()
_chroma = chromadb.Client()
_collection = _chroma.get_or_create_collection("products", embedding_function=_ef)


async def embed_products(products: list[Product]) -> None:
    if not products:
        return
    texts = [f"{p.name} {p.category} {p.brand_tier} {p.sku}" for p in products]
    _collection.upsert(
        ids=[p.sku for p in products],
        metadatas=[p.model_dump() for p in products],
        documents=texts,
    )


async def search_similar(query: str, top_k: int = 5) -> list[dict]:
    results = _collection.query(
        query_texts=[query],
        n_results=top_k,
    )
    return results["metadatas"][0] if results["metadatas"] else []
