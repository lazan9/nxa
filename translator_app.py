import os
import sys
import threading
import logging
import time
import re
from dataclasses import dataclass
from typing import List
import pandas as pd
import pyperclip
import keyboard
from tkinter import Tk, filedialog, messagebox, simpledialog
from openai import OpenAI

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except Exception:  # pragma: no cover - colorama is optional
    class Dummy:
        RESET = RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ''
    Fore = Style = Dummy()

# ---------------------- Configuration ----------------------
@dataclass
class TranslatorConfig:
    max_workers: int = 4
    batch_size: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0
    temperature: float = 0.1
    model: str = "gpt-4.1-mini"
    api_timeout: int = 30

config = TranslatorConfig()

LANGUAGES = {
    'hu': 'Hungarian',
    'en': 'English',
    'de': 'German',
    'fr': 'French',
    'es': 'Spanish',
    'ro': 'Romanian',
    'pl': 'Polish',
}

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not API_KEY:
    print("OPENAI_API_KEY environment variable not set")
    sys.exit(1)
client = OpenAI(api_key=API_KEY)

# ---------------------- Utility Functions ----------------------
def should_translate(text: str) -> bool:
    if text is None:
        return False
    s = str(text).strip()
    if not s:
        return False
    if s.replace('.', '').replace(',', '').replace('-', '').isdigit():
        return False
    return True


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:  # pragma: no cover - network errors
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            logging.warning(f"retry {attempt + 1}/{max_retries} after {delay}s: {e}")
            time.sleep(delay)


def translate_batch_with_retry(texts: List[str], src: str, tgt: str) -> List[str]:
    def _translate():
        batch_text = "\n---SEPARATOR---\n".join(texts)
        sys_msg = (f"Translate the following texts from {LANGUAGES[src]} to {LANGUAGES[tgt]}\n"
                   f"Preserve brand names and HTML tags. Use the separator ---SEPARATOR---")
        resp = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "system", "content": sys_msg},
                      {"role": "user", "content": batch_text}],
            temperature=config.temperature,
            timeout=config.api_timeout
        )
        translated = resp.choices[0].message.content.strip()
        return [t.strip() for t in translated.split("---SEPARATOR---")]

    results = retry_with_backoff(_translate, config.retry_attempts, config.retry_delay)
    if len(results) != len(texts):
        # fall back to single translation if mismatch
        return [translate_single_text(t, src, tgt) for t in texts]
    return results


def translate_single_text(text: str, src: str, tgt: str) -> str:
    def _translate():
        sys_msg = f"Translate from {LANGUAGES[src]} to {LANGUAGES[tgt]}. Preserve brand names and HTML tags."
        resp = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "system", "content": sys_msg},
                      {"role": "user", "content": text}],
            temperature=config.temperature,
            timeout=config.api_timeout
        )
        return resp.choices[0].message.content.strip()
    return retry_with_backoff(_translate, config.retry_attempts, config.retry_delay)


def translate_clipboard():
    src = simpledialog.askstring("Source language", f"Enter source language code ({', '.join(LANGUAGES.keys())}):")
    tgt = simpledialog.askstring("Target language", f"Enter target language code ({', '.join(LANGUAGES.keys())}):")
    if not src or not tgt or src not in LANGUAGES or tgt not in LANGUAGES:
        messagebox.showerror("Error", "Invalid language code")
        return
    text = pyperclip.paste()
    if not text.strip():
        messagebox.showwarning("Clipboard", "Clipboard is empty")
        return
    if should_translate(text):
        translated = translate_single_text(text, src, tgt)
        pyperclip.copy(translated)
        messagebox.showinfo("Translation", "Translated text copied to clipboard")
    else:
        messagebox.showwarning("Translation", "Nothing to translate")


def translate_excel():
    path = filedialog.askopenfilename(title="Select Excel file",
                                      filetypes=[("Excel files", "*.xlsx *.xls")])
    if not path:
        return
    src = simpledialog.askstring("Source language", f"Enter source language code ({', '.join(LANGUAGES.keys())}):")
    tgt = simpledialog.askstring("Target language", f"Enter target language code ({', '.join(LANGUAGES.keys())}):")
    if not src or not tgt or src not in LANGUAGES or tgt not in LANGUAGES:
        messagebox.showerror("Error", "Invalid language code")
        return
    try:
        df = pd.read_excel(path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open Excel file: {e}")
        return
    cols = df.columns.tolist()
    texts: List[str] = []
    cell_indices: List[tuple] = []
    for r_idx, row in df.iterrows():
        for c_idx, col in enumerate(cols):
            val = row[col]
            if should_translate(val):
                texts.append(str(val))
                cell_indices.append((r_idx, col))
    if not texts:
        messagebox.showinfo("Translation", "No text to translate")
        return
    translated_texts = translate_batch_with_retry(texts, src, tgt)
    for (r_idx, col), translated in zip(cell_indices, translated_texts):
        df.at[r_idx, col] = translated
    out_path = os.path.splitext(path)[0] + f"_{tgt}.xlsx"
    try:
        df.to_excel(out_path, index=False)
        messagebox.showinfo("Translation", f"Translated file saved to {out_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save Excel file: {e}")


def open_dialog():
    root = Tk()
    root.title("Translator")
    root.geometry("300x150")
    root.resizable(False, False)
    btn_excel = tk.Button(root, text="Translate Excel", width=20, command=translate_excel)
    btn_clip = tk.Button(root, text="Translate Clipboard", width=20, command=translate_clipboard)
    btn_excel.pack(pady=10)
    btn_clip.pack(pady=10)
    root.mainloop()


def hotkey_listener():
    keyboard.add_hotkey("ctrl+shift+t", open_dialog)
    keyboard.wait()


def main():
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=hotkey_listener, daemon=True).start()
    open_dialog()


if __name__ == "__main__":
    import tkinter as tk
    main()
