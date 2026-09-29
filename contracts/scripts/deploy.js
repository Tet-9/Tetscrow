const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  // --- 1. Deploy the TET token: fixed supply, minted entirely to the deployer's wallet ---
  const TOTAL_SUPPLY = hre.ethers.parseUnits("1000000000", 18); // 1,000,000,000 TET — set your real supply here
  const Token = await hre.ethers.getContractFactory("TetToken");
  const token = await Token.deploy(TOTAL_SUPPLY, deployer.address);
  await token.waitForDeployment();
  console.log("TetToken deployed:", await token.getAddress());

  // --- 2. Deploy the escrow contract ---
  const feeRecipient = process.env.FEE_RECIPIENT || deployer.address;
  const feeBasisPoints = 100; // 1% platform fee, adjust as needed (hard-capped at 10% in the contract)
  const autoReleaseDelay = 14 * 24 * 60 * 60; // 14 days — funds auto-release to receiver if sender goes silent after delivery
  const Escrow = await hre.ethers.getContractFactory("TetEscrow");
  const escrow = await Escrow.deploy(deployer.address, feeRecipient, feeBasisPoints, autoReleaseDelay);
  await escrow.waitForDeployment();
  console.log("TetEscrow deployed:", await escrow.getAddress());

  console.log("\nSave these addresses into backend/.env and frontend/js/config.js");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
