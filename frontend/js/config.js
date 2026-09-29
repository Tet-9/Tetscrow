// Fill these in after deploying (contracts/scripts/deploy.js prints them).
window.TET_CONFIG = {
  API_BASE: "http://localhost:8000",
  CHAIN_ID_HEX: "0xaa36a7", // Sepolia testnet -- change to "0x1" for mainnet
  TET_ESCROW_ADDRESS: "0x270e0F4473A0847624e474D18f88D808e7cCA46a",
  TET_TOKEN_ADDRESS: "0x270e0F4473A0847624e474D18f88D808e7cCA46a",
  UNISWAP_PAIR_URL: "https://app.uniswap.org/explore/pools/ethereum/0x0000000000000000000000000000000000000000",
  // Assets an agreement can be funded with. "native" (ETH) always works. Add more ERC-20s
  // the same way USDC is added below -- address + decimals is all Tet needs.
  ASSETS: {
    ETH:  { kind: "native", symbol: "ETH", decimals: 18 },
    USDC: {
      kind: "erc20", symbol: "USDC", decimals: 6,
      address: { "0x1": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "0xaa36a7": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238" }
    }
  }
};

window.TET_ESCROW_ABI = [
  "function createAgreement(address receiver, address arbiter, address token, uint256 amount, string termsURI) external returns (uint256)",
  "function fund(uint256 id) external payable",
  "function markDelivered(uint256 id) external",
  "function release(uint256 id) external",
  "function autoRelease(uint256 id) external",
  "function autoReleaseDelay() view returns (uint256)",
  "function raiseDispute(uint256 id, string reason) external",
  "function resolveDispute(uint256 id, address winner) external",
  "function cancel(uint256 id) external",
  "function getAgreement(uint256 id) external view returns (tuple(address sender, address receiver, address arbiter, address token, uint256 amount, uint256 createdAt, uint256 deliveredAt, uint8 status, string termsURI))",
  "event AgreementCreated(uint256 indexed id, address indexed sender, address indexed receiver, address token, uint256 amount, string termsURI)",
];

window.ERC20_ABI = [
  "function balanceOf(address) view returns (uint256)",
  "function allowance(address owner, address spender) view returns (uint256)",
  "function approve(address spender, uint256 amount) external returns (bool)",
  "function decimals() view returns (uint8)",
  "function symbol() view returns (string)",
];

// Kept for backwards compatibility with anything still referencing the old name.
window.TET_TOKEN_ABI = window.ERC20_ABI;

// Looks up an asset's display symbol from its on-chain token address (or ETH when null).
window.symbolForToken = function (tokenAddress) {
  if (!tokenAddress || /^0x0+$/.test(tokenAddress)) return "ETH";
  var chain = window.TET_CONFIG.CHAIN_ID_HEX, assets = window.TET_CONFIG.ASSETS;
  for (var key in assets) {
    var a = assets[key];
    if (a.kind === "erc20" && a.address[chain] && a.address[chain].toLowerCase() === tokenAddress.toLowerCase()) return a.symbol;
  }
  return "TOKEN";
};
