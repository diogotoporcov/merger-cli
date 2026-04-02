import sys
from pathlib import Path


def main() -> None:
    import logging
    from .utils import setup_argparse
    from ..logging import setup_logger

    # Defer heavy imports
    from ..utils.config import get_or_create_site_packages_dir
    from ..utils.update import check_for_updates, finalize_update_check

    parser = setup_argparse()
    args = parser.parse_args()
    setup_logger(level=getattr(logging, args.log_level.upper()))
    from ..logging import logger

    # 1. Initialize injected packages path as the highest priority
    injected_path = get_or_create_site_packages_dir()
    if injected_path.exists() and str(injected_path) not in sys.path:
        sys.path.insert(0, str(injected_path))

    check_for_updates()

    try:
        if args.create_ignore:
            from .utils import handle_ignore_creation
            handle_ignore_creation(args.create_ignore)
            return

        if args.install_plugin:
            from .utils import handle_install
            handle_install(args.install_plugin)
            return

        if args.uninstall_plugin:
            from .utils import handle_uninstall
            handle_uninstall(args.uninstall_plugin, force=args.yes)
            return

        if args.update:
            from .utils import handle_update
            handle_update()
            return

        if args.update_plugins:
            from .utils import handle_plugin_update
            handle_plugin_update(force=args.yes)
            return

        if args.list_plugins:
            from .utils import handle_plugin_list
            handle_plugin_list()
            return

        if not args.input_dir:
            parser.error("input_dir is required for merging.")

        ignore_patterns = args.ignore.copy()

        from ..utils.files import read_merger_ignore_file
        if args.merger_ignore.exists():
            logger.info(f"Using ignore file: {args.merger_ignore}")
            ignore_patterns.extend(read_merger_ignore_file(args.merger_ignore))

        else:
            from ..utils.ignore_templates import list_ignore_templates
            templates = ", ".join(list_ignore_templates())
            parser.error(
                f"Ignore file '{args.merger_ignore}' is required.\n"
                f"You can create one using 'merger -c [TEMPLATE]'.\n"
                f"Available templates: {templates}"
            )

        # Normalize and deduplicate ignore patterns to use consistent forward slashes.
        ignore_patterns = list(set(pattern.replace("\\", "/") for pattern in ignore_patterns))

        from ..utils.magic import check_libmagic_availability
        check_libmagic_availability()

        from ..file_tree.scanner import FileTreeScanner
        from ..exporters.factory import get_exporter_strategy
        tree = FileTreeScanner.scan(args.input_dir, ignore_patterns)
        exporter_info = get_exporter_strategy(args.exporter)
        logger.info(f"Using {exporter_info.name} exporter.")

        output_ext = exporter_info.file_extension
        if output_ext.startswith("."):
            output_ext = output_ext[1:]
        output_ext = output_ext.lower()
        output_path = Path(args.output_path)
        if output_path.is_dir():
            output_path = output_path / f"merger.{output_ext}"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(exporter_info.cls.export(tree))
        logger.info(f"Saved to '{output_path.as_posix()}'.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=args.log_level == "DEBUG")

    finally:
        finalize_update_check()


if __name__ == "__main__":
    main()
