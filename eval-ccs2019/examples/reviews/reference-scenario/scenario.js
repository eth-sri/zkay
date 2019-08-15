var helpers = require('./helpers.js');

module.exports = async function(callback) {
    // gives 10 example accounts
    let accounts = await web3.eth.getAccounts();
    
    // remember accounts
    r1 = accounts[0];
    r2 = accounts[1];
    r3 = accounts[2];
    pc = accounts[3];
    author = accounts[4];
    
    // get hold of the deployed PKI
    var pki = artifacts.require("PublicKeyInfrastructure");
    let pki_instance = await pki.deployed();
    
    // announce public keys
    await helpers.tx(pki_instance, "announcePk", [10], pc);
    await helpers.tx(pki_instance, "announcePk", [100], author);
    await helpers.tx(pki_instance, "announcePk", [20], r1);
    await helpers.tx(pki_instance, "announcePk", [30], r2);
    await helpers.tx(pki_instance, "announcePk", [40], r3);
    
    // load the deployed verifiers
    var verify_registerPaper = artifacts.require("Verify_registerPaper");
    let verify_registerPaper_instance = await verify_registerPaper.deployed();

    var verify_recordReview = artifacts.require("Verify_recordReview");
    let verify_recordReview_instance = await verify_recordReview.deployed();
    
    var verify_decideAcceptance = artifacts.require("Verify_decideAcceptance");
    let verify_decideAcceptance_instance = await verify_decideAcceptance.deployed();
    
    // create the contract
    var contract = artifacts.require("Reviews");
    let contract_instance = await helpers.deploy_x(web3, contract, [r1, r2, r3, pki_instance.address, verify_registerPaper_instance.address, verify_recordReview_instance.address, verify_decideAcceptance_instance.address], pc);

    args = [1334, ['0x199059f62797c622254b6b9cb914f1813cec435e1b718d20d63b8adef9cb3315', '0x2fe71de7ec153b8852869ac9d23520f2935830a3375a01fb6955047b68bc648d', '0x2b69f59203315192756144d6d104ac2f13c20c8037f7a9426aecc107d2eb9b0f', '0x29cba7a2f4c4c186da09adf68b36b50d383b01bedafcd842a684277d223d9045', '0x2e1bab6f4ea47aef607faacb56987f2ccb453778778d883ed2238316d0465d4a', '0x016f5a2233b004d36a3076d062af848d3f564223dbdfc0c00bcecf4fff2d1f26', '0x10b29bde099cd8ebafd67bbc62588b61e4e87da88bd9369a9cd1e8f7cad142e5', '0x1813507e817cb4015629f39ae4b8cb2f39215d894e0edfe9a9d9dcae31f9bf8a'], [1244]];
    await helpers.tx(contract_instance, "registerPaper", args, author);
    
    args = [1234, 24, ['0x0633d8dbb5748d61b42aacff1d02ccdf57360fc0fa0126a9c5548501b9a931a0', '0x0b9a2807bdbb8b4aa03a06405fbf4393d01755001c19ad48c039d2740217d713', '0x15ac5273af97be460bc7c8b0a11b4516b5425ffbe8ad9e5dc3bb639f0a8edd65', '0x13ee8c9489cf95a84585cccce020950a5b79edabcb1103964f879ec2fe763642', '0x29ea712b4357c057bcce74c58f53fefd37ff1dc0fcedf47297f83adf9e972c1f', '0x0556a3d911da5f4d51ef3adff841634e878f4ad1a0769de12c7670cb5d6965df', '0x14d5796993e478497961694221b9fac587a1eb19948a69cc1649f34785298b9e', '0x0bbc9eb1ed13252f9b906aaba5f857df40f9b4546d3dd013fa1fc680d314ada2'], [14]];
    await helpers.tx(contract_instance, "recordReview", args, r1);
    
    args = [1234, 32, ['0x177aa945677056f5849e6c73c0b1519c860fa8898928dbee2210648bd31735d7', '0x00acfe8d56ae0d511478f8a6c7c74e710b3906b71053e52d0972ce4c010b98b8', '0x07316bd9c9f93f78862c6216d9cd7fab13b34d9b4a35bd3cb7fdc428f4d6dae9', '0x17282238bf4816e89100a3bfc0196f46e2399cdb17e0ad3c62091fdc73396ee6', '0x09cd96b5bd036a414396365d7e8bffe40277471681f7fc41ac2a38e0e8796b93', '0x1dfc10a0a807ef986f81bee4a695fcbfc6d0dc59c1d3bd4c263236ea21a41d2d', '0x265351a2a52ce6b5c16c44a28ee2bfdabe2073a76619ea032a2c0fef45594262', '0x0d15f5d05b5eb64ce98b8f66dfb4276104f56b9ca639243608d522600d94dbe5'], [12]];
    await helpers.tx(contract_instance, "recordReview", args, r2);
    
    args = [1234, 41, ['0x0108f3553090b59c07db5bda89fe911a14f9091c7dd7f5741ab572048c81e433', '0x1b40cbb8c3ae8e5f08cc97a405f21855d2042e0b91b9d5b52208cb0295d881f6', '0x0c79151ba7ad8eca47e0f9bc256a93d859a07717022cce2f441f3f0da45f0d0e', '0x1cb8ba4b5f7abf3c7f937e818ad41112eb05ae2d5bea3f55df691e4256b7e1eb', '0x2dac1c359d4262f312c7b325f1d18e1633e4b68af06cca91a2c4077aaaf60c88', '0x1b84930ac3f0b269038f41f1500f4c85fbd80e0bdbd6a4eac4f5ed555de05bbd', '0x03b00b40ce96c1bdd234531c9f19c41ef78c2243196a931304762bb7db7670cb', '0x27fc91065ce1471e0041e9bef6adeb7d9d3730a57059f37bb89c5b763a63b78c'], [11]];
    await helpers.tx(contract_instance, "recordReview", args, r3);
    
    args = [author, ['0x264befbb600cfcb6f68da5e5a87df2aa4b6c20fc9a125124360a432f47cc57b6', '0x2350ef97e6aa00e624d9cae7eda78da30eda7a87239c6a241e0d3102dc3da5c0', '0x2cfd6a8e78fa1e1869cf37d358f0d476547c60af1c600d25e35efc1c30028031', '0x05e2d2318f18dd4c4836cd260cdc4cb41fabb2ee4c148acac2790b9ca7006ca4', '0x0616fcf3dfea174ae46f7147146de01b8c2f1c90e0df3f0a3c8b8eb1b67563fc', '0x2c687cb75913940dabce333c07d05eab8db69913d9689f5f06b4cc0860081f54', '0x08c853581848bd922909f697b89b0cab9d0819161243de76da00c73931ae1d9e', '0x221b4bfdeac3cf485385ad29eb6b3399fc96f825d68fa98ecda72c087eda2740'], [1234, 10, 17, 101]];
    await helpers.tx(contract_instance, "decideAcceptance", args, pc);
    
    console.log(">> end of scenario")
}
