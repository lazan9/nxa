#!/usr/bin/env python3
"""
Professional Mail Assistant - Full automation with JXA
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

def has_openai_key():
    return bool(os.getenv("OPENAI_API_KEY"))

def call_openai(prompt, model="gpt-4o-mini"):
    if not has_openai_key():
        return f"TESZT VÁLASZ: {prompt[:50]}... (OpenAI kulcs szükséges)"
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional email assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI hiba: {str(e)}"

def detect_language(text):
    try:
        from langdetect import detect
        return detect(text)
    except:
        return "hu"

def run_jxa_script(script):
    """Run JavaScript for Automation script"""
    try:
        result = subprocess.run(['osascript', '-l', 'JavaScript', '-e', script], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"JXA error: {e.stderr}")

def get_selected_mail():
    """Get selected mail using JXA"""
    script = '''
    const mail = Application('Mail');
    const selection = mail.selection();
    
    if (selection.length === 0) {
        throw new Error("No message selected");
    }
    
    return selection[0].content();
    '''
    return run_jxa_script(script)

def create_summary(email_content):
    if not has_openai_key():
        return "Email összefoglaló (teszt mód - OpenAI kulcs szükséges)"
    
    prompt = f"""
    Foglalja össze magyarul 1-2 mondatban az alábbi e-mail lényegét:
    
    {email_content}
    """
    return call_openai(prompt)

def create_options(email_content):
    if not has_openai_key():
        return ["Köszönöm a levelét", "Megkaptam az üzenetet", "Hamarosan válaszolok"]
    
    prompt = f"""
    Adj három rövid (5-10 szó) magyar válaszopciót az alábbi emailre:
    
    {email_content}
    
    Formátum: egy opció soronként, számozás nélkül.
    """
    response = call_openai(prompt)
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    return lines[:3] if lines else ["Opció 1", "Opció 2", "Opció 3"]

def create_full_response(email_content, chosen_reply, language):
    prompt = f"""
    Írj egy professzionális, részletes email választ ({language} nyelven):
    
    EREDETI EMAIL:
    {email_content}
    
    VÁLASZ TÉMÁJA:
    {chosen_reply}
    
    KÖVETELMÉNYEK:
    - Legalább 150-250 szó
    - Professzionális hangnem
    - Strukturált (bekezdések)
    - Kontextuális és releváns
    - Megfelelő üdvözlés és zárás
    
    Csak a válasz szövegét add meg.
    """
    return call_openai(prompt)

def show_dialog_and_get_reply(summary, options):
    """Show dialog using JXA and get user choice"""
    
    # Escape quotes for JSON
    summary_escaped = json.dumps(summary)
    options_escaped = json.dumps(options)
    
    script = f'''
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;
    
    const summary = {summary_escaped};
    const options = {options_escaped};
    
    const dialogText = summary + "\\n\\nVálaszlehetőségek:\\n\\n" +
                      "1. " + options[0] + "\\n" +
                      "2. " + options[1] + "\\n" +
                      "3. " + options[2] + "\\n\\n" +
                      "Írd be a számot vagy add meg a saját szöveged:";
    
    const result = app.displayDialog(dialogText, {{
        defaultAnswer: "",
        buttons: ["Mégse", "OK"],
        defaultButton: "OK"
    }});
    
    return result.textReturned;
    '''
    
    try:
        choice = run_jxa_script(script)
        
        if choice == "1":
            return options[0]
        elif choice == "2":
            return options[1] if len(options) > 1 else options[0]
        elif choice == "3":
            return options[2] if len(options) > 2 else options[0]
        else:
            return choice
    except:
        return None

def paste_to_mail_jxa(text):
    """Paste text to Mail using JXA - PROPER AUTOMATION"""
    
    # Escape text for JSON
    text_escaped = json.dumps(text)
    
    script = f'''
    const mail = Application('Mail');
    const systemEvents = Application('System Events');
    
    // Get selected message
    const selection = mail.selection();
    if (selection.length === 0) {{
        throw new Error("No message selected");
    }}
    
    const selectedMessage = selection[0];
    
    // Create reply
    const reply = mail.reply(selectedMessage, {{openingWindow: true}});
    
    // Wait for window to open
    delay(2);
    
    // Activate Mail
    mail.activate();
    
    // Wait a bit more
    delay(1);
    
    // Get the reply text
    const replyText = {text_escaped};
    
    // Type the text using System Events
    systemEvents.keystroke(replyText);
    '''
    
    try:
        run_jxa_script(script)
        print("✅ Szöveg sikeresen beillesztve a Mail-be!")
    except Exception as e:
        print(f"❌ JXA hiba: {e}")
        # Fallback to clipboard
        try:
            subprocess.run(['pbcopy'], input=text, text=True, check=True)
            print("✅ Szöveg vágólapra másolva - illeszd be ⌘V-vel!")
        except:
            print("❌ Nem sikerült a vágólapra másolni")

def main():
    try:
        print("📧 Email lekérése...")
        email_content = get_selected_mail()
        
        print("🧠 Összefoglaló készítése...")
        summary = create_summary(email_content)
        
        print("💡 Opciók generálása...")
        options = create_options(email_content)
        
        print("📝 Nyelv detektálása...")
        language = detect_language(email_content)
        
        print("🎯 Párbeszédablak...")
        chosen_reply = show_dialog_and_get_reply(summary, options)
        
        if not chosen_reply:
            print("❌ Megszakítva")
            return
        
        print(f"✅ Választott válasz: {chosen_reply}")
        print("📝 Teljes válasz generálása...")
        
        final_response = create_full_response(email_content, chosen_reply, language)
        
        print("📋 Automatikus beillesztés...")
        paste_to_mail_jxa(final_response)
        
        print("🎉 Kész!")
        
    except Exception as e:
        print(f"❌ Hiba: {e}")
        
        # Show error in dialog
        error_script = f'''
        const app = Application.currentApplication();
        app.includeStandardAdditions = true;
        app.displayDialog("Hiba: {str(e)}", {{buttons: ["OK"]}});
        '''
        try:
            run_jxa_script(error_script)
        except:
            pass

if __name__ == "__main__":
    main()
