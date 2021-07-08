Getting Started
================================

Prerequisites
--------------

Before installing zkay, make sure that the necessary dependencies are installed:

Debian derivatives:

.. code-block:: bash

	sudo apt-get install default-jdk-headless git build-essential cmake libgmp-dev pkg-config libssl-dev libboost-dev libboost-program-options-dev

Arch derivatives:

.. code-block:: bash

	sudo pacman -S --needed jdk-openjdk cmake pkgconf openssl gmp boost


Installation
--------------

You can then build and install zkay as follows:

.. code-block:: bash

	git clone https://github.com/eth-sri/zkay.git
	bash ./babygiant-lib/install.sh
	cd zkay
	pip install --no-binary zkay .


**Note**: zkay requires Python >= 3.8.

Usage
--------------

See the `README <https://github.com/eth-sri/zkay/blob/master/README.md>`_ and the :doc:`tutorial` for general usage instructions.
