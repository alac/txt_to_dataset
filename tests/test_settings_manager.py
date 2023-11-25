import pytest

from library.settings_manager import search_nested_dict, SettingsManager


def test_search_nested_dict_simple():
    nested_dict = {"foo": {"bar": "baz"}}
    dotted_key = "foo.bar"
    result = search_nested_dict(nested_dict, dotted_key)
    assert result == "baz"


def test_search_nested_dict_multiple_levels():
    nested_dict = {"foo": {"bar": {"qux": "quux"}}}
    dotted_key = "foo.bar.qux"
    result = search_nested_dict(nested_dict, dotted_key)
    assert result == "quux"


def test_search_nested_dict_missing_key():
    nested_dict = {"foo": {"bar": "baz"}}
    dotted_key = "foo.qux"
    with pytest.raises(ValueError) as exc_info:
        search_nested_dict(nested_dict, dotted_key)
    assert "setting foo.qux not found in {" in str(exc_info.value)


def test_settings_manager_basic():
    settings_manager = SettingsManager()
    settings_manager._default_settings = {"foo": {"bar": "failure"}}
    settings_manager._user_settings = {"foo": {"bar": "baz"}}

    dotted_key = "foo.bar"
    result = settings_manager.get_setting(dotted_key)
    assert result == "baz"


def test_settings_manager_fallback():
    settings_manager = SettingsManager()
    settings_manager._default_settings = {"foo": {"bar": "baz"}}
    settings_manager._user_settings = {}

    dotted_key = "foo.bar"
    result = settings_manager.get_setting(dotted_key)
    assert result == "baz"
