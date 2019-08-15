pragma solidity ^0.4.25;

import './Verifier.sol';

contract Test {
    Verifier verifier;

    constructor (address _verifier) public {
        verifier = Verifier(_verifier);
    }
    
    function f(
        uint[18] proof1,
        uint[18] proof2,
        uint[18] proof3,
        uint[18] proof4
    ) public returns (bool) {
        
        uint[2] memory publicInput = [uint(113569), uint(1)];
        
        bool result1 = verifier.verifyTx(proof1, publicInput);
        require(result1);
        
        bool result2 = verifier.verifyTx(proof2, publicInput);
        require(result2);
        
        bool result3 = verifier.verifyTx(proof3, publicInput);
        require(result3);
        
        bool result4 = verifier.verifyTx(proof4, publicInput);
        require(result4);
        
        return result1 && result2 && result3 && result4;
    }
}
