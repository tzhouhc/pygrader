#!/bin/bash

# NOTE:
# As of f25 the script has been revised to create the `hwN` dirs in
# ~/.local/share/pygrader instead of directly in the repo. This is a common
# location that the python interface also uses and should reduce clutter.
#
# The homework dirs should be *separetely* version controlled and maintained
# from the grader infra.

SCRIPT_DIR="$(dirname "$0")"  # dir containing this file
TEMPLATE_DIR="$(realpath $SCRIPT_DIR/templates)"
DATA_DIR="${HOME}/.local/share/pygrader"

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <assignment name> [org/repo to clone on setup]" >&2
	exit 1
fi

mkdir -p ${DATA_DIR}
cd ${DATA_DIR}

ASS="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
if [ -d "$ASS" ]; then
	read -p "Overwrite '$ASS'? [y/N]: " RESP
	if [ "$RESP" == y ] || [ "$RESP" == Y ]; then
		rm -rf "$ASS"
	else
		exit 1
	fi
fi

mkdir "$ASS" || exit
cp "${TEMPLATE_DIR}/rubric.json.in" "$ASS/rubric.json"
cp "${TEMPLATE_DIR}/grader.py.in" "$ASS/grader.py"
sed -i "s/ASSIGNMENT/$ASS/g" "$ASS/grader.py"
test "$#" -gt 1 && cp "${TEMPLATE_DIR}/clone_setup.in" "$ASS/setup"
touch "$ASS/setup"
chmod +x "$ASS/setup"
sed -i "s~REPO~$2~g" "$ASS/setup"
