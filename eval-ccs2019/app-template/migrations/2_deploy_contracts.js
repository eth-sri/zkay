var helpers = require('../helpers.js');

// set contract name
// EXAMPLE:
// helpers.contract_name = "Reviews"
$CONTRACT_NAME

// import the built constructs (the strings have to match the contract names, not the original .sol file names)
var genPublicKeyInfrastructure = artifacts.require("PublicKeyInfrastructure");
var bn256g2 = artifacts.require("BN256G2");
var pairing = artifacts.require("Pairing");

// EXAMPLE: var verify_registerPaper = artifacts.require("Verify_registerPaper");
$VERIFIERS_FETCH

// deploy the contracts one after another, inject verifiers
module.exports = async function(deployer) {
    let accounts = await web3.eth.getAccounts();

    // deploy the libraries and PKI
    await helpers.deploy(web3, deployer, bn256g2, [], accounts[0]);
    await helpers.deploy(web3, deployer, pairing, [], accounts[0]);
    await helpers.deploy(web3, deployer, genPublicKeyInfrastructure, [], accounts[0]);
    
    // link libraries _before_ deploying verification contracts
    // EXAMPLE:
    // await deployer.link(pairing, verify_registerPaper);
    // await deployer.link(bn256g2, verify_registerPaper);
    // await helpers.deploy(web3, deployer, verify_registerPaper, [], accounts[0]);
$VERIFIERS_DEPLOY
};
