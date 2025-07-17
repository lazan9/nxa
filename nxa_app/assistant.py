import os
import textwrap

DUMMY_RESPONSES = {
    "summary": "Teszt összefoglaló - add meg az OpenAI API kulcsot a teljes funkcionalitáshoz.",
    "options": [
        "Köszönöm a levelét, hamarosan válaszolok.",
        "Megkaptam az üzenetet, feldolgozás alatt.",
        "Érdekes felvetés, átgondolom és visszaírok."
    ]
}


def has_openai_key() -> bool:
    """Return True if an OpenAI API key is available."""
    return bool(os.getenv("OPENAI_API_KEY"))


def call_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI API if available, otherwise return a test string."""
    if not has_openai_key():
        return f"[TESZT MOD] {prompt[:60]}..."

    try:
        from openai import OpenAI
    except Exception:
        return f"[HIANYZO DEPENDENCIA] {prompt[:60]}..."

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful email assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"[OPENAI HIBA] {exc}"


def detect_language(text: str) -> str:
    """Detect language using langdetect if available."""
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "hu"


def create_summary(email_content: str) -> str:
    """Create a short summary in Hungarian."""
    if not has_openai_key():
        return DUMMY_RESPONSES["summary"]

    prompt = textwrap.dedent(
        f"""
        Foglalja össze röviden magyarul az alábbi e-mail tartalmát.
        Legyen legfeljebb két mondat.

        Email:
        {email_content}
        """
    )
    return call_openai(prompt)


def create_options(email_content: str):
    """Return three short reply options."""
    if not has_openai_key():
        return DUMMY_RESPONSES["options"]

    prompt = textwrap.dedent(
        f"""
        Készíts három rövid válaszlehetőséget magyarul az alábbi emailre.
        Minden opció 5-12 szóból álljon, soronként egyet adj meg, számozás nélkül.

        Email:
        {email_content}
        """
    )
    resp = call_openai(prompt)
    lines = [l.strip() for l in resp.splitlines() if l.strip()]
    return lines[:3] if lines else DUMMY_RESPONSES["options"]


def create_full_response(email_content: str, draft: str, lang: str) -> str:
    """Create a detailed reply in the given language."""
    if not has_openai_key():
        return f"[TESZT VALASZ] {draft}"

    prompt = textwrap.dedent(
        f"""
        Írj egy udvarias, részletes email választ ({lang} nyelven) az alábbiak alapján:

        EREDETI EMAIL:
        {email_content}

        VALASZ TERVE:
        {draft}

        Követelmények:
        - Legyen 3-5 bekezdés
        - Professzionális, barátságos hangnem
        - Legalább 150 szó
        - Használj megfelelő üdvözlést és lezárást

        Csak a kész választ add meg.
        """
    )
    return call_openai(prompt)
