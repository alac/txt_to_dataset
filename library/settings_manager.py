import tomli
import os
from typing import Any

THIS_FILES_FOLDER = os.path.dirname(os.path.realpath(__file__))
ROOT_FOLDER = os.path.join(THIS_FILES_FOLDER, "..")
DEFAULT_SETTINGS = os.path.join(ROOT_FOLDER, "settings.toml")


class SettingsManager:
    def __init__(self, toml_file_path):
        self.toml_file_path = toml_file_path
        self.settings = {}

    def load_settings(self):
        with open(self.toml_file_path, "rb") as f:
            self.settings = tomli.load(f)

    def get_setting(self, setting_name):
        # type: (str, Any) -> Any
        keys = setting_name.split(".")
        current_dict = self.settings
        for k in keys:
            if k not in current_dict:
                raise ValueError(f"setting {setting_name} not found in {current_dict.keys()}")
            current_dict = current_dict[k]
        return current_dict


settings = SettingsManager(DEFAULT_SETTINGS)
settings.load_settings()
