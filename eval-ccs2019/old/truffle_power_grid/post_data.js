module.exports = function(callback) {
    var assert = require('assert');

    var PowerGrid = artifacts.require('PowerGrid');
    var account0 = web3.eth.accounts[0];

    // The proof for the aggreated power consumption of 7 days
    var A = ['0x1c5c0d8929065ad6a36164647e4ce21893cdfea98eeabff855b2a82b448e0f1e','0x10204e30abbcb3e0a0db10c6c397704cdd8c964e8584a171102c4103efcb74ef'];
    var A_p = ['0x55098a921c465c6d6caed2efa2afe874debd81f8907830f323c37749d0ef76b','0x9430cbcc397de70e70d0108228563a2c09e290fdbc05d5653802b20a4e61f38'];
    var B = [['0x9d7adf162cd1a7f7d20c718c3830effc6c9e25b6e8f153607de6fc0ae2a39e8','0x15db2aeca24789a297f396dd78e36472b285e0d1df26d0786bff6c4a0f3797f5'],['0xeb67fd237d73b832b3cdd4974eff371234c8b7f1d3f5b8ae60237dbbba976f3','0xb13a23e39965999ad8646cccdaa746c0ccfdfad05fa653f8f5919875954972e']];
    var B_p = ['0x142f5c5b3b8a2c149de8cde7857576da2deb869cbb81877b8f4c8b023b7f6aee','0x7bdc4f9e539f8c6056d18c1ef39e43d56a34e4ea9589936de605b95ded778d3'];
    var C = ['0x41670d143f7a605ad54aa2e1d9a9bcc4a9fd8d23f281c34226bf73450657751','0x5df3fc2cbe1040f47005d201dc13c33cae3d18053b8fbe1750bcb8cee4b3051'];
    var C_p = ['0xd362507a131e48d7cb8d22edf2bfb155efa52a7bd6dff5e5dbb122c0a25237e','0x255b9057cfe2ffc0f1ee7a76382a9364460325e5b79ad8353483ed7277985699'];
    var H = ['0x28de695deed3bd213015f38eb5afb208259e49a24a584cafbc3e7d232d96a33f','0x2c0a57f2eca796cc4c3aafcb6d3e910e7ce8da21b92656120dc2f11c5204147'];
    var K = ['0x29cdad9d9add408bd44d80f1982c7565f8d693634f2aaaf9e5dd6ddab0b13164','0x5b611c788be810362ebd29400f20d7a253f323166b82d857c455bf6f6c93f27'];

    // The aggreated power consumption and the specific time interval
    var aggregatePowerConsumption = 28;
    var startTime = 1;
    var endTime = 7;


    PowerGrid.deployed().then(function(instance) {
        assert(instance != undefined);
        var result = instance.postData(
            startTime,
            endTime,
            aggregatePowerConsumption,
            A,
            A_p,
            B,
            B_p,
            C,
            C_p,
            H,
            K,
            {
                from: account0
            }
        ).then(function(result) {
            console.log("Data posted with ", account0);
            console.log(result);
            return instance.callData(
                account0,
                {
                    from: account0
                }
            )
        });
    });

    callback(); // I don't really understand what the callback is for; apparently you can pass
                // an error message but it did not really work when I tried it
}
