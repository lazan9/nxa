import argparse
from .assistant import (
    create_summary,
    create_options,
    create_full_response,
    detect_language,
)


def read_email(path: str | None) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    print("Paste the email content. Finish with an empty line:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines)


def choose_option(options: list[str]) -> str:
    for idx, opt in enumerate(options, 1):
        print(f"{idx}. {opt}")
    choice = input("Choose option number or type your own reply: ").strip()
    if choice in {"1", "2", "3"}:
        return options[int(choice) - 1]
    return choice


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Interactive email reply assistant")
    parser.add_argument("email", nargs="?", help="Path to text file containing the email")
    args = parser.parse_args(argv)

    email = read_email(args.email)
    language = detect_language(email)

    summary = create_summary(email)
    print("\n-- Összefoglaló --\n" + summary + "\n")

    options = create_options(email)
    reply_draft = choose_option(options)
    print(f"\nVálasztott vázlat: {reply_draft}\n")

    final = create_full_response(email, reply_draft, language)
    print("\n-- Generált válasz --\n")
    print(final)


if __name__ == "__main__":
    main()
