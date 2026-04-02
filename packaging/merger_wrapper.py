import warnings
import sys

# Suppress experimental warnings from pydantic and others
try:
    from pydantic import PydanticExperimentalWarning
    warnings.filterwarnings("ignore", category=PydanticExperimentalWarning)
except ImportError:
    pass

# Suppress distutils warning (setuptools replacing distutils)
warnings.filterwarnings("ignore", "Setuptools is replacing distutils", category=UserWarning)

from merger_cli.cli.main import main

if __name__ == "__main__":
    main()
