import io
from confluence_poster.config_wizard import config_dialog
from pathlib import Path
from typer.testing import CliRunner
from tomlkit import parse
import pytest
from typing import List

pytestmark = pytest.mark.online

runner = CliRunner()


def setup_input(monkeypatch, cli_input: List[str]):
    """Macro to monkeypatch th"""
    monkeypatch.setattr('sys.stdin', io.StringIO("\n".join(cli_input) + "\n"))


@pytest.mark.parametrize('save_agree', [True, False, None],
                         ids=['User explicitly agrees to save file',
                              'User hits enter to save file - the default choice',
                              'User refuses to save the file'])
def test_single_dialog_new_config(tmp_path, monkeypatch, save_agree):
    """Tests single run of config_dialog by populating a blank file"""
    path: Path = tmp_path / 'config.toml'
    # File will be created as a result of the test
    file_created = save_agree or save_agree is None

    if save_agree:
        save_agree = "Y"
    elif save_agree is None:
        save_agree = ''
    else:
        save_agree = 'N'

    # The monkey patched test cli_input. Should be the same length as the list of params fed to config_dialog later
    # Note: click provides validations for confirmation prompts, no need to test for garbage cli_input
    test_input = ["author name", 'https://confluence.local', 'page title', save_agree]
    setup_input(monkeypatch, test_input)
    #monkeypatch.setattr('sys.stdin', io.StringIO("\n".join(test_input) + "\n"))

    # In this scenario file should be created when and only when the function returned true
    assert config_dialog(Path(path), ['author', 'auth.url', 'pages.page1.page_title']) == path.exists()
    if file_created:
        assert path.read_text() == """author = "author name"

[auth]
url = "https://confluence.local"

[pages]
[pages.page1]
page_title = "page title"
"""


def test_dialog_converts_filename_to_path(tmp_path, monkeypatch):
    """Makes sure the dialog accepts both Path and strings for config file"""
    path_as_path: Path = tmp_path / 'config_path.toml'
    path_as_string: str = str(tmp_path / 'config_string.toml')

    # In this scenario file should be created when and only when the function returned true
    for tested_type in [path_as_path, path_as_string]:
        # Taken from previous test
        test_input = ["author name", 'https://confluence.local', 'page title', "Y"]
        setup_input(monkeypatch, test_input)
        assert config_dialog(tested_type, ['author', 'auth.url', 'pages.page1.page_title'])
        assert Path(tested_type).exists()


# The underlying function is fully tested in unit tests, just need to test the UI wrapper around it
@pytest.mark.parametrize('user_agrees_to_overwrite,mode', [(True, 'update'), (True, 'insert'), (False, 'insert')],
                         ids=["User updates a key in existing config",
                              "User adds a key to existing config",
                              "User decides not to overwrite the file"])
def test_single_dialog_existing_file(mode, user_agrees_to_overwrite, tmp_path, monkeypatch):
    config: Path = tmp_path / 'config.toml'
    config_text = """update_node = 'original_value'
    
    [parent]
    parent_update_node = 'parent_original_value'"""
    config.write_text(config_text)
    new_value = 'new_value'

    if user_agrees_to_overwrite:
        user_input = ['Y', new_value, 'Y']
    else:
        user_input = ['N']

    setup_input(monkeypatch, user_input)

    if user_agrees_to_overwrite:
        if mode == 'update':
            node_path = 'update_node'
        else:
            node_path = 'new_node'
        assert config_dialog(config, [node_path])
        assert parse(config.read_text())[node_path] == new_value, "Value was not set to the new one"
    else:
        assert config_dialog(config, ['update']) is None
        assert config.read_text() == config_text
    # TODO: check the existing value with overwrite interaction


def test_user_input_first_question():
    """Checks:
    * y is default
    * y proceeds to create in xdg home
    * n skips to local config
    * q exits the wizard"""
    pass


def test_no_question_if_running_with_param():
    """Tests that if a parameter is supplied - the initial prompt is not asked"""
    pass


