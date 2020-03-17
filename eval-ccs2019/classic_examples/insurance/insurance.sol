pragma solidity ^0.5.0;

// Description: Insure secret items at secret amounts
// Domain: Insurance
contract Insurance {
    final address insurance;
    final address police;
    final uint MAX_AMOUNT = 3000; // maximum insured amount
    final uint MAX_PAY = 10000; // upper bound on total amount paid to single account

    // book-keeping
    mapping(address => uint) n_items;

    // insured goods
    mapping(address!x => mapping(uint => uint@x)) amounts; // insured amount, per account and id
    mapping(address => mapping(uint => uint)) rates; // rate offered by client
    mapping(address => mapping(uint => bool)) accepted; // per account and id
    mapping(address!x => mapping(uint => bool@x)) stolen; // per account and id
    mapping(address!x => mapping(uint => bool@x)) broken; // per account and id
    mapping(address!x => uint@x) paid; // total paid amount, per account

    constructor(address police_) public {
        insurance = me;
        police = police_;
    }

    function register() public {
        n_items[me] = 0;
        paid[me] = 0;
    }

    function insure_item(uint@me amount, uint rate) public {
        // book-keeping
        uint next = n_items[me];
        n_items[me] = next + 1;

        // omitted: transfer rate
        rates[me][next] = rate;

        // record information
        require(reveal(amount < MAX_AMOUNT, all));
        amounts[me][next] = amount;
        accepted[me][next] =  false;
        stolen[me][next] = false;
        broken[me][next] = false;
    }

    function retract_item(uint id) public {
        require(accepted[me][id] == false);
        uint refund = rates[me][id];
        // omitted: refund client
        // set insured amount to 0
        amounts[me][id] = 0;
    }
    
    function accept_item(address client, uint id) public {
        require(insurance == me);
        accepted[client][id] = true;
    }

    function set_stolen(address client, uint id, bool@me is_stolen) public {
        require(police == me);
        stolen[client][id] = reveal(is_stolen, client);
    }

    function set_broken(address client, uint id, bool@me is_broken) public {
        require(police == me); // could also be some other authority
        broken[client][id] = reveal(is_broken, client);
    }

    function get_refund(uint id) public {
        require(id < n_items[me]);
        require(accepted[me][id]);
        bool item_unusable = reveal(stolen[me][id] || broken[me][id], all);
        require(item_unusable);
        uint@me amount = amounts[me][id];
        require(reveal(paid[me] + amount < MAX_PAY, all));
        // omitted: transfer amount (may require declassification)
        paid[me] = paid[me] + amount; // update total paid amount
    }
}