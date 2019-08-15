pragma solidity ^0.4.21; // I don't know why 0.4.23 does not work for me
pragma experimental ABIEncoderV2;

/* contract DataVerifier {
    function verifyTx(uint[2], uint[2], uint[2][2], uint[2], uint[2], uint[2], uint[2], uint[2], uint[4])
        public returns (bool) {}
} */

contract Verifier {
    function verifyTx(
            uint[2] A,
            uint[2] A_p,
            uint[2][2] B,
            uint[2] B_p,
            uint[2] C,
            uint[2] C_p,
            uint[2] H,
            uint[2] K,
            uint[4] input
        ) public returns (bool) {}
}

contract PowerGrid {
    struct ConsumerData {
        uint _startTime;
        uint _endTime;
        uint _aggregatePowerConsumption;
    }

    mapping(address => ConsumerData) powerConsumption;

    Verifier public dataVerifier_;

    function PowerGrid(address _dataVerifier) public {
        dataVerifier_ = Verifier(_dataVerifier);
    }

    function postData(
        uint _startTime,
        uint _endTime,
        uint _aggregatePowerConsumption,
        uint[2] A,
        uint[2] A_p,
        uint[2][2] B,
        uint[2] B_p,
        uint[2] C,
        uint[2] C_p,
        uint[2] H,
        uint[2] K) public returns (bool)
    {
        uint[4] memory publicInput = [_startTime, _endTime, _aggregatePowerConsumption, 1];
        bool result = dataVerifier_.verifyTx(A, A_p, B, B_p, C, C_p, H, K, publicInput);
        if (!result) {
            return false;
        }
        powerConsumption[msg.sender] = ConsumerData(_startTime, _endTime, _aggregatePowerConsumption);
        return true;
    }

    function callData(address _from) public view returns (uint) {
        return powerConsumption[_from]._aggregatePowerConsumption;
    }
}
