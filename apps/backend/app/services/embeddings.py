from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from app.models.schemas import Product

_ef = ONNXMiniLM_L6_V2()


def _generate(texts: list[str]) -> list[list[float]]:
    return [[float(v) for v in e] for e in _ef(texts)]


async def embed_products(products: list[Product], db) -> None:
    if not products:
        return
    seen = set()
    unique = []
    for p in products:
        key = (p.sku, p.brand_id)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    texts = [f"{p.name} {p.category} {p.brand_tier} {p.sku}" for p in unique]
    embeddings = _generate(texts)
    rows = [
        {
            "sku": p.sku,
            "brand_id": p.brand_id,
            "name": p.name,
            "category": p.category,
            "brand_tier": p.brand_tier,
            "embedding": emb,
        }
        for p, emb in zip(unique, embeddings)
    ]
    await db.table("product_embeddings").upsert(rows).execute()


async def search_similar(query: str, db, brand_id: str | None = None, top_k: int = 5) -> list[dict]:
    embedding = _generate([query])[0]
    result = await db.rpc(
        "match_products",
        {"query_embedding": embedding, "brand_id_filter": brand_id, "match_count": top_k},
    ).execute()
    return result.data or []
