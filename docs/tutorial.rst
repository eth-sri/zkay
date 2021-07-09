================================
Tutorial
================================

-----------------
Example Contract
-----------------

Assume we want to conduct a survey where users can pick between three options a, b, and c. It is possible to express such a survey in zkay such that:

1. Only the voter and the survey organizer can see the value of a vote
2. Everyone can verify that all votes were counted correctly

The contract below contains a zkay implementation of this survey system. See the :ref:`language-overview-label` for details on the individual language constructs. We assume that this contract is stored in the file `survey.zkay` in the current directory.

.. code-block:: zkay

    pragma zkay ^0.3.0;

    contract Survey {
        enum Choice {
            none, a, b, c
        }

        final address organizer;

        // Votes of the individual users (current_votes[a] is only visible to a)
        mapping(address!x => Choice@x) current_votes;

        // Private vote counts allowing homomorphic operations (only visible to the organizer)
        uint32@organizer<+> a_count;
        uint32@organizer<+> b_count;
        uint32@organizer<+> c_count;

        // The minimum number of participants before the vote can be closed
        uint min_votes;

        // Total number of votes
        uint vote_count;

        // Published results (after vote is closed and result published by organizer)
        uint packed_results;

        constructor(uint _min_votes) public {
            require(_min_votes > 0);
            organizer = me;
            min_votes = _min_votes;
        }

        // State altering functions

        function vote(Choice@me votum) public {
            require(reveal(votum != Choice.none && current_votes[me] == Choice.none, all));
            require(!is_result_published());
            current_votes[me] = votum;
            vote_count += 1;
            a_count = a_count + reveal(votum == Choice.a ? 1 : 0, organizer);
            b_count = b_count + reveal(votum == Choice.b ? 1 : 0, organizer);
            c_count = c_count + reveal(votum == Choice.c ? 1 : 0, organizer);
        }

        function publish_results() public {
            require(me == organizer);
            require(min_votes_reached());
            require(!is_result_published());
            packed_results = reveal((uint192(unhom(c_count)) << 128) | (uint192(unhom(b_count)) << 64) | uint192(unhom(a_count)), all);
        }

        // Queries

        function get_result_for(Choice option) public view returns(uint64) {
            require(is_result_published());
            uint64 res;
            if (option != Choice.none) {
                res = uint64(packed_results >> 64*(uint(option)-1));
            }
            return res;
        }

        function get_winning_choice() public view returns(Choice) {
            Choice c = Choice.none;
            uint votes = 0;
            for (uint i = uint(Choice.a); i <= uint(Choice.c); ++i) {
                uint res = get_result_for(Choice(i));
                if (res > votes) {
                    c = Choice(i);
                    votes = res;
                }
            }
            return c;
        }

        // Query with secret result
        function check_if_agree_with_majority() public view returns(bool@me) {
            Choice c = get_winning_choice();
            return c == current_votes[me];
        }

        function min_votes_reached() public view returns(bool) {
            return vote_count >= min_votes;
        }

        function is_result_published() public view returns(bool) {
            return packed_results != 0;
        }
    }



-----------------
Compilation
-----------------

To compile the contract with default encryption algorithms to the output directory `survey_compiled`, you can use:

.. code-block:: bash

    zkay compile ./survey.zkay -o ./survey_compiled/

If you simply wish to type-check the file without generating any output, you can use:

.. code-block:: bash

    zkay check ./survey.zkay

--------------------------
Local Transaction Testing
--------------------------

To run test transactions on the contract, you can use the included `eth-tester <https://github.com/ethereum/eth-tester>`_ blockchain backend.

The following command starts an interactive transaction shell with the eth-tester backend (local blockchain simulation):

.. code-block:: bash

    zkay run --blockchain-backend w3-eth-tester ./survey_compiled


Let's first create some test accounts to interact with the contract (this functionality is exclusive to the eth-tester and ganache backends):

.. code-block:: python

    >>> survey_organizer, user_a, user_b = create_dummy_accounts(3)

We can then deploy the above contract (using the value 2 for the constructor argument `_min_votes`) via:

.. code-block:: python

    >>> survey_organizer = deploy(2, user=survey_organizer)

We should then "connect" the other users to the deployed contract using

.. code-block:: python

    >>> user_a = connect(survey_organizer.address, user=user_a)
    >>> user_b = connect(survey_organizer.address, user=user_b)

The deploy and the connect commands both return a contract interface object, which should be stored in a variable.

You can now issue some zkay transactions by calling the corresponding member functions on those interface objects:

.. code-block:: python

    >>> user_a.vote(Survey.Choice.a)
    >>> user_b.vote(Survey.Choice.a)
    >>> survey_organizer.publish_results()

It is also possible to call public read-only (pure/view) contract functions which don't require a transaction.
If the return value is private (@me), it is automatically decrypted:

.. code-block:: python

    >>> user_a.is_result_published()
        True
    >>> user_a.get_winning_choice()
        Choice.a
    >>> user_a.check_if_agree_with_majority()
        True
    >>> user_b.get_result_for(Survey.Choice.b)
        0
    >>> user_b.get_result_for(Survey.Choice.a)
        2

It is also possible to manually retrieve the value of any state variable:

.. code-block:: python

    >>> user_a.state.get_plain('current_votes', user_a.api.user_address)
        Choice.a

While `state.get_plain` automatically decrypts any private values, you can use `state.get_raw` to retrieve the original ciphertext.

If an exception occurs during transaction simulation (e.g. require assertion fails), an appropriate error will be displayed:

.. code-block:: python

    >>> user_a.vote(Survey.Choice.none)
        ERROR: require(reveal(votum != Choice.none && current_votes[me] == Choice.none, all)) failed

If you are unsure which functions are available in a given contract, you can type `help()` to get a list of all available commands.

-----------------
Deployment
-----------------

You can also use a zkay contract in conjunction with a standalone Ethereum client.

For example, you can test this scenario using zkay's `w3-ganache` backend and `ganache <https://www.trufflesuite.com/ganache>`_, which simulates an Ethereum client for a local test blockchain.

Once you have ganache set up and running, you need to tell zkay to use it. You can either do this via command line flags, or by creating a configuration file '~/.config/zkay/config.json' (global) or './config.json' (local) with the following contents:

.. code-block:: json

    {
        "blockchain_backend":"w3-ganache",
        "blockchain_node_uri":"http://{ganache_ip}:{ganache_port}"
    }

Before you can deploy a zkay contract, you need to know the blockchain addresses of the deployed PKI and zkay library contracts which should be used by your contract. PKI contracts are crypto-backend specific. If there is no PKI contract on your chain yet, you can deploy it using:

.. code-block:: bash

    zkay deploy-pki <account_address_to_deploy_from>

Similarly, if the proving-scheme which you selected requires library contracts which are not yet deployed (the default groth16 scheme has no library dependencies), you can deploy them using:

.. code-block:: bash

    zkay deploy-crypto-libs <account_address_to_deploy_from>

Once the contracts are deployed, you can tell zkay to use those contract addresses by updating the configuration file accordingly:

.. code-block:: json

    {
        "blockchain_backend":"w3-ganache",
        "blockchain_node_uri":"http://{ganache_ip}:{ganache_port}",
        "blockchain_pki_address": "<Ethereum address of the PKI contract>",
        "blockchain_crypto_lib_addresses": "<blank_for_groth16>"
    }

Once this is done, you can then deploy the above Survey contract using (space-separated constructor args at the end):

.. code-block:: bash

    zkay deploy --account <account_address_to_deploy_from> ./survey_compiled 4


------------------------
Test Deployed Contract
------------------------

For contracts deployed in this way, you can open an interactive transaction shell via:

.. code-block:: bash

    zkay connect --account <sender_account_to_use> ./survey_compiled <deployed_contract_address>

In contrast to `zkay run`, the shell directly starts in the context of a contract interface object, i.e. all contract functions are directly available in the global scope (see help()). The address specified via the --account flag is used to send transactions. It can be accessed in the shell via the global 'me' variable.

Example:

.. code-block:: python

    >>> vote(Choice.a)
    >>> is_result_published()
        False


------------------------
Contract Distribution
------------------------

Users who want to interact with a deployed zkay contract need access to the corresponding compilation output, because the output contains the proving keys required to generate zero-knowledge proofs.

To simplify the distribution process, zkay can automatically pack a compiled contract into a standardized archive format which other users can import on their machine.

Export
-------

To export a contract package into a file `contract.zkp`, use:

.. code-block:: bash

    zkay export ./survey_compiled -o contract.zkp

The file `contract.zkp` can then be distributed to users.

Import
-------

Users can unpack `contract.zkp` to a location <path/to/my_survey_compiled> as follows:

.. code-block:: bash

    zkay import contract.zkp -o <path/to/my_survey_compiled>

A deployed contract at <deployed_contract_address> can then be accessed via:

.. code-block:: bash

    zkay connect --account <sender_account_to_use> <path/to/my_survey_compiled> <deployed_contract_address>

The correct zkay configuration (compiler settings, crypto-backend, etc.) is loaded automatically from the manifest file included with the contract package. It is also not necessary to specify the PKI contract address.


**Note**:
The `connect` command automatically verifies whether the contract at <deployed_contract_address> matches the imported contract sources.

------------------
Programmatic Use
------------------

Most command line features described in this tutorial are also available via an API.

See :py:mod:`.zkay_frontend`

- Compilation: :py:meth:`~zkay.zkay_frontend.compile_zkay_file`, :py:meth:`~zkay.zkay_frontend.compile_zkay`
- Deployment: :py:meth:`~zkay.zkay_frontend.deploy_contract`
- Export/Import: :py:meth:`~zkay.zkay_frontend.package_zkay_contract`, :py:meth:`~zkay.zkay_frontend.extract_zkay_package`
- Creating transaction interface object: :py:meth:`~zkay.zkay_frontend.connect_to_contract_at` (after loading the correct zkay configuration using :py:meth:`~zkay.zkay_frontend.use_configuration_from_manifest`)
