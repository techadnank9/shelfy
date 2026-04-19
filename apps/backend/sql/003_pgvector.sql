-- Enable pgvector
create extension if not exists vector;

-- Product embeddings table
create table if not exists product_embeddings (
  sku          text primary key,
  brand_id     text not null,
  name         text,
  category     text,
  brand_tier   text,
  embedding    vector(384)
);

create index if not exists product_embeddings_embedding_idx
  on product_embeddings using ivfflat (embedding vector_cosine_ops)
  with (lists = 10);

-- Match function for similarity search
create or replace function match_products(
  query_embedding vector(384),
  brand_id_filter text default null,
  match_count     int default 5
)
returns table (
  sku        text,
  brand_id   text,
  name       text,
  category   text,
  brand_tier text,
  similarity float
)
language sql stable
as $$
  select
    sku, brand_id, name, category, brand_tier,
    1 - (embedding <=> query_embedding) as similarity
  from product_embeddings
  where brand_id_filter is null or brand_id = brand_id_filter
  order by embedding <=> query_embedding
  limit match_count;
$$;
