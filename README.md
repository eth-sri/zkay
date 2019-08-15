# BPL: Blockchain Privacy Language

## Install

### Using Docker

The simplest way to run BPL is using docker. After installing docker, you may
run the docker image by:

```bash
/.../abc $ /.../bpl-docker.sh
(base) root@ae09e165bd19:/abc_host$
```

This command mounts `abc` (the current working directory) as `abc_host` within
the docker image. This allows you to operate on files of the host, which is
important when compiling BPL contracts.

### Directly On Host

Alternatively, you may install BPL on your host directly. To this end, following
the instructions in the [Dockerfile](./install/Dockerfile), marked by: `To
install on host`.

## Unit Tests

To run unit tests, run (example using docker):

```bash
# run docker container
/path/to/repository/code $ ./bpl-docker.sh
# run tests within docker
(base) root@ae09e165bd19:/code_host$  make test
```

## Compile Contracts

To compile a BPL file `test.bpl` and place the output into the current working
directory:

```bash
# run docker container
/path/to/contract $ /path/to/bpl-docker.sh
# run compilation
(base) root@ff2ddb8da49c:/contract_host# python /bpl/main.py test.bpl
```
