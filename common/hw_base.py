"""hw.py: Base class for all HW's"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import common.printing as printing
import common.submissions as subs
import common.utils as u
import common.env as e


@dataclass
class RubricItem:
    """Representation of a rubric item.

    Attributes:
        code: The code of this item (e.g. B1)
        subitems: list containing (pts, desc) for each subitem (e.g. B1.1, B1.2)
        tester: Callback function to grade this item.
        pretester: Optional Callback function to do pre-grading run and collect
          Gradable artifacts.
    """

    code: str
    deduct_from: int | None
    subitems: list[tuple[int, str]]
    tester: Callable[..., Any]
    pretester: Callable[..., Any] | None = None


class HW:
    """Grading Base Class

    Here's a visual representation of some of the fields:
    ~
    |_ .local/share/pygrader/
        |_ hwN <---- hw_workspace
           |_ grades.json
           |_ deadline.txt
           |_ hwN <----- submission_dir

    Attributes:
        hw_name: the hw name (in the form 'hwN')
        hw_workspace: Path of the form '~/.grade/hw{1,...,8}', which contains
            the submission_dir, deadline.txt, and grades.json
        scripts_dir: The directory that contains this hw's grading logic.
        rubric: Python representation of the hw rubric
        submission_dir: The student/team's submission directory
            In the above example, this is cloned skeleton code for the
            assignment. We simply pull down teams' tags. In Canvas-based
            assignments, there is 1 submission_dir per student.
    """

    def __init__(self, hw_name: str, rubric_name: str):
        self.hw_name: str = hw_name
        self.env = e.Env()
        assert(self.env.has_hw_dir(hw_name))
        self.hw_workspace: str = self.env.get_hw_dir(hw_name)

        # Find grader root relative to hw_base.py: root/common/hw_base.py
        pygrader_root = Path(__file__).resolve().parent.parent

        self.scripts_dir: str = os.path.join(pygrader_root, self.hw_name)

        # Here we assume the rubric file is in the hw workspace dir, since
        # rubrics are per HW.
        rubric_path = os.path.join(self.hw_workspace, rubric_name)
        self.rubric: dict[str, Any] = self.create_rubric(rubric_path)

        self.submission_dir: str | None = None  # Populated in subclasses.

    def create_rubric(self, rubric_file: str) -> dict[str, Any]:
        """Parses a JSON rubric file into a Python representation."""

        # TODO check if file exists
        with open(rubric_file, "r") as f:
            rubric_json: dict[str, Any] = json.load(f)

        rubric: dict[str, Any] = {}
        for table_k, table_v in rubric_json.items():
            if table_k == "late_penalty":
                rubric[table_k] = table_v
                continue
            if table_k not in rubric:
                rubric[table_k] = {}

            for item in table_v:
                deduct_from: int | None = None
                if "deducting_from" in table_v[item]:
                    deduct_from = table_v[item]["deducting_from"]
                ri_obg = RubricItem(
                    table_v[item]["name"],
                    deduct_from,
                    list(
                        zip(
                            table_v[item]["points_per_subitem"],
                            table_v[item]["desc_per_subitem"],
                        )
                    ),
                    getattr(self, "grade_" + item, self.default_grader),
                    pretester=getattr(self, "pre_grade_" + item, None),
                )
                rubric[table_k][item] = ri_obg
        return rubric

    def do_cd(self, path: str) -> None:
        """Changes directory relative to the self.submission_dir.

        For example, if you had the following:
            hw3  <---- self.submission_dir
            |_ part1
               |_ part1-sub

        and you wanted to cd into part1-sub, you would run
        `do_cd(os.path.join('part1', 'part1-sub'))`.
        """
        assert self.submission_dir
        part_dir: str = os.path.join(self.submission_dir, path)
        u.is_dir(part_dir)
        os.chdir(part_dir)

    def exit_handler(self, _signal: Any, _frame: Any) -> None:
        """Handler for SIGINT

        Note: this serves as a template for how the subclasses should do it.
        The subclass is free to override this function with more hw-specific
        logic.
        """
        printing.print_cyan("\n[ Exiting generic grader... ]")
        self.cleanup()
        sys.exit()

    def check_late_submission(self):
        """Grabs the latest commit timestamp to compare against the deadline"""
        proc = u.cmd_popen("git log -n 1 --format='%aI'")
        iso_timestamp, _ = proc.communicate()

        return subs.check_late(
            os.path.join(self.hw_workspace, "deadline.txt"),
            iso_timestamp.strip("\n"),
        )

    def default_grader(self):
        """Generic grade function."""
        printing.print_red("[ Opening shell, ^D/exit when done. ]")
        os.system("bash")

    def setup(self):
        """Performs submission setup (e.g. untar, git checkout tag)."""

    def cleanup(self):
        """Performs cleanup (kills stray processes, removes mods, etc.)."""


def directory(start_dir: str) -> Callable[..., Any]:
    """Decorator function that cd's into `start_dir` before the test.

    If start_dir is 'root', we cd into the root of the submission_dir.
    For example:
        @directory("part1")
        def test_B1(self):
            ...
    This will cd into submission_dir/part1 before calling test_B1().
    """

    # This is definitely overkill, but for ultimate correctness (and
    # for the sake of making the decorator usage sleek), let's allow
    # users to just use '/'. We can correct it here.
    start_dir = os.path.join(*start_dir.split("/"))

    def function_wrapper(test_func: Callable[..., Any]) -> Callable[..., Any]:
        def cd_then_test(hw_instance: HW) -> Any:
            try:
                hw_instance.do_cd("" if start_dir == "root" else start_dir)
            except ValueError:
                printing.print_red(
                    "[ Couldn't cd into tester's @directory, "
                    "opening shell.. ]"
                )
                os.system("bash")
            return test_func(hw_instance)

        return cd_then_test

    return function_wrapper
