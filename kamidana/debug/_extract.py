import traceback
from collections import namedtuple

FrameSet = namedtuple("FrameSet", "kind, frames")
Detail = namedtuple("Detail", "jinja2, framesets, outermost")


def extract_detail(exc: Exception, *, tb=None) -> Detail:
    tb = tb or exc.__traceback__
    aggs = _aggregate_traceback(tb)
    if len(aggs) == 1:
        return Detail(jinja2=[], framesets=aggs, outermost=False)

    aggs = _compact_aggregated(aggs)
    if aggs[-1].kind == "jinja2":
        outermost = True
        fsets = aggs[-1]
    else:
        outermost = False
        fsets = aggs[-2]
    f: traceback.FrameSummary = fsets[-1]
    return Detail(jinja2=fsets, framesets=aggs, outermost=outermost)


def _compact_aggregated(aggs):
    r = []
    for fset in aggs:
        if fset.kind == "jinja2":
            r.append(fset)

    is_last_frame_python = aggs[-1] != r[-1]

    compacted = [f for fset in r for f in fset.frames]
    r.append(FrameSet(kind="jinja2", frames=compacted))

    if is_last_frame_python:
        r.append(aggs[-1])
    return r


def _detect_kind(
    name: str, *, _cands=set(["template", "top-level template code", "template"])
) -> str:
    is_jinja2 = name in _cands or name.startswith('block "')
    return "jinja2" if is_jinja2 else "python"


def _aggregate_traceback(tb, *, detect_kind=_detect_kind):
    frames = traceback.extract_tb(tb)
    kind = None
    cur = []
    r = []
    for fs in frames:
        prev, kind = kind, detect_kind(fs.name)
        if prev != kind:
            if cur:
                r.append(FrameSet(kind=prev, frames=cur))
            cur = []
        cur.append(fs)
    if cur:
        r.append(FrameSet(kind=kind, frames=cur))
    return r
