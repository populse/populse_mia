"""
Utilities for configuring and managing application logging.

This module provides helper functions to initialize logging, create log files,
and remove old log files according to the configured retention policy.
"""

##########################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
##########################################################################

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

__all__ = ["configure_logging", "_cleanup_old_logs"]


def configure_logging(
    log_in_stdout: bool, keep_log_files: int, log_level: str
) -> None:
    """
    Configure the application logging.

    :param log_in_stdout: If True, log messages are written to stdout.
        Otherwise, they are written to a log file.
    :type param log_in_stdout: bool
    :param keep_log_files : Number of log files to retain.
    :type param keep_log_files: int
    :param log_level: Level of the logger.
    :type param log_level: str
    """
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    )

    if log_in_stdout:
        handler = logging.StreamHandler()

    else:
        mia_config_dir = Path.home() / ".populse_mia"
        log_dir = mia_config_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        filename = "mia_" f"{datetime.now():%Y%m%d_%H%M%S}.log"

        handler = logging.FileHandler(
            log_dir / filename,
            encoding="utf-8",
        )

        _cleanup_old_logs(log_dir, keep_log_files)

    handler.setFormatter(formatter)

    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=[handler],
        force=True,
    )


def _cleanup_old_logs(
    log_dir: Path,
    keep_log_files: int,
) -> None:
    """
    Remove the oldest log files from the log directory.

    Deletes log files matching ``mia_*.log`` until at most ``keep_log_files``
    log files remain.

    :param log_dir: Directory containing the log files.
    :type log_dir: pathlib.Path
    :param keep_log_files: Maximum number of log files to keep.
    :type keep_log_files: int
    """
    logs = sorted(log_dir.glob("mia_*.log"))

    while len(logs) > keep_log_files:
        logs[0].unlink(missing_ok=True)
        logs.pop(0)
