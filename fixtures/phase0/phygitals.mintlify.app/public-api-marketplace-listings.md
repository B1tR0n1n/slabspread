# Fixture: https://phygitals.mintlify.app/public-api/marketplace/listings.md
Fetched: 2026-09-26T00:20:22Z

> ## Documentation Index
> Fetch the complete documentation index at: https://dev.phygitals.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List marketplace listings

> Search, filter, sort, and paginate cards listed for sale on the Phygitals marketplace.

Returns a paginated page of marketplace listings with metadata, open offers, and listing activity. Use this to build a buy-now catalog or price-comparison tooling.

<Note>
  **No authentication required.** This is a public read endpoint.
</Note>

## Query parameters

<ParamField query="searchTerm" type="string">
  Free-text search matched against card name and metadata (for example title and cert number).
</ParamField>

<ParamField query="sortBy" type="string" default="fmv-low-high">
  Sort order. One of:

  `price-low-high`, `price-high-low`, `newest`, `recently-listed`, `name-asc`, `name-desc`, `fmv-low-high`, `fmv-high-low`
</ParamField>

<ParamField query="page" type="integer" default="0">
  Zero-based page index. Page `0` is the first page.
</ParamField>

<ParamField query="itemsPerPage" type="integer" default="24">
  Page size. Maximum **200** items per request.
</ParamField>

<ParamField query="metadataConditions" type="string" default="{}">
  JSON object mapping metadata trait names to allowed values. Values are OR'd within a trait; traits are AND'd together.

  Example: `{"Category":["Pokemon"],"Grader":["PSA"]}`

  Trait names are matched case-insensitively and normalized to title case server-side (`Category`, `Grader`, etc.).
</ParamField>

<ParamField query="priceRange" type="string" default="[null,null]">
  JSON `[min, max]` listing price bounds in **USD**. Use `null` for an open bound.

  Example: `[10, 500]`
</ParamField>

<ParamField query="fmvRange" type="string" default="[null,null]">
  JSON `[min, max]` fair-market-value bounds in **USD**. Use `null` for an open bound.
</ParamField>

<ParamField query="listedStatus" type="string" default="any">
  Listing filter: `any`, `listed`, or `unlisted`. Ignored when `hasBorrowOffer=true`.
</ParamField>

<ParamField query="collectionAddresses" type="string">
  JSON array of collection mint addresses to scope results. When omitted, defaults to the primary Phygitals marketplace collections.
</ParamField>

<ParamField query="hasBorrowOffer" type="boolean" default="false">
  When `true`, return only listings with an active Jupiter borrow offer attached. Each listing includes a `_borrowOffer` object. Forces `listedStatus` to `any`.
</ParamField>

## Example request

```http theme={"dark"}
GET /api/marketplace/marketplace-listings?searchTerm=charizard&sortBy=price-low-high&page=0&itemsPerPage=24&listedStatus=listed&metadataConditions=%7B%22Category%22%3A%5B%22Pokemon%22%5D%7D&priceRange=%5Bnull%2C500%5D&fmvRange=%5Bnull%2Cnull%5D
```

## Response

<ResponseExample>
  ```json 200 theme={"dark"}
  {
    "listings": [
      {
        "address": "7YboEnrAwzA1BLYuH3QDCaMRaKxD1AvbYjvd2U71g3m4",
        "slug": "2024-charizard-psa-10",
        "name": "2024 Charizard PSA 10",
        "image": "https://cdn.phygitals.com/cards/charizard.png",
        "owner": "3BqtQbWXtcf73eScw7Rdu34Z2kLuJTziw1bH7RhmDyZm",
        "collection_address": "7QVm5bfXBEKHRKYVhhZm7QsP8GyoD1vFcuMGNaoUWV2x",
        "price": "125000000",
        "listed": true,
        "altFmv": 142.5,
        "marketplace": "TENSOR",
        "metadata": [
          { "key": "Title", "value": "2024 Charizard PSA 10" },
          { "key": "Category", "value": "Pokemon" },
          { "key": "Grader", "value": "PSA" },
          { "key": "Grade", "value": "10" }
        ],
        "offers": [],
        "mostRecentListActivity": { "time": "2026-06-01T12:00:00.000Z" }
      }
    ],
    "amount": 1284
  }
  ```
</ResponseExample>

<ResponseField name="listings" type="array">
  Page of listing objects. Each row is a `UniversalNFTData` record with related `metadata`, `offers`, and listing timestamps included.
</ResponseField>

<ResponseField name="amount" type="number">
  Total number of listings matching the current filters (across all pages, not just this page).
</ResponseField>

## Key listing fields

| Field          | Type                      | Description                                                                                                                     |
| -------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `address`      | `string`                  | On-chain mint / item id. Use as the card identifier in downstream marketplace calls.                                            |
| `slug`         | `string`                  | URL slug when present. Resolves on [phygitals.com/card/:slug](https://phygitals.com).                                           |
| `name`         | `string`                  | Display name.                                                                                                                   |
| `image`        | `string`                  | Primary image URL.                                                                                                              |
| `price`        | `string \| null`          | List price in USDC base units (6 decimals). Divide by `1_000_000` for USD. `null` when not listed.                              |
| `listed`       | `boolean`                 | Whether the item currently has an active list price.                                                                            |
| `altFmv`       | `number \| null`          | Fair-market value in USD from Alt (when available).                                                                             |
| `metadata`     | `Array<{ key, value }>`   | Card traits (`Title`, `Category`, `Grader`, `Grade`, etc.).                                                                     |
| `offers`       | `array`                   | Open bids/offers on the item.                                                                                                   |
| `marketplace`  | `"TENSOR" \| "MAGICEDEN"` | Aggregator the listing is sourced from, when applicable.                                                                        |
| `_borrowOffer` | `object \| null`          | Present only when `hasBorrowOffer=true`. Jupiter borrow-offer terms (`pubkey`, `principal_amount`, `apy_bps`, `expires_at`, …). |

## Pagination

Request the next page by incrementing `page` while keeping other query parameters identical:

```http theme={"dark"}
GET /api/marketplace/marketplace-listings?page=1&itemsPerPage=24&sortBy=price-low-high&listedStatus=listed
```

Stop when `page * itemsPerPage >= amount`.

## Filter facets

Use [`GET /api/marketplace/filters`](/public-api/marketplace/filters) to populate trait pickers (`Set`, `Grader`, `Grade`, etc.) before building `metadataConditions`.

## Error responses

| Status | Body                                   | Cause                     |
| ------ | -------------------------------------- | ------------------------- |
| `500`  | `{ "error": "Internal server error" }` | Unexpected server failure |
