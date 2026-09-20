# X OAuth / API Integration

The Storycrafting Gamer can authorize an X account using OAuth 2.0 Authorization Code with PKCE and publish posts through the X API.

## Setup

1. Create/configure an X Developer App.
2. Enable OAuth 2.0.
3. Add this exact callback URL:

`http://127.0.0.1:8765/callback`

4. Copy `config/.env.example` to `config/.env`.
5. Put the X OAuth 2.0 Client ID in `config/.env`.
6. Run `Storycrafting-Gamer-AI.bat`.
7. Choose **Connect / authorize X account** and complete X's authorization page.

The integration requests `tweet.read`, `tweet.write`, `users.read`, and `offline.access`.

## Commands

`python social\\x_oauth.py connect` — authorize the X account.

`python social\\x_oauth.py status` — verify the authorized account.

`python social\\x_oauth.py post "Your post text"` — publish a post through the X API.

Tokens are stored locally in `config/x_tokens.json` and are excluded by `.gitignore`. Never commit OAuth tokens, client secrets, or other credentials.

The integration uses X's API rather than browser automation and uses PKCE/state validation for the local OAuth flow.
