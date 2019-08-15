module.exports = function(callback) {
    var assert = require('assert');

    var PrivateToken = artifacts.require('PrivateToken');
    var account0 = web3.eth.accounts[0];

    // The proof for buying 5 tokens
    var A = ['0x26d35e2acb600ac05bc3b59baa295e76b79a939cf3f17e55c81e6b1c4f7dff16','0x9621847cd56e4d0967fe257a54239a839c4f0bfef43412fb6bf8c48e8bce664'];
    var A_p = ['0x509bdba5d9a6d012ccde6d9ac7a2e846a052c3cffeb2817b7d8d0337b09b721','0x2c1e3e04e4a19bed921e1191b18c9c19800b77837aba27ff5ee4c2e49fdb8c2'];
    var B = [['0x279bd610e2e5624817256d50e5c41a24c3e71aacd4126669eb5d2a18d5076378','0xc42b8012d34e41c681a62f7400f37a27af9641e2dc96b5b629c657977349b27'],['0x2d111ed2cbe674695a4954f6c2b48e80c32f36f0d383ce78e51695151b6904c2','0x2429dd1d24353bbff7a41fe1bb4a329af4918500b808523968a6f1f733eec717']];
    var B_p = ['0xe7d983f2d8f607e8eeb0b049d9085b3a70d6d867e103aa4a7805b8a254732ee','0x20da7191a1e6921be8684a097663322b6e9720a19fddaddadc7a041d0a5ba17a'];
    var C = ['0x1d7d39dc54440c21b78bd4ff1a5d0458f84696d514d9990136412006b9aeb817','0xc2d00ba0f27cfec1f1bb7a22afd60445283393f0f6d797add7c51108b91e5f7'];
    var C_p = ['0x139a850589200ca29f9bf4c118f5976f91a5439b7aa2c29d6bf8582fb76f0ee','0x26586d9454b19d8beb26b57f063b5c80d88040828ee5bdf56a5e71ed6e9408a6'];
    var H = ['0x27e26e894ed4170b323996d2213914846d25a09a30192434ae2117d90eabdafe','0x2ec0aacce414d7f4e684437580e9d09ab114fbc9389d13baf67a6cb4fdfa4f04'];
    var K = ['0x57ab56662f401037459e90fb846add0098960fe6f89544041d7a843fd950e58','0x2208d63bbbcb781b82fa7e89ee7995e3ab77a71006401f7c54afdf1b09214669'];

    // The initial balance with trivial encryption (+1)
    var initialEncBalance = 1;

    // The updated balanace with trivial encryption (+1)
    var updatedEncBalance = 6;

    PrivateToken.deployed().then(function(instance) {
        assert(instance != undefined);

        var trivialPublicKey = 123; // We don't really use encryption for the proof-of-concept
        var result = instance.register(trivialPublicKey, {from: account0}).then(function(result) {
            console.log("TX succesful: registered", account0, "to participate");

            return instance.buy(
                initialEncBalance,
                updatedEncBalance,
                A,
                A_p,
                B,
                B_p,
                C,
                C_p,
                H,
                K,
                {
                    from: account0,
                    value: 500
                }
            ).then(function(result) {
                console.log("TX succesful: account", account0, "bought 5 tokens");
                return result;
            }, function(err) {
                console.log("TX failed: could not buy any tokens");
            });
        }, function(err) {
            console.log("TX failed: could not register to participate");
        });

        return result;
    });

    callback(); // I don't really understand what the callback is for; apparently you can pass
                // an error message but it did not really work when I tried it
}
