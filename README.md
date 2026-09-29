# Tet — Decentralized & Secure Escrow Platform

A full clone of the crowescrow.io feature set, rebuilt end-to-end under the name **Tet**:
smart-contract escrow, a Python backend, a multi-page wallet-connected frontend, and a
$TET token with a standard DEX-listing pipeline.

## Architecture

```
contracts/   Solidity — TetEscrow.sol (milestone escrow + arbitration), TetToken.sol (ERC-20)
             Hardhat project: compile, deploy, add Uniswap liquidity
backend/     Python FastAPI — wallet-signature auth, off-chain metadata + indexing,
             dispute records, live on-chain token stats. Never holds funds or private keys.
frontend/    Static multi-page site (no build step) — landing page + app:
             dashboard.html, create-escrow.html, escrow-detail.html, disputes.html.
             Wallet connection + all fund-moving transactions happen client-side via
             ethers.js — the user's own wallet signs every transaction.
```

**Why this split:** the actual custody/escrow logic has to live on-chain (Solidity) —
that's what makes it "decentralized" rather than "a company holding your money." Python
runs everything around that: indexing agreements for a fast dashboard, wallet-based
login, dispute record-keeping, and reading live token/liquidity data. This mirrors how
Crow itself is structured (Ethereum smart contract + web app on top).

## Setup

1. **Contracts**
   ```
   cd contracts && npm install
   cp .env.example .env   # fill in RPC URL + your deployer private key
   npx hardhat compile
   npx hardhat run scripts/deploy.js --network sepolia
   ```
   Copy the two printed addresses into `backend/.env` and `frontend/js/config.js`.

2. **Backend**
   ```
   cd backend && pip install -r requirements.txt
   cp .env.example .env   # fill in RPC_URL, contract addresses, JWT_SECRET
   uvicorn app.main:app --reload
   ```

3. **Frontend** — no build step, it's static HTML/JS. Serve it with any static server, e.g.:
   ```
   cd frontend && python -m http.server 5173
   ```
   Open `index.html`, connect a wallet (MetaMask), and the whole flow works: create
   agreement → fund → deliver → release/dispute.

4. **Token + liquidity** (once you're ready)
   ```
   cd contracts
   TET_ADDRESS=0x... LIQUIDITY_TET=... LIQUIDITY_ETH=... npx hardhat run scripts/addLiquidity.js --network mainnet
   ```
   Set `UNISWAP_V2_PAIR_ADDRESS` in `backend/.env` afterward so the `/token/stats`
   endpoint and the landing page's token section can read live reserves.

## What's real vs. what you still need to add

**Fully working:** escrow contract logic (create/fund/deliver/release/dispute/resolve),
wallet-signature login, off-chain indexing, multi-page frontend, ERC-20 token, standard
Uniswap liquidity script, live (non-fabricated) token-stats endpoint.

**You still need to add, before real users touch this:**
- **A security audit of `TetEscrow.sol`.** This is unaudited. Do not put real user
  funds through it until a professional auditor has reviewed it — escrow contracts are
  a classic exploit target (reentrancy, fee-on-transfer token edge cases, etc.).
- **A real arbiter process.** Right now `resolveDispute()` just trusts whoever the
  `arbiter` address is. Decide who that is (you, a panel, a DAO) and how they're notified.
- **Legal review before any public $TET marketing** — token sales/promotion can trigger
  securities and financial-promotion rules depending on your jurisdiction; get a lawyer,
  not me, to sign off on this.
- **KYC/compliance** if you plan to handle real-world-asset transactions or larger sums.
- **Production database** (swap SQLite for Postgres), rate limiting, and moving the
  nonce store from in-memory to Redis if you run more than one backend instance.

## On the token specifically

The contract and liquidity script here are deliberately plain: fixed supply, no owner
mint, no pause/blacklist backdoor, LP tokens go straight to your own wallet. I didn't
build (and won't build) anything that fabricates press coverage, inflates user/trading
numbers, or lets liquidity be pulled out from under holders. If you want the token to be
trusted, the strongest lever you actually have is locking your LP tokens publicly with a
third-party locker and being straightforward about what Tet does and doesn't do yet.

## Landing page (Crow-style layout, purple)

- `frontend/index.html` is the public landing page. The earlier dark landing is kept as `index-v1.html`.
- Page colours are two values at the top of `css/landing.css`: `--page` (purple background) and `--panel` (light panels).
- Every outside link lives in `js/site-config.js` (Gitbook, Pitch Deck, Twitter, Telegram, YouTube, video, DEXTools, CoinMarketCap, contact email). Empty ones show a "coming soon" message instead of a dead link.
- The footer contract address, its copy button, and the Uniswap and Etherscan buttons read `TET_TOKEN_ADDRESS` from `js/config.js`. They stay disabled until a real address is set.
- The "Users Registered" number comes from the backend `/stats` endpoint (real wallet sign-ins). Press cards come from the `press` list in `site-config.js`; add only real coverage.
- The illustrations are simple original SVGs. Replace them with your own artwork.
