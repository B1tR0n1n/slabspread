# Fixture: https://phygitals.mintlify.app/public-api/authentication.md
Fetched: 2026-09-26T00:20:22Z

> ## Documentation Index
> Fetch the complete documentation index at: https://dev.phygitals.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Authentication

> How to send user API keys, what scopes authorize, and how the API responds to auth failures.

Every authenticated Public API request must include a valid user API key. Keys are issued per Phygitals account and act on behalf of that account.

## API key format

User API keys:

* Start with the prefix `phy_`
* Are shown in full **only once** when you create the key
* Are stored by Phygitals as a hash — lost secrets cannot be recovered; revoke and create a new key instead

After creation, the **Settings** page shows only a short prefix (for example `phy_AbCdEfGh`) so you can tell keys apart.

## Sending your key

Include the key on every authenticated request using either header:

<CodeGroup>
  ```http X-API-Key theme={"dark"}
  X-API-Key: phy_your_secret_key_here
  ```

  ```http Bearer theme={"dark"}
  Authorization: Bearer phy_your_secret_key_here
  ```
</CodeGroup>

<Warning>
  Treat API keys like passwords. Store them in a secrets manager or environment variable. Never commit them to source control or embed them in client-side code.
</Warning>

## Scopes

Each key is granted access to the following scopes:

| Scope                       | Endpoints                                                                                                        |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `vm.buy.crypto`             | `POST /api/vm/buy/crypto`, `POST /api/vm/buy/status`                                                             |
| `marketplace.take-claw-bid` | `POST /api/marketplace/transaction/take-claw-bid-init`, `POST /api/marketplace/transaction/take-claw-bid-finish` |

New keys receive both scopes. A request to an endpoint without the matching scope returns `401`.

## Alternative authentication

The same endpoints also accept a Phygitals session token (`Authorization: Bearer <jwt>`) when you are logged in through the web app. API keys are intended for server-side automation where a browser session is not available.

## Error responses

| Status | Body                                              | When                                                                 |
| ------ | ------------------------------------------------- | -------------------------------------------------------------------- |
| `401`  | `{ "message": "Invalid or missing credentials" }` | Missing key, invalid key, expired key, revoked key, or missing scope |
| `401`  | `{ "message": "No token provided" }`              | No key and no session token                                          |
| `401`  | `{ "message": "Invalid token" }`                  | Session token present but invalid                                    |
| `429`  | `{ "message": "Rate limit exceeded" }`            | Too many requests for the same key (see below)                       |

## Rate limits

API key traffic is rate-limited per key. Session-authenticated requests from the web app are not subject to these limits.

| Endpoint                                                 | Limit                    |
| -------------------------------------------------------- | ------------------------ |
| `POST /api/vm/buy/crypto`                                | 1 request per 60 seconds |
| `POST /api/marketplace/transaction/take-claw-bid-init`   | 1 request per 5 seconds  |
| `POST /api/marketplace/transaction/take-claw-bid-finish` | 1 request per second     |

When rate-limited, wait for the window to pass before retrying.

## Key lifecycle

A key is rejected when any of the following is true:

* The key has been **revoked**
* The key has **expired** (unless you chose "never expires" at creation)
* API keys have been **disabled** for your account

Revoked and expired keys return the same `401` response as an invalid key. Check key status in **Settings → API keys** before debugging integration issues.
