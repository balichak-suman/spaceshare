const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const FileLog = await hre.ethers.getContractFactory("FileLog");
  const fileLog = await FileLog.deploy();
  await fileLog.waitForDeployment();
  const address = await fileLog.getAddress();
  console.log("Contract deployed to:", address);
  // Write the address to a file
  fs.writeFileSync(
    "deployedAddress.json",
    JSON.stringify({ address }, null, 2)
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
