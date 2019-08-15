var helpers = require('../helpers.js');

// import the built constructs (the strings have to match the contract names, not the original .sol file names)
var pki = artifacts.require("PublicKeyInfrastructure");
var bn256g2 = artifacts.require("BN256G2");
var pairing = artifacts.require("Pairing");

var verify_registerPaper = artifacts.require("Verify_registerPaper");
var verify_recordReview = artifacts.require("Verify_recordReview");
var verify_decideAcceptance = artifacts.require("Verify_decideAcceptance");

// deploy the contracts one after another, inject verifiers
module.exports = async function(deployer) {
    let accounts = await web3.eth.getAccounts();
        
    // first, deploy the libraries
    await helpers.deploy(web3, deployer, bn256g2, [], accounts[0]);
    await helpers.deploy(web3, deployer, pairing, [], accounts[0]);
    
    await helpers.deploy(web3, deployer, pki, [], accounts[0]);
    
    // link libraries _before_ deploying verification contracts
    await deployer.link(pairing, verify_registerPaper);
    await deployer.link(bn256g2, verify_registerPaper);
    await helpers.deploy(web3, deployer, verify_registerPaper, [], accounts[0]);
    
    await deployer.link(pairing, verify_recordReview);
    await deployer.link(bn256g2, verify_recordReview);
    await helpers.deploy(web3, deployer, verify_recordReview, [], accounts[0]);
    
    await deployer.link(pairing, verify_decideAcceptance);
    await deployer.link(bn256g2, verify_decideAcceptance);
    await helpers.deploy(web3, deployer, verify_decideAcceptance, [], accounts[0]);
};
