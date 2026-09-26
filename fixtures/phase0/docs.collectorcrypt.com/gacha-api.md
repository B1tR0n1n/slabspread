---
url: https://docs.collectorcrypt.com/gacha/api
fetched_at: 2026-09-26T00:22:44Z
status: 200
---



# Gacha Machine API Documentation

🎮 Demo Repository: Check out the Gacha Starter Demo for a working example implementation.

## Overview​

The gacha machine API allows users to purchase mystery packs containing NFTs, open them to receive random NFTs, and optionally sell them back for USDC. This guide covers the standard $50 pack flow.

## Devnet USDC Faucet​

Use this faucet to get the USDC token used on devnet:
https://spl-token-faucet.com/?token-name=USDC-Dev

## Devnet​

You can see all of the API calls in action on the live devnet site:
https://dev-gacha.collectorcrypt.com

## 🔐 Authentication​

Send x-api-key on every request.

It is not an access gate on the play endpoints. A missing or invalid key is not rejected — the
request is simply treated as unauthenticated and your memo prefix falls back to cc-, so those
packs are not attributable to you and slug will not find them. A typo therefore fails silently
rather than erroring. The routes that do hard-fail with 401 on a missing or invalid key are
/api/v1/machines and /api/v1/stock.

### Why It Matters​

- Tags your transactions with a memo prefix unique to your key.

- Scopes /api/v1/* and your private machines to your key.

- Lets you filter all pack/send/buyback activity by your key using the slug query parameter.

### Example Header​

curl -X POST "https://gacha.collectorcrypt.com/api/generatePack" \
 -H "Content-Type: application/json" \
 -H "x-api-key: API_KEY" \
 -d '{
 "playerAddress": "HWPRgtDGpBm8mByTGS57BWCsijMo53qPPSbskWDukfTc"
 }'

## Endpoints​

Transactions can be submitted directly to the blockchain after they've been signed.

### Generate Pack - /api/generatePack​

Creates a transaction for purchasing a pack. The user needs to sign this transaction to begin the purchase. Generates a partially signed transaction that transfers 50 USDC from the player to the gacha wallet. Returns a unique memo identifier and the transaction that needs to be signed by the player.

Method: POST

Request Body:

{
 "playerAddress": "wallet_public_key",
 "packType": "pokemon_50", // optional, defaults to "pokemon_50"; use "pokemon_250" for legendary packs
 "turbo": true, // optional; when true, Common wins are auto-sold during openPack
 "altPlayerAddress": "wallet_public_key", // optional; the won card is sent to this wallet instead of playerAddress
 "altFundsRecipient": "wallet_public_key" // optional, turbo only; the auto-sell USDC is sent here instead of the card recipient
}

Response:

{
 "memo": "slug-uuid",
 "transaction": "base64_encoded_transaction"
}

Error Responses:

- 400: Invalid request body, player address, alt player address, or alt funds recipient

- 403: Player address, alt player address, or alt funds recipient is blocked

- 500: Machine error — the details field gives the cause:

- Machine is off balance — pool expected value is temporarily above the cap; retry shortly or try another machine

- Machine is empty (non-turbo) / Machine is low (turbo) — a prize tier is low on inventory

- Machine is off — machine toggled off or emergency stop active

- 429: Backlog guard — Too many pending packs. Complete a purchase to continue. (more than 50
generatePack calls in 10 minutes with none of them paid for), or Too many open packs (more
than 30 paid-but-unopened non-turbo packs for this wallet and pack type in the last 2 hours).
Both clear as soon as the outstanding packs are paid for or opened. Turbo packs are exempt from
the second guard.

- 503: Machine has too many packs currently open (retry shortly)

Note: turbo mode will automatically process a buyback for Common wins when calling /api/openPack.

Funds split (turbo only): by default the auto-sell USDC and any non-Common card both go to altPlayerAddress (or playerAddress if it's unset). Provide altFundsRecipient to send the auto-sell USDC to a separate address while non-Common cards still go to altPlayerAddress. Recall that in turbo a given pack pays out either USDC (Common, auto-sold) or a card (non-Common) — never both — so altFundsRecipient only affects Common wins. It is ignored for non-turbo packs.

### Generate Yolo Packs - /api/generateYoloPacks​

Creates multiple transactions for purchasing multiple packs at once. Each pack gets its own transaction and memo that needs to be signed individually by the player.

Method: POST

Request Body:

{
 "count": 2,
 "packType": "pokemon_50",
 "playerAddress": "5Kp9FbQ2oEKt6XnEvbovsnkpewW3wm9bg4ff3c3hAPbt",
 "turbo": true, // optional; applies to all generated packs, auto-sells Common wins during openPack
 "altPlayerAddress": "wallet_public_key", // optional; the won NFT is sent to this wallet instead of playerAddress
 "altFundsRecipient": "wallet_public_key" // optional, turbo only; auto-sell USDC for Common wins is sent here instead of the NFT recipient (applies to every pack in the batch)
}

Response:

{
 "yoloId": "uuid",
 "count": 2,
 "transactions": [
 {
 "memo": "slug-uuid-1",
 "transaction": "base64_encoded_transaction_1"
 },
 {
 "memo": "slug-uuid-2",
 "transaction": "base64_encoded_transaction_2"
 }
 ]
}

Error Responses:

- 400: Invalid request body, player address, or count (must be between 1 and 100)

- 403: Player, alt player, or alt funds recipient address is blocked

- 500: Machine error — the details field gives the cause:

- Machine is off balance — pool expected value is temporarily above the cap; retry shortly or try another machine

- Machine is low — a prize tier is low on inventory

- Machine is off — machine toggled off or emergency stop active

What it does:
Generates multiple pack purchase transactions at once (up to 100). Each transaction must be signed separately using /api/submitTransaction, then each memo can be used with /api/openPack to receive the NFTs.

Note: When turbo is true, all generated packs will auto-sell Common wins during /api/openPack.

### Open Pack - /api/openPack​

Opens a purchased pack and sends an NFT to the player. The VRF roll picks the prize tier from the machine's configured rarity weights (each machine has its own odds, so call /api/machines to read the live odds per machine), then a provable selection picks the card within that tier — see Provable Fairness (VRF). The NFT is transferred to the player and the metadata returned. For turbo mode with low-tier wins, automatically processes a buyback.

Method: POST

Request Body:

{
 "memo": "slug-uuid-string"
}

Response (Success):

{
 "success": true,
 "transactionSignature": "nft_transfer_transaction_hash",
 "nft_address": "nft_mint_address",
 "nftWon": {
 "content": {
 "metadata": {
 "name": "Card Name",
 "description": "Card Description",
 "attributes": [...]
 }
 }
 },
 "points": 0,
 "roll": 12345678,
 "rarity": "Epic"
}

rarity is one of "Epic", "Rare", "Uncommon", or "Common".

Response (Turbo Mode Buyback):
When turbo mode is enabled and the pack rolls Common, the NFT is auto-sold for USDC and the response includes additional fields:

{
 "success": true,
 "transactionSignature": "nft_transfer_transaction_hash",
 "nft_address": "nft_mint_address",
 "nftWon": { /* NFT metadata */ },
 "points": 0,
 "code": "TURBO_MODE_BUYBACK",
 "buybackAmount": 42500000,
 "roll": 87654321,
 "rarity": "Common"
}

buybackAmount is the auto-sell payout in USDC base units (6 decimals; e.g. 42500000 = 42.5 USDC). The USDC is sent to altFundsRecipient if it was supplied at /api/generatePack (or /api/generateYoloPacks), otherwise to altPlayerAddress, otherwise to playerAddress.

Response (Waiting for Payment):

{
 "success": true,
 "code": "WAITING_FOR_WEBHOOK",
 "memo": "slug-uuid-string"
}

Response (Already Opened):
Returns success, transactionSignature, nft_address, nftWon, points and rarity, plus
code: "TURBO_MODE_BUYBACK" for any turbo pack and buybackAmount when that turbo pack won a
Common and its buyback row still exists. Two differences from the first response: roll is not
included, and buybackAmount comes back as a string. Read the roll from /api/pack/status.

Deadline: an unopened pack must be opened within 2 hours of /api/generatePack. After that
/api/openPack returns 400 No spin transaction found for memo permanently, and a paid-but-unopened
pack becomes eligible for auto-refund from 2h10m old, processed on the next hourly refund run. This
applies only to packs that were never opened — a memo that already has an award keeps returning that
award indefinitely.

Error Responses:

- 400: No spin transaction found (unknown memo, or the pack is past the 2-hour deadline) or no NFTs available

- 403: Recipient address is blocked

- 404: No on-chain purchase transaction found for this memo (not yet confirmed)

- 500: Machine empty or processing error

### Buyback - /api/buyback​

Generates a transaction to sell an NFT back for a percentage of its insured value in USDC. Verifies the NFT was sent out by the gacha within the last 72 hours and has no confirmed buyback yet, then creates a transaction that transfers the NFT back to the original prize wallet and sends USDC to the player (or to altRecipient if provided). Eligibility is NFT-scoped — the caller does not have to be the original winner, though the seller must still sign the transfer. The transaction needs to be signed by the player and submitted to the blockchain.

Method: POST

Request Body:

{
 "playerAddress": "wallet_public_key",
 "nftAddress": "nft_mint_address",
 "altRecipient": "wallet_public_key" // optional; if provided, USDC refund is sent here instead of playerAddress
}

Response:

{
 "success": true,
 "serializedTransaction": "base64_encoded_transaction",
 "refundAmount": 42500000,
 "memo": "original-memo-string"
}

Error Responses:

- 400: Invalid addresses, NFT not found, or outside 72-hour buyback window

- 403: Player or alt recipient address is blocked

- 500: Transaction building failed

### Buyback Check - /api/buyback/check​

Checks if an NFT buyback has completed.

Method: GET

Query Parameters:

- memo (required): The memo from the original pack purchase

Example Request:

GET /api/buyback/check?memo=953cc94e-fd51-4f5f-bbcc-5a35faf7df65

Response (Buyback Exists):

{
 "exists": true,
 "playerWallet": "GfFAJnHnSgP7C2FQZLz6ogpdTV6Y7259f83qFFm9wxKm",
 "nft": "H9ZXYkudxn6qhyp5S25jm5SrA8Vnu8naSfvymm9TptLA",
 "transactionSignature": "3Dq2kH65vqEzpBKczyDLzNYS8sXmtS5GS9MYTwjVaPM4tqVxjtPGnQG4mKpSPa5iTzqomhFgo9nYs3grRNPp68Fh",
 "buybackAmount": "90000",
 "createdAt": "2025-05-26T17:32:33.588Z",
 "status": "complete"
}

status is "complete" when the buyback has been confirmed via webhook, or empty string "" when still pending.

Response (Buyback Not Found):

{
 "exists": false,
 "message": "No buyback transaction found for this memo"
}

Error Responses:

- 400: Missing memo parameter

- 500: Database query failed

What it does:
Checks if a buyback transaction has been completed for the given memo. Returns the buyback details if it exists, or indicates that no buyback was found.

### Buyback Available - /api/buyback/available​

Checks whether an NFT has an eligible buyback and returns the USDC amount that would be refunded. Lean read-only lookup — no transaction is built. Eligibility matches the same rules as /api/buyback: the NFT must have been sent from the gacha within the last 72 hours and there must be no confirmed buyback for it yet.

Method: GET

Query Parameters:

- nft (required): NFT mint address

- wallet (optional): wallet public key; ignored (eligibility is NFT-scoped)

Example Request:

GET /api/buyback/available?nft=H9ZXYkudxn6qhyp5S25jm5SrA8Vnu8naSfvymm9TptLA

Response (Available):

{
 "available": true,
 "amount": 42500000
}

amount is in USDC base units (6 decimals), already adjusted for the pack type's buyback
percentage. It is clamped in dollars before scaling, to a floor of 0.01 USDC and a cap of
280,000 USDC — the same bounds /api/buyback applies.

Response (Not Available):

{
 "available": false
}

Error Responses:

- 400: Missing nft parameter

- 500: Database query failed

### Pack Status - /api/pack/status​

Returns everything on record for a single memo across the three transaction tables: the pack purchase, the NFT send, and any buyback. Read-only lookup keyed entirely by the memo.

Method: GET

Query Parameters:

- memo (required): The memo from the original pack purchase

Example Request:

GET /api/pack/status?memo=953cc94e-fd51-4f5f-bbcc-5a35faf7df65

Response:

{
 "memo": "953cc94e-fd51-4f5f-bbcc-5a35faf7df65",
 "pack": {
 "wallet": "GfFAJnHnSgP7C2FQZLz6ogpdTV6Y7259f83qFFm9wxKm",
 "transaction_signature": "5Nf9kZ...purchaseSignature",
 "created_at": "2025-05-26T17:30:00.000Z",
 "status": "confirmed",
 "webhook_received": true,
 "refunded": null,
 "refund_transaction_signature": null,
 "turbo_mode": false,
 "pack_type": "pokemon_50",
 "token_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
 },
 "send": {
 "from_wallet": "prize_wallet_public_key",
 "to_wallet": "GfFAJnHnSgP7C2FQZLz6ogpdTV6Y7259f83qFFm9wxKm",
 "nft_address": "H9ZXYkudxn6qhyp5S25jm5SrA8Vnu8naSfvymm9TptLA",
 "transaction_signature": "3Dq2kH65vqEzpBKczyDLzNYS8sXmtS5GS9MYTwjVaPM4tqVxjtPGnQG4mKpSPa5iTzqomhFgo9nYs3grRNPp68Fh",
 "created_at": "2025-05-26T17:31:00.000Z",
 "status": "confirmed",
 "webhook_sent": true,
 "points": 0,
 "insured_value": 50,
 "prize_tier": 4,
 "vrf_proof": "vrf_proof_string"
 },
 "buyback": [
 {
 "user_wallet": "GfFAJnHnSgP7C2FQZLz6ogpdTV6Y7259f83qFFm9wxKm",
 "refund_amount": "42500000",
 "created_at": "2025-05-26T17:32:33.588Z",
 "webhook_confirmed": true,
 "transaction_signature": "3Dq2kH65vqEzpBKczyDLzNYS8sXmtS5GS9MYTwjVaPM4tqVxjtPGnQG4mKpSPa5iTzqomhFgo9nYs3grRNPp68Fh",
 "status": "confirmed",
 "alt_recipient": null
 }
 ]
}

Status values. All three status fields are two-state: "confirmed" or null. There is no
"pending", "failed" or "refunded" value — failure and refund are expressed by other fields.

Field
"confirmed"
null

pack.status

Payment verified; the pack can be opened. Terminal — never reverts, including after a refund.

Pack reserved but payment not yet seen on-chain. Stays null forever for an abandoned checkout. Always moves in lockstep with webhook_received, so either field answers "is it paid".

send.status

The NFT transfer to the winner confirmed on-chain.

Either the award row is still a placeholder (transaction_signature is null), or it is a turbo pack (transaction_signature is "turbomode"), which is never stamped even though it is fully delivered. Treat a send as delivered when status === "confirmed" or webhook_sent === true or transaction_signature === "turbomode".

buyback[].status

The buyback settled: the card returned and the refund was paid.

Quote issued / transaction submitted, not yet settled. A buyback whose transaction never landed is deleted rather than marked failed, so null on an old row means an unused quote. Treat as settled when status === "confirmed" or webhook_confirmed === true.

Do not confuse these with /api/buyback/check, which returns its own derived status of
"complete" or "". That field does not appear here.

Field notes:

- pack and send are the single row for that memo (or null if none exists yet).

- buyback is an array — a memo can have more than one buyback attempt — ordered newest first; [] when there are none.

- webhook_received (pack), webhook_sent (send), and webhook_confirmed (buyback) indicate the on-chain transaction was confirmed via webhook.

- refunded is true when the pack was refunded, otherwise null; the refund's signature is in refund_transaction_signature.

- refund_amount is returned as a string in USDC base units (6 decimals).

- prize_tier values: 1 = Epic, 2 = Rare, 3 = Uncommon, 4 = Common.

Error Responses:

- 400: Missing memo parameter

- 500: Database query failed

### Get Status - /api/status​

Checks the current operational status of all gacha machines.

Method: GET

Request: No parameters required

Response:

{
 "machineStatus": "running",
 "legendaryStatus": "open",
 "eliteStatus": "open",
 "freePacksStatus": "closed",
 "sportsStatus": "closed",
 "gachas": [
 {
 "code": "pokemon_50",
 "name": "Elite Pack",
 "price": 50,
 "status": "open",
 "isOpen": true
 }
 ]
}

machineStatus values:

- "running" — no emergency stop active

- "stopped" — emergency stop active, no purchases possible

status / individual machine values:

- "open" — machine is accepting purchases

- "closed" — machine is temporarily closed

### Get Stock - /api/stock​

Returns current NFT inventory counts by rarity for each machine.

Method: GET

Response:

{
 "elite": { "common": 34, "uncommon": 42, "rare": 86, "epic": 124 },
 "legendary": { "common": 98, "uncommon": 85, "rare": 34, "epic": 24 },
 "sports": { "common": 10, "uncommon": 5, "rare": 3, "epic": 1 },
 "pokemon_50": { "common": 34, "uncommon": 42, "rare": 86, "epic": 124 },
 "pokemon_250": { "common": 98, "uncommon": 85, "rare": 34, "epic": 24 }
}

The response includes both legacy named keys (elite, legendary, sports) and dynamic per-code keys for all machines.

### Get Machines - /api/machines​

Returns full configuration and live stock for every machine. This is the recommended single call to build a machine-picker UI — it includes odds, pricing, and current inventory all at once.

Method: GET

Response:

{
 "machines": [
 {
 "code": "pokemon_50",
 "name": "Elite Pack",
 "shortName": "Elite",
 "image": "image_url",
 "thumbnailUrl": "thumbnail_url",
 "videoSrc": "video_url",
 "videoHevc": "hevc_video_url",
 "videoNobgWeb": "transparent_video_url_webm",
 "videoNobgIos": "transparent_video_url_hevc_mp4",
 "videoNobgAndroid": "transparent_video_url_android",
 "imageNobg": "transparent_image_url",
 "public": true,
 "price": 50,
 "contains": 1,
 "instantBuyback": 85,
 "freeSpins": false,
 "turboMode": false,
 "pointsMultiplier": 1,
 "odds": {
 "epic": 0.01,
 "rare": 0.04,
 "uncommon": 0.15,
 "common": 0.80
 },
 "tierRanges": {
 "common": { "start": 0, "end": 25 },
 "uncommon": { "start": 25, "end": 75 },
 "rare": { "start": 75, "end": 200 },
 "epic": { "start": 200, "end": 99999 }
 },
 "stock": {
 "common": 34,
 "uncommon": 42,
 "rare": 86,
 "epic": 124
 },
 "ev": 51.2
 }
 ]
}

Field notes:

- ev (number or null): the machine's current rarity-weighted expected insured value — each rarity tier's average insured value weighted by its odds — recomputed periodically by a background job. It is null, never 0, until it has first been calculated (and also if the cache read fails), so guard before doing arithmetic on it.

- contains (number): how many cards the pack contains — 1 on every machine today, and 0 if a machine leaves it unset.

- thumbnailUrl, videoSrc, videoHevc (string): always set. A machine without an uploaded asset falls back to the bundled path (/<code>.png, /<code>.webm, /<code>.hevc.mp4).

- videoNobgWeb, videoNobgIos, videoNobgAndroid, imageNobg (string or null): the transparent-background (alpha) assets — one video encode per platform (Web = VP9-alpha webm for Chrome/Firefox, Ios = HEVC-alpha mp4 for Safari and iOS, Android = the Android app's encode) plus the alpha still image. There is no bundled fallback, so null means the machine has no asset for that platform. These replace the single videoNobg field.

### Get NFTs - /api/getNfts​

Retrieves NFTs available in the gacha machine filtered by code and optionally by rarity.

Method: GET

Query Parameters:

- code (optional): The pack/collection code (e.g., "pokemon_50"). Defaults to pokemon_50.

- rarity (optional): Filter by rarity tier - "common", "uncommon", "rare", or "epic"

- limit (optional): how many NFTs to return. Defaults to 40, maximum 100.

- cursor (optional): opaque position token. Omit it for the first page, then pass back the
nextCursor from the previous response.

Results are ordered by insured value descending, then mint address ascending.

Example Requests:

GET /api/getNfts?code=pokemon_50
GET /api/getNfts?code=pokemon_50&rarity=epic

# first page
GET /api/getNfts?code=pokemon_50&limit=50
# every page after it — feed back nextCursor
GET /api/getNfts?code=pokemon_50&limit=50&cursor=630_3ymjGXyc3k2RtjmTMxNWaMNNPSAU5vst2LiFamYUAmKj

Response:

{
 "nfts": [
 {
 "nft_address": "nft_mint_address",
 "name": "Card Name",
 "description": "Card Description",
 "rarity": "epic",
 "attributes": [...],
 "image": "image_url",
 "insured_value": 250
 }
 ],
 "hasMore": true,
 "limit": 50,
 "nextCursor": "630_3ymjGXyc3k2RtjmTMxNWaMNNPSAU5vst2LiFamYUAmKj"
}

Walking a whole pool: request the first page, then keep passing nextCursor back as cursor
until hasMore is false. Keep code, rarity and limit the same across the walk.

- nextCursor is an opaque token — pass it back unchanged. Do not parse or construct it yourself;
its format is not part of the contract and may change.

- hasMore is true when another page is available. When it is false, nextCursor is null
and you have reached the end.

- The cursor resumes exactly after the last row you were given, so pages never overlap or skip
even while inventory changes underneath you, and every page costs the same no matter how deep
you go.

Error Responses:

- 500: Database query failed

### Submit Transaction - /api/submitTransaction​

Submits a signed transaction to the Solana blockchain.

Method: POST

Request Body:

{
 "signedTransaction": "base64_encoded_signed_transaction"
}

Response (Success):

{
 "success": true,
 "signature": "transaction_signature_hash",
 "confirmationStatus": "confirmed"
}

confirmationStatus is one of "confirmed", "finalized", or "submitted" (the last one means the transaction was sent but not yet confirmed within the valid block height window).

Example Request:

curl -X POST "/api/submitTransaction" \
 -H "Content-Type: application/json" \
 -H "x-api-key: API_KEY" \
 -d '{
 "signedTransaction": "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAQABBqF55bPp..."
 }'

Error Responses:

- 400: Missing or invalid signed transaction

- 403: Transaction not signed by the gacha wallet

- 500: Transaction submission failed or blockchain error

What it does:
Takes a fully signed transaction (from /api/generatePack or /api/buyback after user signing) and submits it to the Solana blockchain. Returns the transaction signature for tracking.

### Generate Gift - /api/generateGift​

Creates a transaction to gift packs to another wallet. The sender pays for the packs; after submitting the signed transaction, the receiver will have gifted packs available to open on gacha.collectorcrypt.com.

Method: POST

Request Body:

{
 "sender": "HWPRgtDGpBm8mByTGS57BWCsijMo53qPPSbskWDukfTc",
 "receiver": "daxsSgG4iPvhxWr2jrY76HKtRSjWjQLFveKHdmZKJFc",
 "packType": "pokemon_50",
 "count": 1 // optional; must be an integer between 1 and 20, defaults to 1
}

Response:

{
 "giftId": 2,
 "memo": "cc-86646f0c-2a61-4a0a-89af-495d266684c3",
 "transaction": "base64_encoded_transaction",
 "totalCost": 50,
 "count": 1,
 "packType": "pokemon_50"
}

Note on the memo: The returned memo is prefixed with your API-key slug, or with cc- when no x-api-key is sent (e.g. cc-<uuid>) — it is not prefixed gift-. The gift marker is only appended to the on-chain memo (as a :gift suffix) and never appears in the memo field returned by this endpoint.

Example Request:

curl -X POST "https://gacha.collectorcrypt.com/api/generateGift" \
 -H "Content-Type: application/json" \
 -d '{
 "sender":"HWPRgtDGpBm8mByTGS57BWCsijMo53qPPSbskWDukfTc",
 "receiver":"daxsSgG4iPvhxWr2jrY76HKtRSjWjQLFveKHdmZKJFc",
 "packType":"pokemon_50",
 "count":1
 }'

What it does:
Returns a transaction. Sign it, then POST it to /api/submitTransaction. Once confirmed, the receiver will have gifted packs to open on gacha.collectorcrypt.com.

### Get Gifted - /api/getGifted​

Fetches gift history for a wallet — both sent and received gift packs, totals grouped by pack type, and a per-pack opening history for received gifts.

Method: GET

Query Parameters:

- wallet (required): wallet public key

Example Request:

GET /api/getGifted?wallet=HWPRgtDGpBm8mByTGS57BWCsijMo53qPPSbskWDukfTc

Response:

{
 "wallet": "HWPRgtDGpBm8mByTGS57BWCsijMo53qPPSbskWDukfTc",
 "sent": [
 {
 "id": 1,
 "memo": "cc-86646f0c-2a61-4a0a-89af-495d266684c3",
 "sender": "wallet_public_key",
 "receiver": "wallet_public_key",
 "pack_type": "pokemon_50",
 "count": 1,
 "cost": 50,
 "webhook_confirmed": true,
 "status": "confirmed",
 "transaction_signature": "tx_signature",
 "created_at": "2025-01-01T00:00:00.000Z"
 }
 ],
 "received": [ /* same shape as sent */ ],
 "totals": {
 "sent": [
 { "pack_type": "pokemon_50", "count": 5, "cost": 250 }
 ],
 "received": [
 { "pack_type": "pokemon_50", "count": 3, "cost": 150 }
 ]
 },
 "perpack": [
 {
 "pack_opened_id": 123,
 "purchase_type": "gift",
 "purchase_id": 1,
 "wallet": "receiver_wallet",
 "pack_type": "pokemon_50",
 "opened_date": "2025-01-02T00:00:00.000Z",
 "purchase_signature": "gift_tx_signature",
 "send_nft_txn": "send_nft_signature",
 "memo": "cc-uuid",
 "insured_value": 50,
 "pack_quantity": 1
 }
 ]
}

The perpack array tracks each individual gift pack opening for the receiver wallet.

### Purchased Packs Summary - /api/purchasedPacks​

Returns pack counts for a wallet (purchased vs gifted, used vs unused) grouped by packType. The response contains one entry per configured pack type — derived dynamically from the active machines — so the keys returned depend on which machines exist, not only the two shown below.

Method: GET

Query Parameters:

- wallet (required): wallet public key

Example Request:

GET /api/purchasedPacks?wallet=daxsSgG4iPvhxWr2jrY76HKtRSjWjQLFveKHdmZKJFc

Response:

{
 "pokemon_50": {
 "purchased": 0,
 "gifted": 2,
 "used_purchased": 0,
 "used_gifted": 1
 },
 "pokemon_250": {
 "purchased": 0,
 "gifted": 0,
 "used_purchased": 0,
 "used_gifted": 0
 }
}

### Generate Purchased Pack Challenge - /api/generatePurchasedPack​

Generates a message-to-sign challenge for opening a purchased/gifted pack.

#### Gift opening flow​

- Call /api/generatePurchasedPack to get a nonce + messageToSign.

- Have the user sign messageToSign with their wallet.

- Call /api/usePurchasedPack:

- non-ledger: { signedMessage, signature, publicKey, nonce, packType }

- ledger: { ledger: true, transactionSignature, publicKey, nonce, packType, turbo }
to receive a memo.

- Call /api/openPack with the memo to send the NFT.

#### Reference UI (dev)​

- https://dev-gacha.collectorcrypt.com/user/gifts

- https://dev-gacha.collectorcrypt.com

Method: POST

Request Body:

{
 "publicKey": "daxsSgG4iPvhxWr2jrY76HKtRSjWjQLFveKHdmZKJFc",
 "packType": "pokemon_50",
 "ledger": true
}

- ledger (optional, default: false): when true, the server returns a Ledger-compatible challenge flow.

Response:

{
 "success": true,
 "nonce": "23a8bb98-d975-454f-a410-28e072247afa",
 "expiry": "2026-02-25T20:48:42.317Z",
 "messageToSign": "Open my purchased pokemon_50 pack!\n\nNonce:23a8bb98-d975-454f-a410-28e072247afa",
 "ledger": true
}

### Use Purchased Pack - /api/usePurchasedPack​

Consumes a purchased/gifted pack after the wallet signs the challenge message. Returns a memo you can open like normal (via /api/openPack).

Method: POST

Request Body:

{
 "ledger": true,
 "nonce": "7b24cb5b-f3f6-4f6d-b039-6d1bc05b6060",
 "packType": "pokemon_50",
 "publicKey": "HWPRgtDGpBm8mByTGS57BWCsijMo53qPPSbskWDukfTc",
 "transactionSignature": "signed_transaction",
 "turbo": true
}

Request Body (non-ledger):

{
 "signedMessage": "Open my purchased pokemon_50 pack!\n\nNonce:89c3e1b3-9d50-4cdd-95e6-444ef3fd68e4",
 "signature": "base58_signature",
 "publicKey": "daxsSgG4iPvhxWr2jrY76HKtRSjWjQLFveKHdmZKJFc",
 "turbo": false,
 "packType": "pokemon_50",
 "nonce": "89c3e1b3-9d50-4cdd-95e6-444ef3fd68e4"
}

Response:

{
 "success": true,
 "memo": "cc-83f67f2e-7b53-45fd-9d81-ab4f8243475c",
 "packsRemaining": 0
}

### Get Recent Winners - /api/getRecentWinners​

Returns the most recent winners for a single machine, newest first (up to 5).

Method: GET

Query Parameters:

- packType (optional): The machine/pack code (e.g. pokemon_50, pokemon_250). Defaults to 50.

Example Request:

GET /api/getRecentWinners?packType=pokemon_50

Response:

{
 "success": true,
 "data": [
 {
 "winner": "wallet_address",
 "prize_tier": 1,
 "nft": {
 "content": { "metadata": { "name": "Card Name", "attributes": [...] } },
 "image": "https://..."
 },
 "timestamp": "2024-01-01T12:00:00Z",
 "insuredValue": 250
 }
 ]
}

The best available image URL is merged onto the nft object as image. prize_tier values: 1 = Epic, 2 = Rare, 3 = Uncommon, 4 = Common.

Error Responses:

- 200 with data: [] when that pack type has no winners yet — there is no 404 for an empty or
unknown packType.

- 500: Database query failed

### Get All Winners - /api/getAllWinners​

Retrieves recent winners from the gacha machine.

Method: GET

Query Parameters:

- timestamp (optional): ISO 8601 timestamp to get winners after this time. If omitted, returns the latest winners with no cutoff.

- slug (optional): Filter by memo prefix (e.g., "me")

- epic (optional): Set to "true" to get only epic/legendary wins

- packType (optional): Filter by pack type (e.g., "pokemon_50", "pokemon_250")

- count (optional): Number of results to return (default: 10, max: 200)

Example Request:

GET /api/getAllWinners?timestamp=2024-01-01T00:00:00Z&slug=me&epic=false&packType=pokemon_50&count=20

Response:

{
 "success": true,
 "data": [
 {
 "winner": "wallet_address",
 "nft_address": "nft_mint_address",
 "nft": {
 "content": {
 "metadata": {
 "name": "Card Name",
 "attributes": [...]
 }
 }
 },
 "insuredValue": 250,
 "created_at": "2024-01-01T12:00:00Z",
 "memo_slug": "me",
 "pack_type": "pokemon_50",
 "prize_tier": 1
 }
 ]
}

prize_tier values: 1 = Epic, 2 = Rare, 3 = Uncommon, 4 = Common.

Error Responses:

- 400: Invalid timestamp

- 500: Database query failed

What it does:
Returns a list of recent NFT winners optionally filtered by timestamp, memo prefix (slug), rarity (epic), and pack type. Results are ordered by most recent first.

### Get Winners (Paginated) - /api/getWinners​

Cursor-paginates through all winners for a single memo slug, newest first. Use this instead of /api/getAllWinners when you need to walk a partner's entire win history page by page — it uses keyset pagination, so every page is fast regardless of how deep you go.

Each winner has the same shape as /api/getAllWinners; the response just adds the pagination fields nextCursor and hasMore.

Method: GET

Query Parameters:

- slug (required): The memo slug to fetch winners for (your API key's slug).

- cursor (optional): The nextCursor returned by the previous page. Omit it to fetch the first (most recent) page.

- count (optional): Page size (default: 50, max: 200).

Example Request (first page):

GET /api/getWinners?slug=me&count=50

Example Request (next page):

GET /api/getWinners?slug=me&count=50&cursor=MjAyNS0wMS0wMVQxMjowMDowMC4wMDAwMDBafDEyMzQ1

Response:

{
 "success": true,
 "data": [
 {
 "winner": "wallet_address",
 "nft_address": "nft_mint_address",
 "nft": {
 "content": {
 "metadata": {
 "name": "Card Name",
 "attributes": [...]
 }
 }
 },
 "insuredValue": 250,
 "created_at": "2024-01-01T12:00:00Z",
 "memo_slug": "me",
 "pack_type": "pokemon_50",
 "prize_tier": 1
 }
 ],
 "nextCursor": "MjAyNC0wMS0wMVQxMjowMDowMC4wMDAwMDBafDEyMzQ1",
 "hasMore": true
}

Pagination:

- nextCursor is an opaque token — pass it back as the cursor parameter to fetch the next page. Do not parse or construct it yourself.

- hasMore is true when another page is available. When hasMore is false, nextCursor is null and you've reached the end.

- Results are ordered most recent first and remain stable as new winners arrive, so you won't skip or double-count rows while paginating.

prize_tier values: 1 = Epic, 2 = Rare, 3 = Uncommon, 4 = Common.

Error Responses:

- 400: Missing slug or invalid cursor

- 500: Database query failed

### Live Winners Token - /api/ably/token​

Issues a short-lived Ably token so you can subscribe to live wins in realtime — the same feed that powers the Recent Winners section on the gacha site. Use this instead of polling /api/getAllWinners when you want wins to appear in your UI the moment they happen.

Any valid API key can subscribe to all winner channels; filter by gachaCode (or memo) on your end to show only the machines you care about.

Method: GET

Headers:

- x-api-key (required): your API key.

Example Request:

curl "https://gacha.collectorcrypt.com/api/ably/token" \
 -H "x-api-key: API_KEY"

Response: an Ably TokenRequest object. You don't parse this yourself — hand it straight to the Ably client (see below). It is scoped to subscribe-only on the winner channels and expires after 1 hour; the Ably client auto-renews by re-calling this endpoint.

Usage (browser / Node):

import * as Ably from "ably";

const ably = new Ably.Realtime({
 authUrl: "https://gacha.collectorcrypt.com/api/ably/token",
 authHeaders: { "x-api-key": "API_KEY" },
});

// One channel per pack type, e.g. recent-winners-pokemon_50
ably.channels.get("recent-winners-pokemon_50")
 .subscribe("new-winner", (msg) => {
 console.log(msg.data); // see payload below
 });

The channel name is recent-winners-{packType} and the event name is new-winner. Each message's data is:

{
 "winner": "wallet_address",
 "prizeWallet": "wallet_address",
 "nft": {
 "address": "nft_mint_address",
 "name": "Card Name",
 "image": "https://...",
 "certid": "1234567",
 "gradingCompany": "PSA",
 "grade": "10"
 },
 "timestamp": "2024-01-01T12:00:00Z",
 "insuredValue": 250,
 "weightedInsuredValue": 51.2,
 "gachaCode": "pokemon_50",
 "prizeTier": 1,
 "memo": "me-abc123"
}

prizeTier values: 1 = Epic, 2 = Rare, 3 = Uncommon, 4 = Common.

memo is the unique pack identifier returned by /api/generatePack — use its slug prefix (e.g. me) to filter to your own machines, and the full value to attribute a win to the specific player/pack you created.

Error Responses:

- This endpoint does not 401. Without a recognised x-api-key — or with a key whose slug is empty —
it returns a token scoped to the first-party channel set instead of your partner scope, so a typo
fails silently. If the channels you expect are missing, check that your key is live.

What it does:
Mints a scoped Ably token tied to your key. Subscribe to the recent-winners-{packType} channels and react to new-winner events to render wins live.

## Flow Summary​

- Call /api/generatePack to create a purchase transaction

- Sign the transaction with your wallet

- Submit signed transaction via /api/submitTransaction

- Wait for confirmation

- Call /api/openPack with the memo to receive the NFT

- (Optional) Call /api/buyback within 72 hours to sell the NFT back for USDC

- Use /api/getAllWinners to display recent winners in your UI

## Partner Operations​

Everything above is about playing a machine. This section is about operating one: seeing your
machines' live state, and — if your key is enabled for it — building your own or attaching a fee to
one of ours.

Three independent capabilities are set per API key. All are off by default; ask us to enable them.

Capability
What it allows

can_adopt

Attach a per-pack fee to a CollectorCrypt machine (see Adopting a machine)

can_build_machines

Create and edit your own machines on our shared inventory

can_edit_hashlists

Curate which cards are active in machines you operate

### Fixed EV vs Dynamic EV​

Every machine is one of two kinds, and it changes what "odds" means:

- Fixed EV — the machine re-solves its odds on every pack so it delivers exactly its target
expected value. It moves probability between the uncommon and rare tiers only; the advertised
common (big-win) and epic (jackpot) chances never move. If the pool cannot reach the target, the
machine refuses the sale rather than paying out the wrong value — you'll see
503/500 Machine is off balance. The odds actually used are committed per pack before the roll
and are provable at /verify-selection/<memo>.

- Dynamic EV — the published odds are fixed and the expected value drifts inside a band. A
background job steers it by activating and deactivating cards.

A machine's floor is the cheapest EV its odds can reach on its current cards. It is set mostly by the
common tier, because that is where most of the probability mass sits.

### GET /api/v1/machines​

Your machines only, authenticated by x-api-key. Per machine: config, live status, the solved EV, the
achievable EV band, per-tier active stock, and whether it will sell right now.

Field
Meaning

code

The packType to pass to /api/generatePack

enabled

Machine toggled on

price, instantBuyback, tierRanges

Config

partnerFee

Your per-pack fee, if any

targetEv

The EV this machine aims to deliver

ev

The EV it will actually deliver right now (the dynamic solve)

evLow, evHigh

The cheapest and richest EV the odds can reach on current stock

reachable

Whether targetEv sits inside [evLow, evHigh]

stock

Active owned cards per tier

low

A tier is below its restock threshold

sells

enabled && ev in band && stocked — mirrors the /api/generatePack gates

If sells is false, /api/generatePack will refuse. Check reachable first: a Fixed EV machine
whose target is outside [evLow, evHigh] needs its target moved or its inventory changed.

### GET /api/v1/stock​

Per-tier active card counts for each of your machines, plus the low-stock flag. Cheaper than
/api/v1/machines when you only need availability.

### Adopting a machine​

With can_adopt, you can take one of our machines and attach a per-pack fee. You sell the same cards
from the same pool at the same price; your fee comes out of the expected value, so your players
receive exactly your fee less than ours. Nothing else about the machine changes.

your machine's EV = our machine's EV - your fee

Our machine's EV is the targetEv we set on it, shown per machine on the adoption screen. If we
later change it, your machine's EV follows within a minute; your fee does not change.

The fee is capped two ways, and the smaller wins:

- Policy — at most 10% of the pack price.

- Physical — the EV left over must still be at or above the pool's floor (evLow). A fee that
pushes the EV below what the cards can pay out would never sell, so it is rejected at setup.

So on a $50 pack with a $51 EV the policy cap is $5, but if that pool cannot pay out less than $47
the physical cap binds first at 51 − 47 = $4.00. The adoption screen shows the number you can
actually set.

Adopting creates a new machine code scoped to your key. It is private, starts disabled, and is
listed in /api/v1/machines like any other. Its price and fee are locked at creation so accrued fees
can never move. It has no inventory of its own — we stock the underlying pool.

### How fees accrue and pay out​

A fee is earned when the pack completes, i.e. the card was actually awarded. A completed pack is
non-refundable, so an earned fee cannot be clawed back — there is no maturity window.

Fees are tracked in µUSDC (1 USDC = 1,000,000) and paid to the treasury wallet on your account.
Solana and EVM packs both accrue; payouts settle in Solana USDC either way. Payouts are released by a
CollectorCrypt admin, not automatically.

Previous

VRF

Next

EVM API Docs

- Overview

- Devnet USDC Faucet

- Devnet

- 🔐 Authentication
- Why It Matters

- Example Header

- Endpoints
- Generate Pack - /api/generatePack

- Generate Yolo Packs - /api/generateYoloPacks

- Open Pack - /api/openPack

- Buyback - /api/buyback

- Buyback Check - /api/buyback/check

- Buyback Available - /api/buyback/available

- Pack Status - /api/pack/status

- Get Status - /api/status

- Get Stock - /api/stock

- Get Machines - /api/machines

- Get NFTs - /api/getNfts

- Submit Transaction - /api/submitTransaction

- Generate Gift - /api/generateGift

- Get Gifted - /api/getGifted

- Purchased Packs Summary - /api/purchasedPacks

- Generate Purchased Pack Challenge - /api/generatePurchasedPack

- Use Purchased Pack - /api/usePurchasedPack

- Get Recent Winners - /api/getRecentWinners

- Get All Winners - /api/getAllWinners

- Get Winners (Paginated) - /api/getWinners

- Live Winners Token - /api/ably/token

- Flow Summary

- Partner Operations
- Fixed EV vs Dynamic EV

- GET /api/v1/machines

- GET /api/v1/stock

- Adopting a machine

- How fees accrue and pay out

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

