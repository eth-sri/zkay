# zkay: A Blockchain Privacy Language

zkay (pronounced as `[zi: keɪ]`) is a programming language which enables
automatic compilation of intuitive data privacy specifications to NIZK-enabled
private smart contracts.

## Warning

This is a prototype implementation not intended for use in production. In
particular, it uses "dummy" encryption `Enc(v,R,k)=v+k`, which is **insecure**.

## Install

### Using Docker

The simplest way to run zkay is using docker. After installing docker, the docker image can be run
as follows:

```bash
/path/to/zkay$ ./zkay-docker.sh
(base) root@ae09e165bd19:/zkay_host$
```

This command mounts the directory `zkay` from your host as `/zkay_host`
within the docker container. You can run `zkay-docker.sh` also from any other directory `d` on your host.
In this case, `d` is mounted as `/d_host` inside the container.
This allows you to operate on files from your host machine.

### Directly On Host

As an alternative to docker, you may install zkay on your host directly. To this end, follow
the instructions in the [Dockerfile](./install/Dockerfile) marked by `To install on host`.

Below we show how to test your zkay installation, and how to type-check and
compile zkay contracts from _within the docker container_. However, the
respective commands can similarly be _run directly on the host_ after having
installed zkay properly.

## Unit Tests

To run all unit tests of zkay, run:

```bash
# run docker container
/path/to/zkay$ ./zkay-docker.sh
# run tests within docker
(base) root@ae09e165bd19:/zkay_host$ cd src
(base) root@ae09e165bd19:/zkay_host$ make test
```

If all tests pass, your zkay installation is likely set up correctly.
Note that running all unit tests *may take several hours*.

## Type-Check Contracts

To type-check a zkay file `test.zkay` in `/path/to/contract` without compiling it, run:

```bash
# run docker container
/path/to/contract$ /path/to/zkay-docker.sh
# run compilation
(base) root@ff2ddb8da49c:/contract_host$ python3 /zkay/src/main.py test.zkay --type-check
```

## Compile Contracts

To compile and type-check a zkay file `test.zkay` in `/path/to/contract`, run:

```bash
# run docker container
/path/to/contract$ /path/to/zkay-docker.sh
# run compilation
(base) root@ff2ddb8da49c:/contract_host$ python3 /zkay/src/main.py test.zkay
```

The output comprises the transformed zkay contract, the contracts for proof verification, 
and the proof circuits in ZoKrates' domain-specific language. By default, it is placed
in the current working directory. A different output directory can be specified using
the `--output` command line argument.

Note that the compilation *may take a couple of minutes*.

## Transform and Run Transactions

To run a specific sequence of transactions (i.e., a _scenario_) for the `exam`
example contract, run:

```bash
# run docker container
/path/to/eval-ccs-2019$ ../zkay-docker.sh
# compile contract (omit if already compiled)
(base) root@ff2ddb8da49c:/eval-ccs-2019_host$ python3 "$ZKAYSRC/main.py" --output ./examples/exam/compiled ./examples/exam/exam.sol
# transform scenario
(base) root@ff2ddb8da49c:/eval-ccs-2019_host$ ./generate-scenario.sh ./examples/exam
# run scenario
(base) root@ff2ddb8da49c:/eval-ccs-2019_host$ ./examples/exam/scenario/runner.sh
```

To transform and run your own transactions, you may follow analogous steps. In
particular, see [scenario.py](./eval-ccs2019/examples/exam/scenario.py) for the
specification of the scenario ran by the above code.

## Run Evaluation from CCS 2019

To reproduce the evaluation results from the paper, run:

```bash
/path/to/zkay/eval-ccs2019$ ./zkay-eval-docker.sh
```

Note that running this command *may take several hours* and requires docker
to be installed.
