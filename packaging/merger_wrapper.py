from merger_cli.utils.config import set_distribution_type
set_distribution_type("standalone")

from merger_cli.cli.main import main

if __name__ == "__main__":
    main()
