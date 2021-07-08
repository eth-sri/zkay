.. zkay documentation master file, created by
   sphinx-quickstart on Wed Feb  5 14:52:24 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to zkay's documentation!
================================

Zkay is a programming language which enables automatic compilation of intuitive data privacy specifications to Ethereum smart contracts leveraging (homomorphic) encryption and non-interactive zero-knowledge (NIZK) proofs. The zkay package provides a toolchain for compiling, deploying and using zkay contracts.

The zkay language is closely related to Solidity and allows convenient specification of data ownership, reclassification, and private computations. Given a zkay contract, zkay's compiler automatically transforms it to a Solidity contract that realizes the privacy specification and can be deployed to an Ethereum blockchain.

The core concepts of zkay are introduced in its original `research paper
<https://www.sri.inf.ethz.ch/publications/steffen2019zkay>`_. 


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   tutorial
   language
   release_notes



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Security Disclaimer
===================
Zkay is a research project and its implementation should **not** be considered secure (e.g., it may contain bugs and has not undergone any security review)! Do not use zkay in a productive system or to process sensitive confidential data.

Note that zkay currently relies on zk-SNARKs to enforce its correctness guarantees. These require a trusted setup phase, which is currently performed during local contract compilation and hence can not be trusted if performed by a different user.
