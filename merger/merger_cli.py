import argparse
import logging
from pathlib import Path

from .parsers.parsers import import_parser, remove_parser, list_installed_parsers
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
        help="Root directory to scan for files"
    )

    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=Path("./merger.json"),
        help="Path to save merged output (default: ./merger.json)"
    )

    parser.add_argument(
        "-i", "--install",
        type=Path,
        metavar="MODULE_PATH",
        help="Install a custom parser"
    )

    parser.add_argument(
        "-u", "--uninstall",
        metavar="EXTENSION",
        help="Uninstall a custom parser by extension (use '*' to remove all)"
    )

    parser.add_argument(
        "--list-installed",
        action="store_true",
        help="List all installed custom parsers"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
        help="Show program version and exit"
    )

    parser.add_argument(
        "-l", "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )

    parser.add_argument(
        "--ignore",
        nargs="*",
        default=[],
        help="Glob-style patterns to ignore (e.g., '*.log', '__pycache__', './data/')"
    )

    parser.add_argument(
        "-mi", "--merger-ignore",
        type=Path,
        default=Path("./merger.ignore"),
        help="File containing glob-style patterns to ignore (default: ./merger.ignore)"
    )

    parser.add_argument(
        "--no-tree",
        action="store_true",
        default=False,
        help="Do not include the generated directory tree in the output file"
    )

    args = parser.parse_args()
    setup_logger(level=getattr(logging, args.log_level.upper()))

    # Install parser
    if args.install:
        try:
            import_parser(args.install)
            logger.info("Parser registered successfully.")

        except Exception as e:
            logger.error(f"Could not install parser: {e}")

        return

    # Uninstall parser(s)
    if args.uninstall:
        installed = list_installed_parsers()

        if not installed:
            logger.info("No custom parsers are installed.")
            return

        if args.uninstall == "*":
            for module_name, extensions in installed.items():
                for ext in extensions:
                    try:
                        remove_parser(ext)
                        logger.info(
                            f"Uninstalled parser '{module_name}' for extension '{ext}'"
                        )
                    except Exception as exc:
                        logger.error(
                            f"Failed to uninstall parser '{module_name}' for extension '{ext}': {exc}"
                        )
            return

        ext = args.uninstall
        found = False

        for module_name, extensions in installed.items():
            if ext in extensions:
                try:
                    remove_parser(ext)
                    logger.info(
                        f"Uninstalled parser '{module_name}' for extension '{ext}'"
                    )
                    found = True

                except Exception as e:
                    logger.error(
                        f"Failed to uninstall parser for extension '{ext}': {e}"
                    )
                break

        if not found:
            logger.error(f"No installed parser found for extension '{ext}'")

        return

    # List installed parsers
    if args.list_installed:
        installed = list_installed_parsers()

        if not installed:
            logger.info("No custom parsers installed.")
            return

        logger.info("Installed custom parsers:")
        for module_name, extensions in installed.items():
            logger.info(f"  {module_name}: {', '.join(extensions)}")
        return

    # Require input_dir for normal operation
    if not args.input_dir:
        parser.error(
            "input_dir is required unless installing, uninstalling, or listing parsers."
        )

    # Ignore patterns
    ignore_patterns = args.ignore.copy()
    merger_ignore_path: Path = args.merger_ignore

    if merger_ignore_path.exists():
        if not merger_ignore_path.is_file():
            parser.error(
                f"'{merger_ignore_path}' exists but is not a file."
            )

        logger.info("Found default ignore patterns file.")
        ignore_patterns.extend(
            read_merger_ignore_file(merger_ignore_path)
        )

    ignore_patterns = list(set(ignore_patterns))

    # Ensure output directory exists
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    tree = FileTree.from_path(args.input_dir, ignore_patterns)
    write_tree(tree, args.output_path)
    logger.info(f"Saved to {args.output_path}")


if __name__ == "__main__":
    main()
