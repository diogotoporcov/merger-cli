class InvalidModule(Exception):
    def __init__(self, path: str, message: str):
        if not isinstance(path, str):
            raise TypeError("path must be a string")

        if not isinstance(message, str):
            raise TypeError("message must be a string")

        self.path = path
        self.message = message

        super().__init__(f"Module at '{path}' is invalid: {message}")


class ModuleAlreadyInstalled(Exception):
    def __init__(self, path: str):
        if not isinstance(path, str):
            raise TypeError("path must be a string")

        self.path = path

        super().__init__(f"Module at '{path}' is already installed")

