# Fixture: https://docs.collectorcrypt.com/marketplace/api
Fetched: 2026-09-26T00:20:22Z

Marketplace API | Collector Crypt

Skip to main content

Collector CryptDocumentation

- Introduction

- Products

- $CARDS Token

- 
Vault

- Depositing Cards

- Withdrawing Cards

- Shipping API

- 
Marketplace

- Marketplace Overview

- User Guide

- Program Documentation

- API Docs

- 
Gacha

- VRF

- API Docs

- EVM API Docs

- cc-buyback (Solana program)

- 
Swap

- Swap Overview

- User Guide

- Program Documentation

- 
Cross-Chain

- Overview

- Supported Chains & Contracts

- Bridging Cards

- 
eBay Tools

- eBay Tools

- 
Launchpads

- Launchpads Overview

- Bespoke Launchpads — Design Guide

- Bespoke Launchpads — CSS Presets

- Metadata

- Contact Us

- 

- Marketplace

- API Docs

On this page

# Marketplace API

Build a client on the CollectorCrypt marketplace. Every write follows the same three steps.

- Build — POST to a builder endpoint. You get back an unsigned transaction.

- Sign — the user's wallet signs it.

- Broadcast — POST the signed transaction to /marketplace/broadcast.

Assets are on Solana. Prices are in USDC. A platform fee is deducted from the seller's proceeds — it is never added on top of what the buyer pays. So the buyer pays exactly the listed price.

Marketplace endpoints need no credential. The user's signature on the transaction is the authorisation. An API key is optional and only raises your rate limits — see Rate limits.

## Base URLs​

Environment
Base URL

Production

https://api.collectorcrypt.com

Devnet

https://dev-api.collectorcrypt.com

## Two request styles​

Most endpoints are plain REST. A few are dispatched by name through a single route:

curl -X POST https://api.collectorcrypt.com/ \
 -H 'Content-Type: application/json' \
 -d '{"method":"getCardOffers","params":{"nftAddress":"<mint>"}}'

Dispatch parameters are validated strictly

On POST / and POST /v2, params must contain exactly the declared keys. One extra key is a hard 400:

{"statusCode":400,"message":"[{\"type\":\"objectStrict\",\"message\":\"The object 'params' contains forbidden keys: 'cardId'.\",\"field\":\"params\",\"expected\":\"nftAddress, useV2\",\"actual\":\"cardId\"}]"}

No dispatch method takes a cardId — in params, cards are always identified by nftAddress. (The path segment of GET /cards/publicNft/:cardId does also accept a CollectorCrypt card id.)

Note that message is a string containing JSON, not an array. Parse it if you need the field name.

## List an asset​

POST /marketplace/list

Field
Type
Required
Notes

wallet

string

yes

The seller. The transaction is built for this signer.

nftAddress

string

yes

The asset mint.

price

number

yes

Listing price in USDC.

tokenStandard

string

no

Pnft, Cnft, StandardNft or CoreNft. Skips a lookup. Anything else falls back to Pnft.

Returns a bare base64 string — the unsigned transaction, as the whole response body.

Errors: 400 wallet is required · 400 This card is burned or invalid and cannot be listed. · 409 NFT is already listed on CC Marketplace. Please cancel the existing listing first. · 503 Unable to verify card ownership. Please refresh and try again.

## Buy an asset​

POST /marketplace/buy

Field
Type
Required
Notes

wallet

string

yes

The buyer.

nftAddress

string

yes

The asset mint.

price

number

yes

The listed price in USDC. The buyer pays exactly this.

isV2Listing

boolean

no

Send true for a CollectorCrypt listing. Omit it and the server detects the listing source; a listing held elsewhere is routed to a different builder.

tokenStandard

string

no

As above.

Returns a bare base64 string.

Errors: 404 Card not found · 404 Listing not found · 409 The owner has changed

## Buy with your own token​

POST /marketplace/buy-with-swap

For platforms whose users hold the platform's own token (usually a stablecoin) instead of USDC. Your server runs a swap wallet that holds USDC. One transaction does three things, in this order:

- The buyer sends swapAmount of your token to your swap wallet.

- Your swap wallet sends the buyer the listing price in USDC, exactly.

- The normal CollectorCrypt buy spends that USDC.

The marketplace only checks that the buyer's USDC is there at step 3. You set the exchange rate: swapAmount is your own quote, so any oracle or fixed rate works.

Your swap wallet is the fee payer, and it pays any account rent (for example, creating the buyer's USDC account on their first purchase). CollectorCrypt does not sign or sponsor this transaction.

Field
Type
Required
Notes

wallet

string

yes

The buyer. Must be a signing wallet.

nftAddress

string

yes

The asset mint. Every token standard on the marketplace is supported: Pnft, Cnft, StandardNft and CoreNft.

price

number

yes

The listed price in USDC. Must equal the on-chain listing exactly. Otherwise you get a 409 and nothing is built.

swapWallet

string

yes

Your swap wallet. It signs, pays the fee and pays rent.

swapMint

string

yes

Your token's mint. SPL Token or Token-2022. Transfer-hook accounts are resolved for you.

swapAmount

string

yes

What the buyer pays you, in swapMint base units, as an integer string. For example, "12500000" is 12.5 of a 6-decimal token.

Returns a bare base64 string: an unsigned v0 transaction. Its fee payer is swapWallet, and its two required signers are swapWallet and wallet.

Signing order:

- Your server decodes the transaction and checks it before signing. The instructions are: compute budget, two idempotent associated-token-account creates, the swapMint transfer from wallet, the USDC transfer from swapWallet, then the marketplace buy.

- Your server signs as swapWallet. Sign the message bytes as they are — for example VersionedTransaction.deserialize(bytes).sign([swapWallet]). Do not rebuild or recompile the message.

- The buyer signs.

- Send it through Broadcast with wallet set to the buyer.

Build shortly before use. The transaction carries a recent blockhash, which expires after about a minute.

Compressed NFTs leave little room

A Cnft buy with the swap is about 1,212 of Solana's 1,232 bytes. A Token-2022 mint with a transfer hook adds at least 66 bytes, so it does not fit on a Cnft listing. You get a 400 that says so.

Errors: 400 swapAmount must be a positive integer string in base units · 400 swapWallet must be a signing wallet · 400 swapWallet must differ from wallet · 400 swapMint is invalid · 400 swapMint is not a mint · 400 swapMint transfer hook needs N extra accounts; at most M fit in one transaction · 400 Swap-buy transaction too large · 400 Only CollectorCrypt listings can be bought with a swap · 404 Card not found · 404 Listing not found · 409 Listing price is X USDC, not Y. Re-quote and retry.

## Make an offer​

POST /marketplace/make-offer

This builder also deposits the full offer amount into the buyer's escrow in the same transaction.

Field
Type
Required
Notes

wallet

string

yes

The buyer.

nftAddress

string

yes

The asset mint.

price

number

yes

Offer amount in USDC.

currency

string

no

Send "USDC".

tokenStandard

string

no

As above.

ownerWallet

string

no

The current owner. Skips a lookup.

An offer must be at least 10% of the item's insured value.

Returns a bare base64 string.

Errors: 409 Cannot make an offer on your own card · 403 This user has blocked you · 400 Too low · 400 Could not determine NFT owner

## Accept an offer​

POST /marketplace/accept-offer

Field
Type
Required
Notes

wallet

string

yes

The current owner, and the signer.

nftAddress

string

yes

The asset mint.

buyer

string

yes

The offer maker.

price

number

yes

The amount you expect. Compared against the on-chain offer, tolerance 0.01 USDC.

Two response shapes. Normally a bare base64 string. If the asset is a compressed NFT that is currently listed, you get:

{
 "requiresCancelListing": true,
 "cancelListingTx": "<base64>",
 "message": "This cNFT is currently listed. Please sign the cancel listing transaction first, then accept the offer."
}

Broadcast that leg, then call accept-offer again.

Errors: 404 Offer not found on blockchain · 400 Offer price has changed from $X to $Y. Please refresh and try again. · 400 You no longer own this NFT. Please refresh and try again.

## Broadcast​

POST /marketplace/broadcast

Field
Type
Required
Notes

wallet

string

yes

Base58, 32–44 chars.

signedTransaction

string

yes

Base64, max 4096 chars.

This route rejects any field it does not declare with 400 property <name> should not exist.

{ "success": true, "signature": "<solana signature>", "message": "Transaction broadcast successfully" }

The server finishes writing its own state before responding, so a read straight afterwards is consistent.

Errors:

Status
Meaning

400

Invalid transaction format — the transaction did not deserialise.

400

message is a JSON string with "code":"INSUFFICIENT_FUNDS_RETRYABLE". Rebuild with the same builder; the retry comes back platform-paid.

403

Transaction contains unauthorized program

409

A sale on this asset is mid-payment. Retry shortly.

429

60 broadcasts per minute.

503

Too many broadcasts in flight. Retry in a moment.

Fee sponsorship is automatic

If the signing wallet cannot cover network fees, the returned transaction is already partially signed by the platform. Sign it and broadcast it unchanged — do not rebuild it.

## Browse listings​

GET /marketplace

The query string is a closed set. Any parameter not listed here returns 400 ["property limit should not exist"]. In particular there is no limit — the page-size parameter is step.

Parameter
Type
Notes

step

integer

Page size. Default 100, min 1, max 1000.

page

integer

1-indexed. Must be >= 1.

cursor

string

An opaque nextCursor from a previous response. Overrides page.

orderBy

enum

Default listedDateDesc. One of dateAsc, dateDesc, nameAsc, nameDesc, priceAsc, priceDesc, yearAsc, yearDesc, listedPriceAsc, listedPriceDesc, listedDateAsc, listedDateDesc.

search

string

Substring match on item and catalogue name; exact match on mint address and grading id.

ownerAddress

string

Exact wallet match.

marketplaceSource

enum

CC or ME.

listPriceMin, listPriceMax

number

0–999999999.

Response:

Key
Notes

filterNFtCard

The page of cards.

nextCursor

String or null. null means last page. Prefer paging by cursor until it is null.

total

All marketplace items, filter-independent.

findTotal

Matching count.

totalPages

ceil(findTotal / step).

cardsQtyByCategory

Category name to count.

Each row carries nftAddress, itemName, grade, gradingCompany, insuredValue, frontImage, backImage, year, nftStandard and more, plus:

- listing — { price, currency, marketplace, sellerId, createdAt, updatedAt } or null. price is a number; insuredValue on the row is a string.

- owner — { id, name, wallet } or null.

- images — exactly { cardId, backS, frontM, frontS }. There is no front or back key; full-size art is the row's own frontImage / backImage.

- offers — an array of { id }. It includes accepted offers as well as live ones, so offers.length is not a live-bid count.

Responses carry Cache-Control. Respect it.

## Read one card​

GET /cards/publicNft/:cardId — the static catalogue for one asset, identical for every viewer. :cardId accepts either the mint address or the CollectorCrypt card id.

Returns nftAddress, itemName, grade, gradeNum, gradingCompany, gradingID, insuredValue, frontImage, backImage, year, set, serial, category, nftStandard, images, population and more.

It deliberately carries no ownership or listing state. Errors: 404 Card not found.

GET /cards/publicNft/:cardId/market — the live market state, and the endpoint that tells you whether an asset is buyable and at what price.

Returns id, nftAddress, listing (the preferred active listing), listings (all active listings), owner, author, ownerId, status, nftStatus, inSwap, activeSwapId, burnedForBridge.

Some reads answer "missing" with an empty 200

GET /cards/publicNft/:cardId and /market both return 404 Card not found for an unknown or removed asset. But GET /shipping-address/:id and GET /outbound-shipment/:id in the Shipping API do not 404 — treat an empty 200 there as "no such record".

## Read offers on a card​

Dispatched by name on POST / — not on /v2, which returns 400 Method not found.

curl -X POST https://api.collectorcrypt.com/ \
 -H 'Content-Type: application/json' \
 -d '{"method":"getCardOffers","params":{"nftAddress":"<mint>"}}'

Param
Type
Required
Notes

nftAddress

string

yes

The asset mint.

useV2

boolean

no

Accepted and ignored — the CollectorCrypt offer read is the only path. Kept so cached clients that still send it are not rejected by strict params validation.

Returns a JSON array. Each element carries id, buyerId, price, currency, status, createdAt, card and source. Only live offers are returned, and the result is filtered for the caller — do not share-cache it.

## Rate limits​

Anonymous callers are counted per IP address; a key or a login gets its own counter. Current limits:

Endpoint
Limit

POST / and POST /v2, per method name

300 / minute

POST /marketplace/broadcast

60 / minute

POST /marketplace/cancel-offer

60 / minute

A 429 body looks like this:

{ "statusCode": 429, "message": "Too many requests — calls to getCardOffers. Retry in 60s.", "retryAfter": 60 }

Read retryAfter from the body. Most limiters do not set a Retry-After header.

### Using an API key​

Send the key as a bearer token. It is an opaque string beginning ccsk_:

curl -X POST https://api.collectorcrypt.com/ \
 -H 'Authorization: Bearer ccsk_...' \
 -H 'Content-Type: application/json' \
 -d '{"method":"getCardOffers","params":{"nftAddress":"<mint>"}}'

A key gives you your own counter and a 10× multiplier on every limit in the table above — 3000/minute per dispatch method, 600/minute for broadcast and cancel-offer. A signed-in user gets 5×.

This API does not read an x-api-key header. Use Authorization: Bearer.

Verify a new key on an authenticated route

On these public marketplace routes an invalid or revoked key is ignored silently — you get a 200 and the anonymous allowance, with no error. To confirm a key works, call an authenticated route such as GET /shipping-address and check for a 200.

To request a key, email support@collectorcrypt.com and say which capabilities you need.

## Errors​

Error bodies are not uniform. Always branch on the HTTP status, never on the presence of a field.

{ "statusCode": 400, "message": "Card not found", "error": "Bad Request" }
{ "statusCode": 400, "message": "Invalid request." }
{ "statusCode": 429, "message": "Too many requests — broadcasts. Retry in 60s.", "retryAfter": 60 }

message is always a string. When validation fails it is a string containing JSON — parse it to read the field name.

Status
Meaning

400

Bad input, or the chain rejected the build.

403

Not permitted for this wallet.

404

Asset, listing or offer not found.

409

State changed under you — refresh and retry.

429

Rate limited. Read retryAfter.

503

Temporary. Retry with backoff.

Send a non-empty User-Agent. A request without one is refused at the edge and never reaches the API.

Need help? support@collectorcrypt.com

Previous

Program Documentation

Next

Gacha

- Base URLs

- Two request styles

- List an asset

- Buy an asset

- Buy with your own token

- Make an offer

- Accept an offer

- Broadcast

- Browse listings

- Read one card

- Read offers on a card

- Rate limits
- Using an API key

- Errors

Marketplace

- Marketplace

Gacha Machine

- Play

eBay Tools

- Bid

Community

- Discord

- X

Copyright © 2026 Collector Crypt, Inc. Built with Docusaurus.
