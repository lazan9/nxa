#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reply_assist.py – Mail reply assistant with OpenAI integration
"""

import os, sys, json, argparse, pathlib, subprocess
from langdetect import detect
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load_key():
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key.strip()
    # fallback to config.ini
    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / "config/config.ini")
    return cfg["OpenAI"]["api_key"].strip()

def chat(client, model, system, user):
    resp = client.chat.completions.create(
        model=model,
        temperature=0.4,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}]
    )
    return resp.choices[0].message.content.strip()

def short_summary(client, model, email):
    sys_msg = "Rövidítsd egy mondatba magyarul a megadott e-mail tartalmát."
    return chat(client, model, sys_msg, email)

def three_replies(client, model, email):
    prompt = ("Írj három rövid, segítőkész válaszlehetőséget magyarul "
              "az alábbi levélre, vesszővel elválasztva, hosszuk 3–7 szó legyen.\n\n"
              f"{email}")
    text = chat(client, model, "Dupla idézőjelek nélkül add meg a három opciót.", prompt)
    raw = [x.strip().lstrip("–-•0123456789. ") for x in text.split(",")]
    return [r for r in raw if r][:3]  # max 3 option

def elegant_reply(client, model, email, draft, lang):
    sys_msg = (f"You are an assistant that drafts polite, elegant e-mail replies in {lang}. "
               "Use formal yet friendly style.")
    user_msg = (f"SOURCE EMAIL:\n{email}\n\n"
                f"DRAFT REPLY: {draft}\n\n"
                "Rewrite the DRAFT into a full, well-structured reply. "
                "Keep salutations and signatures neutral.")
    return chat(client, model, sys_msg, user_msg)

def get_mail_content():
    script = """
    tell application "Mail"
        if (count of (get selection)) = 0 then
            error "No message selected"
        end if
        set theMessage to item 1 of (get selection)
        return content of theMessage
    end tell
    """
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"Could not get mail content: {e.stderr}")

def show_dialog(summary, options):
    dialog_text = (f"{summary}\n\n"
                  f"Válaszlehetőségek:\n\n"
                  f"1. {options[0]}\n"
                  f"2. {options[1]}\n" 
                  f"3. {options[2]}\n\n"
                  f"Írd be a számot vagy adj meg saját szöveget:")

    script = f"""
    text returned of (display dialog "{dialog_text}" default answer "" buttons {{"Mégse", "OK"}} default button "OK")
    """
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def paste_to_mail(text):
    script = f"""
    tell application "Mail"
        activate
        set theMessage to item 1 of (get selection)
        set newReply to reply theMessage opening window
        delay 1
    end tell

    set the clipboard to "{text}"
    tell application "System Events"
        keystroke "v" using {{command down}}
    end tell
    """
    subprocess.run(['osascript', '-e', script])

def main():
    try:
        # Get mail content
        email = get_mail_content()

        # Setup OpenAI
        client = OpenAI(api_key=load_key())
        model = "gpt-4o-mini"

        # Detect language
        lang = detect(email)

        # Generate summary and options
        summary = short_summary(client, model, email)
        options = three_replies(client, model, email)

        # Ensure we have 3 options
        while len(options) < 3:
            options.append(f"Opció {len(options) + 1}")

        # Show dialog
        choice = show_dialog(summary, options)
        if not choice:
            return

        # Resolve choice
        if choice == "1":
            reply = options[0]
        elif choice == "2":
            reply = options[1]
        elif choice == "3":
            reply = options[2]
        else:
            reply = choice

        # Generate elegant reply
        final_reply = elegant_reply(client, model, email, reply, lang)

        # Paste to Mail
        paste_to_mail(final_reply)

    except Exception as e:
        subprocess.run(['osascript', '-e', f'display alert "Hiba: {str(e)}"'])
        sys.exit(1)

if __name__ == "__main__":
    main()
