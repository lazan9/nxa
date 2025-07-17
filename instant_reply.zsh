#!/bin/zsh
# instant_reply.zsh - Main launcher

set -e
ROOT="${HOME}/Instant-Reply"

if [[ "$1" == "install" ]]; then
  echo "[+] Installing Python deps globally"
  /usr/bin/python3 -m pip install --upgrade pip --user
  /usr/bin/python3 -m pip install -r "${ROOT}/requirements.txt" --user
  echo "[+] Dependencies installed"
  echo "[+] Set your OpenAI API key in ~/.zshrc:"
  echo "export OPENAI_API_KEY=\"sk-...\"" 
  exit 0
fi

# Direct execution
export PYTHONPATH="${ROOT}/src:$PYTHONPATH"
/usr/bin/python3 "${ROOT}/src/reply_assist.py" "$@"
