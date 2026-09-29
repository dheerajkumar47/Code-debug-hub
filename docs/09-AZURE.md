# BidSmith on Azure: easy steps

Result: the bot runs 24/7 on Azure. Your laptop can be off. Open it on your phone from anywhere.

---

## PART A: On your laptop (3 minutes)

**A1.** Double-click **`update.bat`**. Wait until it says done.

**A2.** Double-click **`azure.bat`**. It asks 3 questions. Type an answer, then press **Enter**:

| Question | Type this |
|---|---|
| 1) Choose your login password | a password you'll remember, at least 8 letters, e.g. `Dheeraj2030` |
| 2) Web address name | `bidsmith-dheeraj` |
| 3) Azure region | `1` |

**A3.** At the end it shows **your address** and **your login**. Take a photo of it with your phone.

A new file, **`azure-cloud-init.txt`**, is now in the BidSmith folder. You need it in B8.

---

## PART B: On portal.azure.com (10 minutes)

**B1.** Search bar at the top → type **virtual machines** → click it → **+ Create** → **Azure virtual machine**.

**B2.** If you see *"Choose recommended defaults that match your workload"* → click **Skip this step** (small link at the bottom).

**B3.** Fill the **Basics** tab (change only these, leave the rest as it is):

| Field | Choose |
|---|---|
| Resource group | click **Create new** → type `bidsmith` → OK |
| Virtual machine name | `bidsmith` |
| Region | **(Middle East) UAE North** |
| Availability options | **No infrastructure redundancy required** |
| Security type | **Standard** |
| Image | **Ubuntu Server 24.04 LTS** |
| Size | click **See all sizes** → search `B1s` → select **B1s** → **Select** |
| Authentication type | **Password** |
| Username | `azureuser` |
| Password / Confirm | any strong password (only for Azure; you won't use it again) |
| Public inbound ports | **Allow selected ports** |
| Select inbound ports | tick **HTTP (80)**, **HTTPS (443)**, **SSH (22)** |

> If B1s is greyed out in UAE North: set Region to **Central India**, then run `azure.bat` again and choose `2`.

**B4.** Click the **Disks** tab at the top → OS disk type: **Standard SSD**.

**B5.** Skip the Networking, Management and Monitoring tabs.

**B6.** Click the **Advanced** tab.

**B7.** On your laptop, right-click **`azure-cloud-init.txt`** → **Open with Notepad** → press **Ctrl+A**, then **Ctrl+C**.

**B8.** Back in Azure, click inside the **Custom data** box → press **Ctrl+V**.

**B9.** Click **Review + create** (bottom) → wait for "Validation passed" → **Create**.

**B10.** Wait 1–2 minutes for **"Your deployment is complete"** → click **Go to resource**.

**B11.** On that page, find **DNS name: Not configured** → click it → in **DNS name label** type `bidsmith-dheeraj`
(the same name as in A2) → click **Save** at the top.

---

## PART C: Open it on your phone (after 10 minutes)

**C1.** Wait **10 minutes**. The server installs everything by itself.

**C2.** On your phone, open the address from A3, for example:
**https://bidsmith-dheeraj.uaenorth.cloudapp.azure.com**

**C3.** Login: **owner** / the password you chose in A2.

**C4.** Chrome menu **⋮** → **Add to Home screen**. Now it's an app on your phone.

**C5.** Close BidSmith on your laptop (only one copy should run), and delete **`azure-cloud-init.txt`**
(it contains your keys).

If the page doesn't open yet → wait 5 more minutes and refresh.

---

## Later

**Update the bot to a new version:**
Azure → VM **bidsmith** → left menu **Operations** → **Run command** → **RunShellScript** →
type `/opt/bidsmith/update.sh` → **Run** → wait 1 minute.

**Something is wrong:**
Same **Run command** box → paste this → **Run** → send me a screenshot:
```
systemctl status bidsmith caddy --no-pager | head -30; tail -20 /var/log/cloud-init-output.log
```

**Pause the bot to save credits:** VM page → **Stop**. Click **Start** to run it again.

**Credits:** B1s costs about $8 a month. New Azure accounts often get B1s free for 12 months.
