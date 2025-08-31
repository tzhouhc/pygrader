#!/usr/bin/env python3.7

"""grade.py: Grading driver"""

import argparse
import importlib.util as iutil
import os
import signal
import sys
from typing import Any

from rich.prompt import Prompt

import common.printing as p
import common.utils as utils
from common.env import Env
from common.grades import Grades
from common.hw_base import RubricItem


assignments: list[Any] = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="pygrader: Python Grading Framework"
    )

    parser.add_argument(
        "submitter",
        type=str,
        nargs="?",
        default=None,
        help="the name of student/group to grade",
    )
    parser.add_argument("-w", "--hw", type=str, help="homework to grade")
    parser.add_argument(
        "-c",
        "--code",
        type=str,
        nargs="?",
        default="all",
        help=("rubric item (e.g. A, B4) to grade; defaults to all"),
    )

    grading_mode = parser.add_mutually_exclusive_group()
    grading_mode.add_argument(
        "-g",
        "--grade-only",
        action="store_true",
        help="grade without running any tests",
        dest="grade_only",
    )
    grading_mode.add_argument(
        "-t",
        "--test-only",
        action="store_true",
        help=("run tests without grading"),
        dest="test_only",
    )
    script_mode = parser.add_mutually_exclusive_group()
    script_mode.add_argument(
        "-r",
        "--regrade",
        action="store_true",
        help="do not skip previously graded items",
        dest="regrade",
    )
    script_mode.add_argument(
        "-d",
        "--dump-grades",
        action="store_true",
        help=(
            "dump grades for this homework -- all if no submitter specified"
        ),
        dest="dump_grades",
    )
    script_mode.add_argument(
        "-s",
        "--status",
        action="store_true",
        help=(
            "return grading status for this homework -- "
            "all if no submitter specified"
        ),
        dest="status",
    )
    script_mode.add_argument(
        "-i",
        "--inspect",
        action="store_true",
        help=("drop into shell to inspect submission"),
        dest="inspect",
    )
    return parser.parse_args()


def main():
    """Entry-point into the grader"""

    grading_env = Env()
    _, subdirs, _ = next(os.walk(grading_env.get_data_dir()))
    asgmnt_map: dict[str, Any] = {}
    for subdir in subdirs:
        if subdir[0] != ".":
            spec = iutil.spec_from_file_location(
                subdir, os.path.join(grading_env.get_hw_dir(subdir), "grader.py")
            )
            assert spec
            assert spec.loader
            grader = iutil.module_from_spec(spec)
            # assignments.append(importlib.import_module(f"{subdir}.grader"))
            sys.modules[subdir] = grader
            spec.loader.exec_module(grader)
            assignments.append(grader)
            asgmnt_map[subdir] = grader

    args = parse_args()
    env = {
        "regrade": args.regrade,
        "grade_only": args.grade_only,
        "test_only": args.test_only,
        "dump_grades": args.dump_grades,
        "status": args.status,
        "inspect": args.inspect,
    }
    if not args.hw:
        args.hw = Prompt.ask(choices=list(asgmnt_map.keys()))

    rubric_code = args.code if args.code else "all"

    tester = Grader(args.hw, args.submitter, rubric_code, env)

    if args.dump_grades:
        tester.grades.dump_grades(args.submitter, rubric_code.upper())
        sys.exit()

    if args.status:
        all_graded = tester.grades.status(args.submitter, rubric_code.upper())
        sys.exit(not all_graded)  # If all graded, exit with 0 (success)

    if args.inspect:
        # (pygrader)user@host:pwd $
        prompt = (
            f"{p.CGREEN}({p.CYELLOW}pygrader{p.CGREEN}){p.CEND}"
            f":{p.CBLUE}\\w{p.CCYAN} ${p.CEND} "
        )
        p.print_red("[ ^D/exit when done ]")
        os.system(
            f"PROMPT_COMMAND='PS1=\"{prompt}\"; unset PROMPT_COMMAND' " f"bash"
        )
        sys.exit()

    if not args.submitter:
        sys.exit("unspecified student/team")

    tester.pregrade()
    tester.grade()

    # TODO: add progress/percentage complete?
    p.print_magenta(
        f"\n[ Pretty-printing pts/comments for {args.submitter}... ]"
    )
    _, _, s = tester.grades.get_submission_grades(
        args.submitter, rubric_code.upper()
    )
    print(s)
    # clean up
    tester.hw_class.cleanup()


class Grader:
    """Represents the current hw grading session

    Attributes:
        hw_name: Homework name being graded (e.g. hw1)
        rubric_code: Rubric code being graded (based on AP/OS-style rubrics)
            This can be a table (A), or an item (A1).
        submitter: Team/uni of the submission
        hw_class: The object representing this homework (rubric, testers)
        env: Flags determining grader behavior (see main routine for argsparse)
        gradables: collection of data / context that will be graded that is
            collected ahead of time.
        grades_file: Path to JSON file containing session grades
        grades: Maps (uni/team) -> (rubric item -> (pts, comments))
    """

    def __init__(
        self,
        hw_name: str,
        submitter: str,
        rubric_code: str,
        env: dict[str, bool],
    ):
        self.hw_name = hw_name
        self.rubric_code = rubric_code
        self.submitter = submitter
        self.env = env
        # convenience accessors
        self.test_only = env.get("test_only", False)
        self.grade_only = env.get("grade_only", False)
        self.regrade = env.get("regrade", False)

        self.hw_class = self._get_hw_class()
        self.hw_class.grader = self
        self.gradables: dict[str, Any] | None = {}

        signal.signal(signal.SIGINT, self.hw_class.exit_handler)

        self.grades_file = os.path.join(
            self.hw_class.hw_workspace, "grades.json"
        )
        self.grades = Grades(
            self.grades_file, self.hw_class.rubric, self.submitter
        )

    def _get_hw_class(self):
        for assignment in assignments:
            if self.hw_name.lower() in assignment.ALIASES:
                return assignment.GRADER(self.submitter)
        sys.exit(f"Unsupported assignment: {self.hw_name}")

    def print_intro(self, rubric_code: str):
        p.print_intro(self.submitter, self.hw_name, rubric_code)

    def print_headerline(self, rubric_item: RubricItem):
        header = "Grading {}".format(rubric_item.code)
        if rubric_item.deduct_from:
            header += " ({}p, deductive)".format(rubric_item.deduct_from)
        p.print_green(header)

    def print_header(self, rubric_item: RubricItem):
        p.print_double()
        self.print_headerline(rubric_item)
        self.print_subitems(rubric_item)
        p.print_double()

    def print_subitems(self, rubric_item: RubricItem):
        for i, (pts, desc) in enumerate(rubric_item.subitems, 1):
            p.print_magenta(
                "{}.{} ({}p): {}".format(rubric_item.code, i, pts, desc)
            )

    def print_subitem_grade(self, code: str, warn: bool = False):
        if self.grades.is_graded(code):
            # We've graded this already. Let's show the current grade.
            awarded = self.grades[code]["award"]
            comments = self.grades[code]["comments"]
            p.print_green(
                f"[ ({code}) Previous Grade: awarded={awarded} "
                f"comments='{comments}']"
            )
        elif warn:
            p.print_yellow(f"[ {code} hasn't been graded yet ]")

    def prompt_grade(
        self,
        rubric_item: RubricItem,
        autogrades: list[tuple[str, str]] | None = None,
    ):
        """Prompts the TA for pts/comments"""

        if autogrades:
            if len(autogrades) != len(rubric_item.subitems):
                raise Exception("Autogrades don't align with rubric item!")

            for i, (a, c) in enumerate(autogrades, 1):
                subitem_code = f"{rubric_item.code}.{i}"
                self.grades[subitem_code]["award"] = a == "y"
                self.grades[subitem_code]["comments"] = c

        else:
            for i, (pts, desc) in enumerate(rubric_item.subitems, 1):
                subitem_code = f"{rubric_item.code}.{i}"
                p.print_magenta(f"{subitem_code} ({pts}p): {desc}")
                self.print_subitem_grade(subitem_code)
                while True:
                    try:
                        award = input(f"{p.CBLUE2}Apply? [y/n]: {p.CEND}")
                        award = award.strip().lower()
                        if award in ("y", "n"):
                            break
                    except EOFError:
                        print("^D")
                        continue
                while True:
                    try:
                        comments = input(f"{p.CBLUE2}Comments: {p.CEND}")
                        break
                    except EOFError:
                        print("^D")
                        continue

                self.grades[subitem_code]["award"] = award == "y"
                self.grades[subitem_code]["comments"] = comments.strip()

        self.grades.synchronize()

    def _check_valid_table(self, table_key: str):
        """Given a key (i.e A, C, N) check if its a valid rubric item"""

        keys = [*self.hw_class.rubric.keys()]
        if table_key not in keys:
            raise ValueError(f"{self.hw_name} does not have table {table_key}")

    def _check_valid_item(self, item_key: str):
        """Given a table item (i.e. A1, B2, D9) check if it is valid.

        Assumes the table is valid (use _check_valid_table() for validation on
        that).
        """
        keys = [*self.hw_class.rubric[item_key[0]].keys()]
        if item_key not in keys:
            raise ValueError(
                f"{self.hw_name} does not have " f"rubric item {item_key}"
            )

    def pregrade(self) -> None:
        """Performs pregrading to generate gradables.

        Pregrading is done in order to frontload all the time-consuming
        processes in grading, e.g. kernel compilation, and gather all
        the necessary gradable context and data, so that once the TA is
        notified to perform the actual grading, they can go through all
        the grading for an instance of homework in one go, as opposed to
        doing some grading, waiting for 10 minutes, then grading another
        item, etc.
        """
        self.grade(pregrade=True)

    def grade(self, pregrade: bool = False):
        key = self.rubric_code
        self.print_intro(key)
        if key.lower() == "all":
            self.grade_all(pregrade)
        elif key.isalpha():
            # e.g. A, B, C, ...
            table = key.upper()
            self._check_valid_table(table)
            self.grade_table(table, pregrade)
        else:
            # e.g. A1, B4, ...
            table = key[0].upper()
            item = key.upper()
            self._check_valid_table(table)
            self._check_valid_item(item)
            rubric_item_obj = self.hw_class.rubric[table][item]
            self.grade_item(rubric_item_obj, pregrade)

    def grade_all(self, pregrade: bool):
        for table in self.hw_class.rubric:
            if table == "late_penalty":
                continue
            self.grade_table(table, pregrade)

    def grade_table(self, table_key: str, pregrade: bool):
        table = self.hw_class.rubric[table_key]

        for item in table:
            self.grade_item(table[item], pregrade)

    def should_skip_item(self, rubric_item: RubricItem) -> bool:
        """Check if RubricItem should be skipped.

        Don't skip if any of the following:
        - test_only is set;
        - regrade is set
        - any rubric item is not yet graded

        """
        return (
            not self.test_only
            and not self.regrade
            and all(
                self.grades.is_graded(f"{rubric_item.code}.{si}")
                for si, _ in enumerate(rubric_item.subitems, 1)
            )
        )

    def show_grades(self, rubric_item: RubricItem) -> None:
        # Let the grader know if the subitems have been graded yet
        for i in range(1, len(rubric_item.subitems) + 1):
            code = f"{rubric_item.code}.{i}"
            self.print_subitem_grade(code, warn=True)

    def grade_item(self, rubric_item: RubricItem, pregrade: bool):
        if self.should_skip_item(rubric_item):
            p.print_yellow(
                f"[ {rubric_item.code} has been graded, skipping... ]"
            )
            return

        # if --grade-only/-g is not provided, run tests else skip tests
        autogrades = None
        gradables = None
        if not self.grade_only:

            def test_wrapper():
                nonlocal autogrades, gradables
                if pregrade and rubric_item.pretester:
                    gradables = rubric_item.pretester()
                else:
                    self.print_header(rubric_item)
                    autogrades = rubric_item.tester()

            try:
                utils.run_and_prompt(test_wrapper)
            except Exception as e:  # pylint: disable=W0703
                p.print_red(f"\n\n[ Exception: {e} ]")
        else:
            self.print_headerline(rubric_item)

        if pregrade:
            # pregrade goes through the same skipping and actual running
            # process, just runs a different method
            self.collect_gradables(rubric_item, gradables)
            return

        # if -t is not provided, ask for grade. If -t is provided skip
        if not self.test_only:
            p.print_line()
            is_late = self.hw_class.check_late_submission()
            if is_late:
                # Once we find one part of the submission that is late, the
                # whole thing is considered late.

                # Since this happens after run_and_prompt, the submission_dir
                # will still be checked out to the specified tag.

                # TODO: I actually think we shouldn't do this here, since
                # we don't want to mark submissions that are late on master
                # late if none of the tags are late...
                self.grades.set_late(True)
            self.prompt_grade(rubric_item, autogrades)
        else:
            self.show_grades(rubric_item)

    def collect_gradables(self, rubric_item: RubricItem, res: Any) -> None:
        if not self.gradables:
            self.gradables = {}
        self.gradables[rubric_item.code] = res
        # TODO: flush gradable to disk


if __name__ == "__main__":
    main()
