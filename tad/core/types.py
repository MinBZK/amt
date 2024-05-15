from typing import Literal

EnvironmentType = Literal["local", "staging", "production"]
LoggingLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DatabaseSchemaType = Literal["sqlite", "postgresql", "mysql", "oracle"]
