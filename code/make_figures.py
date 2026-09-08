"""Render the paper's figures as standalone SVGs, one light and one dark per figure.

Colours are the same sprout tokens the HTML build uses, but written out literally here:
GitHub renders SVG inside Markdown and then strips <style> and refuses to resolve CSS
custom properties, so a themed SVG comes out unstyled. The light/dark pair gets wired up
with <picture> in the Markdown instead.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path("release/figures")

THEMES = {
    "light": dict(bg="#FAFBFD", panel="#F1F4F8", ink="#13171F", mute="#68717F",
                  faint="#6E7785", line="#E2E7EE", line2="#CBD3DE",
                  s1="#2F68A8", s2="#B0452C", s3="#0D7D5C"),
    "dark":  dict(bg="#14171D", panel="#232935", ink="#E4E9F0", mute="#868FA0",
                  faint="#828B99", line="#262C36", line2="#39414E",
                  s1="#5A92D4", s2="#D0603F", s3="#43A982"),
}
FONT = "ui-monospace,SFMono-Regular,Menlo,monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w: int, h: int, body: str, t: dict) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" font-family="{FONT}">'
            f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>{body}</svg>')


def text(s, x, y, fill, size=10, anchor="start", weight="400"):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{esc(str(s))}</text>')


def rect(x, y, w, h, fill, rx=2):
    # clamp the width, a zero-width bar disappears entirely at these sizes
    return f'<rect x="{x}" y="{y:.1f}" width="{max(0.5,w):.1f}" height="{h}" rx="{rx}" fill="{fill}"/>'


def fig_categories(t: dict) -> tuple[int, int, str]:
    data = [("weaken_types", 47, 15, 32), ("deprecate", 18, 5, 11),
            ("teacher:blender", 17, 2, 1), ("implement_from_signature", 9, 3, 3),
            ("hallucinate", 7, 2, 1), ("teacher:roblox", 2, 0, 0)]
    W, rowH, L, R = 760, 50, 200, 96
    H = len(data) * rowH + 42
    mx = 47
    sx = lambda v: (W - L - R) * v / mx
    o = [text("baseline", L, 16, t["mute"], 10),
         rect(L - 16, 9, 9, 9, t["s1"]),
         text("adapter", L + 74, 16, t["mute"], 10),
         rect(L + 58, 9, 9, 9, t["s3"])]
    for i, (k, n, b, a) in enumerate(data):
        y = 32 + i * rowH
        o += [text(k[:26], L - 12, y + 14, t["mute"], 10, "end"),
              text(f"n={n}", L - 12, y + 28, t["faint"], 9, "end"),
              rect(L, y, sx(b), 14, t["s1"]), rect(L, y + 18, sx(a), 14, t["s3"]),
              text(b, L + sx(b) + 6, y + 11, t["faint"], 9),
              text(a, L + sx(a) + 6, y + 29, t["faint"], 9)]
        d = a - b
        col = t["s3"] if d > 0 else (t["s2"] if d < 0 else t["faint"])
        o.append(text(f"+{d}" if d > 0 else (d if d < 0 else "0"),
                      W - 14, y + 21, col, 11, "end", "600"))
    return W, H, "".join(o)


def fig_val(t: dict) -> tuple[int, int, str]:
    runs = [("Run 1", t["s1"], [(1,1.262),(50,.972),(100,.866),(150,.978),(200,.882),
             (250,1.064),(300,1.019),(350,.945),(400,1.183)]),
            ("Run 2", t["s3"], [(1,1.148),(100,.699),(200,.637),(248,.617)]),
            ("Run 3", t["s2"], [(1,1.096),(100,.762),(200,.721),(300,.594),(400,.754),
             (500,.456),(600,.573),(700,.580),(800,.698),(872,.593)])]
    W, H, L, R, T, B = 760, 290, 50, 84, 18, 38
    xmax, ymin, ymax = 880, .4, 1.3
    sx = lambda v: L + (W - L - R) * v / xmax
    sy = lambda v: T + (H - T - B) * (ymax - v) / (ymax - ymin)
    o = []
    for g in (0.4, 0.6, 0.8, 1.0, 1.2):
        o += [f'<line x1="{L}" y1="{sy(g):.1f}" x2="{W-R}" y2="{sy(g):.1f}" stroke="{t["line"]}"/>',
              text(f"{g:.1f}", L - 8, sy(g) + 3.5, t["faint"], 9, "end")]
    for v in (0, 200, 400, 600, 800):
        o.append(text(v, sx(v), H - B + 17, t["faint"], 9, "middle"))
    o += [text("validation loss", L - 8, T - 3, t["faint"], 9, "end"),
          text("iteration", (L + W - R) / 2, H - 6, t["faint"], 9, "middle")]
    for name, col, pts in runs:
        d = " ".join(("M" if i == 0 else "L") + f"{sx(x):.1f} {sy(y):.1f}"
                     for i, (x, y) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2" '
                 f'stroke-linejoin="round"/>')
        for x, y in pts:
            o.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3" fill="{col}"/>')
        # label rides on the last point rather than a legend box
        lx, ly = pts[-1]
        o.append(text(name, sx(lx) + 8, sy(ly) + 3.5, col, 10, "start", "600"))
    return W, H, "".join(o)


def fig_funnel(t: dict) -> tuple[int, int, str]:
    stages = [("candidate files judged", 26385), ("original passed every gate", 6100),
              ("mutant killed, task kept", 4132)]
    ops = [("weaken_types", 1857, t["s1"]), ("implement_from_signature", 1407, t["s3"]),
           ("deprecate", 508, t["s2"]), ("hallucinate", 360, t["mute"])]
    W, L, R, H = 760, 210, 84, 232
    mx = 26385
    sx = lambda v: (W - L - R) * v / mx
    o = []
    for i, (k, v) in enumerate(stages):
        y = 14 + i * 38
        o += [text(k, L - 12, y + 14, t["mute"], 10, "end"),
              rect(L, y, sx(v), 19, t["s1"] if i == 2 else t["panel"]),
              text(f"{v:,}", L + sx(v) + 7, y + 14, t["ink"], 10, "start", "600")]
    o.append(f'<line x1="{L}" y1="140" x2="{W-R}" y2="140" stroke="{t["line2"]}"/>')
    o.append(text("tasks by operator", L - 12, 168, t["mute"], 10, "end"))
    x, tot = L, 4132
    for k, v, c in ops:
        w = (W - L - R) * v / tot
        o.append(rect(x, 156, w - 2, 21, c))
        if w > 96:   # anything narrower and the label runs into the next band
            o.append(text(k.replace("implement_from_signature", "implement_sig"),
                          x + 6, 192, t["faint"], 9))
        x += w
    o.append(text("4,132 tasks · 15.7% yield · zero teacher calls", L, 214, t["faint"], 9))
    return W, H, "".join(o)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    figs = {"fig1-funnel": fig_funnel, "fig2-validation": fig_val, "fig3-categories": fig_categories}
    for name, fn in figs.items():
        for mode, t in THEMES.items():
            w, h, body = fn(t)
            (OUT / f"{name}-{mode}.svg").write_text(svg(w, h, body, t))
    print(f"wrote {len(figs) * 2} SVGs to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
