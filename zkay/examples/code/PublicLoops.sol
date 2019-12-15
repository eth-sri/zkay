pragma solidity ^0.5.0;

contract PublicLoops {
    uint ret;

    function inc() internal {
        ret = ret + 1;
    }

    function test(uint x) public {
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

        ret = 0;
        for (i = 0; i < x; ) {
            i = i + 1;
            inc();
        }
        require(i == x && ret == x);

        for (ret = 0; ret < x; inc()) {}
        require(ret == x);
    }
}
