---
url: https://docs.collectorcrypt.com/gacha/evm-api
fetched_at: 2026-09-26T00:22:44Z
status: 200
---



# Gacha EVM API Documentation

The EVM machine is the same gacha, paid in an ERC-20 stablecoin instead of Solana. You pay a
contract, the server rolls, and an ERC-721 card is minted to your wallet. You can sell it back to
the vault inside the buyback window.

Payment lanes. A chain accepts several tokens, and each is its own lane: you pick one when you
create the pack, and the buyback pays you back in that same token. Lanes never mix — a lane's
buyback float is its own balance. Read the lanes from GET /api/evm/chains (tokens) and pass one
as token to generatePack; omit it for the chain's default lane.

Machines, odds, and buyback percentages match the Solana machine — only the payment and the card
are EVM-native.

## Base URL​

API

https://dev-gacha.collectorcrypt.com

Payment tokens

One or more ERC-20 lanes per chain — read tokens from /api/evm/chains

Decimals

Per lane, never assumed. Read tokens[].decimals

## Chains — GET /api/evm/chains​

The machine is multichain. Ask which chains it serves rather than assuming one, and pass the
chainId you chose on every later call.

GET /api/evm/chains

Response:

{
 "success": true,
 "defaultChainId": 84532,
 "chains": [
 {
 "chainId": 84532,
 "chainKey": "base-sepolia",
 "name": "Base Sepolia",
 "nativeCurrency": "ETH",
 "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
 "usdcDecimals": 6,
 "tokens": [
 {
 "key": "usdc",
 "symbol": "USDC",
 "address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
 "decimals": 6,
 "default": true
 },
 {
 "key": "tusdc",
 "symbol": "tUSDC",
 "address": "0x794A5456be0058a5B8B519AaC274347afC8320A4",
 "decimals": 6,
 "default": false
 }
 ],
 "paymentContract": "0xD97E3b7a05ee16267072B18F0A65C57798057898",
 "vaultContract": "0xD97E3b7a05ee16267072B18F0A65C57798057898",
 "cardContract": "0x34684f2392259D87339f0F7c1601D46A4d47B142",
 "mintGuardContract": "0xd503576f63c2deD4Bf110a9e3ac9ca07187a6C19",
 "paused": false,
 "scopesPaused": { "generatePack": false, "openPack": false, "webhook": false, "buyback": false },
 "ready": true
 }
 ]
}

- paused — the whole chain is stopped; don't offer it. scopesPaused — which individual
operations are stopped, with any global switches already folded in. ready — has a payment
contract and a card contract. Grey the chain out on any of them. Note ready does not cover
mintGuardContract: a chain with that field null reports ready: true and then fails every
generatePack with 503 MINT_NOT_CONFIGURED, so check it too before offering the chain.

- tokens — the chain's payment lanes, default first. Pass tokens[].key (or its address) as
token on generatePack. usdc / usdcDecimals at the top level are the DEFAULT lane under their
original names, so a client written before lanes keeps working unchanged.

- Decimals are per lane and are not always 6. Binance-Peg USDC on BNB is 18. Two lanes on one
chain need not agree. Never build an amount yourself from a human number — use the base-unit
amount the API hands you.

- A pack's lane is fixed when you create it. The buyback pays in that lane, and a lane's float is its
own: a full USDC balance does not fund a tUSDC buyback.

- Omitting chainId on a request means defaultChainId. Sending one we don't serve is never a silent
fallback: generatePack and buyback answer 400 UNSUPPORTED_CHAIN and name the chains that are
enabled. buyback/available is a pure read and simply answers available: false.

chainId is accepted on generatePack (body), buyback (body), buyback/available (query) and
buyback/settle (body). openPack takes only the memo — the chain is read from the pack record,
so you cannot open a pack on the wrong chain.

warning

The same contract addresses are deployed on every chain, so (contract, tokenId) alone does not
identify a card. Token 2615 exists on Base and on Robinhood and they are different cards. Always
carry chainId alongside a token id in your own storage.

## Contract addresses​

Don't hardcode them. They come back in the API responses:

- Every address, per chain → /api/evm/chains

- USDC + payment contract → /api/evm/generatePack (usdc, paymentContract)

- Card contract + token id → /api/evm/openPack (evm_contract_address, evm_token_id)

- Buyback vault → /api/evm/buyback (vault)

Contracts get redeployed. A card you were awarded stays sellable against the vault named in its
own quote, which is why the quote carries vault rather than expecting you to remember one.

## Authentication​

Same as the Solana API: send x-api-key on every request.

- Prefixes your memo with your slug so you can filter your own activity.

- Required for partner machines — they are private to their owner's key and return
400 Unknown machine without it.

- Public machines work without a key (memos are prefixed cc-).

## Machine list​

Use the shared GET /api/machines to get code
(the packType), price, odds, and stock.

For a machine you operate, use GET /api/v1/machines instead — it is
key-scoped and adds the solved EV, the achievable EV band and a sells flag. Partner fees on EVM
packs accrue exactly as they do on Solana and settle in Solana USDC; see
Partner Operations.

## Buying and opening a pack​

Five steps: generatePack → approve → pay → openPack → poll openPack until the token ID is ready.
pack/status remains available as a read-only lifecycle view.

### 1. Generate Pack — POST /api/evm/generatePack​

Reserves the pack and returns the on-chain parameters. Nothing has been paid yet.

Request Body:

{
 "playerAddress": "0xEeC1...9A21",
 "packType": "pokemon_50",
 "chainId": 84532
}

chainId is optional and defaults to defaultChainId. token is optional and defaults to the
chain's default lane; give it a lane key ("usdc", "tusdc"), a symbol, or a token address.

The price is the same number in every lane — you pick a token, never a discount.

Response:

{
 "memo": "cc-6f3a1b2c-...",
 "chainId": 84532,
 "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
 "usdcDecimals": 6,
 "token": {
 "key": "usdc",
 "symbol": "USDC",
 "address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
 "decimals": 6
 },
 "paymentContract": "0xD97E3b7a05ee16267072B18F0A65C57798057898",
 "treasury": "0x1234...abcd",
 "amount": "50000000",
 "amountHuman": 50
}

token is the lane this pack is priced in; usdc / usdcDecimals repeat its address and decimals
under their original names. amount is in that lane's base units — pass it verbatim to approve and
pay. Don't recompute it from amountHuman; at 18 decimals that arithmetic drifts. The memo is the
identifier for the whole pack lifecycle.

Error Responses:

- 400: Invalid playerAddress, unknown machine, UNSUPPORTED_CHAIN, or UNSUPPORTED_TOKEN

- 429: RATE_LIMITED — more than 50 reserves from this wallet in the last 10 minutes with none of
them paid for. Pay for one and the guard clears.

- 503: MACHINE_OFF, OFF_BALANCE, MACHINE_LOW — retry shortly or use another machine.
MINT_NOT_CONFIGURED — this chain has no mint guard and cannot deliver cards at all; retrying
never clears it. Also returned when the chain or its generatePack scope is paused
(CHAIN_PAUSED); /api/evm/chains says which.

- 500: Server error

### 2. Approve the token​

Standard ERC-20 approve of amount to paymentContract, on the lane's own token — token.address
from step 1.

approve(address spender, uint256 amount)

### 3. Pay​

pay(address token, uint256 amount, string memo)

Call it on paymentContract with the token, amount and memo from step 1. This pulls the token
and emits Paid(from, token, amount, memo). Keep the transaction hash.

token must be the lane the pack was priced in. Paying in a different approved lane is rejected —
the server matches the event's token against the pack, so the pack stays unopened and you have spent
the wrong token. Send back exactly what generatePack returned.

warning

EVM payments are final. There is no refund path.

### 4. Open Pack — POST /api/evm/openPack​

Verifies the payment on-chain, rolls the VRF, and mints the ERC-721 to playerAddress.
Idempotent — calling it twice returns the same award.

Open the pack within 2 hours of generatePack. After that the pack returns 410 PACK_EXPIRED.
The window is the same one the Solana machine puts on a pack. An already-opened pack still replays
forever — the window applies only to a pack that was never opened.

Request Body:

{
 "memo": "cc-6f3a1b2c-...",
 "payTxHash": "0x9ab3...f10c"
}

payTxHash is optional, but pass it: it confirms your payment immediately. Without it you'll get
202 WAITING_FOR_PAYMENT until the payment is confirmed independently.

Response (Mint submitted, HTTP 202):

{
 "code": "MINTING",
 "award_ready": true,
 "retryAfterMs": 500,
 "memo": "cc-6f3a1b2c-...",
 "roll": 87654321,
 "rarity": "common",
 "rarity_label": "Common",
 "prize_tier": 4,
 "nft_address": "H9ZXYkud...TptLA",
 "card_name": "Charizard Base Set",
 "nftWon": {
 "id": "H9ZXYkud...TptLA",
 "content": {
 "links": { "image": "https://arweave.net/abc..." },
 "metadata": { "name": "1999 Pokemon Base Charizard" },
 "files": [{ "cc_cdn": "https://cdn.collectorcrypt.com/...front-m.jpg", "mime": "image/jpeg" }]
 }
 },
 "points": 0,
 "insured_value": 50,
 "buyback_amount": 42.5,
 "evm_contract_address": "0x34684f...",
 "evm_token_id": null,
 "transaction_signature": null,
 "transactionSignature": null,
 "status": "minting",
 "chain_id": 84532,
 "chain_key": "base-sepolia",
 "replay": false
}

202 MINTING means the award is final and safe to reveal: award_ready is true, and the response
already contains the roll, rarity, card metadata, insured value, and indicative buyback amount. The
service has prepared, signed, and attempted the ERC-721 mint submission, but the token does not have
an on-chain ID yet, so evm_token_id is null. This status does not promise inclusion: if Alchemy's
submission response is lost or errors, the operation is treated as possibly in flight and resolved
through the mint guard and recovery process below.

Wait retryAfterMs, then repeat the same openPack request. The route is idempotent: it returns the
same award, checks the on-chain mint guard, and records the token ID when the mint lands. Continue
until it returns HTTP 200 with a non-null evm_token_id. A replay cannot select a different card or
submit a second mint for the same memo. Use the token ID only after that point, including for a
buyback. /api/evm/pack/status can display the stored row, but it is read-only; polling openPack
actively performs the guard check that can finish the row.

let opened = await postOpenPack({ memo, payTxHash });

while (opened.status === 202 && opened.body.code === 'MINTING') {
 // The UI can reveal opened.body.nftWon now.
 await delay(opened.body.retryAfterMs);
 opened = await postOpenPack({ memo, payTxHash });
}

if (opened.status !== 200 || opened.body.evm_token_id == null) {
 throw new Error(opened.body.code ?? 'Pack did not finish minting');
}

const tokenId = opened.body.evm_token_id; // now safe to pass to /api/evm/buyback

Response (Success):

{
 "success": true,
 "memo": "cc-6f3a1b2c-...",
 "roll": 87654321,
 "rarity": "common",
 "rarity_label": "Common",
 "prize_tier": 4,
 "nft_address": "H9ZXYkud...TptLA",
 "card_name": "Charizard Base Set",
 "nftWon": {
 "id": "H9ZXYkud...TptLA",
 "content": {
 "links": { "image": "https://arweave.net/abc..." },
 "metadata": {
 "name": "1999 Pokemon Base Charizard",
 "description": "1999 Pokemon Base Set Charizard Holo #4 PSA 9",
 "insuredValue": 50,
 "attributes": [{ "trait_type": "Insured Value", "value": 50 }]
 },
 "files": [
 { "uri": "https://arweave.net/abc...", "cdn_uri": "https://cdn.helius...", "cc_cdn": "https://cdn.collectorcrypt.com/...front-m.jpg", "mime": "image/jpeg" },
 { "uri": "", "cc_cdn": "https://cdn.collectorcrypt.com/...back-m.jpg", "mime": "image/jpeg" }
 ]
 }
 },
 "points": 0,
 "insured_value": 50,
 "buyback_amount": 42.5,
 "escrow_signature": null,
 "escrow_wallet": null,
 "evm_contract_address": "0x34684f...",
 "evm_token_id": "2615",
 "transaction_signature": null,
 "transactionSignature": null,
 "chain_id": 84532,
 "chain_key": "base-sepolia"
}

Field notes:

- nftWon is the full card metadata, byte-identical to the nftWon returned by the Solana
/api/openPack. Read the image from
content.files[0].cc_cdn → content.files[0].cdn_uri → content.files[0].uri (in that
preference order; files[1] is the card back), the name from content.metadata.name, and the
rest from content.metadata.attributes[] (trait_type / value pairs — Insured Value,
Category, Grading Company, GradeNum, The Grade, Year). content.links.image is a
fallback image. nftWon is null only if the card had no stored metadata — don't dereference
it unguarded, and don't use it as a retry condition.

- rarity is lowercase: "epic", "rare", "uncommon", "common". rarity_label is the same
value in the Solana API's capitalized form ("Epic", "Rare", "Uncommon", "Common"), so a
client shared with the Solana API can read one key on both. prize_tier: 1 = epic, 2 = rare,
3 = uncommon, 4 = common.

- points is always 0. There is no points ledger on the EVM machine; the key exists so a shared
client always gets a number.

- insured_value and buyback_amount are in whole USD, not base units. buyback_amount is an
indicative quote, not a payment — the EVM machine never auto-sells. Get a signed, executable
quote from /api/evm/buyback.

- transaction_signature / transactionSignature (the same value under the Solana API's key name)
are the mint transaction hash. They can be null while minting and can remain unavailable when
openPack settles from a guard read, so do not use either field as the ready signal.

- evm_token_id is the ready signal and the value you use for buybacks. Wait for HTTP 200 with a
non-null value before requesting a buyback quote.

- escrow_signature / escrow_wallet are null on a fresh award; cron/evm-escrow-reap fills
them only for cards that outlive the buyback window.

- A replay of an already-opened pack returns the same keys plus "replay": true and status.
On a replay, nftWon is served from the award record, so it survives even after the backing
card is reaped.

Error Responses:

- 202: WAITING_FOR_PAYMENT (payment not confirmed yet — retry, or pass payTxHash) · PROCESSING (a concurrent open is in flight — poll) · MINTING (the award is ready to reveal and mint submission is in flight or its response was ambiguous — poll openPack after retryAfterMs, currently 500). A MINTING response includes the complete award payload with award_ready: true and evm_token_id: null. Your pack is paid and its card is held for it in every one of these cases.

- 400: Missing memo

- 402: PAYMENT_NOT_VERIFIED — the payTxHash doesn't contain a matching Paid event; reason says why

- 404: No pending pack for that memo

- 410: PACK_EXPIRED — the pack is more than 2 hours old. Open a pack within 2 hours of
generatePack. This matches the Solana machine's window.

- 502: MINT_FAILED · MINT_PENDING — the card is held for this pack and cannot be awarded again.
The service checks the mint guard in case the original submission landed, then retries an unused
mint up to three times during its 24-hour automated recovery window. This is recovery, not an
Alchemy delivery guarantee; a mint that exhausts recovery requires operator reconciliation.

- 503: NO_INVENTORY

### 5. Pack Status — GET /api/evm/pack/status​

Everything on record for one memo: the payment, the award, and any buybacks.

Query Parameters:

- memo (required, or signature — the pay transaction hash)

GET /api/evm/pack/status?memo=cc-6f3a1b2c-...

Response:

{
 "memo": "cc-6f3a1b2c-...",
 "pack": { "wallet": "0xEeC1...", "spin_cost": 50, "pack_type": "pokemon_50", "status": "confirmed", "transaction_signature": "0x9ab3...", "chain_id": 84532 },
 "send": { "to_wallet": "0xEeC1...", "roll": 87654321, "prize_tier": 4, "evm_token_id": "2615", "evm_contract_address": "0x34684f...", "transaction_signature": "0x77c1...", "status": "confirmed" },
 "buyback": []
}

pack and send are null until they exist; buyback is an array, newest first.

## Selling a card back​

The buyback is atomic: the server signs a price quote, and the vault pulls the NFT, pays you,
and burns it in a single transaction you send. The server never holds your card.

Window: 72 hours from the award in production; the dev deployment runs a deliberately longer one,
so don't calibrate against what you see there. Payout is the machine's buyback percentage (typically
85%) of the card's insured value.

### 1. Check eligibility — GET /api/evm/buyback/available​

Read-only, no quote issued.

Query Parameters:

- wallet (required): EVM address

- tokenId (required): the evm_token_id from openPack

- contract (optional): card contract; defaults to the configured one

- chainId (optional): defaults to defaultChainId. Pass the chain the card was awarded on —
the same token id on another chain is a different card and will answer available: false.

GET /api/evm/buyback/available?wallet=0xEeC1...&tokenId=2615&chainId=84532

Response:

{ "available": true, "amount": 42.5, "amountBase": "42500000", "chainId": 84532 }

Returns { "available": false } when out of window, already sold back, or unknown.

### 2. Get a quote — POST /api/evm/buyback​

Request Body:

{
 "playerAddress": "0xEeC1...9A21",
 "evmTokenId": "2615",
 "evmContract": "0x34684f...",
 "chainId": 84532
}

evmContract and chainId are optional. playerAddress must be the current on-chain owner — it's
checked.

Response:

{
 "success": true,
 "memo": "cc-6f3a1b2c-...",
 "refundAmount": 42.5,
 "refundAmountBase": "42500000",
 "token": {
 "key": "usdc",
 "symbol": "USDC",
 "address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
 "decimals": 6
 },
 "paymentToken": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
 "cardContract": "0x34684f...",
 "tokenId": "2615",
 "chainId": 84532,
 "chainKey": "base-sepolia",
 "vault": "0xD97E3b7a05ee16267072B18F0A65C57798057898",
 "quoteId": "481",
 "deadline": 1786000000,
 "signature": "0x1c9d...ff",
 "suggestedGasLimit": 250000,
 "instructions": "Approve the vault for token 2615, then call sellBack(0x036CbD53..., 2615, 42500000, 1786000000, 481, signature) on 0xD97E3b7a... with gas limit 250000 (a bare estimate reverts — unused gas is refunded). You are paid in USDC (0x036CbD53...), the token this pack was bought with."
}

paymentToken (and token.address) is the lane you are paid in — the token the pack was bought
with. You do not choose it here and you cannot change it: it is inside the signed quote, so passing
a different token to sellBack fails the signature check. refundAmountBase is in that lane's own
decimals.

The quote is valid for 10 minutes (deadline, a unix timestamp). Re-requesting while it's live
returns the same amount and deadline.

The signature is bound to chainId, vault and token, so a quote is spendable in exactly one
lane on one chain's vault. Send it to the vault in the same response.

Error Responses:

- 400: Invalid playerAddress or evmTokenId, or UNSUPPORTED_CHAIN

- 404: NOT_ELIGIBLE — outside the window, or already bought back

- 409: NOT_TOKEN_OWNER (you don't hold it on-chain) · ALREADY_SOLD · BACKING_RELEASED

- 202: TOKEN_NOT_VISIBLE — the mint is not readable on this RPC node yet. No quote was issued;
retry after retryAfterMs (1000).

- 503: INSUFFICIENT_FLOAT (that lane's float is short — retry shortly) ·
NO_VAULT · LANE_NOT_APPROVED (the lane is not enabled on the vault) ·
UNSUPPORTED_TOKEN (the lane the pack was bought in is no longer served).
Also when the buyback scope is paused — quotes already issued stay spendable until their deadline.

### 3. Approve the vault​

approve(address vault, uint256 tokenId)

on the card contract.

### 4. Sell back​

sellBack(address token, uint256 tokenId, uint256 amount, uint256 deadline, uint256 quoteId, bytes signature)

on vault, using paymentToken, refundAmountBase, deadline, quoteId, and signature from the
quote. One transaction: your NFT is pulled, the token is paid to you, the NFT is burned.

token comes first and must be paymentToken from the quote. It is part of the signed data, so any
other value reverts with BadSignature before anything moves.

Set the gas limit from suggestedGasLimit

Do not send this with a bare estimateGas. sellBack does three things in one transaction and
EIP-150 lets it forward only 63/64 of its remaining gas to the final burn, so a tight estimate leaves
the card collection's reentrancy guard short, the burn reverts, and the whole atomic sell unwinds —
you keep the card, get no payout, and pay for the failed gas anyway. Measured over a 500-pack run,
that hit about 15% of sales.

Put suggestedGasLimit (currently 250000) on the transaction. Over-asking is free: unused gas is
refunded.

### 5. Settle — POST /api/evm/buyback/settle​

Optional — records the completed sale immediately so it shows up in status right away.

Request Body:

{ "txHash": "0x5f21...c0de" }

Response:

{ "ok": true, "results": [ { "ok": true, "quoteId": "481" } ] }

Returns 409 if nothing settleable was found in that transaction.

### Buyback Check — GET /api/evm/buyback/check​

Query Parameters:

- memo (required)

Response:

{
 "exists": true,
 "status": "complete",
 "userWallet": "0xEeC1...",
 "evmTokenId": "2615",
 "evmContractAddress": "0x34684f...",
 "refundAmount": 42.5,
 "refundAmountBase": "42500000",
 "payoutTxHash": "0x5f21...c0de",
 "quoteId": "481",
 "vault": "0xD97E3b7a...7898",
 "quoteExpiresAt": "2026-08-07T18:20:00.000Z",
 "createdAt": "2026-08-07T18:10:00.000Z"
}

status is "quoted" while a quote is outstanding and "complete" once the sale is confirmed.
Returns { "exists": false } when there's no buyback for that memo.

## Provable fairness — GET /api/evm/vrf/verify​

Every EVM pack uses the same ECVRF roll as the Solana machine — see
Provable Fairness (VRF).

Query Parameters:

- memo (required)

GET /api/evm/vrf/verify?memo=cc-6f3a1b2c-...

Response:

{
 "valid": true,
 "memo": "cc-6f3a1b2c-...",
 "proof": "0x...",
 "publicKey": "0x...",
 "alpha": "0x...",
 "beta": "0x...",
 "actualRoll": 87654321,
 "calculatedRoll": 87654321,
 "rollMatches": true,
 "wallet": "0xEeC1...",
 "evmTokenId": "2615",
 "chainId": 84532,
 "algorithm": "ECVRF-EDWARDS25519-SHA512-TAI",
 "vrfMode": 1,
 "vrfAuthority": "13C5cbemzwSg5wNerJDucU5uUJ1kHQENDqoTa3VSAHau",
 "vrfCommitSignature": "2PnAaXGBtutqXah7...",
 "vrfCommitAddress": "1fNrGDCyJrKBEheLcvhTKJXkLrAmWsM7FNXP7cR1hNF",
 "vrfDegraded": false,
 "selectMode": 1,
 "provableSelection": true,
 "poolVersion": "1841",
 "baseIndex": 312,
 "awardedIndex": 312,
 "awardedRank": 0,
 "ownershipSeq": "4820117",
 "selAnchor": "0x181ed2e7...",
 "selectionVerifyUrl": "/verify-selection/cc-6f3a1b2c-..."
}

alpha is sha256(memo + payTxHash) — the hash of the payment transaction you signed, so
the roll cannot be precomputed by the operator. valid and rollMatches must both be true.

An EVM pack uses the same VRF as the Solana machine: the same Ed25519 key, the same
ECVRF-EDWARDS25519-SHA512-TAI suite, and the same on-chain proof commit through the cc-vrf
program on Solana (vrfCommitSignature / vrfCommitAddress). It also uses the same
within-tier card selection: beta[0..8] gives the roll, beta[8..24] seeds the Feistel
walk over the pinned candidate pool, and selectionVerifyUrl replays the whole thing in your
browser. See Provable Fairness (VRF), and
When your card is decided for when in the flow the
outcome is fixed.

## End-to-end example​

Using Foundry's cast:

BASE=https://dev-gacha.collectorcrypt.com
PLAYER=0xEeC1...9A21

# 0. pick a chain
CHAINS=$(curl -s "$BASE/api/evm/chains")
CHAIN_ID=$(echo "$CHAINS" | jq -r '.chains[] | select(.paused == false and .ready) | .chainId' | head -1)
RPC=... # an RPC for that chain

# 0b. pick a payment lane on that chain (omit `token` below for the default one)
LANE=$(echo "$CHAINS" | jq -r --arg c "$CHAIN_ID" \
 '.chains[] | select(.chainId == ($c|tonumber)) | .tokens[] | select(.default) | .key')

# 1. reserve the pack
GEN=$(curl -s -XPOST "$BASE/api/evm/generatePack" \
 -H 'content-type: application/json' \
 -H 'x-api-key: API_KEY' \
 -d "{\"playerAddress\":\"$PLAYER\",\"packType\":\"pokemon_50\",\"chainId\":$CHAIN_ID,\"token\":\"$LANE\"}")

MEMO=$(echo "$GEN" | jq -r .memo)
AMOUNT=$(echo "$GEN" | jq -r .amount)
TOKEN=$(echo "$GEN" | jq -r .token.address)
GATEWAY=$(echo "$GEN" | jq -r .paymentContract)

# 2 + 3. approve and pay, in the lane the pack was priced in
cast send "$TOKEN" "approve(address,uint256)" "$GATEWAY" "$AMOUNT" --rpc-url "$RPC"
PAYTX=$(cast send "$GATEWAY" "pay(address,uint256,string)" "$TOKEN" "$AMOUNT" "$MEMO" --rpc-url "$RPC" --json | jq -r .transactionHash)

# 4. open — mints the card
curl -s -XPOST "$BASE/api/evm/openPack" \
 -H 'content-type: application/json' \
 -H 'x-api-key: API_KEY' \
 -d "{\"memo\":\"$MEMO\",\"payTxHash\":\"$PAYTX\"}"

Then to sell it back:

TOKEN_ID=2615

# 1. quote
BB=$(curl -s -XPOST "$BASE/api/evm/buyback" \
 -H 'content-type: application/json' \
 -d "{\"playerAddress\":\"$PLAYER\",\"evmTokenId\":\"$TOKEN_ID\",\"chainId\":$CHAIN_ID}")

VAULT=$(echo "$BB" | jq -r .vault)
CARD=$(echo "$BB" | jq -r .cardContract)
AMT=$(echo "$BB" | jq -r .refundAmountBase)
PAYTOKEN=$(echo "$BB" | jq -r .paymentToken) # the lane you are paid in — not your choice
DL=$(echo "$BB" | jq -r .deadline)
QID=$(echo "$BB" | jq -r .quoteId)
SIG=$(echo "$BB" | jq -r .signature)
GAS=$(echo "$BB" | jq -r .suggestedGasLimit)

# 2 + 3. approve the vault, then sell back atomically — note --gas-limit, not an estimate
cast send "$CARD" "approve(address,uint256)" "$VAULT" "$TOKEN_ID" --rpc-url "$RPC"
SELL=$(cast send "$VAULT" "sellBack(address,uint256,uint256,uint256,uint256,bytes)" \
 "$PAYTOKEN" "$TOKEN_ID" "$AMT" "$DL" "$QID" "$SIG" --gas-limit "$GAS" --rpc-url "$RPC" --json | jq -r .transactionHash)

# 4. settle
curl -s -XPOST "$BASE/api/evm/buyback/settle" \
 -H 'content-type: application/json' \
 -d "{\"txHash\":\"$SELL\",\"chainId\":$CHAIN_ID}"

## Differences from the Solana API​

Solana
EVM

Payment

Server-built transaction you sign

You call pay(token, amount, memo) yourself

Prize

NFT transferred to you

ERC-721 minted to you

Buyback

Server-built transaction

Server-signed quote, you call sellBack

Refunds

Supported

None — payments are final

Networks

One

Several — carry chainId everywhere

Gas

You pay for the transactions you sign

Same, and sellBack needs suggestedGasLimit

rarity casing

"Epic"

"epic" — plus rarity_label ("Epic") for parity

Values

Base units

Whole USD (insured_value, buyback_amount)

Auto-sell

Turbo mode returns code: "TURBO_MODE_BUYBACK" + buybackAmount

None — buyback_amount is a quote, never a payment

points

Earned per pack

Always 0 — no points ledger

openPack otherwise returns every key the Solana one does: success, roll, nft_address,
nftWon, points, transactionSignature, and rarity_label.

Previous

API Docs

Next

cc-buyback (Solana program)

- Base URL

- Chains — GET /api/evm/chains

- Contract addresses

- Authentication

- Machine list

- Buying and opening a pack
- 1. Generate Pack — POST /api/evm/generatePack

- 2. Approve the token

- 3. Pay

- 4. Open Pack — POST /api/evm/openPack

- 5. Pack Status — GET /api/evm/pack/status

- Selling a card back
- 1. Check eligibility — GET /api/evm/buyback/available

- 2. Get a quote — POST /api/evm/buyback

- 3. Approve the vault

- 4. Sell back

- 5. Settle — POST /api/evm/buyback/settle

- Buyback Check — GET /api/evm/buyback/check

- Provable fairness — GET /api/evm/vrf/verify

- End-to-end example

- Differences from the Solana API

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

