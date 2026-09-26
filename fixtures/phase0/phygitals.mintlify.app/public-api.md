# Fixture: https://phygitals.mintlify.app/public-api.md
Fetched: 2026-09-26T00:20:22Z

> ## Documentation Index
> Fetch the complete documentation index at: https://dev.phygitals.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Public API

> Programmatic access for Phygitals account holders — browse packs and marketplace listings, buy with crypto, and sell back claw items using user-scoped API keys.

The Phygitals Public API lets you automate actions on your own Phygitals account using **user API keys**. Keys are tied to your account, self-managed in **Settings**, and authorize a focused set of transaction endpoints.

<Note>
  Looking for partner integrations (listing packs, purchasing on behalf of your users, inventory, shipping)? See the [Enterprise API](https://api.phygitals.com/api/partner/v1).
</Note>

## What you can do

<CardGroup cols={2}>
  <Card title="List available packs" icon="box" href="/public-api/packs/list">
    Fetch pack catalog, pricing, EV, and rarity tiers — no API key required.
  </Card>

  <Card title="Get chase cards" icon="sparkles" href="/public-api/packs/chase">
    Preview high-value cards for a pack before opening it.
  </Card>

  <Card title="Browse marketplace listings" icon="store" href="/public-api/marketplace/listings">
    Search, filter, and paginate buy-now cards — no API key required.
  </Card>

  <Card title="Buy packs with crypto" icon="coins" href="/public-api/purchase/crypto">
    Submit signed payment transactions and poll for fulfillment on claw machines.
  </Card>

  <Card title="Sell back claw items" icon="arrow-rotate-left" href="/public-api/marketplace/take-claw-bid">
    Accept instant buyback offers on items you own from claw pulls.
  </Card>
</CardGroup>

## Base URL

| Environment    | Base URL                    |
| -------------- | --------------------------- |
| **Production** | `https://api.phygitals.com` |

Pack discovery and marketplace browse endpoints under `/api/vm/*` and `/api/marketplace/*` do not require a key. Authenticated purchase and sellback endpoints use the same path prefixes with a user API key.

## How it works

<Steps>
  <Step title="Check eligibility">
    Open **Settings → API keys** on [phygitals.com](https://phygitals.com). You need API keys enabled on your account and a linked external Solana wallet.
  </Step>

  <Step title="Create a key">
    Name your key and choose an optional expiration. Copy the secret immediately — it is shown only once.
  </Step>

  <Step title="Call an endpoint">
    Send the key on every request via [`X-API-Key`](/public-api/authentication) or `Authorization: Bearer`. Build and sign the on-chain transactions client-side, then submit them to the API.
  </Step>
</Steps>

## Endpoint summary

| Method | Path                                                | Scope                       | Description                                                      |
| ------ | --------------------------------------------------- | --------------------------- | ---------------------------------------------------------------- |
| `GET`  | `/api/vm/available`                                 | —                           | [List available packs](/public-api/packs/list)                   |
| `GET`  | `/api/vm/chase/:slug`                               | —                           | [Get chase cards for a pack](/public-api/packs/chase)            |
| `GET`  | `/api/marketplace/marketplace-listings`             | —                           | [List marketplace listings](/public-api/marketplace/listings)    |
| `GET`  | `/api/marketplace/filters`                          | —                           | [Get marketplace filter facets](/public-api/marketplace/filters) |
| `POST` | `/api/vm/buy/crypto`                                | `vm.buy.crypto`             | [Submit a crypto pack purchase](/public-api/purchase/crypto)     |
| `POST` | `/api/vm/buy/status`                                | `vm.buy.crypto`             | [Poll purchase fulfillment](/public-api/purchase/status)         |
| `POST` | `/api/marketplace/transaction/take-claw-bid-init`   | `marketplace.take-claw-bid` | [Start a claw buyback](/public-api/marketplace/take-claw-bid)    |
| `POST` | `/api/marketplace/transaction/take-claw-bid-finish` | `marketplace.take-claw-bid` | [Complete a claw buyback](/public-api/marketplace/take-claw-bid) |

## Public API vs Enterprise API

|               | Public API                    | Enterprise API                        |
| ------------- | ----------------------------- | ------------------------------------- |
| **Who**       | Individual Phygitals users    | Partners and platforms                |
| **Keys**      | Self-service (`phy_…` prefix) | Issued by Phygitals (`X-API-Key`)     |
| **Scope**     | Your account and wallets      | Your end users via `user_id`          |
| **Use cases** | Bots, scripts, custom tooling | Embedded pack storefronts, vault apps |
