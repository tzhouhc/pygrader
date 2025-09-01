# README for Pygrader

## Installation

The general software dependencies can be installed using
`install_dependencies.sh`. This assumes an Ubuntu VM. Currently it will install
`uv` for python package management.

## Usage

### `gen_assignments.sh`

Format of calling: `./gen_assignment.sh hw1 w4118`

This will use the templated files in `templates` and create a new directory
named `hw1` in `~/.local/share/pygrader`, containing the files from the
templates:

- `rubric.json`
- `setup`
- `grader.py`

These generated HW directories will be picked up by the main CLI access point,
`grade.py` and provided as possible choices when running it.

Practically, though, I recommend copying the `demos/demo` dir and use it as a
more complete example.

### `grade.py`

The primary entry point to all grading work. Assumes that a number of homework
directories are placed in `~/.local/share/pygrader` either by manual creation
or by pulling from github.

It also expects each of these homework directories to contain a number of
crucial files, some listed above already.

Once you have *some* homework in that directory, the simplest way to start is
to just run `uv run grade.py`. Without any parameters, it will interactively
ask you for the specific homework entry to grade, as well as the submitter
(student) to get data and grade for.

## `hw_setup.py`

This is expected to be a tool that facilitates setting up a new homework
project, though as is I find it to be too rigid and not doing enough interesting
things. It helps you setup a deadline file and do a few other things in setting
up a homework, but the general usage pattern of this project is expected to be
new TAs reusing the repo with old code, so it's uncertain how useful it will be.

## `install_dependencies.sh`

Script for, well, installing dependencies -- only on a Ubuntu VM though. It
assumes the presence of `apt`.

## `tmux_grade.py`

I recommend just learning to use `tmux` or `zellij` instead, probably simpler.


> [!NOTE]
> Pygrader itself has very basic git tooling. The script `grader.py` is
> expected to contain the logic for fetching student code and deploying it
> in addition to doing the grading.

You can review the additional commandline flags that allow fine-tuning of the
grading behavior.

TODO: provide thorough usage examples for the flags.

## Repo Structure

`common` contains the python library code that `grade.py` depends on.

`demos` contain demo homework projects. Currently we just have `demo`, which
contains a minimal working example. `cp -r demos/demo ~/.local/share/pygrader/`
to give it a shot -- you might need to create the latter dir first.

`libs` include extensions to the grading framework. As we likely won't be
getting our in-house code published on pypi, this folder houses *git submodules*
that add features that we might need without us having to do clumsy code-copying
work -- at least, not `cp -r`-kind of copying.

`templates` contain template files used by `gen_assignment.sh`.

The `pyproject.toml` file specifies both official package dependencies, as well
as local -- submodule-based -- package dependencies that can be built and loaded
as if they are regular packages. Review how `microwave` is added if you want to
add more.

## Homework Layout

The homework data is expected to be found in `~/.local/share/pygrader`. Each
directory inside should be a standalone homework project with the following
files:

- `rubric.json` with the grading rubric specification.
- `setup` which should be a shebanged file containing the necessarily setup
  processes, e.g. installing deps.
- `grader.py` which contains the python code that will interface with pygrader.
  The main component within should be the `Grader` class that implements the
.  `Grader` interface as outlined in `grade.py`.
- `deadline.txt`, a file containing time spec like "12/31/2026 12:00 AM".

By the time you read this we expect to have a dedicated list of repos containing
the version-controlled HW code that should work with this revised setup.
