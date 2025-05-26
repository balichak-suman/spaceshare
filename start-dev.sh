#!/bin/bash

# Absolute paths (edit if your structure changes)
BLOCKCHAIN_DIR="/Users/balichaksuman/Downloads/plz/SpaceShare/blockchain"
BACKEND_DIR="/Users/balichaksuman/Downloads/plz/SpaceShare/backend"
VENV_PATH="$BACKEND_DIR/venv/bin/activate"
BLOCKCHAIN_VENV_PATH="$BLOCKCHAIN_DIR/venv/bin/activate"
BACKEND_VENV_PATH="$BACKEND_DIR/venv/bin/activate"

osascript <<EOF
tell application "Terminal"
    do script "cd '$BLOCKCHAIN_DIR'; source '$BLOCKCHAIN_VENV_PATH'; npx hardhat node 2>&1 | awk '
      /eth_call/ { c = 1; next }
      c && /<unrecognized-selector>/ { next }
      c && /From:/ { next }
      c && /To:/ { c = 0; next }

      /eth_sendRawTransaction/ { s = 1; next }
      s && /Nonce too low/ { s = 0; next }

      /^ *Error: Transaction reverted without a reason/ { next }

      /^eth_/ { next }

      { print }
    '"
    delay 3
    do script "cd '$BACKEND_DIR'; source '$BACKEND_VENV_PATH'; python3 -m pip install --break-system-packages -r requirements.txt; python3 app.py"
    delay 5
    do script "cd '$BLOCKCHAIN_DIR'; source '$BLOCKCHAIN_VENV_PATH'; npx hardhat run scripts/deploy.js --network localhost"
end tell
EOF
