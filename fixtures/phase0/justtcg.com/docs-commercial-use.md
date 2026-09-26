---
url: https://justtcg.com/docs/commercial-use
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl)
---

Commercial use guidelines - JustTCG API

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

- Commercial use

# Commercial use guidelines

Plain-English answers about what you can build with JustTCG data. If you're on a paid plan and you're building your own product, the answer is almost always yes.

The short version:On a paid plan, you can display our prices to your users, derive your own analytics from them, store them, and charge for the product you build. What you can't do is hand the raw data to someone else, whether as a feed, an export, or a proxied endpoint.

## What you can do

These are all explicitly permitted on any paid subscription tier. You do not need to ask us first.

- ✓Show current prices, price history, and percentage changes to your users.

- ✓Build charts, sparklines, trend indicators, and market dashboards.

- ✓Build portfolio and collection trackers that value a user's cards over time.

- ✓Calculate your own derived metrics, like index values, spreads, movers, and alerts.

- ✓Cache responses server-side and store price points to power your app's features.

- ✓Combine JustTCG data with other market data you lawfully obtain.

- ✓Charge your users money for the product you build.

## What you can't do

There is essentially one boundary, stated a few different ways: don't become a distribution channel for the raw data.

- ✕Resell, redistribute, or sub-license the raw data as a standalone feed.

- ✕Proxy or re-expose JustTCG endpoints so third parties can query them through you.

- ✕Publish or sell bulk exports of stored price data as a dataset.

- ✕Build a pricing API that substitutes for JustTCG.

- ✕Share one API key across separate businesses or products.

Enforcement:Reselling raw data or standing up an API substitute is grounds for immediate termination under Section 7.3 of the Terms. We'd much rather talk first, so if you're unsure whether your design crosses the line, ask us before you build it.

## Free tier

The free tier is for personal, non-commercial use: prototyping, learning, side projects you aren't shipping to users. The commercial rights on this page attach to paid plans. If you're putting a product in front of other people, you need a paid plan, regardless of how few requests it makes.

## Caching and storage

There is no maximum retention period.Cache aggressively, since it's good for your latency and good for your quota. Store price points for as long as your app needs them: a portfolio tracker that keeps five years of a user's collection history is exactly the use case this permits.

The one condition is purpose. Stored data powers yourapplication. It doesn't become a dataset you can export, publish, or sell, and that stays true after your subscription ends: you can't use an accumulated archive to run a service for others once you stop paying for the source.

## Attribution

Attribution is appreciated but not requiredon paid tiers. If you'd like to credit us, any of these work:
text
textCopy

Market data provided by JustTCG
Pricing by JustTCG
Prices via JustTCG (justtcg.com)

As a link, in a footer or tooltip near the prices:
html
htmlCopy

<a href="https://justtcg.com" rel="noopener">Market data provided by JustTCG</a>

Please don't alter the JustTCG name or imply that we endorse, certify, or partner with your product unless you're in the JustTCG Partner Program.

## What the numbers actually mean

If you're displaying our prices to end users, it helps to know what you're showing them.

JustTCG prices are volume-weighted averages of observed market activity, not listing prices and not a number we set. Sales with higher volume exert proportionally more influence on the final figure, which keeps the price stable against thin, outlier, or manipulated transactions. Two streams feed the model: aggregated online marketplace activity, and real physical sales reported in real time by verified local game stores in the JustTCG Partner Program.

Practical implication for your UI: a JustTCG price is a market observation, not a quote or an offer. Describing it as "market value" or "market price" is accurate. Describing it as the price a specific seller will honor is not.

Still unsure?Describe what you're building and we'll tell you plainly whether it's in bounds. Practically every question we get turns out to be a yes.

This page is a plain-English summary for convenience. The Terms of Service are the binding agreement, and Section 7 controls in the event of any conflict.


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

