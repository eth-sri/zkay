pragma solidity ^0.5.0;

contract funccall {
    final address owner;
    uint@owner res;
    uint pubval;

    constructor() public {
        owner = msg.sender;
    }

    // Purely public function with side effects (not allowed inside circuit)
    function update_pubval() public returns(uint) {
        pubval = pubval + 1;
        return 1;
    }

    // Purely public function with static body
    function pure_pub_func(uint val) pure public returns(uint) {
        return val + 42;
    }

    // Purely public function with dynamic body
    function recursive(uint val) pure public returns(uint) {
        return val > 42 ? 0 : recursive(val+1);
    }

    // Illegal recursive function which would require verification
    /*function recursivePriv(uint@me val) pure public returns(uint) {
        return reveal(val > 42 ? 0 : recursive(reveal(val, all) + 1), all);
    }*/

    // Private function used in private expression (inlined)
    function some_comp(uint@me v1, uint@me v2) pure internal returns (uint@me) {
        uint x = some_comp_pub(1, 2);
        return v1 + v2 + x;
    }

    // Mixed function with static body
    function some_comp_pub(uint@me v1, uint@me v2) pure public returns (uint) {
        uint x = recursive(42) + some_comp_pub2(v1, v2);
        return reveal(v1 + v2, all);
    }

    function some_comp_pub2(uint@me v1, uint@me v2) pure public returns (uint) {
        //uint@me hans = some_comp(v1, v2);
        uint x = recursive(42);
        return reveal(v1 + v2, all);
    }

    function priv_inc(uint@me val) public pure returns(uint@me) {
        return val + 1;
    }

    function calc(uint@me v) public {
        require(owner == me);
        pubval = 0;
        uint test = recursive(23) + some_comp_pub(v, v);
        res = priv_inc(v) + 1;
        //res = v + some_comp(v, v) + pure_pub_func(2);
        //update_pubval(); problem, alias analysis forgets that me == owner
        //pubval = some_comp_pub(pubval, res); will not work for non-purely public functions
    }
}
