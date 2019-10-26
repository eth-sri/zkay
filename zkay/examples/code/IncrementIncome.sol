pragma solidity ^0.5.0;

contract IncrementIncome {

    final address business;
    uint@business income;

    constructor() public{
        business = me;
    }

    function f(uint@me amount) public {
        require(business == me);
        income = income + amount;   // this increment is private and should be transformed
    }

}
