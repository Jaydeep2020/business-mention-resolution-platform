"""Sample prompts and texts for quick testing of Mention Extraction and Catalog Q&A."""

SAMPLE_EXTRACTION_TEXTS = [
    {
        "title": "Bakery & Cafe Review",
        "text": "During our stay in Savannah, we visited Magnolia Lantern Bakery at 308 Abercorn Street, Savannah, Georgia. The pastries were fantastic.",
        "source_id": "rev_sav_01",
    },
    {
        "title": "Bookstore Visit",
        "text": "I bought a few books from Willow Creek Books at 126 North 3rd Street in Boise, Idaho. The staff was extremely helpful.",
        "source_id": "rev_boise_42",
    },
    {
        "title": "Pizza Restaurant Review",
        "text": "We ordered from Joe's Pizza near downtown Chicago and it arrived quickly. The crust was crispy and delicious.",
        "source_id": "rev_chi_99",
    },
    {
        "title": "Multi-Business Day Out",
        "text": "Started our morning having coffee at 101 Deli in Santa Barbara, then stopped by 4 Eggs & Pizza for lunch before heading home.",
        "source_id": "rev_sb_55",
    },
]

SAMPLE_QA_QUESTIONS = [
    "Show me restaurants in Santa Barbara",
    "List top businesses in Philadelphia",
    "How many verified businesses are in the catalog?",
    "Find coffee shops or bakeries in Boise",
    "Tell me about 101 Deli in Santa Barbara",
]
