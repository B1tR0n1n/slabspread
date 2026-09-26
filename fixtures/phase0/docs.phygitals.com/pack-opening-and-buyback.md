---
url: https://docs.phygitals.com/platform-features/pack-opening-and-buyback (fetched as .md)
fetched_at: 2026-09-26T00:22:44Z
status: 200
---

> For the complete documentation index, see [llms.txt](https://docs.phygitals.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.phygitals.com/platform-features/pack-opening-and-buyback.md).

# Pack Opening & Buyback

Everything you need to know about purchasing and opening digital packs, the buyback system, buyback rates, and card availability windows on Phygitals.

### Overview

Packs are the primary way to discover and collect trading cards on Phygitals. Each pack contains a randomized selection of real, professionally graded physical trading cards that have been digitized as digital collectibles on the platform. When you open a pack, the cards you receive correspond to actual physical cards securely stored in our vault network.

To provide instant liquidity, Phygitals offers a **buyback system** that allows you to sell cards back to the platform at a percentage of their Fair Market Value (FMV) after pulling them. This provides an optional, time-limited liquidity option on recent pulls, subject to availability and the terms described below.

**Regulatory characterization:** Pack purchases are purchases of digital goods with randomized contents, analogous to the purchase of sealed physical trading card products (e.g., booster packs). Pack outcomes are determined entirely by a cryptographic algorithm with no human involvement in the selection process. While Phygitals does not intend for pack openings to constitute gambling and does not market them as such, regulatory definitions vary by jurisdiction. For jurisdictions where randomized reward mechanics may be regulated, see our Restricted Jurisdictions page.

### Available Packs

Packs are available at **various price points as displayed on the platform**. Higher-priced packs contain cards of greater value and rarity. The specific packs available at any given time may vary based on inventory and featured collections.

Available collections include **Pokémon TCG** (primary), **Baseball**, **Football**, **Soccer**, **Basketball**, **One Piece**, **Riftbound**, **Dragon Ball,** **Yu-Gi-Oh!** and other select collectible card series.

All pack purchases can be made via **credit card**, **wallet balance** (USDC or USDT), or a **hybrid** combination of wallet funds and credit card. Voucher and promo codes may also be applied at checkout where available.

### Pack Contents

Each pack contains a randomized assortment of digitized trading cards. The contents are determined by the pack tier and the available card pool at the time of opening. Key details:

* **Real physical cards** - Every card in a pack corresponds to a real, professionally graded physical card stored in our vault network.
* **Defined rarity distributions** - Each pack tier has a defined probability distribution for card rarities. These distributions are part of the provably fair record for each opening.
* **Fair Market Value (FMV)** - Each card has an FMV sourced from industry-standard pricing providers for graded collectibles.
* **Digital ownership** - Cards are digitized and secured in our digital custody system, giving you verifiable ownership of each card.

### Opening Experience

The pack opening experience on Phygitals is designed to be engaging and interactive:

* **Interactive reveal** - After purchasing a pack, you open it through an animated reveal experience. Cards are unveiled one at a time with visual effects that reflect the rarity of each pull.
* **Rarity effects** - Special animations and effects highlight rare and high-value pulls, making every opening exciting.
* **Instant ownership** - As each card is revealed, it is immediately delivered to your wallet as a digital collectible. You own it the moment it appears on screen.
* **Buyback offers** - After the reveal, eligible buyback offers appear for your pulled cards. You have a limited window to accept these offers (see Buyback System below).

### Buyback System

The Phygitals buyback system provides **instant liquidity** on cards pulled from packs. After opening a pack, you may be presented with an offer to sell one or more of your pulled cards back to the platform at a percentage of the card's Fair Market Value (FMV).

Key details of the buyback system:

* **Automatic offers** - Buyback offers are generated automatically after eligible pack openings, based on the pack tier you purchased.
* **Default buyback rate** - The standard buyback rate is **85% of FMV**. Some packs may offer enhanced buyback rates above 85%, which will be clearly indicated on the pack before purchase.
* **USDC payouts** - All buyback payouts are denominated and paid in **USDC** (a USD-pegged stablecoin), delivered directly to your wallet.
* **Time-limited** - Buyback offers have a limited acceptance window that varies by card type (see Buyback Windows below). Once the window closes, the offer is permanently unavailable.
* **Optional** - Accepting a buyback offer is entirely optional. You are free to keep any card you pull and trade it on the marketplace, hold it, or redeem the physical card.
* **One-time offer** - Each buyback offer is presented once per card. If you decline or let it expire, it cannot be reinstated.

### Buyback Rates

The buyback rate determines what percentage of a card's Fair Market Value you receive when you sell it back to the platform:

* **Standard rate: 85% of FMV** - This is the default buyback rate for all packs. For example, if you pull a card with an FMV of $100, the buyback offer would be $85.
* **Enhanced rates** - Some packs offer buyback rates above 85%. When a pack has an enhanced buyback rate, a badge is displayed on the pack before purchase so you know the exact rate in advance.

**Important notes:**

* The applicable buyback rate and dollar amount for your pull is clearly displayed before you accept or decline the offer.
* FMV is determined at the time of the pull using pricing data from industry-standard pricing providers for graded collectibles.
* Buyback payouts are processed immediately upon acceptance and delivered as USDC to your wallet.
* Phygitals reserves the right to modify buyback rates, tier structures, and eligibility criteria at any time without prior notice. The rate displayed at the time of your specific offer is the rate that applies to that offer.

### Buyback Windows

Buyback offers are time-sensitive. The acceptance window varies depending on the card type:

* **Standard cards:** **30-minute** buyback window.
* **Sealed product cards:** **3-day** buyback window.
* **Inventory cards:** **7-day** buyback window.

The applicable window for each card is clearly displayed alongside the buyback offer at the time of your pull.

Key rules:

* **Countdown starts at reveal** - The buyback window begins the moment your pack opening is complete and your cards are revealed.
* **Permanent expiration** - Once the buyback window closes, the offer is permanently removed. It cannot be extended, reopened, or reinstated under any circumstances.
* **No obligation** - You are under no obligation to accept any buyback offer. If you prefer to keep, trade, or hold a card, simply let the offer expire.
* **Partial acceptance** - If you pull multiple cards, you may accept buyback offers on some cards and decline others. Each card's offer is independent.

We recommend reviewing your buyback offers promptly after each pack opening to ensure you do not miss any offers you wish to accept.

### Provable Fairness

Every pack opening on Phygitals is **provably fair**. The contents of your pack are determined by a cryptographic commit-reveal scheme that combines a server seed and a client seed, ensuring that neither the platform nor the user can manipulate the outcome.

* Before each opening, the server commits a hash of its seed, locking in its contribution to the outcome.
* A client seed unique to you and the transaction is used as the second input.
* The algorithm that combines these seeds to determine your cards is publicly disclosed.
* After the opening, the server seed is revealed so you can independently verify the result.

For a detailed explanation of how provable fairness works, including step-by-step verification instructions, visit our Provable Fairness documentation page. You can view all of your personal fairness proofs at [/fairness](http://localhost:5173/fairness).

### Contact

If you have questions about packs, the buyback system, or card availability, our support team is ready to assist.

* **Support:** <https://www.phygitals.com/contact>
* **Legal:** <legal@phygitals.com>

