import argparse
import logging
from pathlib import Path

from .exceptions.exceptions import UnknownIgnoreTemplate
from .file_tree.exporters.tree_with_plain_text_exporter import TreeWithPlainTextExporter
from .utils.default_ignore_files import read_ignore_template, list_ignore_templates
from .file_tree.exporters.strategy import get_exporter_strategy, get_exporter_strategy_names
from .file_tree.tree import FileTree
from .logging.logger import setup_logger, logger
from .parsing.modules import install_module, uninstall_module, list_modules

from .utils.files import read_merger_ignore_file
from .utils.version import get_version


def main():
    # Args
    parser = argparse.ArgumentParser(
        description="Merge files from a directory into a structured output."
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        nargs="?",
        metavar="INPUT_DIR_PATH",
        help="Root directory to scan for files",
    )

    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=Path("."),
        metavar="OUTPUT_FILE_DIR_PATH",
        help="Path of the directory to save merged output (default: ./merger.txt)",
    )

    parser.add_argument(
        "-e",
        "--exporter",
        type=str,
        choices=get_exporter_strategy_names(),
        default=TreeWithPlainTextExporter.NAME,
        help=f"Output exporter strategy (default: {TreeWithPlainTextExporter.NAME})",
    )

    module_group = parser.add_mutually_exclusive_group()

    module_group.add_argument(
        "-i",
        "--install-module",
        type=Path,
        metavar="MODULE_PATH",
        help="Install a custom parser module",
    )

    module_group.add_argument(
        "-u",
        "--uninstall-module",
        metavar="MODULE_ID",
        help="Uninstall a module by ID (use '*' to remove all)",
    )

    module_group.add_argument(
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
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    parser.add_argument(
        "--ignore",
        nargs="+",
        metavar="GLOB_PATTERN",
        default=[],
        help="Glob-style patterns to ignore (e.g., '*.log', '__pycache__', './data/')",
    )

    parser.add_argument(
        "--merger-ignore",
        type=Path,
        default=Path("./merger.ignore"),
        metavar="IGNORE_PATTERNS_PATH",
        help="File containing glob-style patterns to ignore (default: ./merger.ignore)",
    )

    parser.add_argument(
        "-c",
        "--create-ignore",
        nargs="?",
        const="DEFAULT",
        default=None,
        choices=list_ignore_templates(),
        metavar="TEMPLATE",
        help=(
            "Create a merger.ignore file using a built-in template. "
            "If provided without a value, uses DEFAULT."
        ),
    )

    args = parser.parse_args()
    setup_logger(level=getattr(logging, args.log_level.upper()))

    # Create default merger.ignore file
    if args.create_ignore:
        target = Path("merger.ignore")

        if target.exists():
            parser.error("'merger.ignore' already exists.")

        try:
            body = read_ignore_template(args.create_ignore)

        except UnknownIgnoreTemplate as e:
            parser.error(str(e))

        target.write_text(body, encoding="utf-8")
        logger.info(
            f"Created 'merger.ignore' using '{args.create_ignore}' template."
        )
        return

    # Install module
    if args.install_module:
        try:
            install_module(args.install_module)
            logger.info("Module installed successfully.")

        except Exception as e:
            logger.error(f"Could not install module: {e}")

        return

    # Uninstall module(s)
    if args.uninstall_module:
        try:
            uninstall_module(args.uninstall_module)
            if args.uninstall_module == "*":
                logger.info("All modules uninstalled.")

            else:
                logger.info(f"Module '{args.uninstall_module}' uninstalled.")

        except Exception as e:
            logger.error(f"Could not uninstall module: {e}")

        return

    # List installed modules
    if args.list_modules:
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

    if merger_ignore_path:
        if not merger_ignore_path.exists():
            parser.error(f"'{merger_ignore_path}' does not exist.")

        if not merger_ignore_path.is_file():
            parser.error(f"'{merger_ignore_path}' exists but is not a file.")

        logger.info("Using merger ignore file.")
        ignore_patterns.extend(
            read_merger_ignore_file(merger_ignore_path)
        )

    ignore_patterns = list(set(ignore_patterns))
    ignore_patterns = [pattern.replace("\\", "/") for pattern in ignore_patterns]

    tree = FileTree.from_path(args.input_dir, ignore_patterns)
    exporter = get_exporter_strategy(args.exporter.upper())

    logger.info(f"Using {exporter.NAME} exporter.")

    output_filename = f"merger.{exporter.FILE_EXTENSION.removeprefix('.').lower()}"
    output_path = Path(args.output_path) / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    Path(output_path).write_bytes(
        exporter.export(tree)
    )

    logger.info(f"Saved to '{output_path.as_posix()}'.")


if __name__ == "__main__":
    main()
