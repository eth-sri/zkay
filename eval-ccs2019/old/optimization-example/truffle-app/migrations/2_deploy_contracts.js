var Test = artifacts.require("Test");
var Verifier = artifacts.require("Verifier");

module.exports = function(deployer) {
    deployer.deploy(Verifier).then(function() {
        return deployer.deploy(Test, Verifier.address);
    });
};
