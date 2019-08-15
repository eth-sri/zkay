module.exports = function(callback) {
    var Verifier = artifacts.require('Verifier');
    var account0 = web3.eth.accounts[0];

    A = ['0x1ad8888970687b529055471780a8a79bf27a3b96d9b6cf943bec107726aba84a',
        '0x297664e46874c4dd74586a6fbe7a1efcde88669e4ba616942618c9fffaf77865']
    A_p = ['0x19e958110276b0c3e8b50e57192574e6d1599c58b701f8daa85a40e9e1fa3854', 
        '0x560b7c451e5120377d48f993ef48bef9c71622659bfc2782ee9bee808623ed2']
    B = [['0x10d800134071b52fa1e8dfe7d5004d9db2525e3ad02a36690603d0235d3284e8', 
        '0x2dd0d519c530f57eb54898153002fb56dd901872ab04152d3490501d308406b6'],
        ['0x13ddd15c2d07b6b9ae0106e09850549fc552be2326174754b2c588a08b42a606', 
        '0x134f041ecbef2d8e83acb452a5ca4daf37b2a0b62cedc9d7d77e547d538f7747']]
    B_p = ['0x25aea499dde54e012950b675dd6f09d90eb0d76d1b26974b35c8481caed95ed1', 
        '0x861d2cf87cfad286389bd322581586f31dab708bf1b1b97d087dcfb3d5adc4a']
    C = ['0x738ab2ec0a36685a8e078fb006177381747af2d4d74e40827f764c2a4011b4b', 
        '0x1542890640e306d86762f5719acaf22caf514aeebd52045249ee8ea42e3b7e2']
    C_p = ['0x25e4d9f8e2bd1bdc36a549b145446b4af7c91d6a52523bc66e406ebb3ca4c4d6', 
        '0x19df23985a88372f6a4189f11454e9c27259f80037efbc2e507f4621408f1f78']
    H = ['0x25e6af4038f31fa79670d61386f52b179ad68ccd584408dabec328e46f01258d', 
        '0x12e0d3151ca86957a57041399688ba0ddf2118647eac00ac78cc94bc15a73864']
    K = ['0xc5d973c25d18ab4a6f512dea1eb385bdbc85518f8d59353b1e3594ec525eb61', 
        '0x86ce3e7ab05312e14885732b9f66b5f98edee2db81088e1fce1c8ef8da0c64c']

    var publicInput = ['321', '123', '75']
    
    Verifier.deployed().then(function(instance) {
        instance.verifyTx.call(
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
            console.log("Yes!");
            console.log(result);
        }, function(err) {
            console.log("No!");
            console.log(err);
        });
    });
}

