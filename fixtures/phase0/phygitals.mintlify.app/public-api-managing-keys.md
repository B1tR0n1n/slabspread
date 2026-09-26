# Fixture: https://phygitals.mintlify.app/public-api/managing-keys.md
Fetched: 2026-09-26T00:20:22Z

> ## Documentation Index
> Fetch the complete documentation index at: https://dev.phygitals.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Managing API keys

> Eligibility requirements, creating and revoking keys, and expiration behavior.

API keys are self-managed from your Phygitals account. There is no separate key-management API — create, list, update, and revoke keys from **Settings → API keys** on [phygitals.com](https://phygitals.com) while logged in.

## Eligibility

Before you can create a key, your account must meet both requirements:

1. **API keys enabled** — available on eligible accounts. If the section is unavailable, contact [hello@phygitals.com](mailto:hello@phygitals.com).
2. **External Solana wallet linked** — a self-custodied Solana wallet connected to your account. Embedded or custodial wallets do not qualify.

The Settings page shows specific reasons when you are not eligible.

## Creating a key

<Steps>
  <Step title="Open Settings">
    Go to [phygitals.com/settings](https://phygitals.com/settings) and find the **API keys** section.
  </Step>

  <Step title="Name the key">
    Choose a descriptive name (for example `production-bot` or `buyback-script`). Names help you identify keys later — only the prefix of the secret is shown after creation.
  </Step>

  <Step title="Set expiration">
    Choose **Never expires** or pick a future date and time. Expired keys stop working immediately.
  </Step>

  <Step title="Copy the secret">
    The full key (`phy_…`) is displayed once. Copy it to your secrets manager before closing the dialog. You cannot view it again.
  </Step>
</Steps>

### Limits

* Up to **10 active keys** per account at a time
* Revoke unused keys before creating new ones if you hit the limit

## Listing keys

The Settings page lists all active keys with:

| Field         | Description                                               |
| ------------- | --------------------------------------------------------- |
| **Name**      | Label you chose at creation                               |
| **Prefix**    | First characters of the secret (for identification only)  |
| **Scopes**    | `vm.buy.crypto`, `marketplace.take-claw-bid`              |
| **Expires**   | Expiration date, or "Never"                               |
| **Last used** | Approximate time of the most recent authenticated request |

## Updating expiration

You can change a key's expiration from Settings:

* Switch between **Never expires** and a specific date
* Set a new future expiration on an existing key

Revoked keys cannot be updated. Create a new key instead.

## Revoking a key

Revocation is immediate and permanent. A revoked key returns `401` on the next request. Revoke keys you no longer use — especially if a secret may have been exposed.

<Warning>
  Revocation cannot be undone. Generate a new key if you still need programmatic access.
</Warning>

## Security practices

* **One key per integration** — use separate keys for different scripts or environments so you can revoke individually
* **Rotate on exposure** — if a secret leaks, revoke it immediately and create a replacement
* **Prefer short expirations** for experimental or temporary automation
* **Server-side only** — keys authenticate as you; never ship them to browsers or mobile clients
