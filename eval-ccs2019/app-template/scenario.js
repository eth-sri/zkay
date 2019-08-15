var helpers = require('./helpers.js');

module.exports = async function(callback) {
    // gives 10 example accounts
    let accounts = await web3.eth.getAccounts();
    
    // set contract name
    // EXAMPLE:
    // helpers.contract_name = "Reviews"
$CONTRACT_NAME

    // remember accounts
    // EXAMPLE: r1 = accounts[0];
$ACCOUNTS
    
    // get hold of the contract and the deployed instance
    var pki = artifacts.require("PublicKeyInfrastructure");
    let genPublicKeyInfrastructure = await pki.deployed();

    // fetch contract
    // EXAMPLE:
    // var contract = artifacts.require("Reviews");
    $CONTRACT_FETCH

    // announce public keys
    // EXAMPLE: await helpers.tx(genPublicKeyInfrastructure, "announcePk", [10], pc);
$PK_ANNOUNCE

    // load the deployed verifiers
    // EXAMPLE: var verify_registerPaper = artifacts.require("Verify_registerPaper");
$VERIFIERS_FETCH
    // EXAMPLE: let verify_registerPaper_instance = await verify_registerPaper.deployed();
$VERIFIERS_WAIT

    // deploy contract
    // EXAMPLE:
    // let contract_instance = await helpers.deploy_x(web3, contract, [r1, r2, r3, pki_instance.address, verify_registerPaper_instance.address, verify_recordReview_instance.address, verify_decideAcceptance_instance.address], pc);
$CONTRACT_DEPLOY

    // run transactions
    // EXAMPLE:
    // args = [1334, ['0x199059f62797c622254b6b9cb914f1813cec435e1b718d20d63b8adef9cb3315', '0x2fe71de7ec153b8852869ac9d23520f2935830a3375a01fb6955047b68bc648d', '0x2b69f59203315192756144d6d104ac2f13c20c8037f7a9426aecc107d2eb9b0f', '0x29cba7a2f4c4c186da09adf68b36b50d383b01bedafcd842a684277d223d9045', '0x2e1bab6f4ea47aef607faacb56987f2ccb453778778d883ed2238316d0465d4a', '0x016f5a2233b004d36a3076d062af848d3f564223dbdfc0c00bcecf4fff2d1f26', '0x10b29bde099cd8ebafd67bbc62588b61e4e87da88bd9369a9cd1e8f7cad142e5', '0x1813507e817cb4015629f39ae4b8cb2f39215d894e0edfe9a9d9dcae31f9bf8a'], [1244]];
    // await helpers.tx(contract_instance, "registerPaper", args, author);
$TRANSACTIONS
    
    console.log(">> end of scenario")
}
