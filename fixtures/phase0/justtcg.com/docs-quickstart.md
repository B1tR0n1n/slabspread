---
url: https://justtcg.com/docs -> 200 https://justtcg.com/docs/quickstart
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl)
---

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


# Quickstart

Make your first JustTCG API call in under two minutes — get an API key, hit the base URL, and read live pricing data.

## Overview

The JustTCG API provides real-time pricing data for trading card games including Magic: The Gathering, Pokémon, Yu-Gi-Oh!, Disney Lorcana, One Piece TCG, Digimon, and Union Arena. Our API is designed to be simple, fast, and reliable.

Using Node.js or TypeScript?We strongly recommend the official justtcg-js SDK. It provides type safety, automatic authentication, and cleaner data models. View SDK install →

### Base URL

GEThttps://api.justtcg.com/v1
Copy

Prefer to start from a machine-readable definition? The OpenAPI (Swagger) spec imports straight into Swagger UI, Postman, or a client generator.

### MCP endpoint (BETA)

The MCP endpoint provides comprehensive pricing data to your agentic workflows.

GEThttps://mcp.justtcg.com

## Authentication

All API requests require authentication using an API key. Obtain a key by signing up for an account and subscribing to a plan, then include it in the x-api-key request header.

SDK users:The SDK automatically handles authentication using the JUSTTCG_API_KEY environment variable.

### Auth header

bash — header
headerCopy

x-api-key: tcg_your_api_key_here

### Your first request

List all supported games:

bash — curl
curlCopy

curl https://api.justtcg.com/v1/games \
  -H "x-api-key: tcg_your_api_key_here"

### Same call with the SDK

typescript — quickstart.ts
quickstart.tsCopy

import { JustTCG } from 'justtcg-js';

// Reads JUSTTCG_API_KEY from env, or pass { apiKey } directly
const client = new JustTCG();

const { data } = await client.v1.games.list();
console.log(data);

Keep your API key secure.Never expose it in client-side code. If you suspect your key has been compromised, regenerate it immediately from the dashboard.


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

