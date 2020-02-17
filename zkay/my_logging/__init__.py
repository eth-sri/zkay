"""
This package contains logging functionality.

==========
Submodules
==========
* :py:mod:`.log_context`: Context manager for managing log contexts.
* :py:mod:`.logger`: Log writer
"""

from zkay.my_logging.logger import data, shutdown, prepare_logger, get_log_file
from logging import critical, error, warning, info, debug
