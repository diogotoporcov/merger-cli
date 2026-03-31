import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich_argparse import RichHelpFormatter

from ..exceptions import UnknownIgnoreTemplate
from ..exporters.factory import get_exporter_strategy_names
from ..exporters.registry import (
    install_exporter, uninstall_exporter, list_exporters, get_exporter_module_type
)
from ..exporters.impl.tree_with_plain_text_exporter import TreeWithPlainTextExporter, NAME as TREE_PLAIN_TEXT_NAME
from ..logging import logger
from ..parsing.registry import (
    install_parser, uninstall_parser, list_parsers, get_parser_module_type
)
from ..utils.ignore_templates import read_ignore_template, list_ignore_templates
from ..utils.version import get_version

console = Console()


class RichArgumentParser(argparse.ArgumentParser):
    """
    A custom argument parser that uses rich for help formatting 
    and the logger for reporting errors.
    """
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = RichHelpFormatter
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        logger.error(message)
        sys.exit(2)


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


def handle_install(module_path: Path) -> None:
    try:
        if get_parser_module_type(module_path) == "parser":
            install_parser(module_path)
            logger.info(f"Parser module '{module_path}' installed successfully.")
            
        elif get_exporter_module_type(module_path) == "exporter":
            install_exporter(module_path)
            logger.info(f"Exporter module '{module_path}' installed successfully.")
            
        else:
            logger.error(f"Could not identify module type for '{module_path}'. Make sure it inherits from Parser or TreeExporter.")
        
    except Exception as e:
        logger.error(f"Could not install module '{module_path}': {e}")


def handle_uninstall(module_id: str) -> None:
    try:
        if module_id == "*":
            parsers_count = len(list_parsers())
            exporters_count = len(list_exporters())
            
            if parsers_count == 0 and exporters_count == 0:
                logger.info("No custom modules found to uninstall.")
                return
            
            if not Confirm.ask(f"Are you sure you want to uninstall {parsers_count} parser(s) and {exporters_count} exporter(s)?"):
                logger.info("Uninstallation cancelled.")
                return
            
            uninstall_parser("*")
            uninstall_exporter("*")
            logger.info("All modules uninstalled.")
            
        else:
            # Try both
            uninstalled = False
            try:
                uninstall_parser(module_id)
                uninstalled = True
                logger.info(f"Parser module '{module_id}' uninstalled.")
                
            except KeyError:
                pass
            
            try:
                uninstall_exporter(module_id)
                uninstalled = True
                logger.info(f"Exporter module '{module_id}' uninstalled.")
                
            except KeyError:
                pass
            
            if not uninstalled:
                logger.error(f"Module not found: {module_id}")
        
    except Exception as e:
        logger.error(f"Could not uninstall module: {e}")


def setup_argparse() -> RichArgumentParser:
    parser = RichArgumentParser(
        prog="merger",
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
        type=lambda s: str(s).upper(),
        choices=get_exporter_strategy_names(),
        default=TREE_PLAIN_TEXT_NAME,
        help=f"Output exporter strategy (default: {TREE_PLAIN_TEXT_NAME})",
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
        help="Uninstall a module by ID (use '*' to remove all modules including parsers and exporters)",
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
        type=lambda s: str(s).upper(),
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
        type=lambda s: str(s).upper(),
        choices=list_ignore_templates(),
        help="Create a merger.ignore file using a built-in template.",
    )
    
    return parser
