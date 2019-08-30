// pragma solidity ^0.5.0;
// contract MedStats{
// 	final address hospital;
// 	uint@hospital count;
// 	mapping(address!x => bool@x) risk;
// 	constructor() public  {
// 		hospital = me;
// 		count = reveal(0, hospital);
// 	}
// 	function record(address pat, bool@me r) public  {
// 		require(hospital == me);
// 		risk[pat] = reveal(r, pat);
// 		count = count + (r ? reveal(1, me) : reveal(0, me));
// 	}
// 	function check(bool@me r) public  {
// 		require(reveal(r == risk[me], all));
// 	}
// }

pragma solidity ^0.5.0;

import "./pki.sol";
import "./Verify_record_verifier.sol";
import "./Verify_check_verifier.sol";
import "./Verify_constructor_verifier.sol";

contract MedStats{
	PublicKeyInfrastructure genPublicKeyInfrastructure;
	Verify_record Verify_record_var;
	Verify_check Verify_check_var;
	Verify_constructor Verify_constructor_var;
	address hospital;
	uint count;
	mapping(address => uint) risk;
	constructor(uint[8] memory Verify_constructorproof, uint[1] memory genParam, PublicKeyInfrastructure genPublicKeyInfrastructure_, Verify_record Verify_record_var_, Verify_check Verify_check_var_, Verify_constructor Verify_constructor_var_) public  {
		Verify_constructor_var = Verify_constructor_var_;Verify_check_var = Verify_check_var_;Verify_record_var = Verify_record_var_;genPublicKeyInfrastructure = genPublicKeyInfrastructure_;hospital = msg.sender;
		count = genParam[0];
		uint256[] memory geninputs = new uint256[](2);
		geninputs[0]=genParam[0];
		geninputs[1]=genPublicKeyInfrastructure.getPk(hospital);
		uint128[2] memory genHash = get_hash(geninputs);
		Verify_constructor_var.check_verify(Verify_constructorproof, [genHash[0], genHash[1], uint(1)]);
	}
	function record(address pat, uint r, uint[8] memory Verify_recordproof, uint[3] memory genParam) public  {
		uint[5] memory genHelper;
		genHelper[0] = r;require(hospital == msg.sender);
		genHelper[1] = r;
		risk[pat] = genParam[0];
		genHelper[2] = count;
		genHelper[4] = r;
		genHelper[3] = (genParam[1]);
		count = genParam[2];
		uint256[] memory geninputs = new uint256[](12);
		geninputs[0]=genHelper[0];
		geninputs[1]=genPublicKeyInfrastructure.getPk(msg.sender);
		geninputs[2]=genHelper[1];
		geninputs[3]=genParam[0];
		geninputs[4]=genPublicKeyInfrastructure.getPk(pat);
		geninputs[5]=genHelper[2];
		geninputs[6]=genHelper[4];
		geninputs[7]=genParam[1];
		geninputs[8]=genPublicKeyInfrastructure.getPk(msg.sender);
		geninputs[9]=genHelper[3];
		geninputs[10]=genParam[2];
		geninputs[11]=genPublicKeyInfrastructure.getPk(msg.sender);
		uint128[2] memory genHash = get_hash(geninputs);
		Verify_record_var.check_verify(Verify_recordproof, [genHash[0], genHash[1], uint(1)]);
	}
	function check(uint r, uint[8] memory Verify_checkproof, uint[1] memory genParam) public  {
		uint[3] memory genHelper;
		genHelper[0] = r;genHelper[1] = r;
		genHelper[2] = risk[msg.sender];
		require(genParam[0] == 1);
		uint256[] memory geninputs = new uint256[](5);
		geninputs[0]=genHelper[0];
		geninputs[1]=genPublicKeyInfrastructure.getPk(msg.sender);
		geninputs[2]=genHelper[1];
		geninputs[3]=genHelper[2];
		geninputs[4]=genParam[0];
		uint128[2] memory genHash = get_hash(geninputs);
		Verify_check_var.check_verify(Verify_checkproof, [genHash[0], genHash[1], uint(1)]);
	}

	    function get_hash(uint[] memory preimage) public pure returns (uint128[2] memory) {
	        // start with just the first element
	        bytes32 hash = bytes32(preimage[0]);
        
	        // add one value after the other to the hash
	        for (uint i=1; i<preimage.length; i++) {
	            bytes memory packed = abi.encode(hash, preimage[i]);
	            hash = sha256(packed);
	        }
        
	        // split result into 2 parts (needed for zokrates)
	        uint hash_int = uint(hash);
	        uint128 part0 = uint128(hash_int / 0x100000000000000000000000000000000);
	        uint128 part1 = uint128(hash_int);
	        return [part0, part1];
	    }

}