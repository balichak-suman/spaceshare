# File Upload + Blockchain Log

## Prerequisites

- [Node.js & npm](https://nodejs.org/)
- [Python 3](https://www.python.org/)
- [MetaMask browser extension](https://metamask.io/)

---

## Step-by-Step Guide

### 1. Install Dependencies

Open a terminal and run:

```bash
cd blockchain
npm install
```

### 2. Compile the Smart Contract

```bash
npx hardhat compile
```

### 3. Start the Local Blockchain

```bash
npx hardhat node
```
> **Keep this terminal open and running!**

---

### 4. Deploy the Smart Contract

Open a **new terminal window** and run:

```bash
cd blockchain
npx hardhat run scripts/deploy.js --network localhost
```

- After running, you will see output like:  
  `Contract deployed to: 0xABC123...`
- **Copy** the contract address (starts with `0x`).

---

### 5. Get the Contract ABI

- Open the file:  
  `blockchain/artifacts/contracts/FileLog.sol/FileLog.json`
- Find the `"abi": [...]` section.
- **Copy** the entire ABI array (from `[` to `]`).

---

### 6. Configure the Frontend

- Open:  
  `backend/static/index.html`
- Replace:
  - `PASTE_YOUR_DEPLOYED_CONTRACT_ADDRESS_HERE` with the contract address you copied.
  - `PASTE_YOUR_ABI_HERE` with the ABI array you copied (paste it as valid JavaScript).

Example:
```js
const contractAddress = "0xABC123...";
const contractABI = [ ... ]; // paste ABI here
```

---

### 7. Start the Flask Backend

Open a **new terminal window** and run:

```bash
cd backend
pip install flask
flask run
```

---

### 8. Open the App in Your Browser

- Go to: [http://localhost:5000](http://localhost:5000)
- In MetaMask, select the "Localhost 8545" network.
- Click "Connect MetaMask".
- Choose a file and click "Upload".

---

## Port Forwarding (Ngrok)

To make your local Flask backend accessible over the internet, we use [ngrok](https://ngrok.com/):

### Setup
1. Install ngrok (see below or https://ngrok.com/download).
2. Start your backend as usual (the script will now also start ngrok automatically).
3. Ngrok will provide a public URL to access your Flask backend from anywhere.

### How to install ngrok
- On macOS (recommended):
  ```sh
  brew install --cask ngrok
  ```
- Or download from https://ngrok.com/download and follow their instructions.

### How to use (automated)
- The `start-dev.sh` script now opens a new terminal and runs:
  ```sh
  ngrok http 5001
  ```
- Copy the public forwarding URL from the ngrok terminal and use it to access your backend remotely.

### Notes
- You may need to sign up for a free ngrok account and run `ngrok config add-authtoken <your_token>` once.
- Only the Flask backend is exposed; the blockchain node remains local for security.

---

**You are done!**  
Your file will be uploaded and logged on the blockchain.
