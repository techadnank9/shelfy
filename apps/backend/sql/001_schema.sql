-- 001_schema.sql
-- Run this in Supabase SQL editor

CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brand_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    raw_file_url TEXT,
    parsed_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand_tier TEXT NOT NULL CHECK (brand_tier IN ('hero', 'secondary', 'new')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_id, sku)
);

CREATE TABLE IF NOT EXISTS sales_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    store_format TEXT NOT NULL CHECK (store_format IN ('SMALL', 'MEDIUM', 'LARGE')),
    sku TEXT NOT NULL,
    units_sold INTEGER NOT NULL,
    period TEXT NOT NULL DEFAULT 'Q4-2024'
);

CREATE TABLE IF NOT EXISTS planograms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    store_format TEXT NOT NULL CHECK (store_format IN ('SMALL', 'MEDIUM', 'LARGE')),
    status TEXT NOT NULL DEFAULT 'draft',
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planogram_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planogram_id UUID REFERENCES planograms(id) ON DELETE CASCADE,
    shelf_index INTEGER NOT NULL,
    column_index INTEGER NOT NULL,
    sku TEXT NOT NULL,
    facings INTEGER NOT NULL DEFAULT 1,
    rationale TEXT,
    UNIQUE (planogram_id, shelf_index, column_index)
);

CREATE TABLE IF NOT EXISTS audit_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planogram_id UUID REFERENCES planograms(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    compliance_score FLOAT,
    audited_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS discrepancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID REFERENCES audit_results(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('MISSING', 'WRONG_POSITION', 'WRONG_FACINGS', 'UNEXPECTED')),
    sku TEXT NOT NULL,
    expected_position TEXT,
    detected_position TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW'))
);
