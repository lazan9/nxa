#!/usr/bin/env python3
"""Simple OpenAI-powered translator with global hotkeys.

Features
--------
- ``Ctrl+Alt+T`` translates text from the clipboard and copies the result back.
- ``Ctrl+Alt+O`` opens a file dialog to translate an Excel file.
  The entire sheet is translated and saved alongside the original
  with ``_translated`` suffix.
- ``Esc`` exits the program.

The script requires the ``OPENAI_API_KEY`` environment variable.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import keyboard
import pandas as pd
import pyperclip
from openai import OpenAI

TARGET_LANG = "en"
MODEL = "gpt-4o-mini"


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=key)


def translate_text(text: str, target: str = TARGET_LANG) -> str:
    """Translate ``text`` into ``target`` language using OpenAI."""
    client = _client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"Translate the following text to {target}."},
            {"role": "user", "content": text},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def translate_clipboard() -> None:
    """Translate current clipboard content and copy result back."""
    text = pyperclip.paste().strip()
    if not text:
        print("Clipboard empty – nothing to translate")
        return
    translated = translate_text(text)
    pyperclip.copy(translated)
    print("Translated text copied to clipboard")


def translate_excel() -> None:
    """Ask user for an Excel file, translate its contents and save result."""
    root = tk.Tk()
    root.withdraw()  # hide main window
    path = filedialog.askopenfilename(
        title="Select Excel file",
        filetypes=[("Excel files", "*.xlsx *.xls")],
    )
    root.update()
    if not path:
        return
    df = pd.read_excel(path)
    for col in df.columns:
        df[col] = df[col].astype(str).apply(
            lambda x: translate_text(x) if x.strip() else x
        )
    out = os.path.splitext(path)[0] + "_translated.xlsx"
    df.to_excel(out, index=False)
    messagebox.showinfo("Translation complete", f"Saved to\n{out}")


def main() -> None:
    print("Translator ready. Hotkeys:\n",
          "Ctrl+Alt+T – translate clipboard\n",
          "Ctrl+Alt+O – translate Excel file\n",
          "Esc – quit")
    keyboard.add_hotkey("ctrl+alt+t", translate_clipboard)
    keyboard.add_hotkey("ctrl+alt+o", translate_excel)
    keyboard.wait("esc")


if __name__ == "__main__":
    main()
