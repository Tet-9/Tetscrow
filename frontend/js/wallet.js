// Wallet connection (MetaMask, via EIP-6963 discovery so it's picked correctly even
// when other extensions are installed) + on-chain interaction helper (ethers.js).
const Tet = (() => {
  let provider, signer, address;
  const found = new Map(); // rdns -> { info, provider }

  // EIP-6963: every installed wallet extension announces itself this way. This is the
  // standard, reliable way to find MetaMask specifically instead of guessing at
  // window.ethereum, which can be overwritten when multiple wallets are installed.
  window.addEventListener("eip6963:announceProvider", (e) => {
    found.set(e.detail.info.rdns, e.detail);
  });
  window.dispatchEvent(new Event("eip6963:requestProvider"));

  function pickMetaMask() {
    for (const [rdns, d] of found) {
      if (rdns.includes("metamask") || (d.info.name || "").toLowerCase().includes("metamask")) return d.provider;
    }
    if (window.ethereum) {
      if (Array.isArray(window.ethereum.providers)) {
        const mm = window.ethereum.providers.find((p) => p.isMetaMask);
        if (mm) return mm;
      }
      if (window.ethereum.isMetaMask) return window.ethereum;
    }
    return null;
  }

  function anyInjected() {
    if (found.size) return found.values().next().value.provider;
    return window.ethereum || null;
  }

  async function connectWallet(opts = {}) {
    // Give EIP-6963 announcements a brief moment to arrive on first call.
    if (!found.size) await new Promise((r) => setTimeout(r, 60));
    const eip1193 = opts.preferMetaMask === false ? anyInjected() : (pickMetaMask() || anyInjected());
    if (!eip1193) {
      alert("No Ethereum wallet found. Install the MetaMask extension (or another injected wallet) to continue.");
      return null;
    }
    provider = new ethers.BrowserProvider(eip1193);
    await provider.send("eth_requestAccounts", []);

    const network = await provider.getNetwork();
    if ("0x" + network.chainId.toString(16) !== window.TET_CONFIG.CHAIN_ID_HEX) {
      try {
        await eip1193.request({ method: "wallet_switchEthereumChain", params: [{ chainId: window.TET_CONFIG.CHAIN_ID_HEX }] });
      } catch (e) {
        console.warn("User is on the wrong network and declined to switch.", e);
      }
    }

    signer = await provider.getSigner();
    address = await signer.getAddress();
    renderWalletPill(address);
    return address;
  }

  function renderWalletPill(addr) {
    document.querySelectorAll("[data-wallet-pill]").forEach((el) => {
      el.innerHTML = `<span class="dot"></span> ${addr.slice(0, 6)}...${addr.slice(-4)}`;
    });
  }

  async function signInWithEthereum() {
    const addr = address || (await connectWallet());
    if (!addr) return null;

    const nonceRes = await fetch(`${window.TET_CONFIG.API_BASE}/auth/nonce/${addr}`);
    const { nonce } = await nonceRes.json();

    const message = `Sign in to Tet.\n\nWallet: ${addr}\nNonce: ${nonce}`;
    const signature = await signer.signMessage(message);

    const verifyRes = await fetch(`${window.TET_CONFIG.API_BASE}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ wallet_address: addr, signature, message }),
    });
    if (!verifyRes.ok) throw new Error("Sign-in failed");
    const { access_token } = await verifyRes.json();
    localStorage.setItem("tet_jwt", access_token);
    localStorage.setItem("tet_wallet", addr);
    return access_token;
  }

  function getEscrowContract() {
    return new ethers.Contract(window.TET_CONFIG.TET_ESCROW_ADDRESS, window.TET_ESCROW_ABI, signer);
  }

  // ---- asset helpers (native ETH or an ERC-20 like USDC) ----
  function assetFor(symbol) {
    const a = window.TET_CONFIG.ASSETS[symbol];
    if (!a) throw new Error(`Unknown asset "${symbol}"`);
    return a;
  }
  function tokenAddressFor(symbol) {
    const a = assetFor(symbol);
    if (a.kind === "native") return null;
    const addr = a.address[window.TET_CONFIG.CHAIN_ID_HEX];
    if (!addr) throw new Error(`${symbol} has no address configured for this network yet.`);
    return addr;
  }
  function parseAmount(symbol, amount) {
    return ethers.parseUnits(String(amount), assetFor(symbol).decimals);
  }
  async function balanceOf(symbol, owner) {
    const a = assetFor(symbol);
    if (a.kind === "native") return provider.getBalance(owner);
    const c = new ethers.Contract(tokenAddressFor(symbol), window.ERC20_ABI, provider);
    return c.balanceOf(owner);
  }

  async function createAndFundAgreement({ receiver, arbiter, asset = "ETH", amount, termsURI }) {
    const contract = getEscrowContract();
    const zero = "0x0000000000000000000000000000000000000000";
    const isNative = assetFor(asset).kind === "native";
    const tokenAddress = isNative ? null : tokenAddressFor(asset);
    const amountWei = parseAmount(asset, amount);

    const createTx = await contract.createAgreement(receiver, arbiter || zero, tokenAddress || zero, amountWei, termsURI || "");
    const createReceipt = await createTx.wait();

    const event = createReceipt.logs
      .map((l) => { try { return contract.interface.parseLog(l); } catch { return null; } })
      .find((e) => e && e.name === "AgreementCreated");
    const onchainId = event.args.id;

    if (!isNative) {
      // ERC-20 path (USDC etc.): approve the escrow contract to pull the funds, then fund.
      const token = new ethers.Contract(tokenAddress, window.ERC20_ABI, signer);
      const current = await token.allowance(address, window.TET_CONFIG.TET_ESCROW_ADDRESS);
      if (current < amountWei) {
        const approveTx = await token.approve(window.TET_CONFIG.TET_ESCROW_ADDRESS, amountWei);
        await approveTx.wait();
      }
    }
    const fundTx = await contract.fund(onchainId, isNative ? { value: amountWei } : {});
    const fundReceipt = await fundTx.wait();

    return { onchainId: Number(onchainId), txHash: fundReceipt.hash };
  }

  return {
    connectWallet, signInWithEthereum, getEscrowContract, createAndFundAgreement,
    assetFor, tokenAddressFor, parseAmount, balanceOf,
    getAddress: () => address, listWallets: () => Array.from(found.values()).map((d) => d.info),
  };
})();
