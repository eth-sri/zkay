pragma solidity ^0.5.0;

contract FuncCalls {
    final address owner;
    uint@owner res;
    uint pubval;

    constructor() public {
        owner = msg.sender;
    }

    // Purely public function with dynamic body
    function recursive(uint val) pure internal returns(uint) {
        return val > 42 ? 0 : recursive(val+1);
    }

    // Purely public function with dynamic body and side effects
    function recursive_se(uint val) internal returns(uint) {
        pubval = pubval + 1;
        return val > 42 ? 0 : recursive_se(val+1);
    }

    // Purely public function with dynamic body side effects and priv args
    function recursive_se_priv(uint@me val) internal returns(uint@me) {
        require(owner == me);
        pubval = pubval + 1;
        res = val;
        return pubval > 42 ? val : recursive_se_priv(val);
    }

    // Function which requires verification and has nested calls with a nested recursive public call
    function pub_with_privcall(uint x) internal {
        pubval = priv1(x * 100);
    }

    // Nested function
    function priv1(uint x) internal returns(uint) {
        require(owner == me);
        pubval = priv2(priv2(recursive(x*2 + pubval)));
        return pubval;
    }

    // Nested function with recursive calls
    function priv2(uint@me x) internal returns (uint) {
        require(owner == me);
        res = recursive(23) + recursive_se(reveal(x, all));
        res = res * res;
        return reveal(res, all);
    }

    // Function usable within private expression
    function priv_inlined(uint@me v1, uint@me v2) pure internal returns (uint@me) { // 5, 84
        return -(v1 * v2 - priv_inlined_nested(v2, v1) * priv_inlined_nested(v1, v2));
    } // 420 - (-3100 * -105168)

    // Nested function within private expression
    function priv_inlined_nested(uint@me v1, uint@me v2) pure internal returns (uint@me) {
        bool larger = reveal(v1 + 42 * v2 > 64, all);
        uint@me sum = v1 + 234 - v2;
        sum = sum - 5 * sum;
        return larger ? v1 * sum : v2 - v1;
        // v1 * ((-4)* (v1 + 234 - v2))
    }

    function priv_return(uint v) pure internal returns(uint@me) {
        return ((v + 5) / 10) * 5;
    }

    function compute(uint@me v, uint v2) public {
        recursive_se(v2);
        pub_with_privcall(v2);
        require(owner == me);
        require(pubval == 0);
        uint@me asdf = priv_return(v2);
        v2 = reveal(asdf, all);
        res = priv_inlined(v2, v + v) - v;
        res += v + recursive(v2);
    }
}
