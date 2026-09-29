# BidSmith: Every Step, One by One (Windows)

You need **2 keys**:
1. **Freelancer token**, so the bot can see projects and place bids for you.
2. **Gemini API key**, so the bot can write proposals with AI. It's free.

You will paste both into **one place** (Part 5). You never open or edit any code file.

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

## PART 5: First start and pasting the keys (5 min)
1. In that folder, **double-click `start.bat`**.
   - If Windows shows **"Windows protected your PC"**, click **More info** → **Run anyway**.
2. A black window opens. The **first time** it installs the libraries by itself (1–2 minutes). You don't need to do anything:
   - `httpx`: talks to Freelancer and Gemini
   - `fastapi` + `uvicorn` + `python-multipart`: run the dashboard web page
   - `PyYAML`: reads your profile file
   - `python-dotenv`: reads your keys file
   - `pillow`: makes the portfolio images
   - `pytest`: the self-tests
3. Then it asks you questions, one at a time:

| The window shows | You do |
|---|---|
| `1/2  Freelancer token (Generate Token button) [empty]:` | Copy the Freelancer token from Notepad. In the black window, **right-click** to paste (**not Ctrl+V**; nothing will appear, that's normal). Press **Enter**. It should say `✔ received 40 chars (abcd…wxyz)` or similar. |
| `AI provider: gemini / openai / anthropic / none [gemini]:` | Just press **Enter** |
| `2/2  AI API key (...) [empty]:` | Copy the Gemini key from Notepad. **Right-click** to paste (hidden again). Press **Enter**. |
| `Set up WhatsApp now? You can do it later. (y/N):` | Just press **Enter** (skip for now) |

4. It prints a line like:
   ```
   Dashboard login → user: owner  password: Ab3xY9kLmQ2w  (saved in .env)
   ```
   **Write this password in Notepad.**
5. Your keys are now saved in a file called **`.env`** inside the bot folder.
   - It stays only on your PC and is never uploaded.
   - If you ever need to change a key, run setup again (Part 8). Don't edit `.env` by hand.
6. The bot checks everything. You should see:
   ```
   ✅ Freelancer token works (your user id 12345678)
   ✅ Project search works (3 live 'chatbot' projects returned)
   ✅ AI writer works (gemini: 'OK')
   ℹ️  WhatsApp off → approve bids on the dashboard
   ✅ Dashboard password set
   Ready!
   ```
   If you see ❌, take a screenshot and send it to me. **Blur any key first.**
7. Then it starts and shows:
   ```
   Dashboard on this PC:     http://localhost:8000
   Dashboard on your phone:  http://192.168.1.23:8000   (same Wi-Fi)
   ```
   - If Windows asks **"Allow Python on networks?"**, tick **Private networks** → **Allow**.
8. **Leave the black window open.** Closing it stops the bot.

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
- **To start:** double-click **`start.bat`**. It won't ask for the keys again.
- **To stop:** close the black window.
- **To change or add a key:** double-click **`setup.bat`**. Paste with **right-click**, then press **Enter** to keep the old values.
- **WhatsApp buttons (later, optional):** tell me when you have 30 minutes, and I'll walk you through it one step at a time.
