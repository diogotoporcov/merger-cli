import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .exceptions import UnknownIgnoreTemplate
from .exporters.factory import get_exporter_strategy, get_exporter_strategy_names
from .exporters.registry import install_exporter, uninstall_exporter, list_exporters, get_exporter_module_type
from .exporters.impl.tree_with_plain_text_exporter import TreeWithPlainTextExporter
from .file_tree.tree import FileTree
from .logging import setup_logger, logger
from .parsing.registry import install_parser, uninstall_parser, list_parsers, get_parser_module_type
from .utils.files import read_merger_ignore_file
from .utils.ignore_templates import read_ignore_template, list_ignore_templates
from .utils.version import get_version

console = Console()


def handle_ignore_creation(template: str) -> None:
    target = Path("merger.ignore")
    if target.exists():
        logger.error("'merger.ignore' already exists.")
        return

    try:
        body = read_ignore_template(template)
        target.write_text(body, encoding="utf-8")
        logger.info(f"Created 'merger.ignore' using '{template}' template.")
        
    except UnknownIgnoreTemplate as e:
        logger.error(str(e))


def handle_module_list() -> None:
    parsers = list_parsers()
    exporters = list_exporters()

    if not parsers and not exporters:
        logger.info("No custom modules installed.")
        return

    if parsers:
        table = Table(title="Installed Parser Modules")
        table.add_column("ID", style="cyan")
        table.add_column("Original Name", style="magenta")
        table.add_column("Extensions", style="green")

        for module_id, meta in parsers.items():
            table.add_row(module_id, meta.original_name, ", ".join(meta.extensions))

        console.print(table)

    if parsers and exporters:
        print()

    if exporters:
        table = Table(title="Installed Exporter Modules")
        table.add_column("ID", style="cyan")
        table.add_column("Original Name", style="magenta")
        table.add_column("Extension", style="green")

        for exporter_id, meta in exporters.items():
            ext = meta.extensions[0] if meta.extensions else "unknown"
            table.add_row(exporter_id, meta.original_name, ext)

        console.print(table)


def main():
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
        help="Path of the directory to save merged output (default: .)",
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
        "-i", "--install",
        type=Path,
        metavar="PATH",
        help="Install a custom module (parser or exporter)",
    )

    module_group.add_argument(
        "-u", "--uninstall",
        metavar="MODULE_ID",
        help="Uninstall a module by ID (use '*' to remove all)",
    )

    module_group.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all installed modules",
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
        help="Glob-style patterns to ignore",
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
        help="Create a merger.ignore file using a built-in template.",
    )

    args = parser.parse_args()
    setup_logger(level=getattr(logging, args.log_level.upper()))

    if args.create_ignore:
        handle_ignore_creation(args.create_ignore)
        return

    if args.install:
        try:
            if get_parser_module_type(args.install) == "parser":
                install_parser(args.install)
                logger.info(f"Parser module '{args.install}' installed successfully.")
                
            elif get_exporter_module_type(args.install) == "exporter":
                install_exporter(args.install)
                logger.info(f"Exporter module '{args.install}' installed successfully.")
                
            else:
                logger.error(f"Could not identify module type for '{args.install}'. Make sure it inherits from Parser or TreeExporter.")
            
        except Exception as e:
            logger.error(f"Could not install module '{args.install}': {e}")
            
        return

    if args.uninstall:
        try:
            if args.uninstall == "*":
                uninstall_parser("*")
                uninstall_exporter("*")
                logger.info("All modules uninstalled.")
                
            else:
                # Try both
                uninstalled = False
                try:
                    uninstall_parser(args.uninstall)
                    uninstalled = True
                    logger.info(f"Parser module '{args.uninstall}' uninstalled.")
                    
                except KeyError:
                    pass
                
                try:
                    uninstall_exporter(args.uninstall)
                    uninstalled = True
                    logger.info(f"Exporter module '{args.uninstall}' uninstalled.")
                    
                except KeyError:
                    pass
                
                if not uninstalled:
                    logger.error(f"Module not found: {args.uninstall}")
            
        except Exception as e:
            logger.error(f"Could not uninstall module: {e}")
            
        return

    if args.list:
        handle_module_list()
        return

    if not args.input_dir:
        parser.error("input_dir is required for merging.")

    if not args.merger_ignore.exists():
        templates = ", ".join(list_ignore_templates())
        parser.error(
            f"Ignore file '{args.merger_ignore}' is required.\n"
            f"You can create one using 'merger -c [TEMPLATE]'.\n"
            f"Available templates: {templates}"
        )

    ignore_patterns = args.ignore.copy()
    logger.info(f"Using ignore file: {args.merger_ignore}")
    ignore_patterns.extend(read_merger_ignore_file(args.merger_ignore))

    # Normalize and deduplicate ignore patterns to use consistent forward slashes.
    ignore_patterns = list(set(pattern.replace("\\", "/") for pattern in ignore_patterns))

    try:
        tree = FileTree.from_path(args.input_dir, ignore_patterns)
        exporter_cls = get_exporter_strategy(args.exporter)
        logger.info(f"Using {exporter_cls.NAME} exporter.")

        output_ext = exporter_cls.FILE_EXTENSION
        if output_ext.startswith("."):
            output_ext = output_ext[1:]
        output_ext = output_ext.lower()
        output_path = Path(args.output_path)
        if output_path.is_dir():
            output_path = output_path / f"merger.{output_ext}"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(exporter_cls.export(tree))
        logger.info(f"Saved to '{output_path.as_posix()}'.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=args.log_level == "DEBUG")


if __name__ == "__main__":
    main()
