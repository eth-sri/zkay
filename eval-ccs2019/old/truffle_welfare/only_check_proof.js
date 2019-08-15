module.exports = function(callback) {
    var assert = require('assert');

    var EligibilityChecker = artifacts.require('EligibilityChecker');
    var account0 = web3.eth.accounts[0];

    var A = ['0x71fbc9cd39c044fb507b3425ff7b06074f2d4e8ff1e2d9706c890f6136bf9af',
        '0x222a34fc262f729331970ffaa4e3d97c2c931c5624646eef9b1a62542ddd7708'];
    var A_p = ['0x2304542c1b45c9bbdcd2cd6f8f82845d4f449833f16221fd0a76fcd1dd061c7e',
        '0x2284ad057a79c03ff6b8253251b0d3aafe55ec5559305fdfe7da1f051c3e5aba'];
    var B = [['0x30f02e5718104cb43eb8cfc7e5fc351a20d2f5eda78ba4b3560b26b08014ebd',
        '0xd986485ce1e99c4f523a6c73b792f4ad3d51d491527341404a3f35723467b07'],
        ['0x6e296c87dba3a4ae8b94d460c46d0b495f25f3b7782032081bde59113b76d47',
        '0xfb8ed3af99b50355b7dcd8a5ba00de8a5e3ff7ef4135ca18d691811f5f12b8b']];
    var B_p = ['0xff64d9716729826e3725b6d2eda63c22c318f04881c561f9d698cdb311620ce',
    '0x1eecd4cbcbd12e5498c5064d8a887adfba1081a7363bdf6c1e67ccd84111df54'];
    var C = ['0x1700a87f375479ebfa7abf0750f6ac3d811db4136f586f3fe8d7a4455053af41',
    '0x482c92b77abc4b13c2df40c79f7b0e146760218b8e13bab2280abd7d137109'];
    var C_p = ['0x1a4cbca5e4995d915a595a8fa92e93eba3ffe9cca56b21a556f25922b091b4bd',
        '0x2fe580206cfa1fae78de5c021de732e5e4f94f7cdc34be8a813f79430c65c2c4'];
    var H = ['0x128f9c4d34b08f0ba9dc92981e405dfd45f86ae491390749269eb13b0758a905',
        '0x23b2766c5d19a70b2a4c3bd79c5de2a13f28cfc5f0b7e2f570ce4a4754ef0784'];
    var K = ['0xd9f9802e488fe2063e84740da88fdbae8caa388c63d88ce812af25c35bdbb70',
        '0x183c1deb1edb7da925144ce07d9bdd8fc63a5601363b406b6bdaab22f6172f7'];
    var publicInput = ['46123','1']; // first argument is the "hashed tax return"

    EligibilityChecker.deployed().then(function(instance) {
        assert(instance != undefined);
        //console.log(contract);

        instance.verifyTx(
            A,
            A_p,
            B,
            B_p,
            C,
            C_p,
            H,
            K,
            publicInput,
            {
                from: account0
            }
        ).then(function(result) {
            console.log("Success")
            console.log(result);
        }, function(e) {
            console.log("Error: ", e);
        });
    });

    callback(); // I don't really understand what the callback is for; apparently you can pass
                // an error message but it did not really work when I tried it
}
