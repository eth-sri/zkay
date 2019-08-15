pragma solidity ^0.5.0;

// Description: Track and audit cash receipts
// Domain: Retail
contract Receipts {
    final address business;
    mapping(uint => uint@business) in_receipts;
    mapping(uint => uint@business) out_receipts;
    uint@business income;

    constructor() public {
        business = me;
        income = 0;
    }

    function give_receipt(uint id, uint@me amount) public {
        require(business == me);
        out_receipts[id] = amount;
        income = income + amount;
    }

    function receive_receipt(uint id, uint@me amount) public {
        in_receipts[id] = reveal(amount, business);
    }

    function check(uint id) public {
        require(business == me);
        require(reveal(in_receipts[id] == out_receipts[id], all));
    }
}