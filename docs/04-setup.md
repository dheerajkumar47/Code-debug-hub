# Setup Guide: Running BidSmith with WhatsApp Approval

You'll need about 45 minutes the first time. Everything below uses **free tiers**.

```
Freelancer API ──► BidSmith (your PC or a free VM) ──► WhatsApp card [✅ Bid] [✏️ Edit] [⏭ Skip]
                                   │                          │ you tap
                                   └── web dashboard ◄────────┘  (backup: any phone browser, no VPN)
```

## Why WhatsApp Cloud API (and not an unofficial WhatsApp bot)
| Option | Cost | Ban risk | Verdict |
|---|---|---|---|
| **Meta WhatsApp Cloud API (official)** | Free platform. Replies inside the 24h window are free; after 1 Oct 2026, 1,000 service messages per month per number are free | None | ✅ **Used** |
| Baileys / whatsapp-web.js / WAHA / Evolution API (unofficial) | Free | Numbers usually flagged **within 2–8 weeks** | ❌ Not used. It could get your personal WhatsApp banned. |
| Twilio WhatsApp | Paid per message | None | Possible later |
| **Web dashboard** (built in) | Free | None | ✅ Always on, as a backup |

**The 24-hour rule:** WhatsApp only lets a business number send you free-form messages and buttons for 24 hours after **you** last messaged it.
- **Easiest:** send "hi" (or `list`) to your bot once a day. That keeps the window open.
- **Optional:** create a *utility* template (see step 2.6). When the window is closed, the bot sends that template with a dashboard link.

---

## 1. Freelancer.com API token
1. Log in to Freelancer, then open **https://accounts.freelancer.com/settings/develop** (or go to *Settings → Developer / API*, via developers.freelancer.com).
2. Create an app and generate an **OAuth access token** for your own account. It needs the scopes for **basic** access and **advanced** (bidding).
3. Put it in `.env` as `FREELANCER_OAUTH_TOKEN=...`.
4. Test the token: `python -m bidsmith check` should print `OK: Freelancer user id ...`.
5. Optional: test safely against the sandbox first by setting `FREELANCER_API_URL=https://www.freelancer-sandbox.com/api`.

> ⚠️ Freelancer.com's own pages were blocked from this build environment, so the menu names above may differ slightly. The API endpoints the bot uses are taken from Freelancer's official Python SDK.

## 2. WhatsApp Cloud API (about 20 min)
1. Go to **https://developers.facebook.com** → *My Apps* → **Create app** → type **Business** → add the **WhatsApp** product.
2. In *WhatsApp → API Setup*, Meta gives you a free **test phone number**. Under "To", **add your own number** and verify it with the code. A test number can message up to 5 verified numbers, which is enough for a personal bot.
3. Copy the **Phone number ID** into `WHATSAPP_PHONE_NUMBER_ID`.
4. **Permanent token:** the token on the API Setup page expires after 24h. Instead, go to *Business Settings → System users*, add a user, assign the app with *Full control*, then **Generate token** with the `whatsapp_business_messaging` and `whatsapp_business_management` permissions. Put it in `WHATSAPP_TOKEN`.
5. Go to *App settings → Basic* → copy the **App secret** into `WHATSAPP_APP_SECRET`. The bot uses it to check that webhook calls really come from Meta.
6. *(Optional)* Go to *WhatsApp Manager → Message templates*. Create a **Utility** template named `bid_alert` with the body `New project for review: {{1}}` and set `WHATSAPP_TEMPLATE_NAME=bid_alert`.
7. Set `OWNER_WHATSAPP` to your number, digits only (e.g. `923001234567`). The bot **ignores messages from any other number**.

### Webhook (so button taps reach the bot)
The webhook needs a public HTTPS URL. Choose one:
- **On your PC (easiest):** run `docker compose up -d`. It starts BidSmith plus a free Cloudflare tunnel. Get the URL with `docker compose logs tunnel | grep trycloudflare`.
  - This quick URL **changes on every restart**. For a fixed URL, create a free named Cloudflare tunnel, or use a free VM.
- **Free always-on VM (recommended for 24/7):** use the Oracle Cloud *Always Free* ARM VM, or any $4–5/month VPS. Install Docker, then `docker compose up -d`.
  - Avoid free tiers that sleep, such as Render free. The bot needs to poll every few minutes.

Then, in Meta: *WhatsApp → Configuration → Webhook → Edit*:
- Callback URL: `https://<your-url>/webhook/whatsapp`
- Verify token: the same value as `WHATSAPP_VERIFY_TOKEN`
- Click **Verify and save**, then **subscribe to the `messages` field**.

Send "help" to the test number from your WhatsApp. You should get the command list back.

## 3. AI writer key
| Provider | Why | Setting |
|---|---|---|
| **Google Gemini** | Has a free tier; you have used it before | `LLM_PROVIDER=gemini`, key from https://aistudio.google.com |
| OpenAI | Good quality, low cost with mini models | `LLM_PROVIDER=openai` |
| Anthropic Claude | Strongest writing | `LLM_PROVIDER=anthropic` |
| Groq / OpenRouter | Cheap or free, OpenAI-compatible | `LLM_PROVIDER=openai` and `LLM_BASE_URL=...` |

Without a key the bot still works, but it uses the plainer **template drafts**, which you edit before sending.

## 4. Run
```bash
cp .env.example .env               # fill in the values above + DASHBOARD_PASSWORD
pip install -r requirements.txt
python -m bidsmith check           # verifies token + config
python -m bidsmith demo            # offline demo on sample projects (no bids placed)
python -m bidsmith serve           # starts polling + WhatsApp webhook + dashboard on :8000
# or: docker compose up -d
```
Dashboard: `http://localhost:8000` (or your tunnel URL). Log in with `DASHBOARD_USER` / `DASHBOARD_PASSWORD`.

## 5. Daily use (WhatsApp)
Each good project arrives as two messages: the full draft, then a card with the score, price and reasons plus buttons.
- **✅ Bid**: places the bid through the official API.
- **✏️ Edit**: reply with your new text. The quality checks run again and the card comes back.
- **⏭ Skip**: skips the project.

Text commands: `list`, `bid <id>`, `skip <id>`, `edit <id>`, `regen <id>`, `price <id> <amount> [days]`, `stats`, `pause`, `resume`, `help`.

## 6. Tuning (`profile/owner_profile.yaml`)
- `rates`: your floors. The bot never prices below them.
- `search.queries` / `exclude_keywords` / `max_bid_count`: what the bot looks for.
- `portfolio` / `facts`: the **only** things the writer may claim. Keep them true and up to date.
- `.env`:
  - `SCORE_THRESHOLD` (default 60): raise it if you get too many cards.
  - `AUTO_SUBMIT`: keep it `false` until you trust the drafts. Even then the bot keeps the daily cap and spacing.
