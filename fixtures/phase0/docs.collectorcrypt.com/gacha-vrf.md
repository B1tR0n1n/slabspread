---
url: https://docs.collectorcrypt.com/gacha/vrf
fetched_at: 2026-09-26T00:22:44Z
status: 200
---



# Provable Fairness (VRF)

Every pack is fair in two independent, verifiable steps: a VRF roll decides your
tier (Common / Uncommon / Rare / Epic), then a second provable step decides which
card you win inside that tier. Both steps come from the same cryptographic VRF output,
and everything needed to re-check them is published on Solana. We can't predict, retry, or
steer either one — and neither can you. This page explains how, and how to verify any pack
yourself.

Verify a pack right now

Open /verify-selection/YOUR_MEMO in your browser, or call
GET /api/vrf/verify?memo=YOUR_MEMO. The browser page recomputes everything from scratch
(client-side) and checks it against the on-chain record. See Verify your pack.

## At a glance​

Step
Decides
Driven by
Committed on-chain as

1. The roll

your tier

ECVRF output (beta bytes 0–8)

a VRF proof commit (cc-vrf)

2. The walk

your card

the same ECVRF output (beta bytes 8–24)

the sel_anchor in the award transaction's memo (Solana; on EVM the anchor is published via the verify API — why)

Both steps are decided when you sign, not when the pack opens — see
When your card is decided.

A Verifiable Random Function (VRF) is a keyed function: for an input alpha, the key
holder produces a random-looking output beta and a proof that beta is the one and
only correct output for that key and that input. Anyone with the public key can verify the
proof. The holder cannot bias the result, and it's reproducible by every verifier. We use
the RFC 9381 ECVRF-EDWARDS25519-SHA512-TAI suite — see the spec links.

## Step 1 — The roll picks your tier​

- 

The input is bound to your signature. The VRF input (alpha) is always derived
from something only you can produce by signing. We cannot know or influence it until
after you have signed — so we can't precompute or "shop for" a favorable roll. Two forms
are in use, one per chain, and both are current:

Chain
alpha
Why we can't produce it

Solana

SHA-256("ccgacha-vrf-v1\0" ‖ your_signature)

your wallet's signature on the pack, under a fixed domain tag

EVM

SHA-256(memo ‖ your_payment_tx_hash)

an EVM transaction hash is keccak-256 over the signed transaction, so the hash commits to your own ECDSA signature

These are the same construction in the sense that matters: the input is a value your
wallet creates and we cannot forge or predict. Older Solana packs with no stored
signature fall back to SHA-256(memo ‖ payment_signature) — still a value you produced
by paying.

- 

We evaluate the VRF. Our server runs ECVRF with its secret key over your alpha,
producing an 80-byte proof and a 64-byte output beta.

- 

The roll comes from beta. We read the first 8 bytes of beta as a big-endian
unsigned integer and reduce it:
roll = (beta[0..8] as u64) mod 100,000,000 + 1, a uniform integer in
[1, 100,000,000].

- 

The roll maps to a tier using the machine's published rarity weights (see
GET /api/machines for the live odds per machine).

Because ECVRF (RFC 9381) guarantees exactly one valid proof and one beta per
(public key, alpha), there is no second roll to reach for. The proof either verifies
against our public key or it doesn't.

## Step 2 — The leaf pool and the Feistel walk pick your card​

Once the tier is known, the same beta selects the specific card — over a candidate
set that was frozen and committed before the card was picked.

### The leaf pool (the committed candidate set)​

The "leaf pool" is the machine's live prize inventory, snapshotted into an immutable
pool version and committed as a Merkle tree:

- Every eligible card becomes a leaf:
leaf = SHA-256( 0x00 || nft_mint(32 bytes) || insured_value_in_cents(u64 BE) ).

- Leaves are grouped by tier (epic / rare / uncommon / common) and hashed into a
per-tier Merkle root.

- The four tier roots, their counts, and the version number are folded into one
version_root — a single 32-byte commitment to the entire candidate set of that
pool version.

The pool is rebuilt periodically on a randomized cadence as inventory changes (cards added,
won, or returned). Each rebuild produces a new pool version with a new version_root. When
your pack is created, it is pinned to whatever pool version is current at that moment —
so the set of cards you "could have won" is fixed and committed up front, not chosen after
the roll.

### The Feistel walk​

A Feistel network is the standard way to turn a small secret seed into a
pseudo-random permutation — a keyed shuffle that maps the positions
0, 1, ..., N-1 onto themselves with no repeats and no gaps (a bijection). Think of it as
shuffling the tier's candidate cards with a key, then dealing from the top.

- The shuffle's key is a different window of the same beta: bytes 8–24 (the roll used
bytes 0–8). One VRF output drives both steps, so the card pick is just as unpredictable
and just as verifiable as the roll.

- permIndex(rank) returns the card index at a given position in the shuffle. We walk
rank = 0, 1, 2, ... and award the first card that is still available — skipping any
card already won by an earlier pack and not yet returned.

- "Already won" is determined by a global, monotonic ownership sequence. Your award
sits at some point P in that sequence; the cards considered "taken" are exactly those
with a win event before P and no later return (a card that was bought back becomes
available again). The verifier replays these same events.

- Turbo packs differ. A turbo pack that rolls Common is bought back immediately and never
consumes the card, so its "taken" set is the prior picks of the same turbo session rather
than the global ownership stream — a standalone turbo pack has nothing taken and lands on
rank 0. (A turbo pack rolling uncommon or better is sent out and consumes its card like
any other pack.)

Why a walk rather than index = beta mod N? Cards are being won concurrently by other
buyers, so a single index could land on a card that's already gone. The Feistel permutation
gives a complete, deterministic fallback order for the whole tier, so "skip taken, take
the next" is itself fully reproducible and unbiased — there is no hidden tie-breaker.

### sel_anchor — the on-chain commitment to your card​

The exact card you got is committed with a 32-byte selection anchor:

sel_anchor = SHA-256( 0x04 || version_root || ownership_seq(u64 BE) || awarded_nft_mint(32 bytes) )

This binds three things at once: the entire candidate set (version_root), the exact
point in the global ownership timeline (ownership_seq), and the specific card.

On Solana, the sel_anchor is written into the memo of the award transaction (the
on-chain NFT transfer, or the buyback transaction for turbo packs) as a fixed-width
:r<64-hex> suffix. That memo is immutable once the transaction confirms, so the card you
received is locked to the committed pool and timeline forever.

On EVM, the award is an ERC-721 safeMint(to, uri), which has no memo field — so there
is nothing on the EVM transaction to carry the anchor. The anchor is recorded against the
pack and published through GET /api/evm/vrf/verify and the browser verifier, where you can
still replay the walk and check it. The VRF proof for an EVM pack is committed on-chain
exactly like a Solana pack's — same key, same cc-vrf program on Solana, same reconcile job
— so the roll carries a chain-anchored commitment on both machines, and the card anchor is
chain-anchored on Solana only.

## When your card is decided​

Short version: your card is decided the moment you sign. Not when the pack opens.

Opening the pack does not pick anything. It hands you the card that was already picked.

### The simple version​

Think of a real pack of cards in a shop. The card is inside the pack before you buy it. You
don't know which card it is. The shop doesn't either. Tearing the wrapper doesn't choose the
card — it only shows you the card that was always in there.

Ours works the same way, in this order:

- The list already exists. We do not build a list for your pack. The machine keeps one
standing list of every card you could win, with a version number and a version_root
fingerprint, and rebuilds it every 15 to 60 seconds as inventory moves. When your pack is
created — before you pay — we write that version number onto your pack. That is all that
happens: your pack gets tied to a list that was already frozen, usually seconds earlier,
while somebody else was buying. We can't quietly change it afterwards, because changing
the list changes the fingerprint.

- You sign. That is the moment it's decided. Your signature is the input. We run it
through the VRF with our secret key, and that gives one output, beta. beta decides
everything: your tier, and then the shuffled order of every card in that tier. Your
first-choice card, your second, your third — the whole order is fixed right there, in one
step. Neither side can steer it: we can't pick your signature, and you can't work out the
VRF output without our key.

- Opening delivers it. The animation, the transfer, the mint — that's the wrapper coming
off. No new randomness happens. Nothing is drawn.

The comparison holds for the part that matters — the outcome is fixed before you open —
but be clear on where it stops. A shop pack physically holds one card, and nobody else can
take that card. Ours fixes a decided order over shared inventory. So if another buyer
reaches your first card before you open, you get the next one down your own list. That is the
one moving part, and the next section is about it.

### So what can change between signing and opening?​

One thing only: somebody else may have already taken the card at the top of your list.

Other people are buying from the same inventory. If your first-choice card is gone, you get
the next card on your list. That order was fixed when you signed — so the "backup" was
decided at the same instant as the first choice. We are not picking your replacement. We are
reading down an order you can recompute yourself.

That's why Step 2 uses a shuffle of the whole tier instead of a single index. A single index
could land on a card that's already gone, and then somebody would have to decide what happens
next. With a full shuffled order, there is nothing left to decide.

### Why we built it this way​

Because it matches the physical thing. A card is in a pack from the moment the pack is
sealed. The alternative — rolling at the instant you click open — would decide your outcome
after you had already committed your money. We would rather the outcome be locked at the
moment you commit, and be provable after the fact.

### Exact order of events​

For the record, precisely. "Decided" below means the tier and the full card order are
mathematically fixed and cannot be changed by anyone, including us.

Chain
The list is frozen
Your pack is tied to it
Your card is decided

Solana

on a rolling 15–60s rebuild, before your pack exists

when the pack is created, before you pay

when you sign the payment transaction

EVM

the same rebuild, before your pack exists

when the pack is created, before you pay

when you sign the payment transaction — its hash is the VRF input

Read the three columns in order. Nothing about your outcome is decided in the last step of
that flow. The list is frozen first, your pack is tied to it second, and your signature
decides the result third. Opening the pack is a fourth step that decides nothing.

One more detail, since it affects what "already taken" means: the ownership timeline
(ownership_seq) is a single global stream shared by both machines. A card claimed by a
Solana pack and a card claimed by an EVM pack land in the same ordering, so a verifier on
either chain replays the same history.

## How proofs are committed on-chain​

The VRF proofs are committed through cc-vrf, a standalone, permissionless on-chain VRF
system for Solana (program ccvrfu3fSpbnPLiUqdWAt85Zn9nq96ekwGTbHqGtdgQ, live on
mainnet + devnet). The commit process:

- Register and freeze a key. The operator registers its VRF public key on-chain as a
VrfAuthority, then calls freeze_authority — a one-way action. After freezing, the
public key and ciphersuite are permanent and cannot be swapped.

- Commit each proof. For every pack, after producing the proof we call
commit_proof_with_beta, which writes a Light Protocol compressed PDA storing
SHA-256(proof), SHA-256(alpha), SHA-256(memo), the slot, and the 64-byte beta.
The PDA address is derived from (authority, memo_hash), so the chain enforces one
commit per memo — a proof can't be silently replaced later without it being detectable.

So each pack carries two independent on-chain commitments:

- the cc-vrf commit — proves the roll's beta came from our frozen key over your
alpha; and

- the sel_anchor memo on the award transaction — pins which card you got, over which
committed candidate set.

Verification (/api/vrf/verify) re-runs the ECVRF math off-chain and fetches the
on-chain commit + authority to confirm the authority is frozen and unrevoked, the committed
hashes match, and the recomputed sel_anchor equals the one in the award memo.

### Which commit mode we use​

The cc-vrf program offers three commit instructions. We use the richest one:

Instruction
What lands on-chain
Used

commit_proof_event

an event log only — no account

no

commit_proof

memo hash + proof hash + alpha hash (136 bytes)

no

commit_proof_with_beta

those three hashes plus the full 64-byte beta (200 bytes)

yes

Storing beta in the clear is what lets another Solana program read the random value
directly, and lets a verifier compare the beta it derives from the proof against the one
that was committed. The verify page's registry-beta mode is the one that checks it.

### What the commit record contains​

The compressed PDA is exactly 200 bytes, in this order:

Offset
Size
Field

0

32

authority address

32

32

SHA-256(memo)

64

32

SHA-256(proof)

96

32

SHA-256(alpha)

128

64

beta (stored as two 32-byte halves, beta_lo + beta_hi)

192

8

committed_slot (u64 LE)

memo, alpha and proof are stored as fingerprints, not as raw values. A fingerprint
can't be reversed, but it can't be lied about either: once it's on-chain, the only values
that will ever match it are the originals. We publish the originals through
/api/vrf/verify, and anyone can re-hash them and compare.

beta is the exception — it goes on-chain raw. That's deliberate (see above).

### How the on-chain hash is built​

Two different hashings get confused for each other, so to be explicit:

- beta = proof_to_hash(proof) makes the random number. Deterministic — the same proof
always yields the same beta.

- The SHA-256 fingerprints above have nothing to do with randomness. They only lock the
values in place.

The record itself is anchored to Solana in four rungs:

- Fingerprints. We SHA-256 the memo, the alpha and the proof before sending anything.

- Data hash. Light Protocol squeezes the 200-byte record into a single 32-byte data
hash (Poseidon, not SHA-256).

- Leaf hash. That data hash is combined with the record's identity — program ID, state
tree, leaf index, compressed address, account discriminator — into one leaf hash.

- Merkle root. The leaf is inserted into a Light state Merkle tree whose root lives in
a real on-chain account.

So one 32-byte root covers the whole record. Change a single byte anywhere below it — swap
the proof, nudge the alpha, edit the roll — and the root no longer matches what the chain
holds.

## Worked example — from a memo to the on-chain transaction​

Real mainnet pack. Memo cc-77161af0-8001-425b-9213-e5e1d24083d6 (pokemon_50, 2026-08-07).

Steps 1–4 are pure math — no network, no API, nothing from us. Steps 5–6 read the chain.

1. Start with the memo. It's printed on your pack.

cc-77161af0-8001-425b-9213-e5e1d24083d6

2. Hash it.

SHA-256(memo) = 0x46f31a79c1ae2b87999094278a29f0c6f50843998112fb10fb2e97511629c841

3. Derive the authority address from "vrf_authority" || owner || label, where the owner
is the gacha wallet GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3 and the label is gacha:

13C5cbemzwSg5wNerJDucU5uUJ1kHQENDqoTa3VSAHau

4. Derive the commit address from "vrf_proof" || authority || memo_hash:

1fNrGDCyJrKBEheLcvhTKJXkLrAmWsM7FNXP7cR1hNF

Nothing secret went into that. Anyone holding the memo lands on that exact address — which
is also why we can't hide a commit or write a second one for the same pack. The address is
already taken.

5. Read the record. Leaf 744951 in state tree
bmt1LryLZUMmF7ZtqESaw7wifBXLfXHQYoE4GAmrahU. Its 200 bytes decode to:

authority 008fb0761e0d68e818644fe8f6fee08de44858c5e6e3c891364c441e5847c666
memo hash 46f31a79c1ae2b87999094278a29f0c6f50843998112fb10fb2e97511629c841
proof hash 23c025b668c5eee717756a4e519435cf553331fd83173c116a331fb374d6e62c
alpha hash a35e5296e8596a17f723ba7ee60fb91274d2865590cdc10e3507dbcc0d32e3b0
beta e15d44f4181c1a9016a0589be046ef3c3fbc779b5767ca5ebfb65abe2c4014ba
 6568514ccb234c808fee0912658e1ff1479ca5c6915e3433a673ac5a9a1ac351
slot f734191a00000000 → 437,859,575

6. Ask which transaction created that leaf.

2PnAaXGBtutqXah7rmZA7Fj6Mu4GMGRwUwKbeDtmhuXaaQYb7djwniJM73PD5pSxAqDNJsBrXD8PEd4oU63ujpWD
slot 437,859,575 — 2026-08-07 20:51:27 UTC

That signature is a normal Solana transaction. Open it in any explorer and the logs read:

Program ccvrfu3fSpbnPLiUqdWAt85Zn9nq96ekwGTbHqGtdgQ invoke [1]
Program log: Instruction: CommitProofWithBeta

caution

Paste the transaction signature into an explorer, not the commit address. The commit
address is a Light Protocol compressed address — it isn't a regular Solana account, so
standard explorers won't find it. Use the Lookup page at
vrf.collectorcrypt.com for compressed addresses.

### Checking the values against that record​

The published proof and alpha for this pack (from /api/vrf/verify?memo=…):

alpha 0x800fb99a079d0823110497f6d41d56672c55a58e556426303d3541884f7ed1f1
proof 0x0dfc748650f44a04f9726f3155f0202ef69a1bd0eda7fd9e684cc5ab707ed2c7
 5de8c77faa88f920203d26739ae2c193bf15b93474e055886b67aad727e19fca
 1fb83aaaa50939d54eef6d02ae83df06

Five checks, all reproducible:

Check
Result

SHA-256("ccgacha-vrf-v1\0" ‖ your signature) == alpha

matches — the input came from the buyer's own signature 2hdYcPFQ…hvE2

verifyVRF(pk, alpha, proof) under the frozen key 0x115c9962…cb83

valid

SHA-256(memo) / SHA-256(alpha) / SHA-256(proof) == the three on-chain fingerprints

all three match

proof_to_hash(proof) == the on-chain beta

matches

beta[0..8] → the roll

16,239,211,646,535,080,592 mod 100,000,000 + 1 = 35,080,593 — the stored roll

And the card, from the award transaction
io6XatGJb1TogSGEBpQQC7QP8QGLH3QTfTqqeLzy9x1PZBTadyc8pCiRyHTEiAxaYCY7zRtVsJ5HUnLaVMtvSvB,
whose on-chain memo carries the sel_anchor:

cc-77161af0-8001-425b-9213-e5e1d24083d6:send:r181ed2e79df8903b3ad811fc26ff590122ecd4442a82ccce9d690ac7e1a5968a

Recompute SHA-256(0x04 ‖ version_root ‖ ownership_seq ‖ awarded_nft) and you get that same
181ed2e7…968a. Two independent on-chain commitments, one per step.

## Why it can't be exploited​

### By us (the operator)​

- We can't precompute or steer the roll. alpha is bound to your signature, which we
don't have until you sign. There's nothing to grind against ahead of time.

- We can't retry for a better roll. RFC 9381 ECVRF yields exactly one valid proof and
one beta per (public key, alpha). Our public key is frozen on-chain and unrevoked.
Any substitute proof fails verification against the frozen key, and the original
SHA-256(proof) is already committed on-chain — so swapping it after the fact is
detectable.

- We can't hand-pick your card. Given beta, the Feistel walk is fully determined over
the candidate set that was frozen and committed (version_root) before the pick. To
award a different card we'd have to change beta (can't — see above), the committed
candidate set, or the timeline position — each of which changes the sel_anchor, which is
pinned to the immutable award-transaction memo. Any mismatch shows up as NOT VERIFIED.

- We can't quietly shrink the pool to withhold a card. All four tier roots and counts
are folded into version_root; removing or altering any card changes the root.

### By you (the buyer)​

- You can't predict the output. Computing beta from alpha requires the VRF secret
key, which only we hold. You choose your alpha (indirectly, via your signature), but the
VRF's unpredictability means you can't find a signature that yields a favorable roll
without breaking the VRF.

- You can't choose your card. It's a deterministic function of a beta you can't
predict.

- You can't forge or replay a different outcome. You can verify a proof after the
fact, but only the holder of the secret key can produce a valid one.

### The "memo selection" angle​

The only theoretical lever in any commit-style VRF is choosing which committed input to
honor. We remove it by binding alpha to your own wallet signature and issuing the memo
before you sign: we can't choose your signature, and you can't compute the VRF to know which
signature would be favorable. Neither side can shop for an outcome.

## Verify your pack yourself​

- Card selection (full replay) — open /verify-selection/YOUR_MEMO. Entirely in
your browser, it re-fetches the pinned candidate set, recomputes the Merkle and version
roots, replays the Feistel walk from beta, and hard-checks the recomputed sel_anchor
against the on-chain memo. The frozen candidate set for a pool version is stored durably, so
a pack stays fully replayable indefinitely — there is no expiry window. If a candidate
set ever cannot be reproduced (a pool version predating the durable leaf log, or a
reconstruction whose root does not match what was committed), the page says so rather than
guessing, and the roll and on-chain anchor remain independently verifiable on their own.

- Roll (proof + roll match) — GET /api/vrf/verify?memo=YOUR_MEMO returns the proof,
public key, alpha/beta, the on-chain commit status, the awarded transaction signature,
and whether the stored roll matches the recomputed roll.

The browser verifier shows these checks, all of which must pass for a green VERIFIED:

Check
What it proves

Roll verified (cc-vrf, not degraded)

the roll is a genuine ECVRF roll from our frozen key

Merkle root of candidates matches

the published candidate set is the one that was committed

Selection anchor matches

hard against the on-chain award memo on Solana; on EVM a soft match against the published anchor, because an EVM mint carries no memo

Roll maps to the awarded tier

the verified roll, classified under the odds this pack was sold at, gives your tier

Feistel walk lands on your card

replaying the shuffle from beta reproduces your exact card

Awarded value within the tier band

your card's insured value is inside the tier's published band

## Precise construction (for re-implementers)​

All hashes are SHA-256. || is byte concatenation. Mint addresses are base58-decoded to
their raw 32 bytes. These constants are a frozen contract — they never change, or
verification of past packs would break. The reference implementation is isomorphic (the
same code runs on our server and in your browser).

roll = (beta[0..8] as u64 BE) mod 100_000_000 + 1
selection seed= beta[8..24] # 16 bytes; beta[24..] reserved

leaf(nft,val) = SHA-256( 0x00 || nft(32B) || cents(val) as u64 BE )
node(L,R) = SHA-256( 0x01 || L || R ) # odd level duplicates the last node
tier_root = Merkle root of the tier's leaves # empty tier => 32 zero bytes
version_root = SHA-256( 0x02 || version(u64 BE)
 || root_epic || root_rare || root_uncommon || root_common
 || count_epic || count_rare || count_uncommon || count_common ) # counts are u32 BE
sel_anchor = SHA-256( 0x04 || version_root || ownership_seq(u64 BE) || awarded_nft(32B) )

# Feistel permutation over [0, len): 4-round alternating additive Feistel, cycle-walked
# down to the exact domain. Round function:
F(seed16, round, half) = SHA-256( "ccgacha-sel-v1\0" || seed16 || round(u8) || half(u32 BE) ),
 folded to 48 bits, then reduced mod the half's size.

cents(val) mirrors round(insured_value * 100). The on-chain memo carries sel_anchor
as a trailing :r<64-hex> segment (fixed width, so legacy memos still parse).

## Spec & source​

- Standalone VRF verifier & internals — vrf.collectorcrypt.com

- cc-vrf (program + SDK + ECVRF library), MIT — github.com/collectorcrypt/cc-vrf

- On-chain program — ccvrfu3fSpbnPLiUqdWAt85Zn9nq96ekwGTbHqGtdgQ

- VRF standard — RFC 9381: Verifiable Random Functions (VRFs) (ciphersuite ECVRF-EDWARDS25519-SHA512-TAI)

- Packages — @collectorcrypt/ecvrf (RFC 9381 ECVRF) and @collectorcrypt/vrf-client (Solana SDK: verifyAuthorityCommitEndToEnd, pickCanonicalCommit)

Previous

Gacha

Next

API Docs

- At a glance

- Step 1 — The roll picks your tier

- Step 2 — The leaf pool and the Feistel walk pick your card
- The leaf pool (the committed candidate set)

- The Feistel walk

- sel_anchor — the on-chain commitment to your card

- When your card is decided
- The simple version

- So what can change between signing and opening?

- Why we built it this way

- Exact order of events

- How proofs are committed on-chain
- Which commit mode we use

- What the commit record contains

- How the on-chain hash is built

- Worked example — from a memo to the on-chain transaction
- Checking the values against that record

- Why it can't be exploited
- By us (the operator)

- By you (the buyer)

- The "memo selection" angle

- Verify your pack yourself

- Precise construction (for re-implementers)

- Spec & source

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

