"""Initialization for the analysisweb package."""

from enum import Enum

import logging

logger = logging.getLogger(__name__)


class Status(Enum):
    """Enumeration of supported execution statuses for a step."""

    FAILED = "Failed"
    SUCCESS = "Success"
    SKIPPED = "Skipped"
