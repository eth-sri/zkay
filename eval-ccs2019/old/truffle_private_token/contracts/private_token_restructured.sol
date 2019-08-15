pragma solidity ^0.4.21; // TODO[MG/130618]: Figure out why 0.4.23 does not work for me

contract Verifier {
    // TODO[MG/130618]: Get rid of this and use import statements instead
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

/*
 * A token contract that is ready to leverage ZoKrates to provide privacy for transactions;
 * it has been restructured to avoid the "Stack too deep" exception. In contrast to the earlier
 * version, proofs are now send to a separate method (depositProof), which deposits them to
 * storage so they can be used on a later call to send/receive.
 */
contract PrivateToken {
    struct Pending {
        bool collectable;
        uint amountEnc;
    }

    enum ProofStatus {
        INVALID,
        NEW,
        USED
    }

    struct ZkProof {
        uint[2] A;
        uint[2] A_p;
        uint[2][2] B;
        uint[2] B_p;
        uint[2] C;
        uint[2] C_p;
        uint[2] H;
        uint[2] K;
    }

    struct StoredZkProof {
        ProofStatus status;
        ZkProof proof;
    }

    // balances[user] := with the user's public key encrypted balance
    mapping(address => uint) public balances;
    // pending[receiver][sender] := with the receiver's public key encrypted amount of tokens
    mapping(address => mapping(address => Pending)) public  pending;
    // collection of public keys
    mapping(address => uint) public publicKeys;
    // indicated whether a user is registered
    mapping(address => bool) public isRegistered;

    // helper maps to store zk-proofs; needed for "stack too deep" workaround
    mapping(address => StoredZkProof) depositedSendProofs;
    mapping(address => StoredZkProof) depositedReceiveProofs;

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
     * A helper function that stores the given prove so it can be used later to send or
     * receive money; this function soley exists for the purpose of a workaround around
     * the "Stack too deep exception".
     */
    function depositProof(
        uint proofType,
        uint[2] A,
        uint[2] A_p,
        uint[2][2] B,
        uint[2] B_p,
        uint[2] C,
        uint[2] C_p,
        uint[2] H,
        uint[2] K
    ) public {
        require(proofType == 1 || proofType == 2);

        ZkProof memory proof = ZkProof(A,A_p,B,B_p,C,C_p,H,K);
        if (proofType == 1) {
            depositedSendProofs[msg.sender] = StoredZkProof(ProofStatus.NEW, proof);
        } else if (proofType == 2) {
            depositedReceiveProofs[msg.sender] = StoredZkProof(ProofStatus.NEW, proof);
        }
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
    function buyTokens(
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
        } else {
            balances[msg.sender] = _newBalanceEnc;
            totalSupply += amount;

            return true;
        }
    }

    /*
     * This is used for the first part of a transaction; to work around the "Stack too deep"
     * exception, the  ZK-proof needs to be deposited first using the depositProof function
     *
     * NOTE: This function cannot be called simply 'send'; the transaction will fail in this
     *  case due to a lack of funds
     */
    function sendTokens(
        address _to,
        uint _oldBalanceEnc, // There is actually no need to pass this; it however might be nicer having it explicit
        uint _newBalanceEnc,
        uint _amountEnc
    ) public returns(bool) {
        require(depositedSendProofs[msg.sender].status == ProofStatus.NEW);
        require(balances[msg.sender] == _oldBalanceEnc);
        require(pending[_to][msg.sender].collectable == false);

        uint[5] memory publicInput =
            [balances[msg.sender], _newBalanceEnc, publicKeys[_to], _amountEnc, 1];
        ZkProof storage proof = depositedSendProofs[msg.sender].proof;
        bool result = sendVerification.verifyTx(
            proof.A,
            proof.A_p,
            proof.B,
            proof.B_p,
            proof.C,
            proof.C_p,
            proof.H,
            proof.K,
            publicInput
        );

        // The verification failed, hence return (false)
        if (!result) {
            return false;
        }

        pending[_to][msg.sender] = Pending(true, _amountEnc);
        balances[msg.sender] = _newBalanceEnc;
        depositedSendProofs[msg.sender].status = ProofStatus.USED;

        return true;
    }

    /*
     * This is used for the second part of a transaction, i.e., receiving
     */
    function receiveTokens(
        address _from,
        uint _oldBalanceEnc, // There is actually no need to pass this; it however might be nicer having it explicit
        uint _newBalanceEnc
    ) public returns(bool) {
        require(depositedReceiveProofs[msg.sender].status == ProofStatus.NEW);
        require(_oldBalanceEnc == balances[msg.sender]);
        require(pending[msg.sender][_from].collectable == true);

        uint[4] memory publicInput =
            [_oldBalanceEnc, _newBalanceEnc, pending[msg.sender][_from].amountEnc, 1];
        ZkProof storage proof = depositedReceiveProofs[msg.sender].proof;
        bool result = receiveVerification.verifyTx(
            proof.A,
            proof.A_p,
            proof.B,
            proof.B_p,
            proof.C,
            proof.C_p,
            proof.H,
            proof.K,
            publicInput
        );

        // The verification failed, hence return (false)
        if (!result) {
            return false;
        }

        pending[msg.sender][_from].collectable = false;
        balances[msg.sender] = _newBalanceEnc;
        depositedReceiveProofs[msg.sender].status = ProofStatus.USED;

        return true;
    }
}
