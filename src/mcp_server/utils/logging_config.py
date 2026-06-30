"""Logging configuration module."""

import logging
import logging.handlers
import sys


def setup_logging(use_console: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        use_console: If True, log to console (stdout). If False, log to file only.
                    MCP StdIO server should set this to False to avoid interfering
                    with JSON-RPC message communication.
    """
    from mcp_server.settings import settings

    # Create logs directory if it doesn't exist
    # Use project root relative path, then make absolute
    log_dir = settings.get_project_root() / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # If we can't create the log dir, write to stderr
        print(f"Failed to create log directory {log_dir}: {e}", file=sys.stderr)

    # Convert log level string to logging constant
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Format string for logging
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stdout) - only if requested
    if use_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # For MCP StdIO: also log errors to stderr for debugging
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.ERROR)
        stderr_handler.setFormatter(formatter)
        root_logger.addHandler(stderr_handler)

    # File handler (rotating) - always enabled
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "mcp_server.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set specific module log levels
    mcp_lowlevel_logger = logging.getLogger("mcp.server.lowlevel.server")
    mcp_lowlevel_logger.setLevel(logging.DEBUG)

    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured with level: {settings.log_level} (console: {use_console})"
    )
    logger.debug("MCP lowlevel server logger set to DEBUG")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
