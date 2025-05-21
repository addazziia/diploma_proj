from custom_models import LogisticRegressionCustom

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
from datetime import datetime
from log_utils import write_log
from analysis import analyze_files
from slot_scanner import scan_and_create_accurate_fragment
from slot_recovery import recover_docx_from_fragment
from slot_image_recovery import extract_images_from_all_docx
from gui_logic import run_ml_classification, show_keyword_cloud, show_slot_chart

# Global state
log_box = None
selected_dump_path = ""
slots_stats = (0, 0)

# Styling (light theme)
BG_COLOR = "#f2f2f2"
FG_COLOR = "#000000"
BUTTON_COLOR = "#4CAF50"
FONT = ("Segoe UI", 10)

def browse_file(entry):
    global selected_dump_path
    selected_dump_path = filedialog.askopenfilename(filetypes=[("Dump Files", "*.001 *.bin *")])
    entry.delete(0, tk.END)
    entry.insert(0, selected_dump_path)
    msg = f"Selected dump file: {selected_dump_path}"
    log_box.insert(tk.END, f"[✓] {msg}\n")
    write_log(msg, action_type="select_dump", filename=os.path.basename(selected_dump_path))

def extract_fragments():
    global slots_stats
    if not selected_dump_path:
        messagebox.showerror("Error", "No dump file selected")
        return
    valid, total = scan_and_create_accurate_fragment(selected_dump_path)
    slots_stats = (valid, total)
    msg = f"Extracted {valid} valid fragments from {total} scanned slots."
    log_box.insert(tk.END, f"[✓] {msg}\n")
    write_log(msg, action_type="extract_fragments", filename=os.path.basename(selected_dump_path))
    messagebox.showinfo("Done", msg)

def browse_fragment():
    fragment = filedialog.askopenfilename(title="Select Fragment (.bin)", filetypes=[("Fragment", "*.bin")])
    if not fragment:
        return
    log_box.insert(tk.END, f"[✓] Selected fragment: {fragment}\n")
    write_log("Selected fragment", action_type="select_fragment", filename=os.path.basename(fragment))
    recovered_files = recover_docx_from_fragment(fragment)
    msg = f"Recovered {len(recovered_files)} valid .docx files from fragment."
    log_box.insert(tk.END, f"[✓] {msg}\n")
    write_log(msg, action_type="recovery", filename=os.path.basename(fragment))
    messagebox.showinfo("Recovery", msg)

def run_analysis():
    recovered_path = "recovered_docs_from_fragment"
    if not os.path.exists(recovered_path):
        messagebox.showerror("Missing", "Recover documents before analysis")
        return
    files = [os.path.join(recovered_path, f) for f in os.listdir(recovered_path)
             if f.endswith(".docx") or f.endswith(".doc")]
    report = analyze_files(files)
    with open("forensic_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    extract_images_from_all_docx()
    msg = "Forensic analysis completed and report saved"
    log_box.insert(tk.END, f"[✓] {msg}\n")
    write_log(msg, action_type="analysis")

def run_ml():
    try:
        report = run_ml_classification()
        msg = "ML analysis completed and saved"
        log_box.insert(tk.END, f"[✓] {msg}\n")
        write_log(msg, action_type="ml_classification")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_keywords():
    try:
        show_keyword_cloud()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_chart():
    try:
        show_slot_chart(slots_stats)
    except Exception as e:
        messagebox.showerror("Chart Error", str(e))

def show_security_policy_window():
    policy_text = """
Security Policy

This application adheres to internationally accepted principles of digital forensics and cybersecurity to ensure responsible evidence handling and investigator accountability.

1. Read-Only Data Handling
   - All forensic actions are conducted in read-only mode.
   - Source memory dumps or disk images are never modified during analysis.

2. Fragment Isolation and Recovery
   - Valid fragments are extracted using file signature carving.
   - Extracted files are saved separately in a new directory.

3. Encryption Identification
   - Uses entropy-based heuristics to detect encrypted .enc/.bin fragments.
   - Password-protected Office documents (.docx/.doc) are identified based on standard markers.

4. Integrity and Audit Logging
   - All actions (e.g., file selection, recovery, classification) are logged to a local file and PostgreSQL database.
   - Log entries include timestamp, operation type, filename hash, and operator hash.

5. Data Privacy and Transmission
   - The system performs all analysis locally.
   - No internet connection or data transfer is involved.

6. PostgreSQL Authentication
   - PostgreSQL logging uses role-based access with hashed user tracking.
   - Unauthorized access is restricted by password authentication.

If you have questions about our policy or wish to report a security issue, please contact us.
"""
    window = tk.Toplevel()
    window.title("Security Policy & Contact")
    window.geometry("700x500")
    window.configure(bg=BG_COLOR)

    tk.Label(window, text="Security Policy", font=("Segoe UI", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=(15, 5))
    frame = tk.Frame(window, bg=BG_COLOR)
    frame.pack(expand=True, fill="both", padx=20, pady=(0, 10))

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    text_widget = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, bg="white", fg="black", font=FONT)
    text_widget.insert(tk.END, policy_text)
    text_widget.config(state="disabled")
    text_widget.pack(side="left", fill="both", expand=True)

    scrollbar.config(command=text_widget.yview)
    tk.Label(window, text="Contact Us", font=("Segoe UI", 12, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=(5, 0))
    tk.Label(window, text="📧 tommyzh531@gmail.com", font=FONT, bg=BG_COLOR, fg="blue").pack(pady=(0, 10))

def download_report():
    report_file = "forensic_report.json"
    if not os.path.exists(report_file):
        messagebox.showerror("Error", "No forensic report found")
        return

    save_path = filedialog.asksaveasfilename(
        title="Download Forensic Report",
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")]
    )
    if save_path:
        with open(report_file, "r", encoding="utf-8") as src:
            content = src.read()
        with open(save_path, "w", encoding="utf-8") as dst:
            dst.write(content)
        messagebox.showinfo("Success", f"Report saved to: {save_path}")

def launch_gui():
    global log_box
    root = tk.Tk()
    root.title("ForenDOC - Document Recovery Forensics")
    root.configure(bg=BG_COLOR)

    top_frame = tk.Frame(root, bg=BG_COLOR)
    top_frame.pack(pady=10)
    tk.Label(top_frame, text="Disk dump path:", bg=BG_COLOR, fg=FG_COLOR, font=FONT).pack(side=tk.LEFT)
    path_entry = tk.Entry(top_frame, width=60)
    path_entry.pack(side=tk.LEFT, padx=5)
    tk.Button(top_frame, text="Browse", command=lambda: browse_file(path_entry), bg="darkgreen", fg="white", font=FONT).pack(side=tk.LEFT)

    center = tk.Frame(root, bg=BG_COLOR)
    center.pack(pady=5)

    def add_main_button(text, command):
        tk.Button(center, text=text, command=command, font=FONT, bg=BUTTON_COLOR, fg="white", width=40, height=2).pack(pady=4)

    add_main_button("1. Extract DOCX Signatures", extract_fragments)
    add_main_button("2. Recover from Fragment", browse_fragment)
    add_main_button("3. Run Forensic Analysis", run_analysis)
    add_main_button("4. Run ML Classification", run_ml)

    side = tk.Frame(root, bg=BG_COLOR)
    side.place(x=0, y=0)

    def add_side_button(label, command):
        tk.Button(side, text=label, command=command, font=FONT, bg="#cccccc", fg="black", width=15).pack(pady=1, anchor="w")

    add_side_button("Show Keywords", show_keywords)
    add_side_button("Show Chart", show_chart)
    add_side_button("Security Policy", show_security_policy_window)
    add_side_button("Download Report", download_report)

    log_box_frame = tk.Frame(root, bg=BG_COLOR)
    log_box_frame.pack(pady=10)
    log_box = tk.Text(log_box_frame, height=10, width=100, bg="white", fg="black")
    log_box.pack()

    root.mainloop()

if __name__ == "__main__":
    launch_gui()