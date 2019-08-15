
n = 0;

function log(contract, name, type, status, gas){
    hexexp = /^0x[0-9a-fA-F]+$/;
    if (hexexp.test(gas)){
        hexgas = gas;
        gas = parseInt(hexgas, 16);
        // console.log("gas:" + hexgas + " -> " + gas);
    }
    json = {
        "contract": contract,
        "name": name,
        "n": n,
        "type": type,
        "status": status,
        "gas": gas
    };
    json = JSON.stringify(json);
    console.log("#" + json);
    n += 1;
}

module.exports = {
    contract_name: null,

    // deploy contract (to be used within migrations)
    deploy: async function(web3, deployer, contract, args, sender) {
        try {
            res = await deployer.deploy(contract,
                ...args,
                { from: sender }  // sets msg.sender
            );
            receipt = await web3.eth.getTransactionReceipt(res.transactionHash);
            log(this.contract_name, res.constructor._json.contractName, "deploy", "OK", receipt.gasUsed);
        } catch(error) {
            console.log(error);
            receipt = await web3.eth.getTransactionReceipt(res.transactionHash);
            log(this.contract_name, res.constructor._json.contractName, "deploy", "ERROR", receipt.gasUsed);
        }
    },
    // transaction (to be used within scenario)
    tx: async function(contract, fname, args, sender) {
        try {
            res = await contract[fname](
                ...args,
                { from: sender }  // sets msg.sender
            );
            log(this.contract_name, fname,  "tx", "OK", res['receipt']['gasUsed']);
        } catch(error) {
            console.log(error);
            log(this.contract_name, fname,  "tx", "ERROR", res['receipt']['gasUsed']);
        }
    },
    // deploy contract and return instance (to be used within scenario)
    deploy_x: async function(web3, contract, args, sender) {
        try {
            instance = await contract.new(
                ...args,
                { from: sender }  // sets msg.sender
            );
            receipt = await web3.eth.getTransactionReceipt(instance.transactionHash);
            log(this.contract_name, instance.constructor._json.contractName, "deploy", "OK", receipt.gasUsed);
            return instance;
        } catch(error) {
            console.log(error);
            receipt = await web3.eth.getTransactionReceipt(instance.transactionHash);
            log(this.contract_name, instance.constructor._json.contractName, "deploy", "ERROR", receipt.gasUsed);
            return undefined;
        }
    }
};
