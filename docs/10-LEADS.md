# Lead Finder: real, qualified business leads (for the CallMate AI demo)

What it does:
1. Finds real businesses on Google Maps (e.g. *dental clinic in Ahmedabad*).
2. Reads their Google reviews for call problems ("nobody picks up", "couldn't reach them"…).
3. Checks their website: online booking? public email? doctor/owner name?
4. Ranks them best-first and writes a personal outreach message for each (with your OpenAI key).
5. Gives you an **HTML page** (to screenshot / send) and a **CSV** (opens in Excel or Google Sheets).

Everything comes from Google Maps or the business's own website. Nothing is made up.

---

## PART A: Get a free SerpApi key (one time, 3 minutes, no card)

SerpApi gives the same Google Maps data (phone, website, rating, reviews). Free plan: **250 searches a month**,
no card. One 10-lead demo uses about **13 searches**.

**A1.** Open **https://serpapi.com/users/sign_up** → sign up with your email (or Google login) → verify your email.

**A2.** Open **https://serpapi.com/manage-api-key** → click the copy icon next to **Your Private API Key**.

That's it. (If SerpApi asks to verify a phone number, do it: it's free.)

*Other option: the official Google Places API (needs a card on Google Cloud). Put `GOOGLE_MAPS_KEY=...` in
`.env`, add `LEADS_SOURCE=google`, and press Enter when asked for the SerpApi key.*

## PART B: Make the leads (2 minutes)

**B1.** Double-click **`update.bat`** (gets the Lead Finder).

**B2.** Double-click **`leads.bat`**.
- First time only: paste your **SerpApi key** → Enter. It's saved in `.env`.
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
| `SerpApi said 401` / `Invalid API key` | Key copied wrong. Open `.env` in Notepad, delete the `SERPAPI_KEY=` line, save, run `leads.bat` again. |
| `run out of searches` | Free plan used up for this month. It resets next month. For client work, the client's own SerpApi plan pays for searches. |
| `Google Maps said 403` | (Google option only) Places API (New) not enabled or billing not linked. |
| Messages look basic | The AI was busy, so the safe template was used. Just run it again. |
