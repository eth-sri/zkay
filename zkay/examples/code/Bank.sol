pragma solidity ^0.5.0;

contract bank {
    mapping (address!x => uint@x) balances;

    function deposit() public payable {
        balances[me] = msg.value;
    }

    function send_to(address payable other, uint amount) public {
        uint@me balance = balances[me];
        require(reveal(balance >= amount, all));
        balances[me] = balance - amount;
        other.transfer(amount);
    }
}
