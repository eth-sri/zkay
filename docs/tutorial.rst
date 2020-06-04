================================
Tutorial
================================

-----------------
Example Problem
-----------------

Let's assume we want to conduct a survey where users can pick between the 3 options a, b, and c.
With zkay it is possible to do this on-chain such that:

1. Only the voter and the survey organizer get to see the value of a vote
2. Everyone can verify that all votes were counted correctly

The following example contract shows, how such an implementation could look like:

.. code-block:: zkay

    pragma zkay ^0.2.0;

    contract Survey {
        enum Choice {
            None, a, b, c
        }

        final address organizer;

        // Votes of the individual users (only readable by the respective user)
        mapping(address!x => Choice@x) current_votes;

        // Current vote to be processed by organizer
        bool pending_vote;
        Choice@organizer new_vote;

        // Encrypted counts
        uint64@organizer a_count;
        uint64@organizer b_count;
        uint64@organizer c_count;

        // The minimum number of paticipants before the vote can be closed
        uint min_votes;

        // Total number of votes
        uint vote_count;

        // Published results (after vote is closed and result published by organizer),
        // packed into a single uint
        uint packed_results;

        constructor(uint _min_votes) public {
            require(_min_votes > 0);
            organizer = me;
            min_votes = _min_votes;
        }

        // State altering functions

        function vote(Choice@me votum) public {
            require(!pending_vote);
            require(reveal(votum != Choice.None && current_votes[me] == Choice.None, all));
            require(!is_result_published());

            current_votes[me] = votum;
            new_vote = reveal(votum, organizer);
            pending_vote = true;
        }

        function count_vote() public {
            require(me == organizer);
            require(pending_vote);

            if (new_vote == Choice.a) {
                a_count++;
            } else if (new_vote == Choice.b) {
                b_count++;
            } else {
                c_count++;
            }

            pending_vote = false;
            vote_count++;
        }

        function publish_results() public {
            require(me == organizer);
            require(!pending_vote && min_votes_reached());
            packed_results = reveal((uint192(c_count) << 128) | (uint192(b_count) << 64) | uint192(a_count), all);
        }

        // Queries

        function get_result_for(Choice option) public view returns(uint64) {
            require(is_result_published());
            uint64 res;
            if (option != Choice.None) {
                res = uint64(packed_results >> 64*(uint(option)-1));
            }
            return res;
        }

        function get_winning_choice() public view returns(Choice) {
            Choice c = Choice.None;
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


From now on, we assume that this contract is stored in the file `survey.zkay` in the current directory.

-----------------
Compilation
-----------------

To compile the contract with the default encryption algorithm (ecdh-aes) and with output directory `survey_compiled`, you can simply use:

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
    >>> survey_organizer.count_vote()
    >>> user_b.vote(Survey.Choice.a)
    >>> survey_organizer.count_vote()
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
    >>> user_a.state.get_plain('pending_vote')
        False

While `state.get_plain` automatically decrypts the value, it is also possible to use `state.get_raw`, to retrieve the unmodified cipher text instead.

If an exception occurs during transaction simulation (e.g. require assertion fails), an appropriate error will be displayed.
If you are unsure which functions are available in a given contract, you can type `help()` to get a list of all available commands.

-----------------
Deployment
-----------------

While the eth-tester backend is nice for quick testing, at some point you might want to use a zkay contract in conjunction with a standalone Ethereum client.

You can test this scenario using zkay's `w3-ganache` backend and `ganache <https://www.trufflesuite.com/ganache>`_, which simulates an Ethereum client for a local test blockchain.

Once you have ganache set up and running, you need to tell zkay to use it. You can either do this via command line flags, or by creating a configuration file '~/.config/zkay/config.json' (global) or './config.json' (local) with the following contents:

.. code-block:: json

    {
        "blockchain_backend":"w3-ganache",
        "blockchain_node_uri":"http://{ganache_ip}:{ganache_port}"
    }

Before you can deploy a zkay contract, you need to know the blockchain addresses of the deployed PKI and zkay library contracts which should be used by your contract.
PKI contracts are crypto-backend specific, if there is no PKI contract on your chain yet, you can deploy it using:

.. code-block:: bash

    zkay deploy-pki <account_address_to_deploy_from>

Similarly, if the proving-scheme which you selected requires library contracts which are not yet deployed (the default groth16 scheme has no library dependencies),
you can deploy them using:

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

Once this is done, you can then deploy the above Survey contract using (space separated constructor args at the end):

.. code-block:: bash

    zkay deploy --account <account_address_to_deploy_from> ./survey_compiled 4


------------------------
Test Deployed Contract
------------------------

For contracts deployed in this way, you can open an interactive transaction shell via:

.. code-block:: bash

    zkay connect --account <sender_account_to_use> ./survey_compiled <deployed_contract_address>

In contrast to `zkay run`, the shell directly starts in the context of a contract interface object,
i.e. all contract functions are directly available in the global scope (see help()).
The address specified via the --account flag is used to send transactions. It can be accessed in the shell via the global 'me' variable.

Example:

.. code-block:: python

    >>> vote(Choice.a)
    >>> is_result_published()
        False
    >>> state.get_plain('pending_vote')
        True


------------------------
Contract Distribution
------------------------

Each user which should be able to connect to and use a deployed zkay contract needs access to the corresponding compilation output. (For integrity verification and because the output contains the proving keys required to generate zero-knowledge proofs)

To simplify the distribution process, zkay can automatically pack a compiled contract into a standardized archive format which other users can import on their machine.

Export
-------

To export a contract package into a file `contract.zkp`, use:

.. code-block:: bash

    zkay export ./survey_compiled -o contract.zkp

The file `contract.zkp` can then be hosted somewhere where other users can download it.

Import
-------

Each user needs to download `contract.zkp` and then unpack and compile it to a location <path/to/my_survey_compiled> using:

.. code-block:: bash

    zkay import contract.zkp -o <path/to/my_survey_compiled>

The contract should then be usable just like on your local machine (assuming the other user's zkay configuration points to the same blockchain) via:

.. code-block:: bash

    zkay connect --account <other_users_sender_account_to_use> <path/to/my_survey_compiled> <deployed_contract_address>

The correct zkay configuration (compiler settings, crypto-backend, etc.) is loaded automatically from the manifest file which was also included with the contract package.
It is also not necessary to specify the PKI contract address, as it will be automatically read from the contract on-chain.


**Note**:
The connect command will automatically verify whether the contract at <deployed_contract_address> matches the imported contract sources.
If there is a mismatch, zkay automatically terminates with an error message.

------------------
Programmatic Use
------------------

Most command line features which were described in this tutorial are also available via an API.

See :py:mod:`.zkay_frontend`

- Compilation: :py:meth:`~zkay.zkay_frontend.compile_zkay_file`, :py:meth:`~zkay.zkay_frontend.compile_zkay`
- Deployment: :py:meth:`~zkay.zkay_frontend.deploy_contract`
- Export/Import: :py:meth:`~zkay.zkay_frontend.package_zkay_contract`, :py:meth:`~zkay.zkay_frontend.extract_zkay_package`
- Creating transaction interface object: :py:meth:`~zkay.zkay_frontend.connect_to_contract_at` (after loading the correct zkay configuration using :py:meth:`~zkay.zkay_frontend.use_configuration_from_manifest`)
