import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union


class Reader(ABC):
    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a stateless strategy and must not be instantiated")

    @classmethod
    @abstractmethod
    def validate(
            cls,
            file_chunk: Union[bytes, bytearray],
            *,
            file_path: Optional[Path] = None,
            logger: Optional[logging.Logger] = None
    ) -> bool:
        pass

    @classmethod
    @abstractmethod
    def get_content(
            cls,
            file_bytes: Union[bytes, bytearray],
            *,
            file_path: Optional[Path] = None,
            logger: Optional[logging.Logger] = None
    ) -> str:
        pass
