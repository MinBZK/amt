class TADError(Exception):
    pass


class SettingsError(TADError):
    def __init__(self, message: str = "Settings error"):
        self.message: str = message
        exception_name: str = self.__class__.__name__
        super().__init__(f"{exception_name}: {self.message}")


class RepositoryError(TADError):
    def __init__(self, message: str = "Repository error"):
        self.message: str = message
        exception_name: str = self.__class__.__name__
        super().__init__(f"{exception_name}: {self.message}")
