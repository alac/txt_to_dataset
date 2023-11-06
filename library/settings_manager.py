import tomli
import os
import json
from typing import Any

THIS_FILES_FOLDER = os.path.dirname(os.path.realpath(__file__))
ROOT_FOLDER = os.path.join(THIS_FILES_FOLDER, "..")
DEFAULT_SETTINGS = os.path.join(ROOT_FOLDER, "settings.toml")
USER_SETTINGS = os.path.join(ROOT_FOLDER, "user.toml")


class SettingsManager:
    def __init__(self, defaults_file_path: str, user_file_path: str):
        self.defaults_file_path = defaults_file_path
        self.user_file_path = user_file_path
        self.default_settings = {}
        self.user_settings = {}

    def load_settings(self):
        with open(self.defaults_file_path, "rb") as f:
            self.default_settings = tomli.load(f)

        if os.path.exists(self.user_file_path):
            with open(self.user_file_path, "rb") as f:
                self.user_settings = tomli.load(f)

    def get_setting(self, setting_name: str) -> Any:
        try:
            result = search_nested_dict(self.user_settings, setting_name)
        except ValueError:
            result = search_nested_dict(self.default_settings, setting_name)
        return result


def search_nested_dict(nested_dict: dict, dotted_key: str) -> Any:
    keys = dotted_key.split(".")
    current_dict = nested_dict
    for k in keys:
        if k not in current_dict:
            raise ValueError(f"setting {dotted_key} not found in {json.dumps(nested_dict, indent=2)}")
        current_dict = current_dict[k]
    return current_dict


settings = SettingsManager(DEFAULT_SETTINGS, USER_SETTINGS)
settings.load_settings()
