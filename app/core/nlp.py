from functools import lru_cache

from gliner import GLiNER


# ==========================================================
# GLINER CONFIGURATION
# ==========================================================

GLINER_MODEL_NAME = "gliner-community/gliner_small-v2.5"


# GLiNER is zero-shot.
#
# We tell the model exactly which kinds of
# entities we want to find.
#
# Using several related labels helps it detect
# local-business mentions such as:
#
# Starbucks
# Domino's
# Hilton
# Walmart
# Tony's Pizza
#
BUSINESS_ENTITY_LABELS = [
    "business",
    "restaurant",
    "store",
    "hotel",
    "cafe",
]

# Minimum confidence required from GLiNER.
#
# Lower:
#     more entities detected
#     more false positives
#
# Higher:
#     fewer false positives
#     may miss some businesses
#
GLINER_THRESHOLD = 0.45


# ==========================================================
# LOAD GLINER MODEL
# ==========================================================

@lru_cache(maxsize=1)
def get_nlp() -> GLiNER:
    """
    Load GLiNER only once.

    First request:
        downloads/loads the model.

    Future requests:
        reuse the same model.
    """

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
    """
    Extract possible business names from free-form text.

    Example:

    Input:
        "We ordered pizza from Domino's yesterday."

    Possible GLiNER output:
        Domino's -> restaurant

    Our normalized output:
        [
            {
                "text": "Domino's",
                "label": "BUSINESS",
                "start_char": 22,
                "end_char": 30
            }
        ]
    """

    # ------------------------------------------------------
    # Validate text
    # ------------------------------------------------------

    if (
        not text
        or not text.strip()
    ):
        return []

    # ------------------------------------------------------
    # Load model
    # ------------------------------------------------------

    model = get_nlp()

    # ------------------------------------------------------
    # GLiNER prediction
    # ------------------------------------------------------

    try:

        entities = model.predict_entities(
            text,
            BUSINESS_ENTITY_LABELS,
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
    # Debugging
    # ------------------------------------------------------

    print(
        [
            (
                entity["text"],
                entity["label"],
                round(
                    float(
                        entity["score"]
                    ),
                    3,
                ),
            )
            for entity in entities
        ]
    )

    # ------------------------------------------------------
    # Normalize entities
    # ------------------------------------------------------

    extracted_entities = []

    seen_entities = set()

    for entity in entities:

        raw_text = entity[
            "text"
        ]

        cleaned_text = (
            raw_text.strip()
        )

        if not cleaned_text:
            continue

        # Mention.text maximum length
        if len(cleaned_text) > 255:
            continue

        start_char = int(
            entity["start"]
        )

        end_char = int(
            entity["end"]
        )

        score = float(
            entity["score"]
        )

        # Normalize to avoid duplicate mentions.
        #
        # Example:
        #
        # Starbucks
        # STARBUCKS
        #
        # become the same normalized value.
        normalized_text = (
            " ".join(
                cleaned_text
                .lower()
                .split()
            )
        )

        # Include position in duplicate key.
        #
        # This allows:
        #
        # "Starbucks is better than Starbucks downtown"
        #
        # to still preserve separate occurrences if needed.
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

                # Normalize all GLiNER labels into
                # one label understood by our system.
                "label": "BUSINESS",

                "start_char": start_char,
                "end_char": end_char,

                # We are intentionally NOT returning
                # score here because your current
                # response schema does not contain it.
            }
        )

    # ------------------------------------------------------
    # Sort in same order as original text
    # ------------------------------------------------------

    extracted_entities.sort(
        key=lambda item: (
            item["start_char"]
        )
    )

    return extracted_entities








# SPAcy

# from functools import lru_cache
#
# import spacy
# from spacy.language import Language
#
#
# # ==========================================================
# # NLP CONFIGURATION
# # ==========================================================
#
# SPACY_MODEL_NAME = "en_core_web_sm"
#
# # For the first version of this project,
# # businesses are extracted from spaCy ORG entities.
# #
# # Examples:
# # Starbucks
# # Target
# # Walmart
# # Hilton
# #
# BUSINESS_ENTITY_LABELS = {
#     "ORG",
# }
#
#
# # ==========================================================
# # LOAD NLP MODEL
# # ==========================================================
#
# @lru_cache(maxsize=1)
# def get_nlp() -> Language:
#     """
#     Load spaCy model only once.
#
#     The first API request loads the model.
#     Future requests reuse the same model.
#     """
#
#     try:
#
#         nlp = spacy.load(
#             SPACY_MODEL_NAME
#         )
#
#     except OSError as exc:
#
#         raise RuntimeError(
#             (
#                 f"spaCy model "
#                 f"'{SPACY_MODEL_NAME}' "
#                 f"is not installed. Run: "
#                 f"python -m spacy download "
#                 f"{SPACY_MODEL_NAME}"
#             )
#         ) from exc
#
#     return nlp
#
#
# # ==========================================================
# # EXTRACT BUSINESS ENTITIES
# # ==========================================================
#
# def extract_business_entities(
#     text: str,
# ) -> list[dict]:
#     """
#     Extract possible business names from free-form text.
#
#     Example:
#
#     Input:
#         "I visited Starbucks in Tucson."
#
#     Possible output:
#         [
#             {
#                 "text": "Starbucks",
#                 "label": "ORG",
#                 "start_char": 10,
#                 "end_char": 19
#             }
#         ]
#     """
#
#     if (
#         not text
#         or not text.strip()
#     ):
#
#         return []
#
#     nlp = get_nlp()
#
#     document = nlp(
#         text
#     )
#
#     print([
#         (entity.text, entity.label_)
#         for entity in document.ents
#     ])
#
#     extracted_entities = []
#
#     # Used to avoid duplicates such as:
#     #
#     # "I went to Starbucks.
#     #  Starbucks was crowded."
#     #
#     # We currently create one Mention row
#     # for Starbucks for this source.
#     seen_entities = set()
#
#     for entity in document.ents:
#
#         if (
#             entity.label_
#             not in BUSINESS_ENTITY_LABELS
#         ):
#             continue
#
#         raw_text = entity.text
#
#         cleaned_text = (
#             raw_text.strip()
#         )
#
#         if not cleaned_text:
#             continue
#
#         # Mention.text supports max 255 chars.
#         if len(cleaned_text) > 255:
#             continue
#
#         normalized_text = (
#             " ".join(
#                 cleaned_text
#                 .lower()
#                 .split()
#             )
#         )
#
#         if (
#             normalized_text
#             in seen_entities
#         ):
#             continue
#
#         seen_entities.add(
#             normalized_text
#         )
#
#         # Normally spaCy entities do not contain
#         # surrounding whitespace, but handle it
#         # correctly so offsets remain accurate.
#         leading_spaces = (
#             len(raw_text)
#             - len(raw_text.lstrip())
#         )
#
#         trailing_spaces = (
#             len(raw_text)
#             - len(raw_text.rstrip())
#         )
#
#         start_char = (
#             entity.start_char
#             + leading_spaces
#         )
#
#         end_char = (
#             entity.end_char
#             - trailing_spaces
#         )
#
#         extracted_entities.append(
#             {
#                 "text": cleaned_text,
#                 "label": entity.label_,
#                 "start_char": start_char,
#                 "end_char": end_char,
#             }
#         )
#
#     return extracted_entities