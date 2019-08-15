pragma solidity ^0.5.0;

contract PrivateRequire {
    mapping(address!x => uint@x) bets;

    function f() public {
        require(bets[me] == 10);   // should throw type error
    }
}
