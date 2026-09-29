# Quick Start: Running in 15 Minutes

You need **2 keys** and **1 double-click**. WhatsApp is optional and can wait. You approve bids from a web
page on your phone instead.

## What you need
| # | What | Where | Time |
|---|---|---|---|
| 1 | **Freelancer token** | https://accounts.freelancer.com/settings/develop → blue **Generate Token** button → copy it | 2 min |
| 2 | **Gemini API key** (free) | https://aistudio.google.com → **Get API key** → **Create API key** → copy it | 2 min |
| 3 | **Python 3.11+** on your PC | https://www.python.org/downloads/ → install and **tick "Add python.exe to PATH"** | 5 min |
| 4 | **The code** | https://github.com/dheerajkumar47/Code-debug-hub → switch to branch `claude/funny-noether-d41u0f` → **Code → Download ZIP** → unzip | 2 min |

## Start
1. Open the unzipped folder and **double-click `start.bat`**. (Mac/Linux: run `./start.sh`.)
2. The first time, it asks for:
   - the **Freelancer token** (paste it; it stays hidden while you paste, which is normal)
   - the AI provider (press **Enter** for Gemini)
   - the **Gemini key** (paste it)
   - "Set up WhatsApp now?" (press **Enter** to skip for now)
3. It prints your **dashboard password**. Save it.
4. It runs checks. You should see ✅ lines, then it starts and shows:
   ```
   Dashboard on this PC:     http://localhost:8000
   Dashboard on your phone:  http://192.168.x.x:8000   (same Wi-Fi)
   ```
5. Open the phone link, log in as `owner` with the saved password, and bookmark it.

Keep the black window open. The bot searches every 3 minutes while it runs.

## Daily use (2 minutes per project)
Each card shows the **score**, **why it matched**, the **price**, and a **ready proposal**.
- Read it and fix anything you want in the text box. Change the price or days if needed, then press **Save**.
- **✅ Place bid** submits it. **⏭ Skip** ignores it. **🔁 Regenerate** writes a new version.
- If "Place bid" ever says the token can't place bids, press **📋 Copy** → **↗ Open**, and paste the bid on Freelancer yourself. Everything else still saves you time.

## Tuned to save your limited bids
- Only projects scoring **70+** reach you (`SCORE_THRESHOLD` in `.env`; lower it to 60 if you get too few).
- It skips projects that already have **40+ bids** and projects **older than 12 hours**.
- It never places more than **5 bids a day** automatically, and never places one without your tap.
- Small, fresh projects with new clients score higher. These are the best way to win your **first reviews**.

## Later (optional): WhatsApp buttons
When you have 30 minutes, follow **[04-setup.md → WhatsApp](04-setup.md#2-whatsapp-cloud-api-about-20-min)**, then run `python -m bidsmith setup` again and answer **y** to WhatsApp.

## If something fails
| You see | Do this |
|---|---|
| `python is not recognized` | Reinstall Python and tick **Add to PATH** |
| ❌ Freelancer API error 401 | The token is wrong or expired. Generate a new one and run `python -m bidsmith setup` |
| ❌ AI key error | Paste the Gemini key again with `python -m bidsmith setup` |
| The phone can't open the dashboard | Make sure the phone and PC are on the same Wi-Fi, then allow Python in the Windows Firewall pop-up |
| No cards after an hour | Lower `SCORE_THRESHOLD` to 60 in `.env` and restart |
