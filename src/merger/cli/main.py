import logging
from pathlib import Path

from ..exporters.factory import get_exporter_strategy
from ..file_tree.tree import FileTree
from ..logging import setup_logger, logger
from ..utils.files import read_merger_ignore_file
from ..utils.update import check_for_updates, finalize_update_check
from .utils import (
    handle_ignore_creation,
    handle_module_list,
    handle_install,
    handle_uninstall,
    setup_argparse
)
from ..utils.ignore_templates import list_ignore_templates


def main() -> None:
    parser = setup_argparse()
    args = parser.parse_args()
    setup_logger(level=getattr(logging, args.log_level.upper()))

    check_for_updates()

    try:
        if args.create_ignore:
            handle_ignore_creation(args.create_ignore)
            return

        if args.install:
            handle_install(args.install)
            return

        if args.uninstall:
            handle_uninstall(args.uninstall)
            return

        if args.list:
            handle_module_list()
            return

        if not args.input_dir:
            parser.error("input_dir is required for merging.")

        ignore_patterns = args.ignore.copy()

        if args.merger_ignore.exists():
            logger.info(f"Using ignore file: {args.merger_ignore}")
            ignore_patterns.extend(read_merger_ignore_file(args.merger_ignore))
        else:
            templates = ", ".join(list_ignore_templates())
            parser.error(
                f"Ignore file '{args.merger_ignore}' is required.\n"
                f"You can create one using 'merger -c [TEMPLATE]'.\n"
                f"Available templates: {templates}"
            )

        # Normalize and deduplicate ignore patterns to use consistent forward slashes.
        ignore_patterns = list(set(pattern.replace("\\", "/") for pattern in ignore_patterns))

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
    finally:
        finalize_update_check()


if __name__ == "__main__":
    main()
