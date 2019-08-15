var privateToken = artifacts.require("PrivateToken");
var buyVerification = artifacts.require("BuyVerification");
var sendVerification = artifacts.require("SendVerification");
var receiveVerification = artifacts.require("ReceiveVerification");

module.exports = function(deployer) {
  deployer.deploy(buyVerification).then(function() {
    return deployer.deploy(sendVerification).then(function() {
      return deployer.deploy(receiveVerification).then(function() {
        return deployer.deploy(privateToken, buyVerification.address, sendVerification.address, receiveVerification.address);
      });
    });
  });
};
