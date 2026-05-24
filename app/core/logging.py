import logging
import sys


def configure_logging(level: str) -> None:
    """Configure process-wide structured-enough logging for local operation."""

    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
