class InvalidPlugin(Exception):
    def __init__(self, path: str, message: str):
        if not isinstance(path, str):
            raise TypeError("path must be a string")

        if not isinstance(message, str):
            raise TypeError("message must be a string")

        self.path = path
        self.message = message

        super().__init__(f"Plugin at '{path}' is invalid: {message}")


class PluginAlreadyInstalled(Exception):
    def __init__(self, path: str):
        if not isinstance(path, str):
            raise TypeError("path must be a string")

        self.path = path

        super().__init__(f"Plugin at '{path}' is already installed")


class UnknownIgnoreTemplate(ValueError):
    pass
