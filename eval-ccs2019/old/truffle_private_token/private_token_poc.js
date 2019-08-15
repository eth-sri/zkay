// This is meant to be a full-fledge proof-of-concept of how to implement a private token transfer
// leveraging ZoKrates, a toolbox that produces verifier contracts for zero-knowledge proofs
module.exports = function(callback) {
    var assert = require('assert');

    var PrivateToken = artifacts.require('PrivateToken');

    // In this script, money from account0 is transfered to account1
    var account0 = web3.eth.accounts[0];
    var account1 = web3.eth.accounts[1];

    PrivateToken.deployed().then(function(instance) {
        assert(instance != undefined);

        var pkAccount0 = 123; // We don't really use encryption for the proof-of-concept
        var result = instance.register(pkAccount0, {from: account0}).then(function(result) {
            console.log("TX succesful: registered", account0, "to participate; gas used:",
                result['receipt']['gasUsed']);

            var pkAccount1 = 234; // Same as for the above public key
            return instance.register(pkAccount1, {from: account1}).then(function(result) {
                console.log("TX succesful: registered", account1, "to participate; gas used:",
                    result['receipt']['gasUsed']);

                // The initial balance with trivial encryption (+1)
                var encBalanceBeforeBuy = 1;

                // The updated balanace with trivial encryption (+1)
                var encBalanceAfterBuy = 6;

                // The proof for buying 5 tokens
                var A_buy = ['0x26d35e2acb600ac05bc3b59baa295e76b79a939cf3f17e55c81e6b1c4f7dff16',
                    '0x9621847cd56e4d0967fe257a54239a839c4f0bfef43412fb6bf8c48e8bce664'];
                var A_p_buy = ['0x509bdba5d9a6d012ccde6d9ac7a2e846a052c3cffeb2817b7d8d0337b09b721',
                    '0x2c1e3e04e4a19bed921e1191b18c9c19800b77837aba27ff5ee4c2e49fdb8c2'];
                var B_buy = [['0x279bd610e2e5624817256d50e5c41a24c3e71aacd4126669eb5d2a18d5076378',
                    '0xc42b8012d34e41c681a62f7400f37a27af9641e2dc96b5b629c657977349b27'],
                    ['0x2d111ed2cbe674695a4954f6c2b48e80c32f36f0d383ce78e51695151b6904c2',
                    '0x2429dd1d24353bbff7a41fe1bb4a329af4918500b808523968a6f1f733eec717']];
                var B_p_buy = ['0xe7d983f2d8f607e8eeb0b049d9085b3a70d6d867e103aa4a7805b8a254732ee',
                    '0x20da7191a1e6921be8684a097663322b6e9720a19fddaddadc7a041d0a5ba17a'];
                var C_buy = ['0x1d7d39dc54440c21b78bd4ff1a5d0458f84696d514d9990136412006b9aeb817',
                    '0xc2d00ba0f27cfec1f1bb7a22afd60445283393f0f6d797add7c51108b91e5f7'];
                var C_p_buy = ['0x139a850589200ca29f9bf4c118f5976f91a5439b7aa2c29d6bf8582fb76f0ee',
                    '0x26586d9454b19d8beb26b57f063b5c80d88040828ee5bdf56a5e71ed6e9408a6'];
                var H_buy = ['0x27e26e894ed4170b323996d2213914846d25a09a30192434ae2117d90eabdafe',
                    '0x2ec0aacce414d7f4e684437580e9d09ab114fbc9389d13baf67a6cb4fdfa4f04'];
                var K_buy = ['0x57ab56662f401037459e90fb846add0098960fe6f89544041d7a843fd950e58',
                    '0x2208d63bbbcb781b82fa7e89ee7995e3ab77a71006401f7c54afdf1b09214669'];

                return instance.buyTokens(
                    encBalanceBeforeBuy,
                    encBalanceAfterBuy,
                    A_buy,
                    A_p_buy,
                    B_buy,
                    B_p_buy,
                    C_buy,
                    C_p_buy,
                    H_buy,
                    K_buy,
                    {
                        from: account0,
                        value: 500
                    }
                ).then(function(result) {
                        console.log("TX succesful:", account0, "bought 5 tokens; gas used:",
                            result['receipt']['gasUsed']);

                        // The proof for sending 3 tokens
                        var A_send = ['0x1dacc275caf32a37682f00511268aab5f11998f4b90e210994d13b8c31ac3f60',
                            '0x36b43e08eb49b16957b17f97a80318864bff842eae0df87c6511c567c2f0b8c'];
                        var A_p_send = ['0x47d27cb7670ca4ebdc8352084bf9845c3a1fc1ba96a8e5b3f9c7b57d19fcfd',
                            '0x44fc3de771c8d64cccd83624226ca4788b97705183e2cc130c697fbe685f779'];
                        var B_send = [['0x1df6f771c6e09f6c78acd6614462fcbce46f12500afd815dc5709d9e1021f421',
                            '0x18832cf9135370232026a6c1924cfd7c9415bfda0b106df4878a1f631994bae8'],
                            ['0x1787019a354b81956daf5af9ddbda062970b3ca748102575261dc332ed8749f9',
                            '0x10ef3664838276ff65333b44f47d39d481a3e2c07ae2764c8a1220be27e7dccc']];
                        var B_p_send = ['0x252f696b81c9bef17a5d63eb82b1fdcfb7e746b559a6ab808a4e73512fef1cdc',
                            '0xf2241186450f4262f55e26c59d45adf61d59c1030dbf9269480d0b19b933720'];
                        var C_send = ['0x15c52920110b16d2f4936b9dadc5feacb6871222302360d68cab8fc1df51758f',
                            '0x111f497bfd622d174ea169167d0443902155a523220a48c93c03bd05ec970921'];
                        var C_p_send = ['0xfffe3dae147bc73d182e85c3cf9b18130d5bd3a51f046b3ec76e2c11ddb214c',
                            '0xdf20154943bac2c12b870736eb5ba601d09e66e3bb9383803cab3ecbda2b9c7'];
                        var H_send = ['0x2ea22457c7140ecdf48137d4ed8bf0b27b3b349286a9e2bca07829aee10644e8',
                            '0x86fa62cef59522aa5e7b88dbb38dbbca1746c1810b9389b7007c92e0d62ebf0'];
                        var K_send = ['0x6dd76405d0b3c40bfe498a2df4ef0235ac65c1f9cb4795a49e1a57380edb9dc',
                            '0x194939f2478c3eb79022e1d0d09e5075107e547e672455241a502fc3186da651'];

                        return instance.depositProof(
                            1, // 1 indicates that is a proof for sending tokens
                            A_send,
                            A_p_send,
                            B_send,
                            B_p_send,
                            C_send,
                            C_p_send,
                            H_send,
                            K_send,
                            {
                                from: account0
                            }
                        ).then(function(result) {
                            console.log("TX succesful:", account0,
                                "deposited proof for sending tokens; gas used:",
                                result['receipt']['gasUsed']);

                            var encBalanceBeforeSend = encBalanceAfterBuy;
                            var encAmountToSend = 4
                            var encBalanceAfterSend = encBalanceBeforeSend - encAmountToSend + 1;

                            return instance.sendTokens(
                                account1, // tokens are send to account1
                                encBalanceBeforeSend,
                                encBalanceAfterSend,
                                encAmountToSend,
                                {
                                    from: account0
                                }
                            ).then(function(result) {
                                console.log("TX succesful: sent", encAmountToSend - 1,
                                    "tokens from", account0, "to", account1 + "; gas used:",
                                    result['receipt']['gasUsed']);

                                // The proof for recieving 3 tokens
                                var A_recv = ['0x7755195507b39c3a39d183f8130efafc42adc4a5f9f8ebcf3ee337e5ee89e56',
                                    '0x1913d749bc175c0477048328074d18b4650c038052e3c9e6de77f4ab138401e2'];
                                var A_p_recv = ['0x17ae04af320349f6ff87744914b4482ba07ca97dcd6e10883c3bec971149a1f5',
                                    '0x1cbc9bc178ebebf63e32b3c8674ea1d0f370483cb799df44bb78cc9d26df2fb5'];
                                var B_recv = [['0x251d5deaa111b4dffb9dcf95d6dc106634bc87b6cee641c09d56ddb5db2ddf59',
                                    '0x1800b30ae659487eb5ac90afbe855ab48ef31f7c802d53e2d457c1f79603c20d'],
                                    ['0xf2045fb0cf691966f55367dd1a2ae1c58b0b2145c4ebaa900ee3fd17a52aea8',
                                    '0x16328e19d6fd9271e46f26805eb21c080d17dbf27532f2757a93fbd49b74163b']];
                                var B_p_recv = ['0x52fddf1c0600ad78a633fba4906807329a5792664e3abdd08f0bedccec4c77c',
                                    '0x2add69252b72f8c9db20ff0b57062f6e3d708eccba9895b4f8b2c971cda0438f'];
                                var C_recv = ['0x2b4250ae1eee4c0c92d9ac911f533c622b1c7ca908c8e956a0535a9c78327d30',
                                    '0x2c6b3a330a40d0b7fa6da823e292dea161f30b5512039a88b5375d3115329299'];
                                var C_p_recv = ['0x267854bdeb457b9d261fb27ded5cef28dc870541b5a1aafc00ae29ec2ca12030',
                                    '0x1fc8c873e7ab79cae99d38a708663d406d268e19d96f3446ea2b654e21d3fc4c'];
                                var H_recv = ['0x130fc5a602398f88da943690b4b04184687088691d0f0974a01d0b0db2cc3f96',
                                    '0x32db74cca10423b40f488a973a2466e151ba16838c509ba3cf0027eb21722f4'];
                                var K_recv = ['0x1126d123f1c62fa75d0060d274fe14a8ba4112f9e5be61043c899a9565ca313f',
                                    '0x17ae2d270d378b83f59e5a9e5c01d10d00e40886c2b1b7d28e5a8252a109cefd'];

                                return instance.depositProof(
                                    2, // 2 indicates that it is a proof for receiving tokens
                                    A_recv,
                                    A_p_recv,
                                    B_recv,
                                    B_p_recv,
                                    C_recv,
                                    C_p_recv,
                                    H_recv,
                                    K_recv,
                                    {
                                        from: account1
                                    }
                                ).then(function(result) {
                                    console.log("TX succesful:", account1,
                                        "deposited proof for receiving tokens; gas used:",
                                        result['receipt']['gasUsed']);

                                    var encBalanceBeforeReceive = 1;
                                    var encBalanceAfterReceive = 4;

                                    return instance.receiveTokens(
                                        account0,
                                        encBalanceBeforeReceive,
                                        encBalanceAfterReceive,
                                        {
                                            from: account1
                                        }
                                    ).then(function(result) {
                                        console.log("TX succesful: account", account1, "received",
                                            encAmountToSend - 1, "tokens; gas used:",
                                            result['receipt']['gasUsed']);
                                    }, function(err) {
                                        console.log("TX failed: could not receive the tokens");
                                        console.log(err);
                                    });
                                }, function(err) {
                                    console.log("TX failed: could not deposited proof for receiving tokens");
                                    console.log(err);
                                });
                            }, function(err) {
                                console.log("TX failed: could not send tokens from", account0, "to", account1);
                                console.log(err);
                            })
                        }, function(err) {
                            console.log("TX failed: could not deposit proof for sending tokens");
                            console.log(err);
                        });
                    }, function(err) {
                        console.log("TX failed:", account0, "could not buy 5 tokens");
                        console.log(err);
                    });
            }, function(err) {
                console.log("TX failed: could not register", account1, "to participate");
                console.log(err);
            });
        }, function(err) {
            console.log("TX failed: could not register", account0, "to participate");
            console.log(err);
        });
    }, function(err) {
        console.log("There is no PrivateToken contract deployed on the network")
    });

    callback(); // I don't really understand what the callback is for; apparently you can pass
                // an error message but it did not really work when I tried it
}
