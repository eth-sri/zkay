pragma solidity ^0.4.21; // I don't know why 0.4.23 does not work for me

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

    function verifyTx(
            uint[2] A,
            uint[2] A_p,
            uint[2][2] B,
            uint[2] B_p,
            uint[2] C,
            uint[2] C_p,
            uint[2] H,
            uint[2] K,
            uint[5] input
        ) public returns (bool) {}
}

/* A token contract that is ready to leverage ZoKrates to provide privacy for transactions */
contract PrivateToken {
    struct Pending {
        bool collectable;
        uint amountEnc;
    }

    // balances[user] := with the user's public key encrypted balance
    mapping(address => uint) public balances;
    // pending[receiver][sender] := with the receiver's public key encrypted amount of tokens
    mapping(address => mapping(address => Pending)) public  pending;
    // collection of public keys
    mapping(address => uint) public publicKeys;
    // indicated whether a user is registered
    mapping(address => bool) public isRegistered;

    // visible to anyone
    uint256 public totalSupply;

    uint public tokenPrice = 100; // wei / tokenPrice = # tokens

    // Verifier public initVerification --- would be needed if non-trivial encryption is used
    Verifier public buyVerification;
    Verifier public sendVerification;
    Verifier public receiveVerification;

    function PrivateToken(
        address _buyVerification,
        address _sendVerification,
        address _receiveVerification
    ) public {
        totalSupply = 0;

        buyVerification = Verifier(_buyVerification);
        sendVerification = Verifier(_sendVerification);
        receiveVerification = Verifier(_receiveVerification);
    }

    /*
     * This function has to be called by parties that want to participate in the token contract.
     * It is used to announce the party's public key and to initialize the respective balance
     * to 0.
     */
    function register(uint _pk) public returns(bool) {
        // If non-trivial encryption would be used, the caller would need to additionally pass
        // initialBalanceEnc = enc(0,pk,r), where sk is the caller's public key and r is the
        // randomness used for encryption. Moreover, the caller would need to prove that indeed
        // he has passed an encryption of 0, which can be verified easily using another ZoKrates
        // contract.

        // A party can register only once
        require(!isRegistered[msg.sender]);

        balances[msg.sender] = 1; // 1 because we use enc(m,pk,r) = m + 1 for the proof-of-concept
        publicKeys[msg.sender] = _pk;
        isRegistered[msg.sender] = true;

        return true;
    }

    /*
     * This function allows to initially buy tokens; this inherently cannot be private because
     * ETH is sent to the contract
     */
    function buy(
        uint _oldBalanceEnc, // There is actually no need to pass this; it however might be nicer having it explicit
        uint _newBalanceEnc,
        uint[2] A,
        uint[2] A_p,
        uint[2][2] B,
        uint[2] B_p,
        uint[2] C,
        uint[2] C_p,
        uint[2] H,
        uint[2] K
    ) public payable returns(bool) {
        require(_oldBalanceEnc == balances[msg.sender]);

        uint amount = msg.value / tokenPrice;

        // The '1' at the last index of the public input is the return value
        uint[4] memory publicInput = [_oldBalanceEnc, _newBalanceEnc, amount, 1];
        bool result = buyVerification.verifyTx(
            A,
            A_p,
            B,
            B_p,
            C,
            C_p,
            H,
            K,
            publicInput
        );

        // The verification failed, hence return (false)
        if (!result) {
            return false;
        }

        balances[msg.sender] = _newBalanceEnc;
        totalSupply += amount;

        return true;
    }

    /*
     * This is used for the first part of a transaction
     */
    function send(
        address _to,
        uint _oldBalanceEnc, // There is actually no need to pass this; it however might be nicer having it explicit
        uint _newBalanceEnc,
        uint _amountEnc,
        uint[2] A,
        uint[2] A_p,
        uint[2][2] B,
        uint[2] B_p,
        uint[2] C,
        uint[2] C_p,
        uint[2] H,
        uint[2] K
    ) public returns(bool) {
        require(!pending[_to][msg.sender].collectable);
        require(_oldBalanceEnc == balances[msg.sender]);

        uint[5] memory publicInput =
            [_oldBalanceEnc, _newBalanceEnc, publicKeys[_to], _amountEnc, 1];
        bool result = sendVerification.verifyTx(
            A,
            A_p,
            B,
            B_p,
            C,
            C_p,
            H,
            K,
            publicInput
        );

        // The verification failed, hence return (false)
        if (!result) {
            return false;
        }

        pending[_to][msg.sender] = Pending(true, _amountEnc);
        balances[msg.sender] = _newBalanceEnc;

        return true;
    }

    /*
     * This is used for the second part of a transaction, i.e., receiving
     */
    function receive(
        address _from,
        uint _oldBalanceEnc, // There is actually no need to pass this; it however might be nicer having it explicit
        uint _newBalanceEnc,
        uint[2] A,
        uint[2] A_p,
        uint[2][2] B,
        uint[2] B_p,
        uint[2] C,
        uint[2] C_p,
        uint[2] H,
        uint[2] K
    ) public returns(bool) {
        require(!pending[msg.sender][_from].collectable);
        require(_oldBalanceEnc == balances[msg.sender]);

        uint[4] memory publicInput =
            [_oldBalanceEnc, _newBalanceEnc, pending[msg.sender][_from].amountEnc, 1];
        bool result = receiveVerification.verifyTx(
            A,
            A_p,
            B,
            B_p,
            C,
            C_p,
            H,
            K,
            publicInput
        );

        // The verification failed, hence return (false)
        if (!result) {
            return false;
        }

        pending[msg.sender][_from].collectable = false;
        balances[msg.sender] = _newBalanceEnc;

        return true;
    }
}
