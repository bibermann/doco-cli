import os

import pydantic
import tomli

from src.utils.rsync import RsyncConfig


class TextSubstitutions(pydantic.BaseModel):
    pattern: str
    replace: str


class DocoConfigTextSubstitutions(pydantic.BaseModel):
    bind_mount_volume_path: list[TextSubstitutions] = []


class DocoOutputConfig(pydantic.BaseModel):
    text_substitutions: DocoConfigTextSubstitutions = DocoConfigTextSubstitutions()


class DocoBackupConfig(pydantic.BaseModel):
    rsync: RsyncConfig = RsyncConfig()


class DocoConfig(pydantic.BaseModel):
    output: DocoOutputConfig = DocoOutputConfig()
    backup: DocoBackupConfig = DocoBackupConfig()


def load_doco_config(project_path: str) -> DocoConfig:
    root = os.path.abspath(project_path)
    toml_file_name = "doco.config.toml"
    json_file_name = "doco.config.json"
    while True:
        path = os.path.join(root, toml_file_name)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                return DocoConfig.parse_obj(tomli.load(f))

        path = os.path.join(root, json_file_name)
        if os.path.isfile(path):
            return DocoConfig.parse_file(path)

        if root == "/":
            break
        root = os.path.dirname(root)
    return DocoConfig()
