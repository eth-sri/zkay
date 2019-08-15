module.exports = function(callback) {
    var Verifier = artifacts.require('Verifier');
    var account0 = web3.eth.accounts[0];

    var A = ['0x10566ead864a6ae4da875839d33fd1c833aa2b70647605a37deb91854be8ee90',
        '0x2defb52ea206e78f4f518cb046eb9764a5033a000f28cc52916e691ab7106e2d']
    var A_p = ['0x256ad7d46b742d8f58755c766f4be18f2682bef542c26ca58c38843d9bd19c19',
        '0x2e6a99ee6b26c4b41414c64b8b11c310f9c44606574a27f999c2e84cd71ccef4']
    var B = [['0x18505d198a64c3d6355ef320a0952addc6f78aeb3b0c2470547b435c0680000',
        '0xed92eb13f558753ca32fb74278d1d492b1e487e65f2a16cff63a8a1c2f8180'],
        ['0x2687e9c9c1dd6c9b494f1fe95914ecbc0ea2cd09ccbc040d3147025807dc2385',
        '0x12e12324d6f912e45c59469f28901e81e51ca8ec57f6eca2f7ed1792ad64cfe4']]
    var B_p = ['0x28ce46eaa2ed43e3554987222482f783284c3b18499d281864fbb10b8334e74f', 
        '0x2899708b4c655a331afebd59ed65f8883ff1fdc36cfa232a40ee14939a7e868b']
    var C = ['0x8868c428757e170ce5da22381bca87382dbab5f3a8a87e08b32cfb9e11228f0',
        '0xda0b8dd3c5296a486b43a6365caac115e585a035253af16032cf120ec19b35']
    var C_p = ['0x2ed4e1f35daf9e13b79c6df3c38506f0c65d0d78c2d60c4ac939b5a7af95bc7b',
        '0xd25e55e73a5cf71f238dcbb5191f32b5c0ae6b1019e14844fb5b31f120b581f']
    var H = ['0xaad035c7dda1134514df880a962031abfd75f0f59a4df19575f9c3b85f05b22', 
        '0x1be0e7c933f5e6c91f64eca57e183b9313f6b13f83071e0fc138c66dde5b57eb']
    var K = ['0xf7a4531c8ce8c38285237983fd5c7040c5f65a4ffbd503baa24ce38addce560', 
        '0xd9c2dcce476ae684574f40c90d57fe8c09c5fa2347f03f3d06ceb467727beb0']

    var output = ['9']
    

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
            output,
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

