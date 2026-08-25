from functools import lru_cache

from gliner import GLiNER


# ==========================================================
# GLINER CONFIGURATION
# ==========================================================

GLINER_MODEL_NAME = "gliner-community/gliner_small-v2.5"


# ==========================================================
# ENTITY TYPES GLINER SHOULD DETECT
# ==========================================================

# Tell GLiNER about both businesses and contextual
# entities so that locations are less likely to be
# incorrectly classified as businesses.
ENTITY_LABELS = [
    "business",
    "restaurant",
    "store",
    "hotel",
    "cafe",

    # Context entities
    "city",
    "state",
    "address",
]


# Only these labels should become Mention rows.
BUSINESS_LABELS = {
    "business",
    "restaurant",
    "store",
    "hotel",
    "cafe",
}


GLINER_THRESHOLD = 0.45


# ==========================================================
# LOAD GLINER MODEL
# ==========================================================

@lru_cache(maxsize=1)
def get_nlp() -> GLiNER:

    try:

        model = GLiNER.from_pretrained(
            GLINER_MODEL_NAME
        )

    except Exception as exc:

        raise RuntimeError(
            (
                "Could not load GLiNER model "
                f"'{GLINER_MODEL_NAME}'. "
                f"Original error: {exc}"
            )
        ) from exc

    return model


# ==========================================================
# EXTRACT BUSINESS ENTITIES
# ==========================================================

def extract_business_entities(
    text: str,
) -> list[dict]:

    if not text or not text.strip():
        return []

    model = get_nlp()

    # ------------------------------------------------------
    # GLiNER prediction
    # ------------------------------------------------------

    try:

        entities = model.predict_entities(
            text,
            ENTITY_LABELS,
            threshold=GLINER_THRESHOLD,
        )

    except Exception as exc:

        raise RuntimeError(
            (
                "GLiNER failed while extracting "
                f"business mentions: {exc}"
            )
        ) from exc

    # ------------------------------------------------------
    # Debug: show everything GLiNER detected
    # ------------------------------------------------------

    print(
        [
            (
                entity["text"],
                entity["label"],
                round(
                    float(entity["score"]),
                    3,
                ),
            )
            for entity in entities
        ]
    )

    # ------------------------------------------------------
    # Keep only business entities
    # ------------------------------------------------------

    extracted_entities = []

    seen_entities = set()

    for entity in entities:

        entity_label = (
            entity["label"]
            .strip()
            .lower()
        )

        # Important:
        # City/state/address can be detected by GLiNER,
        # but should NOT become Mention rows.
        if entity_label not in BUSINESS_LABELS:
            continue

        raw_text = entity["text"]

        cleaned_text = raw_text.strip()

        if not cleaned_text:
            continue

        if len(cleaned_text) > 255:
            continue

        start_char = int(
            entity["start"]
        )

        end_char = int(
            entity["end"]
        )

        normalized_text = (
            " ".join(
                cleaned_text
                .lower()
                .split()
            )
        )

        duplicate_key = (
            normalized_text,
            start_char,
            end_char,
        )

        if duplicate_key in seen_entities:
            continue

        seen_entities.add(
            duplicate_key
        )

        extracted_entities.append(
            {
                "text": cleaned_text,
                "label": "BUSINESS",
                "start_char": start_char,
                "end_char": end_char,
            }
        )

    extracted_entities.sort(
        key=lambda item: item["start_char"]
    )

    return extracted_entities