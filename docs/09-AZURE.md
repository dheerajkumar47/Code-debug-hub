# Run BidSmith 24/7 on Azure (laptop off, phone anywhere)

You will get a secure address like **https://bidsmith-dheeraj.uaenorth.cloudapp.azure.com** that works on
your phone over Wi-Fi or mobile data, even when your laptop is off.

Time: about 20 minutes, done once. Cost: about **$8–12 a month from your Azure credits** (VM size B1s,
free for 12 months on many new Azure accounts).

> Your keys never go into chat. They go from your `.env` straight into Azure.

---

## Step 1 — Make a GitHub token (read-only, 3 minutes)

The repo is private, so the server needs permission to download the code.

1. Open **https://github.com/settings/personal-access-tokens/new** (you must be logged in).
2. **Token name:** `bidsmith-azure`
3. **Expiration:** pick **1 year** (Custom → a date next year).
4. **Repository access:** choose **Only select repositories** → pick **Code-debug-hub**.
5. **Permissions → Repository permissions → Contents:** set it to **Read-only**. Leave everything else as it is.
6. Click **Generate token** → **copy** it (starts with `github_pat_`). Keep this page open.

## Step 2 — Make the setup file on your laptop (2 minutes)

1. Get the latest BidSmith first: double-click **`update.bat`** (as before).
2. In the BidSmith folder, double-click **`azure.bat`**.
3. It asks three things:
   - **GitHub token** → paste the token from Step 1 (right-click pastes), then press Enter.
   - **Web address name** → type something like `bidsmith-dheeraj`, then press Enter.
   - **Azure region** → press **1** (UAE North, the closest to Pakistan), then press Enter.
     If Azure doesn't allow that region later, run `azure.bat` again and pick another one.
4. It creates **`azure-cloud-init.txt`** in the BidSmith folder and shows your address. **Write it down.**
   If your dashboard password was short, it also shows a new strong password. **Write that down too.**

## Step 3 — Create the server in the Azure Portal (10 minutes)

1. Open **https://portal.azure.com** → search bar at the top → type **Virtual machines** → open it.
2. Click **+ Create** → **Azure virtual machine**.
3. **Basics** tab:
   | Field | What to choose |
   |---|---|
   | Subscription | the one with your credits |
   | Resource group | **Create new** → `bidsmith` |
   | Virtual machine name | `bidsmith` |
   | Region | **the same region you picked in Step 2** (e.g. *(Middle East) UAE North*) |
   | Availability options | No infrastructure redundancy required |
   | Security type | Standard |
   | Image | **Ubuntu Server 24.04 LTS – x64 Gen2** |
   | Size | **Standard_B1s** (click "See all sizes" if it isn't shown; if B1s isn't available, pick **B1ms** or **B2ats_v2**) |
   | Authentication type | SSH public key |
   | Username | `azureuser` |
   | SSH public key source | Generate new key pair |
   | Public inbound ports | **Allow selected ports** |
   | Select inbound ports | tick **HTTP (80)**, **HTTPS (443)** and **SSH (22)** |
4. Click **Next: Disks** → OS disk type: **Standard SSD**.
5. Skip **Networking** and **Management** (leave the defaults).
6. Open the **Advanced** tab → find **Custom data** → open `azure-cloud-init.txt` in Notepad →
   **Ctrl+A, Ctrl+C** → click in the Custom data box → **Ctrl+V**.
7. Click **Review + create** → **Create** → **Download private key and create resource** (keep that file safe; you
   probably won't need it).
8. Wait for **"Your deployment is complete"** → click **Go to resource**.

## Step 4 — Give the server its web address (1 minute)

1. On the VM **Overview** page, find **DNS name** → click **Not configured**.
2. **DNS name label** → type exactly the name from Step 2 (e.g. `bidsmith-dheeraj`) → **Save** (top).

## Step 5 — Open it on your phone (after about 10 minutes)

The server installs everything by itself. Give it **10 minutes**, then open your address on the phone:

**https://bidsmith-dheeraj.uaenorth.cloudapp.azure.com** (your own name and region)

- Login: **owner** / your dashboard password (the one in `.env`).
- Chrome → ⋮ → **Add to Home screen** makes it an app icon.
- If you see a "certificate" or "can't connect" error, wait 5 more minutes and try again. The secure lock is
  created automatically.

Then:
- **Close BidSmith on your laptop.** Run only one copy at a time (the Azure one).
- **Delete `azure-cloud-init.txt`** from your laptop. It contains your keys.

---

## Everyday use

| I want to… | Do this |
|---|---|
| See projects / apply | Open your address on the phone or laptop |
| Pause searching | **Pause** button on the dashboard |
| Install a new BidSmith version | Portal → VM **bidsmith** → left menu **Operations → Run command** → **RunShellScript** → type `/opt/bidsmith/update.sh` → **Run** (about 1 minute) |
| See the bot's log | Same Run command box → `journalctl -u bidsmith -n 60 --no-pager` → **Run** |
| Stop paying for a while | VM **Overview** → **Stop** (the bot stops too). **Start** brings it back. |
| Change a key | Send me a message. Don't paste the key in chat. |

## Keep an eye on credits

Portal → search **Cost Management** → **Budgets** → **+ Add** → amount `15` (USD per month) → an alert at 80%
emails you before the credits run low.

## If something doesn't work

Run this in **Run command → RunShellScript**:

```
systemctl status bidsmith caddy --no-pager | head -30; tail -20 /var/log/cloud-init-output.log
```

Send me a screenshot of the output. It shows no keys.
