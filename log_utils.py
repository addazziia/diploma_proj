import os
import hashlib
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import psycopg2

# === PostgreSQL connection settings ===
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Fqpflf",
    "host": "localhost",
    "port": "5432"
}

# === Path to local log file ===
LOG_FILE = "activity.log"

# === Utility to hash strings using SHA-256 ===
def hash_string(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# === Write a structured log entry ===
def write_log(details, action_type="generic", filename=None, operator="local"):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{timestamp} [{action_type}] {filename or ''} - {details}\n"

    # Save to local plain text file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # Save to PostgreSQL (hashed fields, correct timezone)
    hashed_operator = hash_string(operator)
    hashed_filename = hash_string(filename) if filename else None

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Set timezone to Kazakhstan
        cur.execute("SET TIME ZONE 'Asia/Almaty';")

        cur.execute("""
            INSERT INTO logs (timestamp, action_type, filename, details, operator)
            VALUES (NOW(), %s, %s, %s, %s)
        """, (action_type, hashed_filename, details, hashed_operator))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB error] {e}")

# === GUI Log Viewer ===
def show_log_window():
    if not os.path.exists(LOG_FILE):
        messagebox.showerror("Error", "No logs found")
        return

    log_window = tk.Toplevel()
    log_window.title("Log Viewer")
    log_window.geometry("600x400")
    log_window.configure(bg="#2a2a3d")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    text_box = tk.Text(log_window, bg="#2a2a3d", fg="white", wrap="word")
    text_box.insert(tk.END, content)
    text_box.pack(expand=True, fill="both")

# === Export log to file ===
def export_log():
    if not os.path.exists(LOG_FILE):
        messagebox.showerror("Error", "No logs to export")
        return

    save_path = filedialog.asksaveasfilename(
        title="Export Logs As",
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")]
    )
    if save_path:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        with open(save_path, "w", encoding="utf-8") as out:
            out.write(content)
        messagebox.showinfo("Success", f"Logs exported to: {save_path}")
