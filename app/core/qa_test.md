# QA Test Questions — Natural Language QA over Business Catalog

These questions are designed to test the major intents supported by the Natural Language QA over Business Catalog feature.

## List Businesses

- Show me cafes in Philadelphia.
- List verified restaurants in Tucson.
- Show hotels in New York.
- Find grocery stores in San Diego.
- List pizza restaurants in California.
- Show unverified businesses in Phoenix.

## Count Businesses

- How many cafes are in Tucson?
- How many verified businesses are in Philadelphia?
- How many Starbucks locations are in the catalog?
- How many hotels are in New York?
- How many restaurants are in California?
- How many unverified businesses are in San Diego?

## Business Details

- Tell me about Hilton in New York.
- Find Tony's Pizza.
- Show details for Starbucks in Philadelphia.
- Tell me about businesses named Magnolia Bakery.
- Find Domino's in Tucson.
- Show me information about a cafe named Copper Finch Cafe.

## Top Businesses by Mentions

- Which businesses have the most mentions?
- Which cafes have the most resolved mentions?
- Show the most mentioned restaurants in Tucson.
- Which hotels are mentioned the most?
- Show the top 5 most mentioned businesses in Philadelphia.
- Which verified businesses have the most mentions?

## Category + Location Combinations

- Show verified cafes in Philadelphia.
- Find restaurants in Tucson, Arizona.
- List hotels in San Francisco, California.
- Show grocery stores in Phoenix.
- Find verified pizza restaurants in New York.
- Show cafes in San Diego that are verified.

## Clarification Cases

Use these to verify that the system asks for missing location information instead of guessing.

```text
Show restaurants near me.
Find cafes around here.
Show businesses in my area.
```

Expected behavior:

```text
needs_clarification = true
```

The system should ask the user to provide a city, state, or other location because it does not automatically know the user's location for catalog querying.

## Unsupported Questions

Use these to verify that the system rejects questions that cannot be answered from the business catalog.

```text
What is the weather in California?
Who is the president of the US?
What is the stock price of Apple?
Which restaurant has the best food in America?
```

Expected behavior:

```text
intent = unsupported
```

## Minimum Test Set

These 10 questions cover almost every major path in the current QA flow.

```text
1. Show verified cafes in Philadelphia.
2. How many restaurants are in Tucson?
3. Tell me about Hilton in New York.
4. Which businesses have the most mentions?
5. Show the top 5 most mentioned restaurants in Tucson.
6. How many Starbucks locations are in the catalog?
7. Show unverified businesses in Phoenix.
8. Find Tony's Pizza.
9. Show restaurants near me.
10. What is the weather in California?
```
