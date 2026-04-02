import argparse
import logging
import os
import shutil
import subprocess
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
from ..utils.config import get_or_create_site_packages_dir

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


def handle_uninstall(module_id: str, force: bool = False) -> None:
    try:
        if module_id == "*":
            parsers_count = len(list_parsers())
            exporters_count = len(list_exporters())
            
            if parsers_count == 0 and exporters_count == 0:
                logger.info("No custom modules found to uninstall.")
                return
            
            if not force and not Confirm.ask(f"Are you sure you want to uninstall {parsers_count} parser(s) and {exporters_count} exporter(s)?"):
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


def handle_inject(packages: list = None, requirements_file: Path = None) -> None:
    """Installs external packages into the merger-cli site-packages directory."""
    site_packages = get_or_create_site_packages_dir()

    if getattr(sys, "frozen", False):
        try:
            # For bundled apps, we try to use the internal pip
            # Using pip._internal.cli.main is generally more robust for modern pip
            try:
                from pip._internal.cli.main import main as pip_main
            except ImportError:
                import pip
                pip_main = getattr(pip, "main", None)

            if not pip_main:
                logger.error("Could not find internal 'pip' module in the bundle.")
                return

            cmd_args = ["install", "--target", str(site_packages), "--upgrade", "--no-input"]
            if requirements_file:
                if not requirements_file.exists():
                    logger.error(f"Requirements file not found: {requirements_file}")
                    return
                cmd_args.extend(["-r", str(requirements_file)])
            if packages:
                cmd_args.extend(packages)

            logger.info(f"Injecting packages into '{site_packages.as_posix()}' using internal pip...")
            
            # We must ensure pip doesn't try to use a non-existent python executable
            # for subprocesses if possible, or we just hope it works for simple packages.
            # Some pip versions/operations require a real python.exe.
            exit_code = pip_main(cmd_args)
            if exit_code == 0:
                logger.info("Successfully injected packages.")
            else:
                logger.error(f"Pip injection failed with exit code {exit_code}.")
            return

        except Exception as e:
            logger.error(f"Failed to inject packages using internal pip: {e}")
            return

    # We use sys.executable to ensure we use the same Python interpreter as the caller
    cmd = [sys.executable, "-m", "pip", "install", "--target", str(site_packages), "--upgrade"]

    if requirements_file:
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return
        cmd.extend(["-r", str(requirements_file)])

    if packages:
        cmd.extend(packages)

    logger.info(f"Injecting packages into '{site_packages.as_posix()}'...")
    try:
        # Note: --no-input is used for non-interactive professional installs
        subprocess.check_call(cmd + ["--no-input"])
        logger.info("Successfully injected packages.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to inject packages. Ensure 'pip' is available in the bundle. Error: {e}")


def handle_purge_packages(force: bool = False) -> None:
    """Removes all injected packages while keeping the core merger dependencies intact."""
    site_packages = get_or_create_site_packages_dir()
    if not site_packages.exists() or not any(site_packages.iterdir()):
        logger.info("No injected packages found to purge.")
        return

    if not force and not Confirm.ask(f"Are you sure you want to purge [bold red]ALL[/bold red] injected packages in '{site_packages.as_posix()}'?"):
        logger.info("Purge cancelled.")
        return

    try:
        shutil.rmtree(site_packages)
        site_packages.mkdir(parents=True, exist_ok=True)
        logger.info("All injected packages have been purged.")
    except Exception as e:
        logger.error(f"Could not purge packages: {e}")


def handle_update() -> None:
    """Updates the merger-cli tool itself."""
    if getattr(sys, "frozen", False):
        logger.info("You are using a standalone binary version of merger-cli.")
        logger.info("To update, please download the latest release from: ")
        logger.info("[bold magenta]https://github.com/diogotoporcov/merger-cli/releases[/bold magenta]")
        return

    # Check if we are in a virtualenv/pip environment
    logger.info("Attempting to update merger-cli via pip...")
    try:
        # Check if pipx is used (common for global CLI tools)
        if os.environ.get("PIPX_BIN_DIR") or "pipx" in sys.executable:
            logger.info("It seems you are using pipx. Trying 'pipx upgrade merger-cli'...")
            try:
                subprocess.run(["pipx", "upgrade", "merger-cli"], check=True)
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("pipx upgrade failed or pipx not found. Falling back to pip...")

        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "merger-cli"]
        subprocess.check_call(cmd + ["--no-input"])
        logger.info("Update successful.")
    except Exception as e:
        logger.error(f"Failed to update merger-cli: {e}")


def handle_update_injected() -> None:
    """Updates all injected packages in the site-packages directory."""
    site_packages = get_or_create_site_packages_dir()
    if not site_packages.exists() or not any(site_packages.iterdir()):
        logger.info("No injected packages found to update.")
        return

    # Find all packages in the site-packages directory using importlib.metadata if available
    packages = []
    try:
        from importlib.metadata import distributions
        dists = list(distributions(path=[str(site_packages)]))
        for dist in dists:
            # metadata['Name'] or dist.name (depending on version)
            name = getattr(dist, 'name', None)
            if not name and hasattr(dist, 'metadata'):
                name = dist.metadata.get('Name')

            if name and name.lower() != "merger-cli":  # Should not happen, but for safety
                packages.append(name)
    except Exception as e:
        logger.debug(f"Metadata lookup failed: {e}. Falling back to directory scan.")
        # Fallback to simple directory listing
        for path in site_packages.iterdir():
            if path.is_dir() and path.suffix == ".dist-info":
                # name-version.dist-info
                name = path.stem.split("-")[0]
                if name:
                    packages.append(name)

    # Deduplicate
    packages = list(set(packages))

    if not packages:
        logger.info("Could not identify any injected packages to update.")
        return

    logger.info(f"Updating {len(packages)} injected package(s): {', '.join(packages)}...")
    handle_inject(packages=packages)


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

    module_group.add_argument(
        "--inject",
        nargs="+",
        metavar="PACKAGE",
        help="Inject Python packages (e.g. 'pymupdf' or 'pydantic>=2.0'). Wrap requirements with quotes if they contain special characters.",
    )

    module_group.add_argument(
        "--inject-package",
        action="store_true",
        help="Inject packages from a requirements file (requires -r)",
    )

    module_group.add_argument(
        "--purge-packages",
        action="store_true",
        help="Remove all injected packages and their dependencies",
    )

    module_group.add_argument(
        "--update",
        action="store_true",
        help="Update merger-cli and its dependencies to the latest version",
    )

    module_group.add_argument(
        "--update-injected",
        action="store_true",
        help="Update all injected packages to their latest versions",
    )

    parser.add_argument(
        "-r",
        "--requirements",
        type=Path,
        metavar="FILE",
        help="Path to requirements.txt for --inject-package",
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
    
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Confirm all prompts automatically (non-interactive mode)",
    )

    return parser
