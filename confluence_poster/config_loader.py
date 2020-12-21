from xdg import xdg_config_dirs, xdg_config_home
from confluence_poster.poster_config import Config, PartialConfig
from collections import UserDict
from collections.abc import Mapping
from pathlib import Path


def merge_configs(first_config: Mapping, other_config: Mapping):
    """Merges two configs together, like so:
    {'auth': {'user': 'a'}} + {'auth': {'password': 'b'}} = {'auth': {'user': 'a', 'password': 'b'}}"""
    for key in set(first_config).union(other_config):
        if key in first_config and key in other_config:
            if all([isinstance(_, dict) for _ in [first_config[key], other_config[key]]]):
                yield key, dict(merge_configs(first_config[key], other_config[key]))
            else:
                raise ValueError(f"{key} key is malformed in one of the configs")
        elif key in first_config:
            yield key, first_config[key]
        else:
            yield key, other_config[key]


def load_config(local_config: Path) -> Config:
    """Function that goes through the config directories trying to load the config.
    Reads configs from XDG_CONFIG_DIRS, then from XGD_CONFIG_HOME, then the local one - either the default one, or
    supplied through command line."""
    final_config = UserDict()
    for path in xdg_config_dirs() + [xdg_config_home()]:
        final_config = dict(merge_configs(final_config, PartialConfig(file=path/"confluence_poster/config.toml")))

    final_config = dict(merge_configs(final_config, PartialConfig(file=local_config)))

    return Config(data=final_config)
