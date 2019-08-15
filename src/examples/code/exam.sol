pragma solidity ^0.5.0;

contract Exam {
    final address examinator;
    uint pass_points;

    mapping (uint => uint@examinator) solutions;
    mapping (address => mapping (uint => uint@examinator)) answers;
    mapping (address => uint@examinator) points;
    mapping (address!x => bool@x) passed;
	
    constructor(uint pass) public {
        examinator = me;
        pass_points = pass;
    }

    function set_solution(uint task, uint@me sol) public {
        require(examinator == me);
        solutions[task] = sol;
    }

    function record_answer(uint task, uint@me ans) public {
        answers[me][task] = reveal(ans, examinator);
        passed[me] = false;
        points[me] = 0;
    }

    function grade_task(uint task, address examinee) public {
        require(examinator == me);
        uint@me p;
        p = answers[examinee][task] == solutions[task] ? 1 : 0;
        points[examinee] = points[examinee] + p;
        passed[examinee] = reveal(points[examinee] > pass_points, examinee);
    }
}