# README for Pygrader

## Usage

### `gen_assignments.sh`

Format of calling: `./gen_assignment.sh hw1 w4118`

This will use the templated files in `templates` and create a new directory
named `hw1` in `~/.local/share/pygrader`, containing the files from the
templates:

- `rubric.json` with the grading rubric specification.
- `setup` which should be a shebanged file containing the necessarily setup
  processes, e.g. installing deps.
- `grader.py` which contains the python code that will interface with pygrader.
  The main component within should be the `Grader` class that implements the
  `Grader` interface as outlined in `grade.py`
