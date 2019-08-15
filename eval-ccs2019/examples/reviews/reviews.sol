pragma solidity ^0.5.0;

// Description: Blind paper reviews and acceptance decisions
// Domain: Academia
contract Reviews {
    final address pc;
    uint threshold = 2;
    mapping (address!x => bool@x) accepted;
    mapping (address => uint@pc) paperForAuthor;
    mapping (address => mapping (uint => uint@pc)) reviews;

    address reviewer1;
    address reviewer2;
    address reviewer3;

    constructor(address r1, address r2, address r3) public {
        pc = me;
        reviewer1 = r1;
        reviewer2 = r2;
        reviewer3 = r3;
    }

    function registerPaper(uint@me paperId) public {
        paperForAuthor[me] = reveal(paperId, pc);
    }

    function recordReview(uint paperId, uint@me merit) public {
        require(me == reviewer1 || me == reviewer2 || me == reviewer3);
        reviews[me][paperId] = reveal(merit, pc);
    }

    function decideAcceptance(address author) public {
        require(pc == me);
        uint paperId = reveal(paperForAuthor[author], all);
        uint@me sum = 0;
        sum = sum + reviews[reviewer1][paperId] + reviews[reviewer2][paperId]
                + reviews[reviewer3][paperId];
        accepted[author] = reveal(sum >= threshold, author);
    }
}
