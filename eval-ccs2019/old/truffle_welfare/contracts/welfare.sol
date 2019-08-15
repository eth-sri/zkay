pragma solidity ^0.4.21;

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
            uint[2] input
        ) public returns (bool) {}
}

/*
 * A contract that automatically checks the eligibility for welfare while keeping private data,
 * such as income, assets, and liabilities secret.
 */
contract Welfare {
    // Only the tax authority will be allowed to post hashed tax returns to ensure the integrity
    // of data (In practice, the tax authority would have to publicly announce its address
    // in a trusted way somewhere else such that everyone can check that it indeed matches)
    address taxAuthority_;
    Verifier dataVerifier_;

    function Welfare(address _taxAuthority, address _dataVerification) {
        taxAuthority_ = _taxAuthority;
        dataVerifier_ = Verifier(_dataVerification);
    }

    // Steuerbehörde
    // mapping address -> hash
    // post hash(Steuererklärung)
    mapping(address => uint) hashedTaxDeclaration_;
    mapping(address => bool) public isEligible_;

    /*
     * Used by the tax authority to post hashed tax returns that are later used in checks
     * for welfare eligibility.
     */
    function postHashedTaxDeclaration(address _taxpayer, uint _hashedTaxDeclaration) {
        require(msg.sender == taxAuthority_);
        hashedTaxDeclaration_[_taxpayer] = _hashedTaxDeclaration;
    }

    // User
    // Post proof
    // Proof: show ownership of hashed data, show eligibility for finanical support
    // income 40000, assets 80000, liabilities 20000, social security number 1234
    function checkWelfareEligibility(
        uint[2] A,
        uint[2] A_p,
        uint[2][2] B,
        uint[2] B_p,
        uint[2] C,
        uint[2] C_p,
        uint[2] H,
        uint[2] K
    ) public returns (bool) {
        uint[2] memory publicInput = [hashedTaxDeclaration_[msg.sender], 1];
        bool result = dataVerifier_.verifyTx(A, A_p, B, B_p, C, C_p, H, K, publicInput);

        if (!result) {
            isEligible_[msg.sender] = false;
        } else {
            isEligible_[msg.sender] = true;
        }

        return isEligible_[msg.sender];
    }
}
