import tkinter as tk
from tkinter import messagebox
import json, os, threading, subprocess, smtplib, time, queue
from email.mime.text import MIMEText
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

CONFIG_FILE  = "config.json"
MARKER_FILE  = r"C:\Temp\pending_reboot.flag"
LOG_FILE     = "sharepulse_log.txt"

monitoring      = False
monitor_thread  = None
icon            = None
msg_q           = queue.Queue()   # cross-thread status messages

# ----------------------------------------------------------------------
def write_log(msg):
    ts=time.strftime("%Y-%m-%d %H:%M:%S")
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE)>5*1024*1024: os.remove(LOG_FILE)
    with open(LOG_FILE,"a",encoding="utf-8") as f: f.write(f"[{ts}] {msg}\n")

def load_cfg():  return json.load(open(CONFIG_FILE,"r",encoding="utf-8")) if os.path.exists(CONFIG_FILE) else {}
def save_cfg(c): json.dump(c,open(CONFIG_FILE,"w",encoding="utf-8"),indent=4)

def add_creds(s,u,p):
    try: subprocess.run(["cmdkey",f"/add:{s}",f"/user:{u}",f"/pass:{p}"],
                        shell=True,capture_output=True,text=True,check=True); return True
    except subprocess.CalledProcessError as e: write_log(e.stderr.strip()); return False
def del_creds(s):
    try: subprocess.run(["cmdkey",f"/delete:{s}"],shell=True,
                        capture_output=True,text=True,check=True)
    except subprocess.CalledProcessError: pass

def test_smb(path, sz):
    try:
        tf = os.path.join(path, "sharepulse.tmp")
        with open(tf, "wb") as f:
            f.write(os.urandom(sz * 1024))
        os.remove(tf)
        write_log(f"SMB OK → {path}")
        return True
    except Exception as e:
        write_log(f"SMB FAIL → {path} → {e}")
        return False

def send_mail(smtp,sub,body):
    try:
        msg=MIMEText(body); msg["Subject"],msg["From"],msg["To"]=sub,smtp["sender_email"],smtp["receiver_email"]
        with smtplib.SMTP(smtp["server"],int(smtp["port"])) as s:
            s.starttls(); s.login(smtp["smtp_user"],smtp["smtp_password"]); s.send_message(msg)
        return True
    except Exception as e: write_log(f"SMTP error {e}"); return False

# ----------------------------------------------------------------------
def monitor_loop():
    cfg=load_cfg(); 
    if not cfg: msg_q.put("⚠ No config.json"); return
    paths=cfg["smb_paths"]; srv=paths[0].split("\\")[2]
    user,pwd=cfg["username"],cfg["password"]; smtp=cfg["smtp_info"]
    intv=int(cfg.get("check_interval",300)); sz=int(cfg.get("file_size_kb",1))

    if os.path.exists(MARKER_FILE):
        for p in paths:
            ok = test_smb(p, sz)
            result = "reachable" if ok else "still broken"
            write_log(f"Recovery flag check: {p} is {result}")
            send_mail(
                smtp,
                "SharePulse Auto-Heal Retry Result: " + ("OK" if ok else "FAIL"),
                f"{p}: {result} after reboot or restart."
            )
        os.remove(MARKER_FILE)
        write_log("Removed reboot marker after recovery check.")

    msg_q.put("Monitoring thread running")
    while monitoring:
        for p in paths:
            if test_smb(p,sz): continue
            msg_q.put(f"Healing {p} …")
            if not os.path.exists(MARKER_FILE): open(MARKER_FILE,"w").write("pending")
            del_creds(srv); add_creds(srv,user,pwd); time.sleep(10)
            if test_smb(p,sz):
                send_mail(smtp,"SharePulse Auto-Heal OK",f"{p} reachable again"); os.remove(MARKER_FILE)
                msg_q.put(f"Heal success on {p}")
            else:
                send_mail(smtp,"SharePulse Auto-Heal FAIL",f"{p} still broken"); msg_q.put(f"Heal failed on {p}")
        time.sleep(intv)
    msg_q.put("Monitoring stopped")

# ----------------------------------------------------------------------
def tray_img(): 
    return Image.open("sharepulse.ico") if os.path.exists("sharepulse.ico") else \
           Image.new("RGB",(64,64),"green")

def menu_template(): 
    return (item(f"Monitoring: {'ON' if monitoring else 'OFF'}",lambda *_:None,enabled=False),
            item("Open Settings", lambda *_: threading.Thread(target=settings_win,daemon=True).start()),
            item("Start Monitoring", lambda *_: start_monitor()),
            item("Stop Monitoring",  lambda *_: stop_monitor()),
            item("Exit", lambda i, it: (stop_monitor(), icon.stop())))

def start_monitor():
    global monitoring, monitor_thread
    write_log("Monitoring started via GUI or tray.")
    if not monitoring:
        monitoring=True
        monitor_thread=threading.Thread(target=monitor_loop,daemon=True); monitor_thread.start()
        icon.menu=pystray.Menu(*menu_template()); icon.update_menu()

def stop_monitor():
    global monitoring
    write_log("Monitoring stopped.")
    monitoring=False
    icon.menu=pystray.Menu(*menu_template()); icon.update_menu()

def tray_loop():
    global icon
    icon=pystray.Icon("SharePulse",tray_img(),"SharePulse",pystray.Menu(*menu_template()))
    icon.run()

# ----------------------------------------------------------------------
def settings_win():
    cfg=load_cfg(); win=tk.Tk(); win.title("SharePulse Settings")
    status=tk.StringVar(value="")

    def set_stat(t): status.set(t); write_log(t)

    def save():
        new={ "smb_paths": txt.get("1.0","end").strip().splitlines(),
              "username": u.get(), "password": p.get(),
              "check_interval": inter.get(), "file_size_kb": size.get(),
              "smtp_info": { "server": srv.get(),"port":prt.get(),
                             "sender_email":frm.get(),"receiver_email":to.get(),
                             "smtp_user":su.get(),"smtp_password":sp.get() } }
        save_cfg(new); set_stat("Settings saved ✔"); win.destroy()

    def smtp_test():
        smtp={ "server": srv.get(),"port":prt.get(),"sender_email":frm.get(),
               "receiver_email":to.get(),"smtp_user":su.get(),"smtp_password":sp.get() }
        ok=send_mail(smtp,"SharePulse SMTP Test","Test email"); set_stat("SMTP ✔" if ok else "SMTP ✖")

    def validate():
        bad=[p for p in txt.get("1.0","end").strip().splitlines() if not test_smb(p,int(size.get()))]
        if bad: messagebox.showerror("Validate","Failed:\n"+"\n".join(bad)); set_stat("Validation ✖")
        else:   messagebox.showinfo("Validate","All OK");                   set_stat("Validation ✔")

    def poll():
        if not win.winfo_exists():
            return  # Stop polling if window is closed
        try:
            while True:
                msg = msg_q.get_nowait()
                if win.winfo_exists():
                    status.set(msg)
        except queue.Empty:
            pass
        win.after(500, poll)

    # layout helpers
    def row(lbl,hide=False,val=""):
        tk.Label(win,text=lbl).pack(); e=tk.Entry(win,show="*" if hide else None)
        e.insert(0,val); e.pack(); return e

    tk.Label(win,text="SMB Paths (one per line):").pack()
    txt=tk.Text(win,height=5); txt.pack(); txt.insert("end","\n".join(cfg.get("smb_paths",[])))

    u=row("Username:",False,cfg.get("username",""));  p=row("Password:",True,cfg.get("password",""))
    inter=row("Check Interval (sec):",False,str(cfg.get("check_interval",300)))
    size=row("Test File Size (KB):",False,str(cfg.get("file_size_kb",1)))

    si=cfg.get("smtp_info",{})
    srv=row("SMTP Server:",False,si.get("server",""));  prt=row("SMTP Port:",False,si.get("port",""))
    frm=row("Sender Email:",False,si.get("sender_email","")); to=row("Receiver Email:",False,si.get("receiver_email",""))
    su=row("SMTP Username:",False,si.get("smtp_user",""));     sp=row("SMTP Password:",True,si.get("smtp_password",""))

    tk.Button(win,text="Validate Settings",command=validate).pack(pady=2)
    tk.Button(win,text="Save Settings",command=save).pack(pady=2)
    tk.Button(win,text="Test SMTP Settings",command=smtp_test).pack(pady=2)
    tk.Button(win,text="Enable Monitoring",command=start_monitor).pack(pady=2)

    tk.Label(win,textvariable=status,fg="blue").pack(pady=4)
    poll(); win.mainloop()

# ----------------------------------------------------------------------
def on_ready():
    # Called after tray icon has time to initialize
    cfg = load_cfg()
    if cfg.get("smb_paths") and cfg.get("username") and cfg.get("password"):
        start_monitor()

if __name__ == "__main__":
    print("SharePulse tray running — check your system tray")
    write_log("SharePulse launched at system startup.")

    threading.Thread(target=tray_loop).start()
    threading.Timer(2.0, on_ready).start()  # Delay start_monitor until tray is ready