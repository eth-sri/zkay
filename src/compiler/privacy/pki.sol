pragma solidity ^0.5;

contract PublicKeyInfrastructure{
    mapping(address => uint) pks;
    mapping(address => bool) hasAnnounced;

    function announcePk(uint pk) public {
        pks[msg.sender] = pk;
        hasAnnounced[msg.sender] = true;
    }

    function getPk(address a) public view returns(uint) {
        require(hasAnnounced[a]);
        return pks[a];
    }
}
