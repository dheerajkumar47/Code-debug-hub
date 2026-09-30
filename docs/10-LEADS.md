# Lead Finder: real, qualified business leads (for the CallMate AI demo)

What it does:
1. Finds real businesses on Google Maps (e.g. *dental clinic in Ahmedabad*).
2. Reads their Google reviews for call problems ("nobody picks up", "couldn't reach them"…).
3. Checks their website: online booking? public email? doctor/owner name?
4. Ranks them best-first and writes a personal outreach message for each (with your OpenAI key).
5. Gives you an **HTML page** (to screenshot / send) and a **CSV** (opens in Excel or Google Sheets).

Everything comes from Google Maps or the business's own website. Nothing is made up.

---

## PART A: Get a Google Maps key (one time, 5 minutes)

**A1.** Open **https://console.cloud.google.com** → log in with your Google account.

**A2.** Top bar → project dropdown → **New project** → name `leadfinder` → **Create** → select it.

**A3.** Left menu **Billing** → link a billing account (add your card).
Google gives a **free monthly allowance**. A 10-lead demo uses only about 3 searches, so it costs **$0**.

**A4.** Search bar at the top → type **Places API (New)** → open it → **Enable**.

**A5.** Left menu **APIs & Services → Credentials** → **+ Create credentials → API key** → **copy** it (starts with `AIza`).

**A6.** Click the new key → **API restrictions → Restrict key** → tick **Places API (New)** → **Save**.

(Safety: optional, but good. **Billing → Budgets & alerts → Create budget → $5** sends you an email if anything is ever charged.)

## PART B: Make the leads (2 minutes)

**B1.** Double-click **`update.bat`** (gets the Lead Finder).

**B2.** Double-click **`leads.bat`**.
- First time only: paste your Google Maps key → Enter. It's saved in `.env`.
- **Industry** → e.g. `dental clinic` → Enter
- **City** → e.g. `Ahmedabad` → Enter
- **How many leads?** → `10` → Enter

**B3.** Wait about 1 minute. Then open the folder **`data\leads`**:
- **`dental-clinic-ahmedabad.html`** → double-click → opens in your browser. Take screenshots for the client.
- **`dental-clinic-ahmedabad.csv`** → opens in Excel, or upload it to Google Sheets (File → Import).

## PART C: Before you send it to the client

- Open the HTML and **read every lead**. Remove any that look wrong (closed, a chain, a hospital, etc.).
- Send **screenshots or the Google Sheet** inside Freelancer chat. Don't send the program itself.
- The demo shows the result. The program is what he pays for.

## If it fails

| Message | Fix |
|---|---|
| `Google Maps said 403` | Places API (New) isn't enabled (A4), or the key is restricted to the wrong API (A6), or billing isn't linked (A3). |
| `Google Maps said 400` | The key is wrong. Delete the `GOOGLE_MAPS_KEY=` line in `.env` and run `leads.bat` again. |
| Messages look basic | The AI was busy, so the safe template was used. Just run it again. |
