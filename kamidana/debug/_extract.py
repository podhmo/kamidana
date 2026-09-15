import os.path
import traceback
from collections import namedtuple

import jinja2

# the output shape is a pair of
# - template frames (deduplicated, outermost -> innermost)
# - trailing python frames, dropped when the innermost frame is inside jinja2
Detail = namedtuple("Detail", "jinja2_frames, python_frames")

_JINJA2_DIR = os.path.dirname(jinja2.__file__)

# names given to the code objects that jinja2 generates for a template
# (see jinja2.debug.rewrite_traceback_stack):
#   "root"          -> "top-level template code"
#   "block_<name>"  -> "block <name>!r" (e.g. "block 'title'")
#   anything else   -> "template"      (macros, loop bodies, ...)
_JINJA2_FRAME_NAMES = frozenset(["template", "top-level template code"])


def _is_jinja2_frame(fs: traceback.FrameSummary) -> bool:
    name = fs.name
    if name in _JINJA2_FRAME_NAMES or name.startswith("block "):
        return True
    return name == "<module>" and fs.filename.endswith((".j2", ".jinja2"))


def _is_jinja2_internal_frame(fs: traceback.FrameSummary) -> bool:
    return os.path.dirname(fs.filename) == _JINJA2_DIR


def _deduplicate(frames):
    seen = set()
    r = []
    for f in reversed(frames):  # innermost -> outermost
        k = (f.filename, f.lineno)
        if k in seen:
            continue
        seen.add(k)
        if r and r[-1].filename == f.filename:
            continue
        r.append(f)
    return list(reversed(r))


def extract_detail(exc: Exception) -> Detail:
    frames = traceback.extract_tb(exc.__traceback__)
    jinja2_indices = [i for i, f in enumerate(frames) if _is_jinja2_frame(f)]
    if not jinja2_indices:
        return Detail(jinja2_frames=None, python_frames=None)

    # python frames after the last template frame (e.g. inside a filter
    # function written in python). meaningless when the innermost frame is
    # jinja2's own code.
    python_frames = frames[jinja2_indices[-1] + 1:]
    if python_frames and _is_jinja2_internal_frame(python_frames[-1]):
        python_frames = []

    jinja2_frames = _deduplicate([frames[i] for i in jinja2_indices])
    return Detail(jinja2_frames=jinja2_frames, python_frames=python_frames)
