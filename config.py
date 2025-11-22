import os
from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    GUEST = "guest"


class DatabaseConfig:
    SERVER = "localhost\\SQLEXPRESS"
    DATABASE = "LearnEasy"

    ADMIN_CONNECTION_STRING = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
    )

    @staticmethod
    def get_connection_string(username: str = None, password: str = None, use_trusted: bool = True):

        if use_trusted:
            return DatabaseConfig.ADMIN_CONNECTION_STRING
        else:
            return (
                f'DRIVER={{SQL Server}};'
                f'SERVER={DatabaseConfig.SERVER};'
                f'DATABASE={DatabaseConfig.DATABASE};'
                f'UID={username};'
                f'PWD={password};'
            )


class AppConfig:

    APP_NAME = "Learn Easy"
    VERSION = "2.0.0"

    SESSION_TIMEOUT_MINUTES = 30

    DEFAULT_POPUP_INTERVAL_MINUTES = 5

    LOGO_PATH = "logo.jpg"