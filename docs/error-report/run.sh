#!/bin/bash
# regenerate outputs/ -- kamidana's gentle error vs jinja2's raw traceback.
#
# per case, three files are written under outputs/<case>/:
#   kamidana.txt        -- `kamidana` (gentle error, the feature under test)
#   kamidana-debug.txt  -- `kamidana --debug` (raw traceback, same environment)
#   jinja2.txt          -- ../j2.py (plain jinja2, raw traceback)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
export PYTHONPATH=.

mask() {
    sed -e "s@$HERE@HERE@g" \
        -e "s@$HOME/.pyenv/versions/[^/]*/lib/python[0-9.]*/site-packages@<site-packages>@g" \
        -e "s@$HOME@~@g"
}

run() { # <case> <outfile> <cmd...>
    local case=$1 out=$2
    shift 2
    mkdir -p "outputs/$case"
    (
        cd "cases/$case" || exit 2
        echo "\$ $*"
        "$@" 2>&1
        echo "[exit $?]"
    ) | mask > "outputs/$case/$out"
}

K="kamidana --logging=WARNING"

run_case() { # <case> <kamidana-template-arg> <j2-template-name> [extra kamidana args...]
    local case=$1 kt=$2 jt=$3
    shift 3
    run "$case" kamidana.txt $K "$kt" "$@"
    run "$case" kamidana-debug.txt $K --debug "$kt" "$@"
    run "$case" jinja2.txt python ../../j2.py "$jt"
}

run_case 00extends-super ./child.html child.html
run_case 01multi-inheritance ./child.html child.html
run_case 02python-filter ./main.jinja2 main.jinja2 -a additionals.py
run_case 03include-missing ./main.html main.html
run_case 04syntax-error-jinja2 ./main.jinja2 main.jinja2
run_case 05syntax-error-html ./main.html main.html
run_case 06extends-syntax-error ./child.html child.html
run_case 07macro-caller ./child2.html child2.html
run_case 08include-chain ./main.html main.html

run_case 10deep-chain ./c0.html c0.html -a additionals.py
run 10deep-chain kamidana-level50.txt python ../../level.py ./c0.html 50 -a additionals.py
run 10deep-chain kamidana-level5.txt python ../../level.py ./c0.html 5 -a additionals.py

# recursion / same-file dedup probes (unlimited default vs level=50)
run 11recursive self-include.txt $K ./loop.html
run 11recursive self-include-level50.txt python ../../level.py ./loop.html 50
run 11recursive self-include-jinja2.txt python ../../j2.py loop.html
run 11recursive mutual-include.txt $K ./ping.html
run 11recursive mutual-include-level50.txt python ../../level.py ./ping.html 50
run 11recursive mutual-include-jinja2.txt python ../../j2.py ping.html
run 11recursive same-file-macro.txt $K ./samemacro.html -a additionals.py
run 11recursive same-file-macro-level50.txt python ../../level.py ./samemacro.html 50 -a additionals.py
run 11recursive same-file-macro-jinja2.txt python ../../j2.py samemacro.html

# kamidana-only CLI errors (no jinja2 counterpart)
run 09cli-errors missing-template.txt $K ./no-such.html
run 09cli-errors missing-data.txt $K -d ./missing.json ./hello.html
run 09cli-errors missing-additionals.txt $K -a missing.py ./hello.html
