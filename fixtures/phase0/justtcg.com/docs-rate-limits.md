---
url: https://justtcg.com/docs/rate-limits
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl)
---

Rate limits — JustTCG API

JustTCG

ProductDocsBlogMCP ServerPricingPartner Program
Toggle theme
Toggle menu
LoginSign Up Free

#### Get started

- Quickstart

- SDK install

#### API reference

- GET/games

- GET/sets

- /cards
- GETOne card

- POSTBatch (≤200)

- GET/v2/cardsNEW
- Graded cards

- Localized pricing

- GET/mcp

#### Schema

- Card object

- Variant object

- IdentifiersUPDATED

#### Operations

- Response format

- Errors

- Rate limits

#### Resources

- Examples

- OpenAPI (Swagger)NEW

- Commercial useNEW

- Changelog

Documentation

- Docs


# Rate limits

Rate limits are tied to your subscription plan. Monitor usage in the dashboard.

## Plans

Plan
Monthly
Daily
Per minute

Free

1,000 requests

100 requests

10 / min

Starter

10,000 requests


50 / min

Professional

50,000 requests

5,000 requests

100 / min

Enterprise

500,000 requests


500 / min

If you exceed your minute rate limit, the API returns 429 Too Many Requests. If you exceed your monthly limit, you'll need to upgrade your plan to continue.

## Reset times

Plan type
Daily reset
Monthly reset


Midnight (00:00) UTC

On the day-of-month the account was created, at 00:00 UTC.

Paid


On successful payment at the start of each billing cycle.

Retry strategy:Use exponential backoff with jitter when handling 429 responses. Start at ~1s and double up to a sensible cap (~30s); always honor any Retry-After header when present.

## Free tier on shared infrastructure

Running on shared infrastructure?If your backend runs on Cloudflare Workers, AWS Lambda, Vercel, or another serverless or shared‑hosting platform with a Free API key, you may occasionally see an EXCESSIVE_FREE_TIER_USAGE block. Paid plans are not subject to these shared‑environment protections. Upgrading to any paid plan resolves it.

Why am I seeing EXCESSIVE_FREE_TIER_USAGE on a Free key?Applies only to Free tier traffic from shared cloud environments

Free API keys carry additional abuse protections beyond the per‑plan limits in the table above. In a shared cloud environment, requests from many unrelated Free tier users can be grouped together by the underlying platform, so the combined activity may trigger a temporary block; even when your own key's usage is well within the Free tier. When this happens the API returns: EXCESSIVE_FREE_TIER_USAGE.

Resolution: Move to any paid plan. Paid traffic is exempt from these shared‑environment protections, so your requests are no longer affected by other tenants on the same platform.


The dedicated pricing API for trading card games. Fast, accurate data for Magic: The Gathering, Pokémon, Yu-Gi-Oh!, Disney Lorcana, and more.

## Product

- Pricing & plans

- Features

- Use cases

- Supported games

- Partner Program

## Developers

- API quickstart

- Cards API reference

- SDKs & client libraries

- MCP API reference

- Rate limits & quotas

- API changelog

## Resources

- Blog

- MCP server for AI agents

- Commercial use & licensing

- API status

## Company

- Contact us

- Email support

- Terms of Service

- Privacy Policy

© 2026 JustTCG. All rights reserved.

Magic: The Gathering, Pokémon, Yu-Gi-Oh!, Disney Lorcana, One Piece, Digimon, and all related names, characters, logos, and distinctive likenesses thereof, are trademarks or registered trademarks of their respective owners. JustTCG is not affiliated with, endorsed by, or sponsored by these companies.

