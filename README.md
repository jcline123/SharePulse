# SharePulse

**SharePulse** is a Windows tray application that monitors SMB (network share) paths and automatically heals lost credentials if access is interrupted. It's ideal for ensuring persistent connectivity to critical network shares, especially in environments where Windows forgets saved credentials after reboots or logons.

---

## 🚀 Features

- ✅ Monitors multiple UNC paths (e.g., `\\192.168.0.25\Media`)
- 🛠 Automatically re-adds saved credentials using `cmdkey` when access fails
- 🔁 Triggers recovery attempts after reboots or logons if prior auto-heal failed
- ✉️ Sends email alerts for:
  - Auto-heal success or failure
  - Post-reboot recovery checks
- 📊 Logs all SMB access attempts and actions to `sharepulse_log.txt`
- 📁 Stores settings in a portable `config.json`
- 🖥️ Runs quietly in the system tray with a configurable GUI

---

## 📦 Installation

### Option 1: Download the Installer (Recommended)

Download the latest SharePulse installer from the [Releases](https://github.com/yourusername/sharepulse/releases) page.

The installer:
- Installs to `C:\Program Files\SharePulse`
- Adds SharePulse to the Startup folder so it runs at login
- Launches SharePulse immediately after install

### Option 2: Build from Source

#### 🧩 1. Clone the repository

```bash
git clone https://github.com/yourusername/sharepulse.git
cd sharepulse
```

#### 📦 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> Requirements:
> - `pystray`
> - `Pillow`

#### 🧱 3. Compile into an EXE (optional)

Use PyInstaller:

```bash
pyinstaller --onefile --windowed --icon=sharepulse.ico SharePulse.py
```

The result will be in `dist/SharePulse.exe`.

#### 🛠 4. Build the Installer

Use [Inno Setup](https://jrsoftware.org/isinfo.php) and the included `setup_sharepulse.iss`:

1. Open the script in Inno Setup Compiler
2. Make sure `SharePulse.exe` and `sharepulse.ico` are in the same folder
3. Click **Build**

---

## 🖼 GUI Configuration

Open the SharePulse tray icon to:
- ✅ Set SMB paths, credentials, and check interval
- ✅ Test connectivity to shares
- ✅ Configure SMTP settings for email alerts
- ✅ Start or stop monitoring manually

All configuration is stored in `config.json`, created after the first save.

---

## 📁 Logs & Config

| File | Purpose |
|------|---------|
| `config.json` | Stores all SMB and SMTP settings |
| `sharepulse_log.txt` | Rolling log of all actions, capped at 5MB |
| `C:\Temp\pending_reboot.flag` | Internal flag used to track failed heals that should be rechecked after reboot |

---

## 📮 Email Alerts

SharePulse uses the SMTP settings you provide to notify:
- 📈 When it recovers SMB access after a problem
- ❌ When a healing attempt fails
- 🔁 When it verifies recovery after a reboot or relaunch

You can use services like **SendGrid** or any SMTP-compatible provider.

---

## 🧪 Testing Auto-Heal

To test SharePulse's healing logic:
1. Open **Credential Manager** and delete the saved credential for the share
2. Restart SharePulse or wait for the next check interval
3. SharePulse will detect the failure, re-add the credential, and test again
4. Log entries and email (if configured) will confirm healing

---

## 🛡 Known Limitations

- Currently only manages credentials for the **first server** listed in SMB paths
- Requires administrative rights to add credentials and create startup shortcuts
- Only supports Windows systems

---

## 🛠 Planned Features

- [ ] Multi-server credential support
- [ ] Reboot trigger (optional)
- [ ] Credential viewer
- [ ] Retry counter and escalation options
- [ ] Service-based version (non-tray)

---

## 🧑‍💻 Credits

Developed by jcline.  
Tray logic powered by [pystray](https://pypi.org/project/pystray/).  
Icon rendering via [Pillow](https://pypi.org/project/Pillow/).

---

## 📜 License

MIT License
