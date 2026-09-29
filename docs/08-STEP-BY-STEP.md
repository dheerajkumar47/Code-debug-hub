# BidSmith: Every Step, One by One (Windows)

You need **2 keys**:
1. **Freelancer token**, so the bot can see projects and place bids for you.
2. **Gemini API key**, so the bot can write proposals with AI. It's free.

You put both into **one Notepad file** called `keys.txt` (Part 5). You never open or edit any code file.

---

## PART 1: Get the Freelancer token (2 min)
1. Open Chrome on your **PC**.
2. Go to **freelancer.com** and log in.
3. In the same tab, open: **https://accounts.freelancer.com/settings/develop**
4. You'll see the "Application Dashboard" page (the one from your screenshot).
5. In the top box **"Generate Token"**, click the blue **Generate Token** button.
6. If it asks you to allow or confirm, click **Allow / Confirm**.
7. A long token appears. Select **all** of it and **copy** it (Ctrl+C).
8. Open **Notepad**, paste it (Ctrl+V), and write `FREELANCER:` in front of it so you remember what it is.
   - Keep Notepad open. **Don't send this token to anyone, including me.**
9. **Do not** fill in the "Create New Application" form. You don't need it.

## PART 2: Get the Gemini API key (2 min, free)
1. In Chrome, go to **https://aistudio.google.com**
2. Sign in with your **Google (Gmail) account**.
3. Click **Get API key** (top-right, or in the left menu).
4. Click **Create API key**.
5. If it asks for a project, choose **Create API key in new project**.
6. A key appears that starts with **`AIza...`**. Click **Copy**.
7. Paste it into the same Notepad on a new line, with `GEMINI:` in front.

✅ You now have 2 keys in Notepad.

## PART 3: Install Python (5 min, once)
1. Go to **https://www.python.org/downloads/**
2. Click the yellow **Download Python 3.12.x** (or newer) button.
3. Open the downloaded file (`python-3.12.x-amd64.exe`).
4. ⚠️ **Important:** at the **bottom** of the first screen, **tick "Add python.exe to PATH"**.
5. Click **Install Now** and wait until it says "Setup was successful". Click **Close**.
6. To check it worked:
   - press the **Windows key**, type `cmd`, press **Enter**;
   - in the black window, type `python --version` and press **Enter**;
   - it should show `Python 3.12.x`. ✅ Close the window.

   If it says "not recognized", run the installer again, choose **Modify**, and make sure **Add to PATH** is ticked.

## PART 4: Download the bot (2 min)
1. Open this link. It downloads a ZIP straight away:
   **https://github.com/dheerajkumar47/Code-debug-hub/archive/refs/heads/claude/funny-noether-d41u0f.zip**
2. Open your **Downloads** folder.
3. Right-click the ZIP → **Extract All…** → **Extract**.
4. Open the extracted folder. Inside it, open the folder named **`Code-debug-hub-claude-funny-noether-d41u0f`**.
5. You should see `start.bat`, `bidsmith`, `docs`, `profile`, `requirements.txt` and more.
   - Tip: move this folder to your **Desktop** so it's easy to find.

## PART 5: Put your keys in a file, then start (5 min)
**A. Make the keys file**
1. Open **Notepad**, then **File → New**.
2. Type exactly these two lines, pasting your keys after the colons (Ctrl+V works fine in Notepad):
   ```
   FREELANCER: paste-your-freelancer-token-here
   GEMINI: paste-your-gemini-key-here
   ```
   - The Freelancer token goes all on **one line**. Don't add spaces inside it.
3. Click **File → Save As**:
   - Folder: the bot folder (the one with `start.bat`).
   - File name: `keys.txt`
   - Save as type: **Text Documents (*.txt)**
   - Click **Save**.

**B. Start**
1. Double-click **`start.bat`**. If Windows shows a blue warning: **More info → Run anyway**.
2. The first time, it installs the libraries by itself (1–2 minutes):
   - `httpx`: talks to Freelancer and Gemini
   - `fastapi` + `uvicorn` + `python-multipart`: the dashboard web page
   - `PyYAML`: your profile
   - `python-dotenv`: your keys
   - `pillow`: images
   - `pytest`: self-tests
3. It reads `keys.txt` and shows:
   ```
   Read keys.txt:
      ✔ Freelancer token  32 chars (abcd…wxyz)
      ✔ gemini key  53 chars (AQ.A…5TCw)
      (keys.txt deleted — your keys are now only in .env)
   Dashboard login → user: owner  password: xxxxxxxx
   ```
   - The numbers can differ.
   - **Write the password down.**
   - `keys.txt` is deleted automatically, so your keys only stay in the hidden `.env` file.
4. The bot checks everything:
   ```
   ✅ Freelancer token works (your user id 12345678)
   ✅ Project search works (…)
   ✅ AI writer works (gemini · model …)
   ```
   - `⚠️ AI key accepted, but gemini is busy`: that's fine. Google is busy, and the bot retries by itself.
   - ❌ on any line: send me a screenshot, **hiding the keys**.
5. If Windows asks **"Allow Python on networks?"**: tick **Private networks → Allow**.
6. **Leave the black window open.** Closing it stops the bot.

**To change a key later:** make a new `keys.txt` the same way (only the line you want to change is needed), then double-click `start.bat`.

## PART 6: Open the dashboard
**On your PC:**
1. Open Chrome and go to **http://localhost:8000**.
2. Log in: username `owner`, and the password from Part 5.

**On your phone:**
1. Connect the phone to the **same Wi-Fi** as the PC.
2. Open the phone link from Part 5 (for example `http://192.168.1.23:8000`).
3. Log in the same way, then **bookmark** it.

The first cards appear within a few minutes, once good projects are found.

## PART 7: Use it (for each card)
1. Read the **title**, the **score**, the **reasons** and the **price**.
2. Read the proposal in the box and change anything you want.
3. Change the **price** or **days** if needed, then press **Save**.
4. Press **✅ Place bid** to send it, **⏭ Skip** to ignore it, or **🔁 Regenerate** for a new proposal.
5. If "Place bid" shows an error that the token can't place bids:
   - press **📋 Copy**, then **↗ Open**;
   - paste the proposal on Freelancer yourself and click Place Bid there.

## PART 8: Next day and later
- **To get the newest version:** close the black window, then double-click **`update.bat`**. It keeps your keys and history, then starts the bot.
- **To start:** double-click **`start.bat`**. It won't ask for the keys again.
- **To stop:** close the black window.
- **To change or add a key:** make a new `keys.txt` (Part 5A) and double-click `start.bat`.
- **WhatsApp buttons (later, optional):** tell me when you have 30 minutes, and I'll walk you through it one step at a time.
