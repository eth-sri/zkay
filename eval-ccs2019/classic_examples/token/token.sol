pragma solidity ^0.5.0;

// Description: Buy and transfer secret amount of tokens
// Domain: Finance
contract Token {
    mapping (address!x => uint@x) balance;
    mapping (address => mapping (address!x => uint@x)) pending;
    mapping (address => bool) has_pending;
    mapping (address => bool) registered;

    function register() public {
        balance[me] = 0;
        registered[me] = true;
        has_pending[me] = false;
    }

    function buy(uint amount) public payable {
        require(registered[me]);
        // amount should actually be computed based on the payed value
        balance[me] = balance[me] + amount;
    }

    function send_tokens(uint@me v, address receiver) public {
        require(registered[me] && registered[receiver]);
        require(!has_pending[receiver]);
        require(reveal(balance[me] > v, all));
        balance[me] = balance[me] - v;
        pending[me][receiver] = reveal(v, receiver);
        has_pending[receiver] = true;
    }

    function receive_tokens(address sender) public {
        require(registered[me] && registered[sender]);
        require(has_pending[me]);
        balance[me] = balance[me] + pending[sender][me];
        pending[sender][me] = 0;
        has_pending[me] = false;
    }
}