# Fixture: https://phygitals.mintlify.app/public-api/packs/list.md
Fetched: 2026-09-26T00:20:22Z

> ## Documentation Index
> Fetch the complete documentation index at: https://dev.phygitals.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List available packs

> Fetch every pack that can currently be purchased, including pricing, expected value, and rarity distribution.

Returns every pack available on Phygitals. Use this to discover pack IDs, prices, and chase previews before calling authenticated purchase endpoints.

<Note>
  **No authentication required.** This is a public read endpoint. Authenticated purchase flows use [`POST /api/vm/buy/crypto`](/public-api/purchase/crypto).
</Note>

## Query parameters

<ParamField query="platform" type="string" default="mainnet">
  Platform filter. For example `mainnet` for first-party Phygitals packs.
</ParamField>

<ParamField query="includeRepacks" type="boolean" default="false">
  When `true`, include partner repack listings in the response. Defaults to `false`.
</ParamField>

## Example request

```http theme={"dark"}
GET /api/vm/available?platform=mainnet
```

## Response

<ResponseExample>
  ```json 200 theme={"dark"}
  [
    {
      "id": "BSG6Dy...",
      "slug": "topps-chrome-2024",
      "platform": "mainnet",
      "name": "Topps Chrome 2024",
      "enable": true,
      "description": "Pull from the latest Topps Chrome series.",
      "mint_price": 100.00,
      "max_per_mint": 10,
      "in_stock": true,
      "categories": ["Baseball", "Basketball"],
      "ev": 104.00,
      "min_ev": 101.00,
      "max_ev": 105.00,
      "ev_updated_at": "2026-03-10T18:00:00.000Z",
      "buyback_percent": 0.85,
      "claw_image_url": "https://cdn.phygitals.com/packs/topps-chrome-2024.png",
      "rarity_distribution": [
        { "id": 0, "name": "Common", "color": "#22C55E", "lower": 60, "upper": 100, "weight": 80 },
        { "id": 1, "name": "Rare",   "color": "#A855F7", "lower": 100, "upper": 200, "weight": 15 },
        { "id": 2, "name": "Epic",   "color": "#EF4444", "lower": 200, "upper": 500, "weight": 4 },
        { "id": 3, "name": "Mythic", "color": "#F59E0B", "lower": 500, "upper": 15000, "weight": 1 }
      ]
    }
  ]
  ```
</ResponseExample>

## Key fields

<ResponseField name="id" type="string">
  Pack identifier (mint address). Pass as `claw_id` in [`POST /api/vm/buy/crypto`](/public-api/purchase/crypto).
</ResponseField>

<ResponseField name="slug" type="string">
  URL-friendly identifier. Pass as `:slug` in [`GET /api/vm/chase/:slug`](/public-api/packs/chase).
</ResponseField>

<ResponseField name="mint_price" type="number">
  Price per pull in USD.
</ResponseField>

<ResponseField name="max_per_mint" type="number">
  Maximum pulls per transaction. Enforce client-side before calling [`POST /api/vm/buy/crypto`](/public-api/purchase/crypto).
</ResponseField>

<ResponseField name="in_stock" type="boolean">
  `false` means sold out. Disable the buy button when this is `false`.
</ResponseField>

<ResponseField name="ev" type="number">
  Expected value per pull in USD.
</ResponseField>

<ResponseField name="buyback_percent" type="number">
  Fraction of FMV paid on sellback. For example, `0.85` = 85%.
</ResponseField>

<ResponseField name="rarity_distribution" type="array">
  Array of rarity tiers with color, value range (`lower`/`upper` in USD), and weight (relative probability).
</ResponseField>

## Additional fields

The response also includes the following fields. You only need the documented fields above for most integrations. Additional fields are returned for forward-compatibility and may be ignored.

| Field                      | Type                                                                                | Description                                                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `type`                     | `"CORE" \| "EBAY"`                                                                  | Pack source. `"EBAY"` = packs backed by the secondary card market. `"CORE"` = packs backed by minted core inventory.  |
| `chase`                    | `Array<{ id, name, image, fmv }>`                                                   | Inline preview of high-value chase cards. Equivalent to calling [`GET /api/vm/chase/:slug`](/public-api/packs/chase). |
| `num_pulls_7d`             | `number`                                                                            | Total pulls from this pack over the past 7 days.                                                                      |
| `category`                 | `string`                                                                            | Singular convenience copy of `categories[0]`. Prefer `categories`.                                                    |
| `creator_profile`          | `{ id, wallet_address?, username?, profile_picture?, twitter_username?, socials? }` | Pack creator profile.                                                                                                 |
| `pack_managers`            | `Array<{ id, username, profile_picture, role }>`                                    | Users with management rights on the pack.                                                                             |
| `repack`                   | `boolean`                                                                           | `true` if the pack is a partner repack, `false` for first-party Phygitals packs.                                      |
| `last_pull`                | `string \| null`                                                                    | ISO timestamp of the most recent pull on this pack.                                                                   |
| `variant_of`               | `string \| null`                                                                    | If this pack is a variant, the parent pack's `id`.                                                                    |
| `variants`                 | `Array<object>`                                                                     | Sibling/child variants of this pack.                                                                                  |
| `rewards_amounts`          | `number[]`                                                                          | Per-pull bonus token amounts (in raw token units).                                                                    |
| `sellback_rewards_amounts` | `number[]`                                                                          | Per-sellback bonus token amounts.                                                                                     |
| `rewards_mint_addresses`   | `string[]`                                                                          | SPL/EVM mint addresses for bonus tokens.                                                                              |
| `rewards_symbols`          | `string[]`                                                                          | Display symbols for bonus tokens.                                                                                     |
| `rewards_decimals`         | `number[]`                                                                          | Decimals for bonus tokens.                                                                                            |
