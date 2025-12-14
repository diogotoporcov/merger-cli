import argparse
import logging
from pathlib import Path

from .parsers.modules import (
    install_module,
    uninstall_module,
    list_modules,
)
from .file_tree.tree import FileTree
from .files.files import read_merger_ignore_file, write_tree
from .logging.logger import setup_logger, logger
from .utils.version import get_version


def main():
    # Args
    parser = argparse.ArgumentParser(
        description="Merge files from a directory into a structured JSON output."
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        nargs="?",
        help="Root directory to scan for files",
    )

    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=Path("./merger.json"),
        help="Path to save merged output (default: ./merger.json)",
    )

    parser.add_argument(
        "-i",
        "--install-module",
        type=Path,
        metavar="MODULE_PATH",
        help="Install a custom parser module",
    )

    parser.add_argument(
        "-u",
        "--uninstall-module",
        metavar="MODULE_ID",
        help="Uninstall a module by ID (use '*' to remove all)",
    )

    parser.add_argument(
        "-l",
        "--list-modules",
        action="store_true",
        help="List all installed parser modules",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
        help="Show program version and exit",
    )

    parser.add_argument(
        "-ll",
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    parser.add_argument(
        "--ignore",
        nargs="*",
        default=[],
        help="Glob-style patterns to ignore (e.g., '*.log', '__pycache__', './data/')",
    )

    parser.add_argument(
        "-mi",
        "--merger-ignore",
        type=Path,
        default=Path("./merger.ignore"),
        help="File containing glob-style patterns to ignore (default: ./merger.ignore)",
    )

    args = parser.parse_args()
    setup_logger(level=getattr(logging, args.log_level.upper()))

    # Install module
    if args.install:
        try:
            install_module(args.install)
            logger.info("Module installed successfully.")
        except Exception as e:
            logger.error(f"Could not install module: {e}")
        return

    # Uninstall module(s)
    if args.uninstall:
        try:
            uninstall_module(args.uninstall)
            if args.uninstall == "*":
                logger.info("All modules uninstalled.")

            else:
                logger.info(f"Module '{args.uninstall}' uninstalled.")

        except Exception as e:
            logger.error(f"Could not uninstall module: {e}")

        return

    # List installed modules
    if args.list_installed:
        modules = list_modules()

        if not modules:
            logger.info("No modules installed.")
            return

        logger.info("Installed modules:")
        for module_id, meta in modules.items():
            name = meta.get("original_name", "unknown")
            extensions = ", ".join(meta.get("extensions", []))
            logger.info(f"  {module_id} ({name}) -> {extensions}")

        return

    # Require input_dir for normal operation
    if not args.input_dir:
        parser.error(
            "input_dir is required unless installing, uninstalling, or listing modules."
        )

    # Ignore patterns
    ignore_patterns = args.ignore.copy()
    merger_ignore_path: Path = args.merger_ignore

    if merger_ignore_path.exists():
        if not merger_ignore_path.is_file():
            parser.error(f"'{merger_ignore_path}' exists but is not a file.")

        logger.info("Found default ignore patterns file.")
        ignore_patterns.extend(
            read_merger_ignore_file(merger_ignore_path)
        )

    ignore_patterns = list(set(ignore_patterns))

    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    tree = FileTree.from_path(args.input_dir, ignore_patterns)
    write_tree(tree, args.output_path)
    logger.info(f"Saved to {args.output_path}")


if __name__ == "__main__":
    main()
