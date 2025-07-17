#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Mail Assistant - Handles everything in Python
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

# Dummy data if no OpenAI key
DUMMY_RESPONSES = {
    "summary": "Bejövő email összefoglaló (teszt mód - add meg az OpenAI kulcsot!)",
    "options": [
        "Köszönöm a levelét, hamarosan válaszolok",
        "Megkaptam az üzenetet, feldolgozás alatt", 
        "Érdekes felvetés, átgondolom és visszaírok"
    ],
    "lang": "hu"
}

def has_openai_key():
    """Check if OpenAI API key is available"""
    return bool(os.getenv("OPENAI_API_KEY"))

def get_selected_mail():
    """Get selected mail content from Mail app"""
    script = '''
    tell application "Mail"
        if (count of (get selection)) = 0 then
            error "Nincs kijelölt üzenet"
        end if
        set theMessage to item 1 of (get selection)
        return content of theMessage
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"Nem sikerült lekérni az emailt: {e.stderr}")

def call_openai(prompt, model="gpt-4o-mini"):
    """Call OpenAI API"""
    if not has_openai_key():
        return "TESZT VÁLASZ - Add meg az OpenAI API kulcsot!"
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful email assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI hiba: {str(e)}"

def detect_language(text):
    """Detect language of text"""
    try:
        from langdetect import detect
        return detect(text)
    except:
        return "hu"

def create_summary(email_content):
    """Create Hungarian summary of email"""
    if not has_openai_key():
        return DUMMY_RESPONSES["summary"]
    
    prompt = f"""
    Foglalja össze röviden magyarul az alábbi e-mail tartalmát.
    Legyen max 2 mondat, lényegre törő.
    
    Email:
    {email_content}
    """
    return call_openai(prompt)

def create_options(email_content):
    """Create 3 response options"""
    if not has_openai_key():
        return DUMMY_RESPONSES["options"]
    
    prompt = f"""
    Készíts három különböző, rövid válaszlehetőséget magyarul az alábbi emailre.
    Minden opció legyen 5-12 szó hosszú, segítőkész hangvételű.
    Add meg csak a három opciót, számozás nélkül, soronként egyet.
    
    Email:
    {email_content}
    """
    response = call_openai(prompt)
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    return lines[:3] if lines else DUMMY_RESPONSES["options"]

def create_full_response(email_content, chosen_reply, target_language):
    """Create full, elegant response"""
    if not has_openai_key():
        return f"[TESZT VÁLASZ] {chosen_reply} - Add meg az OpenAI kulcsot a teljes funkcionalitáshoz!"
    
    prompt = f"""
    Írj egy udvarias, professzionális és részletes email választ a következő alapján:
    
    EREDETI EMAIL:
    {email_content}
    
    VÁLASZ IRÁNYA/TÉMA:
    {chosen_reply}
    
    NYELV: {target_language}
    
    KÖVETELMÉNYEK:
    - Legyél udvarias és professzionális
    - A válasz legyen strukturált és részletes (3-5 bekezdés)
    - Használj megfelelő üdvözlést és zárást
    - A válasz legyen értelmes és kontextuális
    - Minimum 100-200 szó legyen
    - Ha kérdéseket tesznek fel, válaszolj rájuk
    - Ha valamilyen akciót kérnek, reflektálj rá
    
    Csak a válasz szövegét add meg, semmi mást.
    """
    return call_openai(prompt)

def show_dialog(summary, options):
    """Show selection dialog using osascript"""
    # Escape quotes and newlines for AppleScript
    summary_clean = summary.replace('"', '\\"').replace('\n', ' ')
    opt1_clean = options[0].replace('"', '\\"') if len(options) > 0 else "Opció 1"
    opt2_clean = options[1].replace('"', '\\"') if len(options) > 1 else "Opció 2"
    opt3_clean = options[2].replace('"', '\\"') if len(options) > 2 else "Opció 3"
    
    script = f'''
    set dialogResult to display dialog "{summary_clean}

Válaszlehetőségek:

1. {opt1_clean}
2. {opt2_clean}
3. {opt3_clean}

Írd be a számot vagy adj meg saját szöveget:" default answer "" buttons {{"Mégse", "OK"}} default button "OK"
    
    return text returned of dialogResult
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True)
        choice = result.stdout.strip()
        
        if choice == "1":
            return options[0]
        elif choice == "2":
            return options[1] if len(options) > 1 else options[0]
        elif choice == "3":
            return options[2] if len(options) > 2 else options[0]
        else:
            return choice
            
    except subprocess.CalledProcessError:
        return None

def paste_to_mail(text):
    """Copy to clipboard and open Mail reply window"""
    try:
        # Copy to clipboard
        subprocess.run(['pbcopy'], input=text, text=True, check=True)
        print("✅ Válasz vágólapra másolva!")
        
        # Open Mail reply window
        script = '''
        tell application "Mail"
            activate
            set theMessage to item 1 of (get selection)
            set newReply to reply theMessage opening window
            delay 1
        end tell
        '''
        
        subprocess.run(['osascript', '-e', script], check=True)
        
        # Show instruction
        instruction_script = '''
        display dialog "A válasz a vágólapra került!

Nyomd meg Cmd+V a beillesztéshez a Mail ablakban." buttons {"OK"} default button "OK" giving up after 3
        '''
        
        subprocess.run(['osascript', '-e', instruction_script])
        
    except Exception as e:
        print(f"Hiba: {e}")
        # Just copy to clipboard as fallback
        try:
            subprocess.run(['pbcopy'], input=text, text=True, check=True)
            print("✅ Szöveg vágólapra másolva - illeszd be kézzel!")
        except:
            print("❌ Nem sikerült a vágólapra másolni")

def main():
    try:
        print("📧 Email tartalom lekérése...")
        email_content = get_selected_mail()
        
        print("🧠 Összefoglaló készítése...")
        summary = create_summary(email_content)
        
        print("💡 Válaszopciók generálása...")
        options = create_options(email_content)
        
        print("📝 Nyelv detektálása...")
        language = detect_language(email_content)
        
        print("🎯 Párbeszédablak megjelenítése...")
        chosen_reply = show_dialog(summary, options)
        
        if not chosen_reply:
            print("❌ Megszakítva")
            return
        
        print(f"✅ Választott válasz: {chosen_reply}")
        print("📝 Részletes válasz generálása...")
        
        final_response = create_full_response(email_content, chosen_reply, language)
        
        print("📋 Válasz előkészítése...")
        paste_to_mail(final_response)
        
        print("🎉 Kész!")
        
    except Exception as e:
        subprocess.run(['osascript', '-e', f'display alert "Hiba: {str(e)}"'])
        print(f"❌ Hiba: {e}")

if __name__ == "__main__":
    main()
