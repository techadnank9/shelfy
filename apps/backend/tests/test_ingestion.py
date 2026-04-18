import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ingestion import parse_planogram_pdf


@pytest.mark.asyncio
async def test_parse_planogram_pdf_returns_products():
    sample_pdf_bytes = b"%PDF-1.4 fake pdf content"

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='''{
        "brand_rules": {"eye_level": "hero products only"},
        "products": [
            {"sku": "LS-001", "name": "Vitamin C Serum", "category": "skincare",
             "brand_tier": "hero", "default_facings": 2},
            {"sku": "LS-002", "name": "Moisturizer", "category": "skincare",
             "brand_tier": "hero", "default_facings": 2}
        ]
    }''')]

    mock_pdf_page = MagicMock()
    mock_pdf_page.extract_text.return_value = "Planogram document content"
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_pdf_page]

    with patch("app.services.ingestion.anthropic_client") as mock_client, \
         patch("app.services.ingestion.embed_products", new_callable=AsyncMock), \
         patch("pdfplumber.open", return_value=mock_pdf):
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        result = await parse_planogram_pdf(sample_pdf_bytes, "b1")

    assert result["products_parsed"] == 2
    assert result["parsed_products"][0]["sku"] == "LS-001"
