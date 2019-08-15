var Welfare = artifacts.require("Welfare");
var EligibilityChecker = artifacts.require("EligibilityChecker");

module.exports = function(deployer) {
    deployer.deploy(EligibilityChecker).then(function() {
        var taxAuthority = web3.eth.accounts[0];
        return deployer.deploy(Welfare, taxAuthority, EligibilityChecker.address);
    });
};
