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

These generated HW directories will be picked up by the main CLI access point,
`grade.py` and provided as possible choices when running it.

### `grade.py`

The primary entry point to all grading work. Assumes that a number of homework
directories are placed in `~/.local/share/pygrader` either by manual creation
or by pulling from github.

It also expects each of these homework directories to contain a number of
crucial files, some listed above already.
