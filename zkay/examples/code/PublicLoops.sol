pragma solidity ^0.5.0;

contract PublicLoops {
    uint ret;

    function inc() internal {
        ret = ret + 1;
    }

    function test(uint@me some_x) public {
        uint x = reveal(some_x, all);
        uint@me value = 5;

        uint i = 0;
        ret = 0;
        while (true) {
            if (i < x) {
                inc();
                i = i + 1;
                continue;
            }
            else {
                break;
            }
        }
        require(i == x && ret == x);
        value = 2;

        do {
            ret = 0;
            if (true) {
                break;
            }
            ret = 42;
        } while(false);

        value = 3;
        i = 0;
        for (value = 0; i < x; ) {
            i = i + 1;
            inc();
        }
        require(i == x && ret == x);

        for (ret = 0; ret < x; inc()) {}
        require(ret == x);
    }
}
