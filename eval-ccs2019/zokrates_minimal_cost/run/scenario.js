var helpers = require('./helpers.js');

module.exports = async function(callback) {
    // gives 10 example accounts
    let accounts = await web3.eth.getAccounts();
    
    // select account
	var account = accounts[0];
    
    // load contract and the deployed instance
    var verifier = artifacts.require("Verifier");
	let verifier_instance = await verifier.deployed();

	// load pre-generated proof
	var proof = require('./proof.js').proof;
	
	// run transaction with pre-generated proof directly
	args = [proof.proof.A, proof.proof.B, proof.proof.C, proof.input];
	await helpers.tx(verifier_instance, "verifyTx", args, account);

    console.log(">> end of scenario")
}
