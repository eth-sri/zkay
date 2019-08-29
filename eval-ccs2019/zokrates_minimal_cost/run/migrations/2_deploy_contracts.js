var helpers = require('../helpers.js');

// import libraries
var bn256g2 = artifacts.require("BN256G2");
var pairing = artifacts.require("Pairing");

// import verifier
var verifier = artifacts.require("Verifier");

// deploy the contracts one after another, inject verifiers
module.exports = async function(deployer) {
    let accounts = await web3.eth.getAccounts();

    // deploy libraries
    await helpers.deploy(web3, deployer, bn256g2, [], accounts[0]);
    await helpers.deploy(web3, deployer, pairing, [], accounts[0]);
    
    // link libraries _before_ deploying verification contracts
	await deployer.link(pairing, verifier);
	await deployer.link(bn256g2, verifier);
	await helpers.deploy(web3, deployer, verifier, [], accounts[0]);
};
