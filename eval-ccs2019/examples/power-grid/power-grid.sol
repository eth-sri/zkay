pragma solidity ^0.5.0;

// Description: Track consumed energy 
// Domain: Energy
contract PowerGrid {
    final address master;
    mapping (address!x => uint@x) consumed;
    mapping (address => uint@master) total;

    constructor() public {
        master = me;
    }

    function init() public {
        consumed[me] = 0;
    }

    function register_consumed(uint@me amount) public {
        consumed[me] = consumed[me] + amount;
    }

    function declare_total() public {
        total[me] = reveal(consumed[me], master);
    }
}