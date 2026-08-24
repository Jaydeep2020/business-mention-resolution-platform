# Business Mention Extraction --- Quick Notes

## 1. Goal

The project needs to detect **business names mentioned in free-form
text**.

Example:

``` text
"We ordered pizza from Domino's yesterday."
```

Expected extraction:

``` text
Domino's
```

This step is called **mention/entity extraction**.

------------------------------------------------------------------------

## 2. Extraction vs Resolution

These are two separate stages.

### Mention Extraction

Answers:

> **What business name is mentioned in the text?**

Example:

``` text
"I really liked Domino's near downtown."
                ↓
            Domino's
```

### Resolution

Answers:

> **Which actual business record does that mention refer to?**

Example:

``` text
Domino's
   ↓
Candidate 1 → Domino's, Philadelphia
Candidate 2 → Domino's, Pittsburgh
Candidate 3 → Domino's, Tampa
   ↓
Use context + location + similarity
   ↓
Correct business record
```

**Important:** Use an NLP model for extraction and the PostgreSQL
business catalog for resolution.

------------------------------------------------------------------------

## 3. Extraction Options

  ------------------------------------------------------------------------------------
  Approach           Training       Business Extraction Difficulty     Use
                     Needed?                                           
  ------------------ -------------- ------------------- -------------- ---------------
  spaCy              No             Generic             Easy           Baseline
  `en_core_web_sm`                                                     

  Fine-tuned BERT    Yes            Potentially very    Harder         Later
  NER                               good                               

  **GLiNER**         No, for        Can request         Medium         **Recommended
                     zero-shot use  business-specific                  now**
                                    entities                           
  ------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Why spaCy Alone Is Not Enough

`en_core_web_sm` is a **general-purpose NER model**. It is not
specifically trained to recognize every local business.

Observed examples:

``` text
Starbucks → ORG     ✅
Domino    → PERSON  ❌
```

Our original code accepted only:

``` python
BUSINESS_ENTITY_LABELS = {"ORG"}
```

Therefore:

``` text
Domino → PERSON
          ↓
PERSON is not ORG
          ↓
Mention ignored ❌
```

Adding `PERSON` is **not a good fix**.

For example:

``` text
"I went to dinner with John."
```

spaCy may detect:

``` text
John → PERSON
```

If `PERSON` were accepted as a business, `John` could incorrectly become
a business mention.

------------------------------------------------------------------------

## 5. Why GLiNER Is Better for the Current Stage

GLiNER supports **zero-shot entity extraction**.

Instead of depending on fixed generic labels, we can tell it what kinds
of entities we want:

``` python
labels = [
    "business",
    "restaurant",
    "store",
    "hotel",
    "cafe",
]
```

Then:

``` text
"We ordered pizza from Domino's yesterday."
                    ↓
                  GLiNER
                    ↓
          Domino's → business
```

This is much closer to the project's requirement.

------------------------------------------------------------------------

## 6. Basic GLiNER Usage

Install:

``` bash
pip install gliner
```

Load a model:

``` python
from gliner import GLiNER

model = GLiNER.from_pretrained(
    "gliner-community/gliner_small-v2.5"
)
```

Define labels:

``` python
labels = [
    "business",
    "restaurant",
    "store",
    "hotel",
    "cafe",
]
```

Extract entities:

``` python
entities = model.predict_entities(
    text,
    labels,
    threshold=0.45,
)
```

Possible output:

``` python
[
    {
        "text": "Domino's",
        "label": "restaurant",
        "start": 22,
        "end": 30,
        "score": 0.91,
    }
]
```

The exact result and score depend on the model.

------------------------------------------------------------------------

## 7. Project Architecture

Recommended pipeline:

``` text
Review / free-form text
        ↓
      GLiNER
        ↓
Business mention extraction
        ↓
mentions table
        ↓
Candidate generation
        ↓
Search PostgreSQL businesses
        ↓
Candidate scoring
        ↓
Resolution decision
        ↓
High confidence → Auto resolved
Low confidence  → Human review
```

Example:

``` text
"We ordered pizza from Domino's."
              ↓
            GLiNER
              ↓
          "Domino's"
              ↓
       Save Mention
              ↓
     Candidate Generation
              ↓
Domino's location A
Domino's location B
Domino's location C
              ↓
       Candidate Scoring
              ↓
       Correct location
```

------------------------------------------------------------------------

## 8. Role of the Existing MentionExtractionService

The existing FastAPI architecture does **not** need to be rewritten.

Keep:

``` text
POST /extraction/mentions
        ↓
MentionExtractionService
        ↓
extract_business_entities()
        ↓
Mention table
```

Only the implementation behind `extract_business_entities()` changes
from spaCy-only extraction to GLiNER.

Normalized output can remain:

``` python
[
    {
        "text": "Domino's",
        "label": "BUSINESS",
        "start_char": 22,
        "end_char": 30,
    }
]
```

This allows the existing service and API response structure to stay
mostly unchanged.

------------------------------------------------------------------------

## 9. What About Fine-Tuned BERT?

A fine-tuned BERT token classifier could become a strong long-term
solution.

Training data would need business annotations such as:

``` text
I ordered food from Domino's yesterday.
                    ^^^^^^^^
                    BUSINESS
```

``` text
Starbucks near downtown was crowded.
^^^^^^^^^
BUSINESS
```

``` text
John went to Walmart.
             ^^^^^^^
             BUSINESS
```

The model learns token labels such as:

``` text
B-BUSINESS
I-BUSINESS
O
```

However, this requires a sufficiently large and correctly labeled
training dataset.

Therefore:

``` text
Fine-tuned BERT
      ↓
Potentially powerful
      ↓
But requires labeled data + training
      ↓
Use later if needed
```

------------------------------------------------------------------------

## 10. Recommended Implementation Strategy

### Version 1 --- Baseline

Keep the existing spaCy implementation for comparison.

``` text
Text → spaCy → ORG entities
```

### Version 2 --- Main Extraction

Use GLiNER zero-shot extraction.

``` text
Text
 ↓
GLiNER
 ↓
Business mentions
 ↓
Candidate generation
 ↓
Scoring
 ↓
Resolution
```

### Later --- Optional Improvement

If enough labeled training data becomes available:

``` text
Annotated business mentions
        ↓
Fine-tune BERT
        ↓
Evaluate against GLiNER
```

------------------------------------------------------------------------

## 11. Evaluation Idea

Create a small manually labeled extraction test set and compare:

``` text
              Test Reviews
                   ↓
          ┌────────┴────────┐
          ↓                 ↓
       spaCy              GLiNER
          ↓                 ↓
    Predictions        Predictions
          ↓                 ↓
 Precision/Recall     Precision/Recall
```

Useful metrics:

-   **Precision** --- Of the extracted mentions, how many were actually
    businesses?
-   **Recall** --- Of all real business mentions, how many did the model
    find?
-   **F1-score** --- Balance between precision and recall.

Example finding:

> spaCy's general-purpose NER incorrectly classified some business
> names, such as `Domino` as `PERSON`. GLiNER was therefore evaluated as
> a zero-shot extraction model using business-specific entity labels.

------------------------------------------------------------------------

## 12. Key Decision

For the current project:

``` text
Mention Extraction → GLiNER
Candidate Search   → PostgreSQL business catalog
Candidate Scoring  → Resolution engine
Final Decision     → Auto-resolve or human review
```

Do **not** use the complete PostgreSQL business catalog as the primary
mention extractor.

The separation should remain:

``` text
GLiNER
"What business is mentioned?"
        ↓
     Domino's

Resolution Engine
"Which Domino's record is it?"
        ↓
Correct business row
```

### Final Choice

**Use GLiNER as the main zero-shot business mention extractor and keep
spaCy as a baseline for comparison. Consider fine-tuned BERT later if
enough labeled business-mention training data becomes available.**
