var PowerGrid = artifacts.require("PowerGrid");
var DataVerifier = artifacts.require("DataVerifier");

module.exports = function(deployer) {
    deployer.deploy(DataVerifier).then(function() {
        return deployer.deploy(PowerGrid, DataVerifier.address);
    });
};
