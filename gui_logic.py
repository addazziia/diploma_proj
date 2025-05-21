import os
import json
import numpy as np
import joblib
import matplotlib.pyplot as plt
from tkinter import messagebox
from wordcloud import WordCloud

# === Load pretrained ML models ===
rf_model = joblib.load("rf_encryption_model.pkl")         # For encryption detection
ensemble_model = joblib.load("ensemble_classifier.pkl")   # For category classification

# === Run ML classification and write predictions to forensic_report.json ===
def run_ml_classification(report_path="forensic_report.json"):
    if not os.path.exists(report_path):
        raise FileNotFoundError("forensic_report.json not found")

    with open(report_path, "r", encoding="utf-8") as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in forensic_report.json")

    names = list(report.keys())
    texts = [report[name].get("extracted_text", "") for name in names]

    # Feature engineering for RF encryption model
    def extract_entropy_features(text):
        from collections import Counter
        import math
        byte_data = text.encode("utf-8", errors="ignore")
        counter = Counter(byte_data)
        total = len(byte_data)
        entropy = -sum((c / total) * math.log2(c / total) for c in counter.values()) if total > 0 else 0
        uniformity = len(counter) / 256
        printable_ratio = sum(c in range(32, 127) for c in byte_data) / total if total > 0 else 0
        return [entropy, uniformity, printable_ratio]

    X_entropy = np.array([extract_entropy_features(text) for text in texts])
    encryption_preds = rf_model.predict(X_entropy)

    # Use the ensemble model to classify document category
    X_text = np.array([text[:3000] for text in texts])  # Truncate for safety if needed
    category_preds = ensemble_model.predict(X_text)

    for i, name in enumerate(names):
        report[name]["ml_encryption"] = "Encrypted" if encryption_preds[i] == 1 else "Not Encrypted"
        report[name]["ml_category"] = str(category_preds[i])

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

# === Generate a keyword cloud from extracted text ===
def show_keyword_cloud(json_path="forensic_report.json", bg_color="#1e1e2f"):
    if not os.path.exists(json_path):
        raise FileNotFoundError("forensic_report.json not found")

    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    text = " ".join(info.get("extracted_text", "") for info in report.values())
    if not text.strip():
        messagebox.showinfo("Info", "No extracted text found for word cloud.")
        return

    wc = WordCloud(width=800, height=400, background_color=bg_color, colormap="viridis").generate(text)
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    plt.title("Keyword Cloud")
    plt.show()

# === Show a pie chart of detected vs empty .docx signature slots ===
def show_slot_chart(slots_stats):
    if not slots_stats or slots_stats[1] == 0:
        messagebox.showerror("Error", "No slot data available or total is zero.")
        return

    found, total = slots_stats
    empty = max(0, total - found)

    sizes = [max(0, found), max(0, empty)]
    if sum(sizes) == 0:
        messagebox.showerror("Error", "Both valid and empty slots are zero.")
        return

    labels = ['Valid .docx Slots', 'Empty Slots']
    colors = ['#4CAF50', '#F44336']

    plt.figure(figsize=(5, 5))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title("DOCX Signature Density in Dump")
    plt.axis("equal")
    plt.show()
