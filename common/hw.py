import common.hw_base as hw_base
import git

class GitBasedHW(hw_base.HW):
    def __init__(self, hw_name: str, rubric_name: str, submitter: str | None):
        # Set up the minimum to at least dump grades for all students
        super().__init__(hw_name, rubric_name)
        self.submitter = submitter
        self.repo: git.Repo | None = None
        self.written_answers: str = "written_answers.txt"
