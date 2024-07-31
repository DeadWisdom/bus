import fastapi, pydantic, starlette
import logging
from rich.logging import RichHandler

SUPPRESS = [fastapi, pydantic, starlette]

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=SUPPRESS)]
)