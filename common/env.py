"""Grading environment -- prevents storing all data directly in repo."""

import os

HOME_DIR: str | None = os.environ.get("HOME")
assert HOME_DIR
LOCAL_SHARE: str = os.path.join(HOME_DIR, ".local/share")
HW_DATA_DIR: str = os.path.join(LOCAL_SHARE, "pygrader")


class Env:
    def __init__(self, root_dir: str = HW_DATA_DIR) -> None:
        self.root_dir: str = root_dir
        self.ensure_data_dir()

    def ensure_data_dir(self) -> None:
        os.makedirs(self.root_dir, 0o755, True)

    def get_data_dir(self) -> str:
        return self.root_dir

    def make_hw_dir(self, name: str) -> None:
        # fail loud if dir already exists -- should be handled by caller
        os.makedirs(os.path.join(self.root_dir, name), 0o755, False)

    def has_hw_dir(self, name: str) -> bool:
        return os.path.isdir(os.path.join(self.root_dir, name))

    def ensure_hw_dir(self, name: str) -> None:
        os.makedirs(os.path.join(self.root_dir, name), 0o755, True)

    def get_hw_dir(self, name: str) -> str:
        return os.path.join(self.root_dir, name)
