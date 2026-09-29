// Standard Uniswap V2 liquidity provisioning.
// Run AFTER deploy.js. Requires the deployer wallet to hold both TET and ETH.
// The deployer receives the LP tokens back — nothing here can pull liquidity
// out from under holders; that would require a separate malicious contract,
// which this repo does not include and will not add.
//
// Usage: TET_ADDRESS=0x... LIQUIDITY_TET=... LIQUIDITY_ETH=... npx hardhat run scripts/addLiquidity.js --network mainnet

const hre = require("hardhat");

const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"; // mainnet Uniswap V2 Router02
const ROUTER_ABI = [
  "function addLiquidityETH(address token,uint amountTokenDesired,uint amountTokenMin,uint amountETHMin,address to,uint deadline) external payable returns (uint amountToken, uint amountETH, uint liquidity)",
];
const ERC20_ABI = [
  "function approve(address spender, uint256 amount) external returns (bool)",
];

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const tokenAddress = process.env.TET_ADDRESS;
  if (!tokenAddress) throw new Error("Set TET_ADDRESS env var");

  const tetAmount = hre.ethers.parseUnits(process.env.LIQUIDITY_TET || "0", 18);
  const ethAmount = hre.ethers.parseEther(process.env.LIQUIDITY_ETH || "0");
  if (tetAmount === 0n || ethAmount === 0n) throw new Error("Set LIQUIDITY_TET and LIQUIDITY_ETH env vars");

  const token = new hre.ethers.Contract(tokenAddress, ERC20_ABI, deployer);
  const router = new hre.ethers.Contract(UNISWAP_V2_ROUTER, ROUTER_ABI, deployer);

  console.log("Approving router to spend TET...");
  await (await token.approve(UNISWAP_V2_ROUTER, tetAmount)).wait();

  console.log("Adding liquidity (TET + ETH)...");
  const deadline = Math.floor(Date.now() / 1000) + 60 * 20;
  const tx = await router.addLiquidityETH(
    tokenAddress,
    tetAmount,
    (tetAmount * 95n) / 100n, // 5% slippage tolerance
    (ethAmount * 95n) / 100n,
    deployer.address, // LP tokens returned to YOUR wallet
    deadline,
    { value: ethAmount }
  );
  const receipt = await tx.wait();
  console.log("Liquidity added. Tx:", receipt.hash);
  console.log(
    "\nConsider time-locking your LP tokens with a reputable third-party locker " +
    "(e.g. Team.Finance, Unicrypt) and publishing the lock publicly — that is what " +
    "actually earns holder trust, not a claim in marketing copy."
  );
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
