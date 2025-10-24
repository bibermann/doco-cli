import pathlib
import subprocess
import time
from pathlib import Path
from typing import TypedDict

import pytest
from python_on_whales import DockerClient

from tests.cli.utils.helpers import rmtree_keeping_root


class RsyncDaemonConfig(TypedDict):
    chroot_dir: Path
    host: str
    port: int
    module: str
    rsync_url: str


def _wait_for_rsync(docker_client: DockerClient, max_retries=5) -> None:  # noqa: C901
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["rsync", "--list-only", "rsync://localhost:8873/test_module/"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                break
            print(f"Attempt {attempt + 1}: {result.stderr}")
            if attempt < max_retries - 1:
                time.sleep(1)
        except subprocess.TimeoutExpired as exc:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            # Get logs using python-on-whales
            try:
                logs = docker_client.compose.logs("rsync-ssh")
            except Exception:  # noqa: B902 pylint: disable=broad-except
                logs = "Could not retrieve logs"
            raise RuntimeError(f"Timeout connecting to rsync daemon. Container logs:\n{logs}") from exc
    else:
        # Get logs using python-on-whales
        try:
            logs = docker_client.compose.logs("rsync-ssh")
        except Exception:  # noqa: B902 pylint: disable=broad-except
            logs = "Could not retrieve logs"
        raise RuntimeError(
            f"Failed to connect to rsync daemon after {max_retries} attempts. Container logs:\n{logs}"
        )


@pytest.fixture
def doco_config_path():
    return pathlib.Path(__file__).parent / "data" / "doco.config.toml"


@pytest.fixture(scope="session")
def rsyncd_conf_path():
    return pathlib.Path(__file__).parent / "data" / "doco-pytest-rsyncd" / "rsyncd.conf"


@pytest.fixture(name="compose_path", scope="session")
def fixture_compose_path():
    return pathlib.Path(__file__).parent / "data" / "doco-pytest-rsyncd" / "compose.yml"


@pytest.fixture
def doco_test_compose_project_files_path():
    return pathlib.Path(__file__).parent / "data" / "test-project-files"


@pytest.fixture(scope="session")
def rsync_daemon(remote_data_dir, compose_path):
    """
    Session-scoped fixture that runs an rsync daemon using Docker Compose.
    Provides a chrooted directory within the container.
    """
    docker_client = DockerClient(compose_project_directory=compose_path.parent)

    try:
        # Start services with docker-compose
        docker_client.compose.up(detach=True)

        _wait_for_rsync(docker_client)

        yield RsyncDaemonConfig(
            chroot_dir=remote_data_dir,
            host="localhost",
            port=8873,
            module="test_module",
            rsync_url="rsync://localhost:8873/test_module/",
        )
    finally:
        try:
            # Stop and remove services
            docker_client.compose.down()
        except Exception as e:  # noqa: B902 pylint: disable=broad-except
            print(f"Warning: Failed to stop docker-compose services: {e}")


@pytest.fixture(name="local_instance_workdir")
def fixture_local_instance_workdir():
    dir_ = pathlib.Path(__file__).parent / "tmp" / "local-workdir"
    dir_.mkdir(parents=True, exist_ok=True)
    return dir_


@pytest.fixture(name="local_data_dir")
def fixture_local_data_dir():
    dir_ = pathlib.Path(__file__).parent / "tmp" / "local-data"
    dir_.mkdir(parents=True, exist_ok=True)
    return dir_


@pytest.fixture(name="remote_data_dir", scope="session")
def fixture_remote_data_dir():
    dir_ = pathlib.Path(__file__).parent / "tmp" / "remote-data"
    dir_.mkdir(parents=True, exist_ok=True)
    return dir_


@pytest.fixture
def clean_local_instance_workdir(local_instance_workdir):
    rmtree_keeping_root(local_instance_workdir)

    yield local_instance_workdir


@pytest.fixture
def clean_local_data_dir(local_data_dir):
    rmtree_keeping_root(local_data_dir)

    yield local_data_dir


@pytest.fixture
def clean_remote_data_dir(remote_data_dir):
    rmtree_keeping_root(remote_data_dir)

    yield remote_data_dir
