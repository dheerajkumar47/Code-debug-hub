# Lead Finder: real, qualified business leads

Type an industry and a city, and it:
1. Finds real businesses on Google Maps (area by area for more results).
2. Removes chains, shared call-centre numbers and listings without a phone.
3. Reads their Google reviews for call problems ("nobody picks up", "phone nahi uthate"…).
4. Checks each website for online booking, public email and owner/doctor name.
5. Ranks them and writes a personal outreach message for each (with your AI key).
6. Gives you a **CSV** (Excel / Google Sheets) and a **printable report** (save as PDF).

Everything comes from Google Maps or the business's own website. Nothing is made up.

---

## Folders on your Desktop

```
Desktop\
  FreelancerBot\   ← the Freelancer bid bot   (start.bat, update.bat)
  LeadFinder\      ← this tool                 (start.bat, update.bat)
```

The two are separate: each has its own `start.bat`, `update.bat`, `.env` and `data`.

## First time (3 minutes)

**1. Free SerpApi key (no card).** Sign up at **https://serpapi.com/users/sign_up**, then copy your key from
**https://serpapi.com/manage-api-key**. Free plan: 250 searches a month.

**2. Double-click `start.bat`.** The first run takes about 1 minute to set up.
- If your `FreelancerBot` folder is next to this one, your keys (OpenAI, SerpApi…) are copied from it automatically.
- The dashboard opens in your browser. If it asks for the SerpApi key, paste it and click **Save**.

## Every time

1. Double-click **`start.bat`** to open the dashboard (http://127.0.0.1:8010).
2. Type the **industry** and **city**, and choose **how many leads**.
3. Optional: tick **Search area by area** for many more leads. Type areas (e.g. `Navrangpura, Satellite, Bopal`)
   or leave them empty and the AI picks the main areas.
4. It shows how many of your free searches the run will use. Click **Find leads**.
5. **Download CSV** gives the sheet. **Printable report** opens a page to save as PDF (Ctrl+P).

Results are also saved in the `data\leads` folder. Keep the black window open while you use it.

**Update:** double-click **`update.bat`** (your keys and results are kept).

## If it fails

| Message | Fix |
|---|---|
| `SerpApi said 401` / `Invalid API key` | Open `.env` in Notepad, fix the `SERPAPI_KEY=` line, save, start again. |
| `run out of searches` | The free plan resets next month. |
| Messages look basic | No AI key in `.env`, or the AI was busy, so the clean template was used. |

## Before sending leads to a client

- Read every lead and remove any that look wrong (a hospital, a chain…).
- Send screenshots, the PDF or a view-only Google Sheet. Never send the program or your `.env`.
