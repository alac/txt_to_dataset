import tomli
import os
import json
from typing import Any, Optional

THIS_FILES_FOLDER = os.path.dirname(os.path.realpath(__file__))
ROOT_FOLDER = os.path.join(THIS_FILES_FOLDER, "..")
DEFAULT_SETTINGS = os.path.join(ROOT_FOLDER, "settings.toml")
USER_SETTINGS = os.path.join(ROOT_FOLDER, "user.toml")


class SettingsManager:
    def __init__(self):
        self.default_settings = {}
        self.user_settings = {}
        self.override_settings = None  # type: Optional[dict]

    def load_settings(self, defaults_file_path: str, user_file_path: Optional[str]):
        with open(defaults_file_path, "rb") as f:
            self.default_settings = tomli.load(f)

        if user_file_path and os.path.exists(user_file_path):
            with open(user_file_path, "rb") as f:
                self.user_settings = tomli.load(f)

    def override_settings(self, file_path):
        with open(file_path, "rb") as f:
            self.override_settings = tomli.load(f)

    def remove_override_settings(self):
        self.override_settings = None

    def get_setting(self, setting_name: str) -> Any:
        main_settings = self.user_settings
        if self.override_settings is not None:
            main_settings = self.override_settings

        try:
            result = search_nested_dict(main_settings, setting_name)
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


settings = SettingsManager()
settings.load_settings(DEFAULT_SETTINGS, USER_SETTINGS)
