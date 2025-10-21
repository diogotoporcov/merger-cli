import argparse
import logging
from pathlib import Path

from .utils import parse_escape_chars
from .files import merge, read_ignore_file
from .logger import logger, setup_logger
from .registry import register_reader, unregister_reader, list_readers, load_installed_readers, load_custom_readers


def main():
    parser = argparse.ArgumentParser(
        description="Merge readable files in a directory with support for ignore patterns and custom file readers."
    )

    # Required positional args
    parser.add_argument("input_dir", type=Path, nargs="?", help="Root directory to scan for files")
    parser.add_argument("output_file", type=Path, nargs="?",
                        help="File to save merged output (default: <input_dir>/merger.txt)")

    # Reader management
    parser.add_argument("-i", "--install", nargs=2, metavar=("EXT", "MODULE_PATH"),
                        help="Install a custom reader for a given extension (e.g., .pdf)")

    parser.add_argument("-u", "--uninstall", metavar="EXT",
                        help="Uninstall a custom reader by extension (use '*' to remove all)")

    parser.add_argument("--list-installed", action="store_true",
                        help="List all installed custom readers")

    # Logging
    parser.add_argument(
        "-l", "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )

    # Ignore logic
    parser.add_argument("--ignore", nargs="*", default=[],
                        help="Glob-style patterns to ignore (e.g., '*.log', '__pycache__')")

    parser.add_argument(
        "-f", "--ignore-file", type=Path,
        help="File containing glob-style patterns to ignore (default: <input_dir>/merger.ignore)")

    # Custom reader overrides
    parser.add_argument("--overrides", type=Path,
                        help="Path to Python module with `validators` and `readers` dictionaries for custom overrides")

    parser.add_argument("--empty", action="store_true", default=False,
                        help="Include empty files in the merged output")

    parser.add_argument("--prefix", type=str, default="<<FILE_START: {path}>>\n",
                        help="Format string for file start marker (set empty string to disable)")

    parser.add_argument("--suffix", type=str, default="\n<<FILE_END: {path}>>\n\n",
                        help="Format string for file end marker (set empty string to disable)")

    # Tree
    parser.add_argument(
        "--no-tree",
        action="store_true",
        default=False,
        help="Do not include the generated directory tree in the output file"
    )

    # CLI Logic
    args = parser.parse_args()

    setup_logger(level=getattr(logging, args.log_level.upper()))

    if args.install:
        ext, path = args.install
        register_reader(ext, path)
        logger.info(f"Installed reader for '{ext}' from '{path}'")
        return

    if args.uninstall:
        if args.uninstall == "*":
            installed = list_readers()
            if not installed:
                logger.info("No custom readers to uninstall.")
            else:
                for ext in list(installed.keys()):
                    unregister_reader(ext)
                    logger.info(f"Uninstalled reader for '{ext}'")
        else:
            unregister_reader(args.uninstall)
            logger.info(f"Uninstalled reader for '{args.uninstall}'")
        return

    if args.list_installed:
        installed = list_readers()
        if not installed:
            logger.info("No custom readers installed.")
        else:
            logger.info("Installed Custom Readers:")
            for ext, mod_path in installed.items():
                logger.info(f"  {ext}: {mod_path}")
        return

    # Handle default output file
    if not args.input_dir:
        parser.error("input_dir is required unless installing/uninstalling/listing readers.")

    if not args.output_file:
        args.output_file = args.input_dir / "merger.txt"

    if not args.ignore_file and args.input_dir:
        default_ignore = args.input_dir / "merger.ignore"
        if default_ignore.exists():
            args.ignore_file = default_ignore
            logger.info("Found default ignore file 'merger.ignore' in input directory. Using it for ignore patterns.")

    ignore_patterns = args.ignore.copy()
    if args.ignore_file:
        ignore_patterns.extend(read_ignore_file(args.ignore_file))

    readers, validators = load_installed_readers()

    if args.overrides:
        r, v = load_custom_readers(args.overrides)
        readers.update(r)
        validators.update(v)

    merge(
        dir_path=args.input_dir,
        ignore_patterns=ignore_patterns,
        output_path=args.output_file,
        validation_func_override=validators,
        read_func_override=readers,
        write_if_empty=args.empty,
        prefix_format=parse_escape_chars(args.prefix),
        suffix_format=parse_escape_chars(args.suffix),
        include_tree=not args.no_tree
    )

    logger.info(f"Saved to {args.output_file}")


if __name__ == "__main__":
    main()
