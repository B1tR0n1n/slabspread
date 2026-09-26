---
url: https://docs.collectorcrypt.com/gacha/cc-buyback
fetched_at: 2026-09-26T00:22:44Z
status: 200
---



# cc_buyback — buybacks for program-owned wallets

The ordinary Solana buyback hands you a transaction to sign: you call POST /api/buyback, Collector
Crypt builds and co-signs it, and your wallet adds the second signature. That requires a private
key.

A smart-contract wallet does not have one. Its address is a PDA — it authorises actions through its
own program, never with an ed25519 signature — so it can never complete a transaction CC built. Same
for a custody vault that holds a card on a user's behalf.

cc_buyback is the path for those sellers. CC signs a quote — a message, not a transaction — and
you build and broadcast the transaction yourself. The program verifies the quote, confirms the card
already reached its destination, and pays you.

It is the Solana counterpart of GachaVault.sellBack on the EVM side, and it works the same way in
the way that matters: a signed price, a single-use quote, and an atomic swap.

It is not a CPI-only buyback, and cc_buyback never moves the card

The card is moved by you, before you call in. cc_buyback reads the transaction's instruction
history to confirm the transfer happened, then releases the payment. A total compromise of this
program cannot move an NFT. It also does not have to be called by CPI — a plain wallet can use the
same path with three top-level instructions (see Plain wallets).

## The rule​

Move the card first. Then ask to be paid, in the same transaction.

cc_buyback reads the list of instructions that have already completed alongside it and requires one
that transferred this asset to this destination. If it is not there, nothing is paid. Because a
Solana transaction is all-or-nothing, you can never end up paid without delivering, or having
delivered without being paid.

Reading the current owner would not be equivalent, and that is why the check is what it is: a card
sitting in the prize wallet because somebody else just sold it back would satisfy an
"is-it-there-now" test while you delivered nothing.

## What an integrator must satisfy​

No registration, no allow-list, no account CC creates for you, and no counter you have to keep.

- Sign as the seller — the exact address named in the quote. A PDA signing via its program's
invoke_signed counts.

- Own the card, and transfer it to destinationOwner as an instruction that completes before
authorize_and_pay in the same transaction.

- Include CC's quote as a top-level instruction. It is an Ed25519 precompile instruction, and
precompiles cannot be reached by CPI — it must sit at the top level of the transaction, not inside
your program's call.

- Own a token account for the payment mint. That is where the money lands; create it before you
call, or the program fails with AccountNotInitialized (3012).

- Send to an allow-listed destination. destinationOwner comes from the quote; you cannot
choose it.

Everything else — expiry, replay, float — the program handles.

## Transaction shape​

[0] ComputeBudget (optional)
[1] Ed25519SigVerify… the quote. TOP-LEVEL, always
[2] <your program> e.g. a smart wallet's "execute" instruction
 ├─ transfer asset → destinationOwner ← must complete first
 ├─ cc_buyback::authorize_and_pay
 └─ spl-memo "<memo>:buyback" emitted by the program itself

The transfer and the authorize_and_pay call must share the same parent instruction, so that the
transfer counts as a completed sibling.

### Plain wallets​

A wallet with a private key needs no program at all — top-level instructions are siblings of each
other:

[0] Ed25519SigVerify… the quote
[1] transfer asset → destinationOwner
[2] cc_buyback::authorize_and_pay

### Address lookup table​

A Core buyback fits a legacy transaction. A pNFT one does not — Token Metadata's TransferV1 brings
the metadata, edition and both token records with it — so CC publishes a lookup table and you build a
v0 transaction against it. Measured, for a custody program's swap:

Path
Legacy
v0 + the table

Core

1046 bytes — fits

not needed

pNFT

1383 bytes — over the 1232 cap

1047 bytes

The table holds CC's constants only, twelve of them: the cc_buyback program and its policy PDA,
the payment lane's mint and treasury, CC's rent destination, CC's pNFT rule set, and the Token
Metadata, auth-rules, SPL Token, Associated Token and System programs plus the instructions sysvar.

What is deliberately not in it matters more, because it is what keeps the table stable:

- the card, its metadata, edition and token records — per prize

- your program, its config PDA, the seller and its payout account — per integrator

- destinationOwner and its token account — per prize wallet

- quoteMarker — derived from the quote's digest, so different every time

Those travel in the transaction's static keys at 32 bytes each. That is the trade: a new prize wallet,
a new card, or a redeploy of your program costs you a handful of bytes instead of an amendment to a
table you do not control — and it lets CC freeze the table, which is what stops an entry being
appended and then resolved into an account slot the program validates only by CPI. Entries are
append-only, so nothing already at an index can be rewritten even before freezing.

## Supported card standards​

The transfer you emit must be one the program recognises.

nft_standard
Transfer instruction

core

mpl-core TransferV1

pnft, nft

mpl-token-metadata TransferV1

cnft-core

Bubblegum transferV2

Compressed cards work like any other. A transferV2 that appears in the completed list means
Bubblegum has already verified the Merkle proof and the leaf owner, so cc_buyback needs none of
the proof accounts.

## Getting a quote — POST /api/buyback​

Add sellerProgram to the ordinary buyback request and the route answers with a quote instead of a
transaction. The field is only a mode switch — any non-empty string turns the response into a
quote. Its value is not validated, not stored and not an allow-list; cc_buyback never inspects the
caller.

Request Body:

{
 "playerAddress": "DjXQhLaUMCvjQGeiFGR1mz28drf5wWJZwRUMfCyMhT9b",
 "nftAddress": "DYBgWyBTCyYp21Vs3nVn53YgCEYLVBE9KFQUJALQ4Nxr",
 "sellerProgram": "XmSwiXQsxSZYKVYbSAkkvQVvdrKo1nwwfvZBPQrLzbU"
}

playerAddress is the seller — the PDA that owns the card and will be paid.

Response:

{
 "success": true,
 "memo": "cc-6f3a1b2c-...",
 "refundAmount": 28050000,
 "quote": {
 "hash": "9ZecA6tJ5xbWCsbS13rgjucvtbR4QjHxU5aD5vJa3XNz",
 "signature": "base64 ed25519 signature",
 "ed25519Instruction": { "programId": "Ed25519SigVerify111111111111111111111111111", "keys": [], "data": "base64" },
 "quoteMarker": "4kQq1B8n2Ym9cTZs7pW3vRfL6dXhJ1u5aNbE2gK9mS4t",
 "quoteId": "84213",
 "price": "28050000",
 "expiresAt": 1789154944,
 "paymentMint": "Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr",
 "destinationOwner": "Lowovruwau5pKnA7yhGj3JiE5moXTsn7mGG6dU53S2z",
 "treasury": "9ZSgA3PMjeAU8K6CWzgJ8oDnhZwwSgHZu6KP3X95t7Jq",
 "rentVault": "HypwMQDGznHy2h3mTwkTAViCnT11TxAFti1dpWeV4Vyk",
 "ccProgram": "CcBuyM7sDhedBGLZxivBvgZVdqzrQAG66KYHgnTTEpLF",
 "memoProgram": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
 "tokenProgram": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
 "standard": "core",
 "computeUnitLimit": 250000,
 "addressLookupTable": "HKv5pvGESQB7EQyzrypGyhJvP1YSn74uVx9mQWqEH9B8",
 "memo": "cc-6f3a1b2c-...:buyback"
 }
}

Use it as follows:

- ed25519Instruction — build instruction [1] verbatim from programId, no accounts, and data
base64-decoded.

- standard — tells you which transfer to emit.

- treasury, rentVault, paymentMint, destinationOwner, memoProgram, tokenProgram —
accounts for authorize_and_pay. Use tokenProgram as given, do not assume legacy SPL: it is
legacy SPL for the USDC, USDT and JupUSD lanes and Token-2022 for CASH (and devnet RIP). It decides
both the seller ATA derivation and the token_program account, and you cannot infer it from the mint.

- price — base units of paymentMint. refundAmount is the same number.

- expiresAt — unix seconds. Quotes live 600 seconds.

- addressLookupTable — when set, build a v0 transaction against it; see Address lookup table
above for what it contains. null means CC has published none for that cluster, in which case Core
still sells on a legacy transaction and pNFT cannot be built at all.

Error codes: NOT_OWNER (403, playerAddress does not currently hold the card on chain — ask for
the quote before you move it), ALT_RECIPIENT_UNSUPPORTED (400, altRecipient is not supported
in quote mode; the payout always goes to playerAddress), NO_LANE (503, that token has no payment
lane), INSUFFICIENT_FLOAT (503, top-up pending), QUOTE_SIGNER_MISMATCH (503, CC-side signer
misconfiguration — not retryable by you), ALREADY_SETTLED (409, this card has already been bought
back). A malformed playerAddress is a 400.

A failed attempt does not lock the card. Ask for a new quote and try again — two live quotes
cannot both pay, because each needs the card delivered and the card only moves once.

## authorize_and_pay​

authorize_and_pay(price: u64, quote_id: u64, expires_at: i64, memo: String)

Anchor discriminator: sha256("global:authorize_and_pay")[..8]
= [196, 1, 233, 204, 98, 232, 22, 54].

#
Account
Signer
Writable
Notes

0

policy

PDA [b"policy"]

1

seller_authority

yes

you. Its owner is not inspected

2

asset

the card. Matched against your transfer; never read or written

3

destination_owner

from the quote

4

treasury_token

yes

from the quote

5

seller_token

yes

your token account for payment_mint

6

payment_mint

from the quote

7

sysvar_instructions

Sysvar1nstructions1111111111111111111111111

8

quote_marker

yes

quoteMarker from the quote

9

rent_vault

yes

rentVault from the quote

10

system_program

11

token_program

12

memo_program

MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr (memoProgram from the quote)

Checks run in this order:

- not paused; price > 0; memo non-empty and ≤ 256 bytes; not expired

- seller_authority signed

- delivery — a completed sibling transferred asset to destination_owner

- rent return — for nft/pnft only, see below

- destination_owner is allow-listed

- the payment lane exists and treasury_token is that lane's treasury

- the lane's float and delegate allowance cover price

- the quote signature verifies against CC's signer

- the quote has not been spent — then it is marked spent

- payment is transferred to seller_token

- the memo is emitted as an SPL Memo instruction

### Returning the token-account rent​

Collector Crypt pays for the token account that holds your card when it is
awarded — the rent-exempt minimum of a 165-byte SPL token account, currently
1,488,440 lamports. On a buyback that account is emptied, and that rent has
to come back or the wallet funding buybacks drains one sale at a time.

So when the delivery that matched was an mpl-token-metadata TransferV1 — that
is, nft or pnft — the transaction must also contain one of these as a
completed sibling:

- an spl-token or Token-2022 CloseAccount (data == [9]) whose destination
(account index 1) is CC's rent destination. Closing the emptied card account is
the natural way to do this, and it costs you nothing you had.

- a System Transfer to CC's rent destination of at least that minimum, if
your program cannot close the account itself. The program reads the figure
from the rent sysvar rather than hardcoding it, so it always matches the
cluster. Do not hardcode 2,039,280 — that is the retired 3480
lamports/byte-year rate and is 37% too high.

Otherwise the program returns RentNotReturned and nothing settles.

core and cnft-core are exempt. An mpl-core asset needs no account at the
destination and a compressed NFT has none at all, so CC fronted nothing for them
and charging would invent a fee.

The rent destination is a field on CC's own policy, changeable only by CC's
multisig. It is deliberately not a program-derived address: lamports sent to a
PDA could not be spent on the awards that produced them.

The memo matters to you only in that you must pass memo_program.
authorize_and_pay always emits <memo>:buyback itself as a CPI, so a settled
sale without a memo cannot exist — that CPI is what Solscan and the buyback
reports show. CC's settlement webhook keys on the signed quote note and the
authorize_and_pay call, not on the memo.

### Errors​

Code
Name
Meaning

6003

QuoteExpired

past expiresAt

6027

QuoteAlreadyUsed

this quote already paid

6025

AssetNotDelivered

no qualifying transfer in this transaction

6029

LaneNotFound

no payment lane for that mint

6030

RentNotReturned

an nft/pnft buyback did not return the token-account rent

6007

WrongTreasury

treasury is not the one the lane names

6010

DelegateNotSet

CC's allowance is missing

6011

AllowanceExhausted

allowance below price — retry shortly

6012

InsufficientFloat

lane balance below price

3012

(Anchor) AccountNotInitialized

your seller_token does not exist yet

## Quotes are single-use​

On success the program creates a small account at [b"quote", digest] — the quoteMarker in the
response. Its existence is the record that the quote was spent, so presenting the same quote twice
fails with QuoteAlreadyUsed.

You never have to track this. There is no nonce to read and no counter to keep in sync, which is what
lets an arbitrary wallet integrate: cc_buyback owns replay protection, not you.

The marker outlives the quote by 1800 seconds: close_quote_marker is callable by anyone once
expiresAt + 1800 has passed, not at expiry. Replay stops at expiresAt either way — a stale quote
fails the expiry check — so the extra window costs nothing but parked rent, and it exists because the
marker is the only receipt a self-broadcast buyback produces. CC's reconciliation reads a marker's
absence after expiry as proof the quote never paid; close it at expiresAt and a buyback that
settled near the deadline could lose its receipt before that job ever saw it.

You do not need to call it: CC fronts the marker's rent from a program-owned vault, so a wallet
with no fee payer can still sell, and CC's own job sweeps markers and refunds the vault. The refund
goes to the vault rather than to whoever closed the account, so there is nothing to farm here.

## The signed quote​

CC signs the SHA-256 of:

"cc-buyback-quote-v2" | cc_buyback program id | seller | asset
 | destinationOwner | paymentMint | price (u64 LE) | expiresAt (i64 LE)
 | quoteId (u64 LE) | memo (UTF-8)

Every field is bound, so a quote cannot be moved to another seller, card, destination, price or
payment token. paymentMint is in there because the treasury has several payment lanes — without it
a quote priced in one token would be redeemable against another's float.

## Payment lanes​

Each payment token is its own lane with its own treasury and its own float, and a buyback pays in the
token the pack was bought with. A lane with no float answers INSUFFICIENT_FLOAT; a token with no
lane answers NO_LANE. Same model as the EVM vault's lanes.

## Settlement​

You broadcast the transaction, so CC may never see it. Reconciliation is automatic: a cron derives
the marker from the stored quote and asks the chain whether it exists. The marker is the proof —
cc_buyback only creates it after its own delivery check passed, so its presence settles the row and
returns the card to the prize pool. No transaction signature is needed or searched for; recovering
one from history was deliberately dropped as forgeable.

You can also report it yourself by posting the signed transaction to POST /api/submitTransaction,
which records the signature and broadcasts on your behalf. It accepts v0 transactions only — a
legacy transaction is rejected with 403 must be signed by gacha wallet, so build your buyback as v0.
Either way, GET /api/pack/status?memo=… shows the result.

## Addresses​

Mainnet
Devnet

Program

CcBuyM7sDhedBGLZxivBvgZVdqzrQAG66KYHgnTTEpLF

same

Policy

6UjEiB4XzrFmxxfzchy95Vygaeo11uvstBYJTqDTbHjq

same

Rent vault

HypwMQDGznHy2h3mTwkTAViCnT11TxAFti1dpWeV4Vyk

same

Rent destination

GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3

A4ahkivAG4NoZAE8Sy4qv8nn2DU9yoXRQcttuCeGtTJv

USDC lane mint

EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v

Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr

Lane treasury

D9CEogjHA6CpS12F8St9zpSco7pQKJB5uR1RqDsuzQZk

9ZSgA3PMjeAU8K6CWzgJ8oDnhZwwSgHZu6KP3X95t7Jq

Address lookup table

HbtcHZ3GNcZrxQEMcPRPiT5Yhn7SXGY8Us7tUuF7vY6M

HKv5pvGESQB7EQyzrypGyhJvP1YSn74uVx9mQWqEH9B8 (12 entries)

The program is live on both clusters. The policy PDA is [b"policy"] and the rent vault
[b"rent"] under the program, so both derive from the program id and are the same address on
mainnet and devnet — reading one cluster's state while pointed at the other looks plausible and is
wrong. The lane mint, lane treasury, rent destination and lookup table are per-cluster.

## Worked example​

A devnet swap by a PDA with no private key —
3iRzAyeH7Rk1jwWivHiKPoghqRgxdrek4E26pEbsXm5eE2tM7qb2QQt7Nrj76LP7SheRLMRu136YSB8AFUZMRpp8:

Program log: Instruction: Sell the seller's program
Program log: Instruction: Transfer mpl-core — the card moves
Program CcBuyM7s… invoke [2]
Program log: Instruction: AuthorizeAndPay then the payment
Program CcBuyM7s… success

The transaction carries exactly one signature — the fee payer's. The seller,
DjXQhLaUMCvjQGeiFGR1mz28drf5wWJZwRUMfCyMhT9b, is a PDA: it authorised the sale through its own
program, received 28.05 USDC, and gave up the card, without ever producing a signature.

Previous

EVM API Docs

Next

Swap

- The rule

- What an integrator must satisfy

- Transaction shape
- Plain wallets

- Address lookup table

- Supported card standards

- Getting a quote — POST /api/buyback

- authorize_and_pay
- Returning the token-account rent

- Errors

- Quotes are single-use

- The signed quote

- Payment lanes

- Settlement

- Addresses

- Worked example

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

