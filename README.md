# BPL: Blockchain Privacy Language

## Install

### Using Docker

The simplest way to run BPL is using docker. After installing docker, the docker image can be run
as follows:

```bash
/path/to/bpl-implementation$ ./bpl-docker.sh
(base) root@ae09e165bd19:/bpl-implementation_host$
```

This command mounts the directory `bpl-implementation` from your host as `/bpl-implementation_host`
within the docker container. You can run `bpl-docker.sh` also from any other directory `d` on your host.
In this case, `d` is mounted as `/d_host` inside the container. 
This allows you to operate on files from your host machine.

### Directly On Host

As an alternative to docker, you may install BPL on your host directly. To this end, follow
the instructions in the [Dockerfile](./install/Dockerfile) marked by `To install on host`.

Below we show how to run unit tests and how to type-check and compile BPL
contracts from _within the docker container_. However, the respective commands
can similarly be _run directly on the host_ after having installed BPL properly.

## Unit Tests

To run unit tests, run:

```bash
# run docker container
/path/to/bpl-implementation$ ./bpl-docker.sh
# run tests within docker
(base) root@ae09e165bd19:/bpl-implementation_host$ cd src
(base) root@ae09e165bd19:/bpl-implementation_host$ make test
```

## Type-Check Contracts

To type-check a BPL file `test.bpl` in `/path/to/contract` without compiling it, run:

```bash
# run docker container
/path/to/contract$ /path/to/bpl-docker.sh
# run compilation
(base) root@ff2ddb8da49c:/contract_host$ python /bpl-implementation/src/main.py test.bpl --type-check
```

## Compile Contracts

To compile and type-check a BPL file `test.bpl` in `/path/to/contract`, run: 

```bash
# run docker container
/path/to/contract$ /path/to/bpl-docker.sh
# run compilation
(base) root@ff2ddb8da49c:/contract_host$ python /bpl-implementation/src/main.py test.bpl
```

The output is placed in the current working directory and consists of the transformed BPL contract,
the contracts for proof verification, and the proof circuits in ZoKrates' domain-specific language.
Note that the compilation may take a couple of minutes.

## Transform Transactions

To see how a sequence of transactions (i.e., a _scenario_) can be specified,
see the example in `/path/to/eval-ccs-2019/examples/exam/scenario.py`. 
To transform this scenario, run the `scenario.py` script. 
To transform the `exam` scenario example, run

```bash
# run docker container
/path/to/eval-ccs-2019$ ../bpl-docker.sh
# compile contract (omit if already compiled)
(base) root@ff2ddb8da49c:/eval-ccs-2019_host$ python3 "$BPLSRC/main.py" --output ./examples/exam/compiled ./examples/exam/exam.sol
# run scenario
(base) root@ff2ddb8da49c:/eval-ccs-2019_host$ ./generate-scenario.sh ./examples/exam
```

## Run Evaluation from CCS 2019

To reproduce the evaluation results from the paper, run:

```bash
/path/to/bpl-implementation/eval-ccs2019$ ./bpl-eval-docker.sh
```

Note that running this command requires docker to be installed.
