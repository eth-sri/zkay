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

    // Private function used in private expression
    function some_comp_priv(uint@me v1, uint@me v2) pure internal returns (uint@me) {
        return v1 + v2 - some_comp_priv2(v1);
    }

    // Private function used in private expression
    function some_comp_priv2(uint@me v1) pure internal returns (uint@me) {
        return v1 * 3;
    }

    // Private function used in private expression
    function some_comp(uint@me v1, uint@me v2) pure internal returns (uint@me) {
        uint x = some_comp_pub(1, 2);
        return v1 + v2 + x;
    }

    // Mixed function with static body
    function some_comp_pub(uint@me v1, uint@me v2) pure public returns (uint) {
        uint x = recursive(42) + some_comp_pub2(v1, v2);
        return reveal(v1 + v2, all) + x;
    }

    function some_comp_pub2(uint@me v1, uint@me v2) pure public returns (uint) {
        //uint@me hans = some_comp(v1, v2);
        uint x = recursive(42);
        return reveal(v1 + v2, all);
    }

    function priv_inc2(uint@me val) internal pure returns(uint@me) {
        return val + 1;
    }

    function priv_inc(uint@me val) public pure returns(uint@me) {
        return val + priv_inc2(42 * val);
    }

    function get_res() public view returns(uint@owner) {
        return res;
    }

    function getself(uint@me self) public returns(uint) {
        return reveal(self, all);
    }

    function getself2(uint self) public returns(uint) {
        return self;
    }

    function getself3(uint@me self) public returns(uint@me) {
        return self;
    }

    function calc(uint@me v) public {
        require(owner == me);
        res = priv_inc(v) + 1 + get_res();
        uint test = recursive(23) + getself(v) + some_comp_pub(getself3(v), getself3(v)) + getself(42);
        uint@me asdf = getself(2);
        asdf = getself(getself2(53)) + 1;
        res = v + some_comp_priv(v, v) + pure_pub_func(2); // 42 + (42 + 42 - 3 * 42) + 44 = 44 -> enc(44) = 86
        update_pubval();
        pubval = some_comp_pub(pubval, res);
    }
}
