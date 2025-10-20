from pathlib import Path
from typing import Callable, Dict, Optional, List

import chardet

from .filtering import filter_files_by_patterns
from .tree import generate_tree_visualizer
from .logger import logger


def is_text_file(
    file_path: Path,
    chunk_size: int = 1024,
    *,
    validation_func_override: Optional[Dict[str, Callable[[Path], bool]]] = None,
    min_encoding_detection_confidence: float = 0.8
) -> bool:
    logger.debug(f"Checking if file is text: {file_path}")
    try:
        if validation_func_override and callable(validation_override_func := validation_func_override.get(file_path.suffix)):
            result = validation_override_func(file_path)
            logger.debug(f"Custom validator used for {file_path.suffix}: {result}")
            return result

        with open(file_path, "rb") as file:
            chunk = file.read(chunk_size)

        result = chardet.detect(chunk)
        encoding = result.get("encoding")
        confidence = result.get("confidence", 0)
        logger.debug(f"Detected encoding for {file_path}: {encoding} (confidence: {confidence})")

        if not encoding or confidence < min_encoding_detection_confidence:
            encoding = "utf-8"
            logger.debug(f"Low confidence for {file_path}. Falling back to utf-8")

        chunk.decode(encoding)
        return True

    except Exception as e:
        logger.error(f"Failed to decode {file_path}: {e}")
        return False


def append_content(
    root: Path,
    file_path: Path,
    output_path: Path,
    *,
    prefix: Optional[str] = "<<FILE_START: {path}>>\n",
    suffix: Optional[str] = "\n<<FILE_END: {path}>>\n\n",
    read_func_override: Optional[Dict[str, Callable[[Path], str]]] = None,
    write_if_empty: bool = False
) -> None:
    relative_path = ".\\" + str(file_path.relative_to(root))
    formatted_prefix = prefix.format(path=relative_path) if prefix else ""
    formatted_suffix = suffix.format(path=relative_path) if suffix else ""

    try:
        if read_func_override and callable(read_override_func := read_func_override.get(file_path.suffix)):
            content = read_override_func(file_path)
            logger.debug(f"Used custom reader for {file_path}")
        else:
            content = file_path.read_text(encoding="utf-8")
            logger.debug(f"Read text from {file_path} using utf-8")

        if not write_if_empty and not content:
            logger.debug(f"Skipping empty file: {file_path}")
            return

        with output_path.open("a", encoding="utf-8") as f:
            f.write(formatted_prefix + content + formatted_suffix)
            logger.debug(f"Merged: {file_path}")

    except Exception as e:
        logger.error(f"Failed to append content from {file_path}: {e}")


def merge(
    dir_path: Path,
    ignore_patterns: List[str],
    output_path: Path,
    *,
    read_func_override: Optional[Dict[str, Callable[[Path], str]]] = None,
    validation_func_override: Optional[Dict[str, Callable[[Path], bool]]] = None,
    min_encoding_detection_confidence: float = 0.8,
    write_if_empty: bool = False,
    prefix_format: Optional[str] = "<<FILE_START: {path}>>\n",
    suffix_format: Optional[str] = "\n<<FILE_END: {path}>>\n\n",
    include_tree: bool = True
) -> None:
    logger.debug(f"Starting merge from: {dir_path}")
    paths = filter_files_by_patterns(dir_path, ignore_patterns, True)
    paths = [path for path in paths if path.resolve() != output_path.resolve()]
    logger.debug(f"Filtered paths: {len(paths)} files to process")

    if include_tree:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                tree = generate_tree_visualizer(dir_path, paths)
                f.write(f"{tree}\n")
                logger.debug(f"Directory tree written to {output_path}")

        except Exception as e:
            logger.error(f"Failed to write tree header to {output_path}: {e}")
            return

    else:
        output_path.write_text("", encoding="utf-8")

    paths = [path for path in paths if not path.is_dir()]

    for path in paths:
        if not is_text_file(
            path,
            validation_func_override=validation_func_override,
            min_encoding_detection_confidence=min_encoding_detection_confidence
        ):
            logger.debug(f"Skipped non-text file: {path}")
            continue

        append_content(
            root=dir_path,
            file_path=path,
            output_path=output_path,
            prefix=prefix_format,
            suffix=suffix_format,
            read_func_override=read_func_override,
            write_if_empty=write_if_empty
        )


def read_ignore_file(file_path: Path) -> list[str]:
    if not file_path.is_file():
        logger.error(f"Ignore file not found: {file_path}")
        raise FileNotFoundError(f"Ignore file not found: {file_path}")

    logger.debug(f"Reading ignore patterns from: {file_path}")
    return [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
