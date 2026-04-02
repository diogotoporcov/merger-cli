import argparse
import sys
from pathlib import Path

from ..exceptions import UnknownIgnoreTemplate
from ..exporters.factory import get_exporter_strategy_names
from ..exporters.impl.tree_with_plain_text_exporter import NAME as TREE_PLAIN_TEXT_NAME
from ..exporters.registry import (
    install_exporter, uninstall_exporter, list_exporters, get_exporter_plugin_type
)
from ..logging import logger
from ..parsing.registry import (
    install_parser, uninstall_parser, list_parsers, get_parser_plugin_type
)
from ..utils.ignore_templates import read_ignore_template, list_ignore_templates
from ..utils.version import get_version


class LazyChoices:
    """
    A container for argparse choices that evaluates the list of choices 
    lazily only when needed (e.g., for validation or help generation).
    """
    def __init__(self, loader):
        self._loader = loader
        self._choices = None

    def _get_choices(self):
        if self._choices is None:
            self._choices = self._loader()
        return self._choices

    def __contains__(self, item):
        return item in self._get_choices()

    def __iter__(self):
        return iter(self._get_choices())

    def __len__(self):
        return len(self._get_choices())


class RichArgumentParser(argparse.ArgumentParser):
    """
    A custom argument parser that uses rich for help formatting 
    and the logger for reporting errors.
    """
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            try:
                from rich_argparse import RichHelpFormatter
                kwargs["formatter_class"] = RichHelpFormatter
            except ImportError:
                pass
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


def handle_plugin_list() -> None:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    
    parsers = list_parsers()
    exporters = list_exporters()

    if not parsers and not exporters:
        logger.info("No custom plugins installed.")
        return

    if parsers:
        table = Table(title="Installed Parser plugins")
        table.add_column("ID", style="cyan")
        table.add_column("Original Name", style="magenta")
        table.add_column("Extensions", style="green")

        for p in parsers:
            table.add_row(p.id, p.original_name, ", ".join(p.extensions))

        console.print(table)

    if parsers and exporters:
        print()

    if exporters:
        table = Table(title="Installed Exporter plugins")
        table.add_column("ID", style="cyan")
        table.add_column("Original Name", style="magenta")
        table.add_column("Extension", style="green")

        for p in exporters:
            ext = p.extensions[0] if p.extensions else "unknown"
            table.add_row(p.id, p.original_name, ext)

        console.print(table)


def handle_install(plugin_path: Path) -> None:
    try:
        if get_parser_plugin_type(plugin_path) == "parser":
            install_parser(plugin_path)
            logger.info(f"Parser plugin '{plugin_path}' installed successfully.")
            
        elif get_exporter_plugin_type(plugin_path) == "exporter":
            install_exporter(plugin_path)
            logger.info(f"Exporter plugin '{plugin_path}' installed successfully.")
            
        else:
            logger.error(f"Could not identify plugin type for '{plugin_path}'. Make sure it inherits from Parser or TreeExporter.")
        
    except Exception as e:
        logger.error(f"Could not install plugin '{plugin_path}': {e}")


def handle_uninstall(plugin_id: str, force: bool = False) -> None:
    from rich.prompt import Confirm
    try:
        if plugin_id == "*":
            parsers_count = len(list_parsers())
            exporters_count = len(list_exporters())
            
            if parsers_count == 0 and exporters_count == 0:
                logger.info("No custom plugins found to uninstall.")
                return
            
            if not force and not Confirm.ask(f"Are you sure you want to uninstall {parsers_count} parser(s) and {exporters_count} exporter(s)?"):
                logger.info("Uninstallation cancelled.")
                return
            
            uninstall_parser("*")
            uninstall_exporter("*")
            logger.info("All plugins uninstalled.")
            
        else:
            # Try both
            uninstalled = False
            try:
                uninstall_parser(plugin_id)
                uninstalled = True
                logger.info(f"Parser plugin '{plugin_id}' uninstalled.")
                
            except KeyError:
                pass
            
            try:
                uninstall_exporter(plugin_id)
                uninstalled = True
                logger.info(f"Exporter plugin '{plugin_id}' uninstalled.")
                
            except KeyError:
                pass
            
            if not uninstalled:
                logger.error(f"Plugin not found: {plugin_id}")
        
    except Exception as e:
        logger.error(f"Could not uninstall plugin: {e}")


def handle_update() -> None:
    """Updates the merger-cli tool itself."""
    logger.info("merger-cli is now distributed via standalone installers and GitHub releases.")
    logger.info("To update, please download the latest release from: ")
    logger.info("[bold magenta]https://github.com/diogotoporcov/merger-cli/releases[/bold magenta]")


def handle_plugin_update(force: bool = False) -> None:
    """Updates the dependencies for all installed custom plugins."""
    from rich.prompt import Confirm
    from ..utils.db import DatabaseManager
    from ..utils.plugin_loader import PluginManager
    from ..utils.uv import uv_install
    from ..utils.config import get_or_create_site_packages_dir

    db = DatabaseManager()
    plugins = db.list_plugins()
    if not plugins:
        logger.info("No custom plugins installed to check for dependency updates.")
        return

    all_requirements = set()
    for plugin in plugins:
        reqs = PluginManager.extract_requirements(Path(plugin.path))
        for req in reqs:
            all_requirements.add(req)
            db.add_plugin_dependency(plugin.id, req)

    if not all_requirements:
        logger.info("No dependencies found for any installed plugins.")
    else:
        logger.info(f"Updating dependencies: {', '.join(all_requirements)}")
        site_packages = get_or_create_site_packages_dir()
        try:
            uv_install(list(all_requirements), target=site_packages)
            logger.info("Plugin dependencies updated successfully.")
        except Exception as e:
            logger.error(f"Failed to update plugin dependencies: {e}")

    # Core dependencies update confirmation
    if not force:
        if not Confirm.ask("Do you wish to update core dependencies too?"):
            return
    
    logger.info("Updating core dependencies...")
    try:
        core_deps = ["pydantic", "rich", "pathspec", "packaging", "rich-argparse"]
        site_packages = get_or_create_site_packages_dir()
        uv_install(core_deps, target=site_packages)
        logger.info("Core dependencies updated in plugin environment.")

    except Exception as e:
        logger.error(f"Failed to update core dependencies: {e}")


def setup_argparse() -> RichArgumentParser:
    parser = RichArgumentParser(
        prog="merger",
        description="Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file."
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
        choices=LazyChoices(get_exporter_strategy_names),
        default=TREE_PLAIN_TEXT_NAME,
        help=f"Output exporter strategy (default: {TREE_PLAIN_TEXT_NAME})",
    )

    plugin_group = parser.add_mutually_exclusive_group()

    plugin_group.add_argument(
        "-i", "--install-plugin",
        type=Path,
        metavar="PATH",
        help="Install a custom plugin (parser or exporter)",
    )

    plugin_group.add_argument(
        "-u", "--uninstall-plugin",
        metavar="PLUGIN_ID",
        help="Uninstall a plugin by ID (use '*' to remove all plugins including parsers and exporters)",
    )

    plugin_group.add_argument(
        "-l", "--list-plugins",
        action="store_true",
        help="List all installed plugins",
    )

    plugin_group.add_argument(
        "--update",
        action="store_true",
        help="Update merger-cli and its dependencies to the latest version",
    )

    plugin_group.add_argument(
        "--update-plugins",
        action="store_true",
        help="Update all custom plugin dependencies",
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
        choices=LazyChoices(list_ignore_templates),
        help="Create a merger.ignore file using a built-in template.",
    )
    
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Confirm all prompts automatically (non-interactive mode)",
    )

    return parser
