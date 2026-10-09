"""The film — silent, subtitled, one character per scene. 22 scenes.

Scenes in `ORDER`; every subtitle is paired with its own animation in a single
`beat(text, fn)`. Subtitles are timed by syllable count (`syllables()/SPS`).

Render (from romania-video):
    ./render.sh                    # whole film
    ./render.sh scenes             # one mp4 per scene
    SCENES=sc_race .venv/bin/python -m manim -qh film.py Film   # one scene
"""
import os
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scene_kit import RoadMap, DATA, label, INK, MUTED, CYAN, GOLD, GREEN, PURPLE, RED  # noqa: E402
from manim import *  # noqa: E402

FONT = 'Avenir Next'
CHAR = ROOT.parent / 'character'
MAXW = 11.8
AUDIT = bool(os.environ.get('AUDIT'))


def km(a, b):
    return next(e['km'] for e in DATA['graph'][a]['edges'] if e['to'] == b)


def syllables(text):
    """Rough English syllable count: vowel groups, minus a silent final 'e'.

    Subtitle timing is driven by this instead of word count, so a line of long
    words holds longer than a line of short ones at the same word count.
    """
    n = 0
    for w in re.findall(r'[a-zA-Z]+', text.lower()):
        groups = len(re.findall(r'[aeiouy]+', w))
        if groups > 1 and w.endswith('e'):
            groups -= 1
        n += max(1, groups)
    return n


def subtitle(text, size=28):
    one = label(text, size, INK)
    if one.width <= MAXW:
        lines = [text]
    else:
        w = text.split()
        best, bw = None, 1e9
        for i in range(1, len(w)):
            a, b = ' '.join(w[:i]), ' '.join(w[i:])
            x = max(label(a, size, INK).width, label(b, size, INK).width)
            if x < bw:
                best, bw = (a, b), x
        lines = list(best)
    body = VGroup(*[label(l, size, INK) for l in lines]).arrange(DOWN, buff=0.14)
    box = SurroundingRectangle(body, color=BLACK, fill_color=BLACK, fill_opacity=0.6,
                               stroke_width=0, buff=0.20)
    return VGroup(box, body).to_edge(DOWN, buff=0.95)


def split_line(p, q, c1, c2, stroke=7, gap=0.045):
    d = np.array(q) - np.array(p)
    n = np.array([-d[1], d[0], 0.0])
    n = n / (np.linalg.norm(n) + 1e-9) * gap
    return VGroup(Line(p + n, q + n, color=c1, stroke_width=stroke),
                  Line(p - n, q - n, color=c2, stroke_width=stroke))


def code_panel(src, width=7.6, fs=17, lines=0.52, lang='typescript'):
    """A syntax-highlighted code card, sized to a fixed width."""
    return Code(code_string=src, language=lang, formatter_style='monokai',
                background='rectangle',
                background_config={'stroke_width': 0, 'fill_color': BLACK, 'fill_opacity': 0},
                add_line_numbers=False,
                paragraph_config={'font': 'Menlo', 'font_size': fs, 'line_spacing': lines}
                ).scale_to_fit_width(width)


def card(text, color, w=3.2, h=0.46, size=18, fill=None):
    r = RoundedRectangle(corner_radius=0.09, width=w, height=h, stroke_color=color,
                         stroke_width=2, fill_color=BLACK, fill_opacity=0.0)
    return VGroup(r, label(text, size, color).move_to(r))


def hl_lines(code, i0, i1, color=GOLD):
    return VGroup(*[SurroundingRectangle(code.code_lines[i], color=color,
                                         buff=0.045, stroke_width=2)
                    for i in range(i0, i1 + 1)])


def tag(text, size, color):
    """A map annotation. No background plate (only subtitles may be filled),
    so callers must place these clear of the geometry they label."""
    return label(text, size, color)


UCS_SRC = """\
while (frontier.length > 0) {
  frontier.sort((a, b) => a.cost - b.cost)
  const { id, cost } = frontier.shift()

  for (const edge of ROMANIA[id].edges) {
    const nc = cost + edge.km
    if (nc < reached[edge.to]) {
      reached[edge.to] = nc
      parent[edge.to] = id
      frontier.push({ id: edge.to, cost: nc })
    }
  }
}"""

ASTAR_SRC = """\
while (frontier.length > 0) {
  let bestI = 0
  for (let i = 1; i < frontier.length; i++)
    if (frontier[i][0] < frontier[bestI][0]) bestI = i

  const [f, g, current] = frontier[bestI]

  if (g > bestG[current]) continue    // stale copy

  for (const edge of ROMANIA[current].edges) {
    const ng = g + edge.km
    frontier.push([ng + h(edge.to, goal), ng, edge.to])
  }
}"""

BOUNDS_SRC = """\
function h(node, goal) {
  const lp = HEURISTIC_TABLE[node + "|" + goal]

  let alt = 0
  for (const L of landmarks) {
    const d = Math.abs(dist[L][node] - dist[L][goal])
    if (d > alt) alt = d
  }

  return Math.max(lp, alt)   // never overshoots
}"""

LINPROG_SRC = """\
def lp_value(a, b):
    ca, cb = coords[a], coords[b]
    res = linprog(
        edge_costs,                        # km per arrow
        A_eq=[xs, ys],                     # sum alpha*vec = chord
        b_eq=[cb[0] - ca[0], cb[1] - ca[1]],
        bounds=[(0, 1)] * len(edge_costs),
        method="highs",
    )
    return res.fun"""

BOTH_SRC = """\
while (frontF.length > 0 && frontB.length > 0) {
  if (Math.max(minF(frontF), minF(frontB)) >= mu) break

  // every expansion can improve the best route mu
  if (u in gOther) {
    const candidate = gu + gOther[u]
    if (candidate < mu) { mu = candidate; muNode = u }
  }
}"""


ORDER = ['sc_route', 'sc_explore', 'sc_ucsproof', 'sc_estimate', 'sc_twoways', 'sc_lpproof',
         'sc_triangle', 'sc_landmark', 'sc_max', 'sc_tightness', 'sc_code_search', 'sc_code_astar',
         'sc_code_bounds', 'sc_code_table', 'sc_code_both', 'sc_race', 'sc_cutwork',
         'sc_complexity', 'sc_guarantee', 'sc_bothends', 'sc_stop', 'sc_recap']
WHO = {'sc_route': ['Bird'], 'sc_explore': ['Bird'], 'sc_ucsproof': ['Bird'], 'sc_estimate': ['Bird'],
       'sc_twoways': ['Whale'], 'sc_lpproof': ['Whale'], 'sc_triangle': ['Whale'], 'sc_landmark': ['Whale'],
       'sc_max': ['Bird', 'Whale'],
       'sc_tightness': ['Whale'], 'sc_code_search': ['Whale'], 'sc_code_astar': ['Whale'],
       'sc_code_bounds': ['Whale'], 'sc_code_table': ['Whale'], 'sc_code_both': ['Whale'],
       'sc_race': ['Whale'], 'sc_cutwork': ['Bread'], 'sc_complexity': ['Bread'],
       'sc_guarantee': ['Bread'], 'sc_bothends': ['Bread'], 'sc_stop': ['Bread'], 'sc_recap': ['Bread']}


class Film(Scene):
    K = 1.3       # global slowdown factor for animations
    BEAT = 0.4    # pause right after a subtitle appears
    SPS = 4.2     # syllables per second -> each block's hold (calm 3b1b pace)
    MIN_HOLD = 0.8
    END = 1.1     # hold on a scene's final frame

    def play(self, *animations, **kwargs):
        if 'run_time' in kwargs:
            kwargs['run_time'] = kwargs['run_time'] * self.K
        return super().play(*animations, **kwargs)

    def wait(self, duration=DEFAULT_WAIT_TIME, stop_condition=None, frozen_frame=None):
        # Manim freezes the frame during a plain wait and, in doing so, stops
        # ticking mobject updaters. That would freeze the mascot and every loop
        # token between beats, so force updaters to keep running during holds.
        if AUDIT and duration >= 0.35:
            self._audit()
        return super().wait(duration, stop_condition=stop_condition, frozen_frame=False)

    def _audit(self):
        """Accumulate settled-frame collisions between text and graphics.

        Runs at the start of every substantial hold, i.e. exactly the frames the
        viewer reads. Text is compared against leaf geometry (lines, arrows,
        chips, ...) so large container groups do not produce meaningless hits;
        intentional text-on-node cases (map initials over their Dot) are
        excluded. Character (image) collisions are tracked separately.
        """
        try:
            from manim.mobject.text.text_mobject import Text as _T
        except Exception:
            return
        shapes = (Line, Arrow, Rectangle, RoundedRectangle, Circle, Polygon,
                  Triangle, Star, DashedLine, Arc, Square)
        texts, gr = [], []
        for m in self.mobjects:
            if m is self._sub or isinstance(m, Code):
                continue
            fam = m.get_family()
            if isinstance(m, ImageMobject):
                gr.append(('CHARACTER', m))
                continue
            t = [x for x in fam if isinstance(x, _T) and not getattr(x, 'map_label', False)]
            if t:
                texts.extend((getattr(x, 'text', '?'), x) for x in t)
                continue
            gr.extend((type(x).__name__, x) for x in fam
                      if isinstance(x, shapes) and not isinstance(x, Dot))

        def box(m):
            return (m.get_left()[0], m.get_right()[0], m.get_bottom()[1], m.get_top()[1])

        def area(a):
            return max((a[1] - a[0]) * (a[3] - a[2]), 1e-6)

        def shrink(a, f=0.08):
            dx, dy = (a[1] - a[0]) * f, (a[3] - a[2]) * f
            return (a[0] + dx, a[1] - dx, a[2] + dy, a[3] - dy)

        def crosses_rect(gm, r):
            """True if geometry actually passes through the rect (sample the
            path densely), not merely if bounding boxes overlap."""
            P = gm.get_all_points()
            if len(P) == 0:
                return False
            pts = list(P)
            for a, b in zip(P, P[1:]):
                for t in np.linspace(0, 1, 6)[1:-1]:
                    pts.append(a + (b - a) * t)
            return any(r[0] < p[0] < r[1] and r[2] < p[1] < r[3] for p in pts)

        for txt, tm in texts:
            tr = shrink(box(tm))
            for gt, gm in gr:
                if gt == 'CHARACTER':
                    continue
                if isinstance(gm, (Rectangle, RoundedRectangle, Square)):
                    gb = box(gm)
                    hit = (tr[0] < gb[0] and tr[1] > gb[1] and tr[2] < gb[2] and tr[3] > gb[3])
                    hit = bool(hit) or crosses_rect(gm, tr)
                else:
                    hit = crosses_rect(gm, tr)
                if hit:
                    key = ('TEXT', txt[:30], gt)
                    self._hits[key] = max(self._hits.get(key, 0.0), round(area(tr) / area(box(tm)), 2))
        # character vs text (both are blobs, so bounding boxes are the right test)
        for gt, gm in gr:
            if gt != 'CHARACTER':
                continue
            cb = box(gm)
            for txt, tm in texts:
                tb = box(tm)
                w = min(cb[1], tb[1]) - max(cb[0], tb[0])
                h = min(cb[3], tb[3]) - max(cb[2], tb[2])
                if w > 0.04 and h > 0.04:
                    key = ('CHARACTER', 'x', f'TEXT "{txt[:24]}"')
                    self._hits[key] = max(self._hits.get(key, 0.0), round(w * h / area(cb), 2))

    def construct(self):
        self._sub = None
        self._scene = '?'
        names = os.environ.get('SCENES', '').split(',') if os.environ.get('SCENES') else ORDER
        for name in names:
            self._sub = None
            self._scene = name
            self._hits = {}
            self._speaker(WHO[name])
            getattr(self, name)()
            if AUDIT and self._hits:
                print(f'[AUDIT {name}] {len(self._hits)} collision types')
                for (kind, what, gt), frac in sorted(self._hits.items(), key=lambda kv: -kv[1])[:12]:
                    print(f'    {frac:4.2f} frac  {kind:9s} "{what}"  x  {gt}')
            self.wait(self.END)
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _speaker(self, who):
        self.mc = None
        xs = [LEFT * 6.55, LEFT * 5.75]
        for i, name in enumerate(who):
            m = ImageMobject(str(CHAR / f'cast_{name}.png')).set_z_index(20)
            m.scale_to_fit_height(0.72)
            m.move_to(xs[i] + DOWN * 2.75)
            base = m.get_center().copy()
            m.add_updater(lambda mm, b=base: mm.move_to(
                b + UP * 0.20 * np.sin(self.time * 2.3) + RIGHT * 0.12 * np.sin(self.time * 3.5)))
            self.add(m)
            if self.mc is None:
                self.mc = m

    def sub(self, text):
        s = subtitle(text)
        if self._sub is not None:
            self.play(FadeOut(self._sub), run_time=0.2)
        self.play(FadeIn(s, shift=UP * 0.06), run_time=0.25)
        self._sub = s
        self.wait(self.BEAT)

    def beat(self, text, fn=None, hold=None):
        self.sub(text)
        if fn is not None:
            fn()
        if hold is None:
            hold = max(self.MIN_HOLD, syllables(text) / self.SPS)
        self.wait(hold)

    def title(self, text):
        self.add(label(text, 30, INK).to_corner(UL, buff=0.5))

    def diagram(self, width=7.2, center=LEFT * 3.0 + UP * 0.2):
        d = RoadMap(width=width, center=center, initials=True)
        self.play(FadeIn(d), run_time=0.6)
        return d

    def counter(self, caption, color, pos, unit=""):
        if caption:
            self.add(label(caption, 20, MUTED).move_to(pos + UP * 0.42))
        tr = ValueTracker(0)
        txt = Text(f"0{unit}", font=FONT, font_size=38, color=color).move_to(pos)
        txt.add_updater(lambda m: m.become(
            Text(f"{int(round(tr.get_value()))}{unit}", font=FONT, font_size=38, color=color).move_to(pos)))
        self.add(txt)
        return tr

    def bar(self, value, y, color, text, scale, x0=-6.4, rt=0.5):
        b = Rectangle(width=max(value * scale, 1e-3), height=0.34, fill_color=color,
                      fill_opacity=0.95, stroke_width=0).move_to([x0 + value * scale / 2, y, 0])
        t = label(text, 20, color).next_to(b, UP, buff=0.06).align_to(b, LEFT)
        self.play(GrowFromEdge(b, LEFT), FadeIn(t), run_time=rt)
        return b, t

    def token(self, points, color, speed=1.6, r=0.1):
        """A dot that loops forever along a polyline — keeps a beat's diagram alive.

        Uses move_to only, so the dot's opacity is untouched and the scene-end
        FadeOut still works without clearing updaters.
        """
        pts = [np.array(p, dtype=float) for p in points]
        segs = list(zip(pts, pts[1:]))
        lens = [np.linalg.norm(b - a) for a, b in segs]
        tot = sum(lens)
        d = Dot(pts[0], radius=r, color=color).set_z_index(7)

        def upd(m):
            x = (self.time * speed) % tot
            for (a, b), ln in zip(segs, lens):
                if x <= ln:
                    m.move_to(a + (b - a) * (x / ln))
                    return
                x -= ln
        d.add_updater(upd)
        return d

    # ── scenes ────────────────────────────────────────────────────────────────
    def sc_route(self):
        self.title('Which route is cheapest?')
        r1 = ['Arad', 'Sibiu', 'Fagaras', 'Bucharest']
        r2 = ['Arad', 'Sibiu', 'Rimnicu Vilcea', 'Pitesti', 'Bucharest']
        box, drawn = {}, {}

        def start():
            box['d'] = self.diagram()
            self.play(Indicate(box['d'].nodes['Arad'], color=GREEN),
                      Indicate(box['d'].nodes['Bucharest'], color=RED), run_time=0.6)
        self.beat("From Arad, we want to reach Bucharest.", start)

        def gold():
            t1 = self.counter("", GOLD, RIGHT * 3.4 + UP * 1.1, unit=" km")
            tot = 0
            for a, b in zip(r1, r1[1:]):
                tot += km(a, b)
                mob = Line(box['d'].points_by_city[a], box['d'].points_by_city[b], color=GOLD, stroke_width=7).set_z_index(2)
                drawn[frozenset((a, b))] = mob
                self.play(Create(mob), t1.animate.set_value(tot), run_time=0.6)
        self.beat("Three roads look shorter than four.", gold)
        self.beat("Yet those three roads cost 450 kilometres.")

        def purple():
            t2 = self.counter("", PURPLE, RIGHT * 3.4 + UP * 0.2, unit=" km")
            tot = 0
            for a, b in zip(r2, r2[1:]):
                tot += km(a, b)
                key = frozenset((a, b))
                p, q = box['d'].points_by_city[a], box['d'].points_by_city[b]
                if key in drawn:
                    self.remove(drawn[key])
                    mob = split_line(p, q, GOLD, PURPLE).set_z_index(2)
                    self.add(mob)
                    self.play(Indicate(mob), t2.animate.set_value(tot), run_time=0.5)
                else:
                    mob = Line(p, q, color=PURPLE, stroke_width=7).set_z_index(2)
                    self.play(Create(mob), t2.animate.set_value(tot), run_time=0.6)
                drawn[key] = mob
            self.add(self.token([box['d'].points_by_city[c] for c in r2], GREEN, speed=1.5))
        self.beat("The four-road route costs just 418.", purple)
        self.beat("We want less distance, not fewer roads.")

    def sc_explore(self):
        self.title('Explore by cost')
        d = self.diagram()
        ucs = DATA['demo']['algos']['ucs']['steps']
        costs = {'Arad': 0}
        st = {'n': 0}
        explored = self.counter('explored', PURPLE, RIGHT * 3.4 + UP * 1.5)
        gcost = self.counter('cost so far', GOLD, RIGHT * 3.4 + UP * 0.5, unit=" km")

        def expand():
            for step in ucs:
                cur = step['current']
                self.play(Indicate(d.nodes[cur], color=PURPLE, scale_factor=1.3), run_time=0.25)
                gcost.set_value(costs[cur])
                if cur != 'Bucharest':      # stop at the goal: no stray edges past it
                    for e in DATA['graph'][cur]['edges']:
                        nb = e['to']
                        c = costs[cur] + e['km']
                        if c < costs.get(nb, 1e9):
                            costs[nb] = c
                            self.add(Line(d.points_by_city[cur], d.points_by_city[nb], color=PURPLE, stroke_width=4).set_z_index(1))
                st['n'] += 1
                explored.set_value(st['n'])
                self.wait(0.15)
        self.beat("At Arad, no travel cost has accumulated.")
        self.beat("Extend the lowest-cost route so far.", expand)
        self.beat("This rule defines uniform cost search.",
                  lambda: self.play(FadeIn(label('priority = g', 24, PURPLE).move_to(RIGHT * 3.4 + DOWN * 0.7)), run_time=0.4))
        self.beat("The first goal it settles is optimal.",
                  lambda: self.play(FadeIn(label('optimal   complete', 24, GREEN).move_to(RIGHT * 3.4 + DOWN * 1.5)), run_time=0.4))

        def waste():
            for rt in (['Arad', 'Timisoara', 'Lugoj'], ['Arad', 'Zerind', 'Oradea']):
                for a, b in zip(rt, rt[1:]):
                    self.play(Create(Line(d.points_by_city[a], d.points_by_city[b], color=PURPLE, stroke_width=4).set_z_index(1)), run_time=0.35)
        self.beat("Without a guide, it spreads in all directions.", waste)

    def sc_ucsproof(self):
        self.title('Why cheapest-first works')
        pts = [LEFT * 6.0 + UP * 0.4, LEFT * 1.6 + UP * 0.4, RIGHT * 3.0 + UP * 0.4]
        for p, t in zip(pts, ['start', 'frontier', 'goal']):
            self.add(Dot(p, color=PURPLE), label(t, 20, MUTED).next_to(p, DOWN, buff=0.25))
        self.beat("Why does choosing by cost work?",
                  lambda: self.play(Create(Line(pts[0], pts[1], color=PURPLE, stroke_width=5)), run_time=0.5))
        self.beat("Suppose it chooses a goal too soon.",
                  lambda: (self.play(Create(Line(pts[0], pts[2], color=GREEN, stroke_width=5)), run_time=0.5),
                           self.add(self.token([pts[0], pts[2]], INK)),
                           self.add(tag('picked first', 18, GREEN).move_to((pts[0] + pts[2]) / 2 + UP * 0.45))))
        self.beat("A cheaper route must remain unfinished.",
                  lambda: (self.play(Create(DashedLine(pts[1], pts[2], color=GOLD)), run_time=0.5),
                           self.add(self.token([pts[0], pts[1], pts[2]], GOLD)),
                           self.add(tag('still hidden', 18, GOLD).move_to((pts[1] + pts[2]) / 2 + DOWN * 0.5))))
        self.beat("Its frontier city has a lower cost.",
                  lambda: self.play(Indicate(Dot(pts[1], color=GOLD), color=GOLD), run_time=0.6))
        self.beat("That city must come first, a contradiction.",
                  lambda: self.add(label('chosen first  →  contradiction', 22, RED).move_to(DOWN * 1.3)))

    def sc_estimate(self):
        self.title('Guide with an estimate')
        d = self.diagram(width=7.2)
        lbls = []

        def b1():
            ga = DoubleArrow(d.nodes['Arad'], d.nodes['Rimnicu Vilcea'], buff=0.16,
                             color=PURPLE, stroke_width=6).set_z_index(4)
            self.play(Indicate(d.nodes['Arad'], color=PURPLE),
                      Indicate(d.nodes['Rimnicu Vilcea'], color=PURPLE),
                      Create(ga), run_time=0.7)
            l = tag('g = 220', 20, PURPLE).move_to(RIGHT * 1.4 + UP * 1.35)
            lbls.extend([ga, l])
            self.add(l)
        self.beat("Reaching Rimnicu Vilcea has cost 220.", b1)

        def b2():
            ha = DoubleArrow(d.nodes['Rimnicu Vilcea'], d.nodes['Bucharest'], buff=0.16,
                             color=GOLD, stroke_width=6).set_z_index(4)
            self.play(Indicate(d.nodes['Rimnicu Vilcea'], color=GOLD),
                      Indicate(d.nodes['Bucharest'], color=GOLD),
                      Create(ha), run_time=0.7)
            l = tag('h = 198', 20, GOLD).move_to(RIGHT * 1.4 + UP * 0.55)
            lbls.extend([ha, l])
            self.add(l)
        self.beat("Estimate the rest: about 198.", b2)

        def b3():
            self.play(*[FadeOut(m) for m in [d, *lbls]], run_time=0.4)
            self.bar(220, 1.5, PURPLE, 'g  already paid   220', 6.0 / 450)
            self.bar(198, 0.5, GOLD, 'h  estimated left   198', 6.0 / 450)
        self.beat("Combine cost so far with cost still to come.", b3)
        self.beat("A* ranks routes by their sum: f = g + h.",
                  lambda: self.bar(418, -0.6, GREEN, 'f = g + h   418', 6.0 / 450))

    def sc_twoways(self):
        self.title('Two ways to estimate the rest')

        def b1():
            self.add(label('LP  (vectors)', 24, CYAN).move_to(LEFT * 4.0 + UP * 2.6))
            p = LEFT * 6.4 + DOWN * 0.3
            for vec, c in [(RIGHT * 1.5 + UP * 1.1, PURPLE), (RIGHT * 1.7, GOLD), (RIGHT * 0.9 + DOWN * 0.9, GREEN)]:
                self.play(GrowArrow(Arrow(p, p + vec, buff=0, color=c, stroke_width=6)), run_time=0.35)
                p += vec
            self.play(GrowArrow(Arrow(LEFT * 6.4 + DOWN * 0.3, p, buff=0, color=CYAN, stroke_width=3)), run_time=0.4)
        self.beat("Allow fractional amounts of road vectors.", b1)
        self.beat("The cheapest combination costs 388.",
                  lambda: self.add(label('min  Σ α·cost  →  388', 20, CYAN).move_to(LEFT * 4.0 + DOWN * 1.7)))

        def b3():
            self.add(label('ALT  (landmark)', 24, GOLD).move_to(RIGHT * 3.6 + UP * 2.6))
            for yy, t in [(1.2, 'd(Giurgiu, Bucharest) = 90'), (0.4, 'd(Giurgiu, Arad) = 508')]:
                self.play(FadeIn(label(t, 20, GOLD).move_to(RIGHT * 3.6 + UP * yy)), run_time=0.35)
        self.beat("Alternatively, use distances from a landmark.", b3)
        self.beat("Their difference gives a bound of 418.",
                  lambda: self.play(FadeIn(label('difference = 418', 22, GOLD).move_to(RIGHT * 3.6 + DOWN * 0.6)), run_time=0.4))

    def sc_lpproof(self):
        self.title('Why the LP is a lower bound')
        width, center = 7.6, RIGHT * 1.5 + UP * 0.35
        cities = ['Arad', 'Sibiu', 'Rimnicu Vilcea', 'Pitesti', 'Bucharest']
        pt = {c: np.array([(DATA['graph'][c]['x'] - 2043) / 2540 * width,
                           -(DATA['graph'][c]['y'] - 1254) / 2540 * width, 0]) + center
              for c in cities}
        a, b = pt['Arad'], pt['Bucharest']
        dhat = (b - a) / np.linalg.norm(b - a)
        normal = np.array([-dhat[1], dhat[0], 0])
        if normal[1] < 0:
            normal = -normal
        pairs = list(zip(cities, cities[1:]))
        kms = [km(u, v) for u, v in pairs]
        colors = [CYAN, GOLD, PURPLE, GREEN]
        tr = ValueTracker(0.0)

        def endpoints(u, p):
            proj = np.dot(pt[p] - a, dhat) * dhat
            return a + (pt[p] - a) * (1 - u) + proj * u

        def chain_at(u):
            return VGroup(*[Arrow(endpoints(u, p), endpoints(u, q), buff=0, color=col,
                                  stroke_width=5).set_z_index(3)
                            for (p, q), col in zip(pairs, colors)])

        def labels_at(u):
            return VGroup(*[label(str(k), 20, col).set_z_index(6).move_to(
                (endpoints(u, p) + endpoints(u, q)) / 2 + normal * 0.34)
                for (p, q), k, col in zip(pairs, kms, colors)])

        chain = chain_at(0)
        kml = labels_at(0)
        for m in (chain, kml):
            m.add_updater(lambda mm, f=(chain_at if m is chain else labels_at): mm.become(f(tr.get_value())))

        def draw():
            self.add(VGroup(*[Dot(pt[c], radius=0.075, color=INK).set_z_index(5) for c in cities]))
            self.add(label('a', 20, INK).move_to(pt['Arad'] + normal * 0.34),
                     label('b', 20, INK).move_to(pt['Bucharest'] + normal * 0.34),
                     label('Arad', 17, MUTED).move_to(pt['Arad'] - normal * 0.36),
                     label('Bucharest', 17, MUTED).move_to(pt['Bucharest'] - normal * 0.36))
            self.bdot = Dot(b, color=GREEN, radius=0.1).set_z_index(7)
            self.add(chain, kml)
        self.beat("Place the route's road arrows head to tail.", draw)
        self.beat("Together, they reach Bucharest exactly.",
                  lambda: self.play(Indicate(self.bdot, color=GREEN, scale_factor=2.0), run_time=0.6))

        chord = DashedLine(a, b, color=GOLD, stroke_width=3).set_z_index(2)
        self.beat("Their vector sum spans the start-to-goal gap.",
                  lambda: (self.play(Create(chord), run_time=0.6),
                           self.add(label('the gap', 20, GOLD).move_to((a + b) / 2 + normal * 0.95))))

        read = label('real route   140+80+97+101 = 418', 20, INK).set_z_index(6).move_to(DOWN * 2.45)
        self.add(read)
        self.beat("Now allow fractional amounts of each arrow.",
                  lambda: self.play(tr.animate.set_value(0.55), run_time=1.0, rate_func=smooth))
        self.beat("The minimum falls from 418 to 388.",
                  lambda: self.play(tr.animate.set_value(1.0),
                                    Transform(read, label('cheapest mixture  =  388', 20, PURPLE).set_z_index(6).move_to(DOWN * 2.45)),
                                    run_time=1.6, rate_func=smooth))
        chain.clear_updaters()
        kml.clear_updaters()
        self.beat("This minimum cannot exceed a real route's cost.",
                  lambda: self.play(FadeIn(label('never overshoots the goal', 24, GREEN).move_to(RIGHT * 4.6 + UP * 2.0)), run_time=0.4))

    def sc_triangle(self):
        self.title('Why subtract landmark distances')
        L = LEFT * 5.4 + UP * 1.3
        n = LEFT * 6.2 + DOWN * 1.2
        t = RIGHT * 0.8 + DOWN * 1.2
        for p, name, d in [(L, 'L', UP), (n, 'n', DOWN), (t, 't', UP)]:
            self.add(Dot(p, color=MUTED), label(name, 24).next_to(p, d, buff=0.15))
        self.beat("Why use the difference in distances?",
                  lambda: (self.play(Create(Line(L, t, color=GREEN, stroke_width=5)), run_time=0.5),
                           self.add(self.token([L, t], GOLD)),
                           self.add(tag('d(L,t)', 20, GREEN).move_to((L + t) / 2 + UP * 0.35))))
        self.beat("Going via t cannot shorten the shortest path.",
                  lambda: (self.play(Create(Line(L, n, color=CYAN, stroke_width=5)), run_time=0.5),
                           self.add(tag('d(L,n)', 20, CYAN).move_to((L + n) / 2 + LEFT * 0.7))))
        self.beat("Thus d(L,n) ≤ d(L,t) + d(t,n).",
                  lambda: (self.play(Create(Line(n, t, color=RED, stroke_width=5)), run_time=0.5),
                           self.add(self.token([L, n, t], GOLD)),
                           self.add(tag('d(n,t)', 20, RED).move_to((n + t) / 2 + UP * 0.30))))
        self.beat("Swap n and t, then rearrange both inequalities.", lambda: self.add(
            VGroup(label('|', 28, INK), label('d(L,n)', 28, CYAN), label('  −  ', 28, INK),
                   label('d(L,t)', 28, GREEN), label('|   ≤   ', 28, INK),
                   label('d(n,t)', 28, RED)).arrange(RIGHT, buff=0.06).move_to([0, -1.7, 0])))
        self.beat("So |d(L,n) − d(L,t)| ≤ d(n,t).")

    def sc_landmark(self):
        self.title('One landmark, one triangle')
        L = np.array([-4.6, -1.9, 0.0])
        n = np.array([-2.1, 0.4, 0.0])
        t = np.array([2.2, 0.5, 0.0])

        star = Star(n=5, outer_radius=0.2, color=GOLD, fill_opacity=1).set_z_index(5).move_to(L)
        dn = Dot(n, color=CYAN, radius=0.1).set_z_index(5)
        dt = Dot(t, color=GREEN, radius=0.1).set_z_index(5)
        marks = VGroup(label('L', 22, GOLD).next_to(star, DOWN, buff=0.12),
                       label('n', 22, CYAN).next_to(dn, LEFT, buff=0.12),
                       label('t', 22, GREEN).next_to(dt, UP, buff=0.12))
        poly = Polygon(L, n, t, color=CYAN, stroke_width=4)
        seed = Triangle(color=CYAN, stroke_width=3).scale_to_fit_height(0.28).move_to(n)

        def morph():
            self.play(FadeIn(star), FadeIn(dn), FadeIn(dt), FadeIn(marks), run_time=0.4)
            self.play(ReplacementTransform(seed, poly), run_time=0.8)
        self.beat("The landmark forms a triangle with n and t.", morph)

        # Plain lines (no arrowheads) so the swiped arm does not leave a tip
        # sitting on top of the red leftover segment.
        arm_n = Line(L, n, color=CYAN, stroke_width=5).set_z_index(5)
        arm_t = Line(L, t, color=GREEN, stroke_width=5).set_z_index(4)
        ln = tag('d(L,n)', 20, CYAN).move_to((L + n) / 2 + LEFT * 0.85)
        lt = tag('d(L,t)', 20, GREEN).move_to((L + t) / 2 + DOWN * 0.45)

        def arms():
            self.play(Create(arm_n), Create(arm_t), run_time=0.6)
            self.play(FadeIn(ln), FadeIn(lt), run_time=0.3)
        self.beat("Its arms measure distances to n and t.", arms)

        def ang(v):
            return np.arctan2(v[1], v[0])
        delta = float(ang(n - L) - ang(t - L))

        def swipe():
            self.play(FadeOut(lt), Rotate(arm_t, angle=delta, about_point=L), run_time=1.1)
        self.beat("Align the arms to compare their lengths.", swipe)

        over = Line(n, arm_t.get_end(), color=RED, stroke_width=10).set_z_index(6)

        def leftover():
            self.play(Create(over), run_time=0.4)
            self.add(tag('the leftover', 20, RED).move_to(over.get_center() + RIGHT * 0.6 + DOWN * 0.66))
        self.beat("The red remainder is their length difference.", leftover)

        def compare():
            self.play(Create(Line(n, t, color=RED, stroke_width=5)), run_time=0.4)
            self.add(tag('d(n,t)', 20, RED).move_to((n + t) / 2 + DOWN * 0.4))
            x0, y1, y2 = 0.6, -1.45, -2.15
            ol, nl = over.get_length(), float(np.linalg.norm(t - n))
            ob = Line([x0, y1, 0], [x0 + ol, y1, 0], color=RED, stroke_width=9).set_z_index(6)
            nb = Line([x0, y2, 0], [x0 + nl, y2, 0], color=RED, stroke_width=6).set_z_index(6)
            self.play(Create(ob), Create(nb), run_time=0.5)
            self.add(label('leftover', 18, RED).next_to(ob, UP, buff=0.08).align_to(ob, LEFT),
                     label('d(n,t)', 18, RED).next_to(nb, DOWN, buff=0.08).align_to(nb, LEFT),
                     VGroup(label('|', 24, INK), label('d(L,n)', 24, CYAN), label(' − ', 24, INK),
                            label('d(L,t)', 24, GREEN), label('| ≤ ', 24, INK),
                            label('d(n,t)', 24, RED)).arrange(RIGHT, buff=0.05).move_to([1.0, 3.4, 0]))
        self.beat("That remainder cannot exceed d(n,t).", compare)

    def sc_max(self):
        self.title('Keep the maximum')
        x0, span = -6.2, 6.4

        def b1():
            self.play(Create(Line([x0, 1.7, 0], [x0 + span, 1.7, 0], color=INK, stroke_width=4)), run_time=0.5)
            self.add(label('true distance  d', 20, INK).move_to([x0 + 1.6, 1.95, 0]))
        self.beat("Neither bound exceeds the true distance.", b1)

        def b2():
            self.bar(388 / 418, 0.6, PURPLE, 'LP   388', span, x0)
            self.bar(418 / 418, -0.25, GOLD, 'ALT   418', span, x0)
        self.beat("Take whichever bound is larger.", b2)
        self.beat("Adding them could exceed the true distance.", lambda: self.play(
            FadeIn(label('388 + 418  overestimates', 22, RED).move_to(RIGHT * 5.0 + UP * 1.0)), run_time=0.4))
        self.beat("The maximum preserves both bounds' strengths.", lambda: self.play(
            FadeIn(label('max  =  both, combined', 24, GREEN).move_to(RIGHT * 5.0 + DOWN * 0.5)), run_time=0.4))

    def sc_tightness(self):
        self.title('How tight is the bound')
        x0, span = -5.4, 7.0

        def b1():
            self.play(Create(Line([x0, 1.5, 0], [x0 + span, 1.5, 0], color=INK, stroke_width=3)), run_time=0.4)
            self.add(label('true distance  =  1.0', 20, INK).move_to([x0 + 2.0, 1.72, 0]))
        self.beat("Compare each bound with the true distance.", b1)
        self.beat("The LP bound reaches 0.73.", lambda: self.bar(0.73, 0.8, PURPLE, 'LP   0.73', span, x0))
        self.beat("The landmark bound reaches 0.98.", lambda: self.bar(0.98, 0.0, GOLD, 'ALT   0.98', span, x0))
        self.beat("Their maximum also reaches 0.98.",
                  lambda: self.bar(0.98, -0.8, GREEN, 'max  ≥  0.98', span, x0))

    def sc_race(self):
        self.title('Watch it steer')
        left = RoadMap(width=5.0, center=LEFT * 4.1 + UP * 0.1, initials=True)
        right = RoadMap(width=5.0, center=RIGHT * 4.1 + UP * 0.1, initials=True)
        ucs = DATA['demo']['algos']['ucs']['steps']
        ast = DATA['demo']['algos']['astarAlt']['steps']
        gL, gR = iter(ucs), iter(ast)
        cL, cR = {'Arad': 0}, {'Arad': 0}
        st = {'L': 0, 'R': 0, 'sL': None, 'sR': None}

        def adv(dia, gen, costs, color, settle, n):
            step = next(gen, None)
            if step is None:
                return n
            cur = step['current']
            self.play(Indicate(dia.nodes[cur], color=color, scale_factor=1.3), run_time=0.25)
            if cur != 'Bucharest':          # stop expanding at the goal (no edges to U/G)
                for e in DATA['graph'][cur]['edges']:
                    nb = e['to']
                    c = costs[cur] + e['km']
                    if c < costs.get(nb, 1e9):
                        costs[nb] = c
                        self.add(Line(dia.points_by_city[cur], dia.points_by_city[nb], color=color, stroke_width=4).set_z_index(1))
            n += 1
            settle.set_value(n)
            self.wait(0.12)
            return n

        def race():
            self.add(label('uniform cost', 24, PURPLE).next_to(left, UP, buff=0.1),
                     label('A*  (guided)', 24, GREEN).next_to(right, UP, buff=0.1))
            st['sL'] = self.counter('explored', PURPLE, LEFT * 1.1 + UP * 2.6)
            st['sR'] = self.counter('explored', GREEN, RIGHT * 1.1 + UP * 2.6)
            for _ in range(len(ucs)):
                st['L'] = adv(left, gL, cL, PURPLE, st['sL'], st['L'])
                if st['R'] < len(ast):
                    st['R'] = adv(right, gR, cR, GREEN, st['sR'], st['R'])
        self.beat("The left search ranks by cost so far.", lambda: self.play(FadeIn(left), run_time=0.6))
        self.beat("The right also estimates distance to the goal.", lambda: self.play(FadeIn(right), run_time=0.6))
        self.beat("That guidance reduces the cities explored.", race)
        self.beat("13 versus 5, with the same 418 km route.")

    def sc_cutwork(self):
        self.title('Does it cut the work?')
        self.beat("These averages cover all 380 pairs.", lambda: self.bar(11, 1.0, PURPLE, 'uniform cost   11', 0.35, x0=-6.0))
        self.beat("Average work falls from 11 to 5.", lambda: self.bar(5, 0.1, GREEN, 'A* (guided)   5', 0.35, x0=-6.0))
        self.beat("Greedy is quicker, but wrong on 61 pairs.", lambda: self.bar(5, -0.8, RED, 'greedy   wrong on 61', 0.35, x0=-6.0))
        self.beat("UCS and A* remain optimal on all pairs.",
                  lambda: self.play(FadeIn(label('all optimal on 380 pairs', 24, GREEN).move_to(DOWN * 0.6)), run_time=0.4))

    def sc_complexity(self):
        self.title('Time and space')
        CL, CR = -3.7, 3.7
        Y = [1.7, 0.9, 0.1, -0.7]

        def layout(cx):
            return {
                'root': np.array([cx, Y[0], 0]),
                'l1': [np.array([cx + d, Y[1], 0]) for d in (-1.0, 1.0)],
                'l2': [np.array([cx + d, Y[2], 0]) for d in (-1.5, -0.5, 0.5, 1.5)],
                'l3': [np.array([cx + d, Y[3], 0]) for d in (-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75)],
            }

        def road(a, b, color='#53627A', w=2.4):
            return Line(a, b, color=color, stroke_width=w).set_z_index(1)

        def node(p, color=MUTED):
            return Dot(p, radius=0.085, color=color).set_z_index(3)

        def level_edges(P, i):
            if i == 1:
                return [(P['root'], P['l1'][0]), (P['root'], P['l1'][1])]
            if i == 2:
                return [(P['l1'][0], P['l2'][0]), (P['l1'][0], P['l2'][1]),
                        (P['l1'][1], P['l2'][2]), (P['l1'][1], P['l2'][3])]
            return [(P['l2'][k], P['l3'][2 * k]) for k in range(4)] + \
                   [(P['l2'][k], P['l3'][2 * k + 1]) for k in range(4)]

        def level_nodes(P, i):
            return [P['root']] if i == 0 else P[f'l{i}']

        L, R = layout(CL), layout(CR)
        timeL = label('time      O(b^d)', 20, PURPLE).move_to([CL, -1.35, 0])
        spaceL = label('space     O(b^d)', 20, PURPLE).move_to([CL, -1.85, 0])
        timeR = label('time      O(b^d)', 20, GREEN).move_to([CR, -1.35, 0])
        spaceR = label('space     O(b^d)', 20, GREEN).move_to([CR, -1.85, 0])

        def start():
            self.play(FadeIn(label('blind search', 22, PURPLE).move_to([CL, 2.6, 0])),
                      FadeIn(label('A*  (heuristic)', 22, GREEN).move_to([CR, 2.6, 0])), run_time=0.4)
            self.play(FadeIn(node(L['root'], PURPLE)), run_time=0.2)
            for i in (1, 2, 3):
                self.play(LaggedStart(*[Create(road(a, b)) for a, b in level_edges(L, i)],
                                      *[FadeIn(node(p, PURPLE)) for p in level_nodes(L, i)],
                                      lag_ratio=0.1), run_time=0.55)
        self.beat("Unguided search fills all 15 nodes here.", start)

        self.beat("Worst-case time and space are both O(b^d).",
                  lambda: self.play(FadeIn(timeL), FadeIn(spaceL), run_time=0.4))

        def narrow():
            path = [(R['root'], R['l1'][0]), (R['l1'][0], R['l2'][0]), (R['l2'][0], R['l3'][0])]
            self.play(LaggedStart(*[Create(road(a, b, GREEN, 3.5)) for a, b in path],
                                  *[FadeIn(node(p, GREEN)) for p in (R['root'], R['l1'][0], R['l2'][0])],
                                  lag_ratio=0.15), run_time=0.7)
            self.play(FadeIn(node(R['l3'][0], GREEN)),
                      FadeIn(Star(n=5, outer_radius=0.16, color=GREEN, fill_opacity=1).move_to(R['l3'][0])),
                      run_time=0.3)
            self.play(Create(road(R['root'], R['l1'][1], GOLD, 3.0)),
                      FadeIn(node(R['l1'][1], GOLD)), run_time=0.35)
            self.add(self.token([R['root'], R['l1'][0], R['l2'][0], R['l3'][0]], GREEN, speed=1.2))
        self.beat("A*'s estimate focuses this search on 5 nodes.", narrow)

        self.beat("That is a third as many expansions here.",
                  lambda: self.play(FadeIn(card('15 nodes', PURPLE, w=2.0, size=20).move_to([CL, 2.15, 0])),
                                    FadeIn(card('5 nodes   3x fewer', GREEN, w=3.1, size=18).move_to([CR, 2.15, 0])),
                                    FadeIn(timeR), FadeIn(spaceR), run_time=0.5))

        self.beat("Its frontier can still need O(b^d) memory.",
                  lambda: self.play(FadeIn(tag('same memory', 20, GOLD).move_to([0, -1.85, 0])),
                                    Indicate(spaceL, color=PURPLE), Indicate(spaceR, color=GREEN),
                                    run_time=0.7))

    def sc_guarantee(self):
        self.title('Why an honest guess stays optimal')
        self.beat("Suppose A* chooses the 450 route too soon.",
                  lambda: self.bar(450, -1.0, PURPLE, 'selected goal   450', 6.0 / 450, x0=-6.4))
        self.beat("The 418 route still has a frontier city.",
                  lambda: self.bar(418, 0.2, GREEN, 'optimal   418', 6.0 / 450, x0=-6.4))
        self.beat("That city's f cannot exceed 418.",
                  lambda: self.bar(418, 1.2, GOLD, 'frontier  ≤  418', 6.0 / 450, x0=-6.4))
        self.beat("It must come first, a contradiction.",
                  lambda: self.add(label('contradiction  →  optimal', 24, GREEN).move_to(RIGHT * 3.6 + UP * 0.5)))

    def sc_bothends(self):
        self.title('Search from both ends')
        box = {}
        self.beat("We can also explore from both endpoints.", lambda: box.__setitem__('d', self.diagram(width=7.0)))

        def fronts():
            d = box['d']
            costs = [{'Arad': 0}, {'Bucharest': 0}]
            for i, step in enumerate(DATA['demo']['algos']['biastar']['steps'][:-1]):
                side = i % 2
                color = [CYAN, GOLD][side]
                cur = step['current']
                self.play(Indicate(d.nodes[cur], color=color, scale_factor=1.3), run_time=0.3)
                for e in DATA['graph'][cur]['edges']:
                    nb = e['to']
                    c = costs[side][cur] + e['km']
                    if c < costs[side].get(nb, 1e9):
                        costs[side][nb] = c
                        self.add(Line(d.points_by_city[cur], d.points_by_city[nb], color=color, stroke_width=4).set_z_index(1))
            route = [d.points_by_city[c] for c in ['Arad', 'Sibiu', 'Rimnicu Vilcea', 'Pitesti', 'Bucharest']]
            self.add(self.token(route, CYAN, speed=1.4), self.token(route[::-1], GOLD, speed=1.4))
        self.beat("Begin a second search at Bucharest.", fronts)
        self.beat("Joining the fronts gives a candidate route.",
                  lambda: self.add(label('the fronts meet  →  a route', 24, GREEN).move_to(RIGHT * 3.3 + UP * 0.6)))
        self.beat("A meeting alone does not prove it optimal.")

    def sc_stop(self):
        self.title('When can we stop?')
        box = {}

        def b1():
            box['bound'] = self.counter('frontier bound', GOLD, LEFT * 4.2 + UP * 0.6)
            box['best'] = self.counter('best route found', GREEN, RIGHT * 4.2 + UP * 0.6)
            box['best'].set_value(418)
        self.beat("Could an unfinished route still be cheaper?", b1)
        self.beat("The frontier bound limits unfinished routes.", lambda: box['bound'].set_value(120))
        self.beat("Stop when the bound reaches the route cost.",
                  lambda: self.play(box['bound'].animate.set_value(418), run_time=1.6))
        self.beat("At 418, no cheaper route can remain.",
                  lambda: self.add(label('reaches it  →  stop', 26, GREEN).move_to(DOWN * 0.6)))

    # ── implementation section ────────────────────────────────────────────────
    def sc_code_search(self):
        self.title('Inside the search')
        code = code_panel(UCS_SRC).move_to(LEFT * 3.55 + UP * 0.45)
        self.play(FadeIn(code), run_time=0.5)
        fx = RIGHT * 4.4
        self.add(label('frontier', 22, MUTED).move_to(fx + UP * 2.45))
        arad = card('Arad   0', PURPLE, w=2.6).move_to(fx + UP * 1.65)
        self.beat("Pending routes share a frontier list.",
                  lambda: self.play(FadeIn(arad), run_time=0.4))

        def take():
            b = hl_lines(code, 1, 2)
            self.play(Create(b), run_time=0.35)
            self.play(FadeOut(arad), FadeOut(b), run_time=0.3)
        self.beat("Sort by cost and remove the first entry.", take)

        def relax():
            b = hl_lines(code, 6, 9, GREEN)
            self.play(Create(b), run_time=0.4)
            sib = card('Sibiu   140', GREEN, w=2.6).move_to(fx + UP * 1.0)
            tim = card('Timisoara   118', GREEN, w=2.6).move_to(fx + UP * 0.44)
            zer = card('Zerind   75', GREEN, w=2.6).move_to(fx + DOWN * 0.12)
            self.play(*[FadeIn(c, shift=UP * 0.1) for c in (sib, tim, zer)], run_time=0.4)
            self.wait(0.2)
            self.play(zer.animate.move_to(fx + UP * 1.0), sib.animate.move_to(fx + DOWN * 0.12),
                      run_time=0.5)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Update neighbours when a cheaper route appears.", relax)
        self.beat("The lowest-cost route stays at the front.")

    def sc_code_astar(self):
        self.title('Adding the guess')
        code = code_panel(ASTAR_SRC).move_to(LEFT * 3.55 + UP * 0.45)
        self.play(FadeIn(code), run_time=0.5)
        fx = RIGHT * 4.4
        self.add(VGroup(label('f', 26, GREEN), label(' = ', 26, INK), label('g', 26, PURPLE),
                        label(' + ', 26, INK), label('h', 26, GOLD)).arrange(RIGHT, buff=0.06)
                 .move_to(fx + UP * 2.45),
                 label('frontier   g → f', 20, MUTED).move_to(fx + UP * 1.95))

        sib = card('Sibiu   140 → 418', GREEN, w=2.9, size=16).move_to(fx + UP * 1.25)
        zer = card('Zerind   75 → 568', GOLD, w=2.9, size=16).move_to(fx + UP * 0.62)
        tim = card('Timisoara   118 → 654', MUTED, w=2.9, size=16).move_to(fx + DOWN * 0.01)
        self.beat("Sibiu's cost 140 becomes an f of 418.",
                  lambda: self.play(FadeIn(sib), run_time=0.4))

        def smallest():
            b = hl_lines(code, 1, 3)
            c = hl_lines(code, 5, 5, CYAN)
            self.play(Create(b), Create(c), run_time=0.4)
            self.play(Indicate(sib, color=GREEN, scale_factor=1.08), run_time=0.5)
            self.play(FadeOut(b), FadeOut(c), run_time=0.2)
        self.beat("Each turn takes the entry with smallest f.", smallest)

        def nearer():
            self.play(FadeIn(zer, shift=UP * 0.1), FadeIn(tim, shift=UP * 0.1), run_time=0.35)
            self.play(Indicate(zer, color=GOLD), run_time=0.5)
        self.beat("Zerind costs only 75, but its f is 568.", nearer)

        def stale():
            b = hl_lines(code, 7, 7, RED)
            old = card('Zerind   568', MUTED, w=2.9, size=16).move_to(fx + DOWN * 0.66)
            cross = Line(old.get_corner(DL) + RIGHT * 0.1, old.get_corner(UR) + LEFT * 0.1,
                         color=RED, stroke_width=3)
            self.play(Create(b), FadeIn(old), Create(cross), run_time=0.4)
            self.play(FadeOut(b), FadeOut(old), FadeOut(cross), run_time=0.3)
        self.beat("Discard stale entries with higher costs.", stale)

        def push():
            b = hl_lines(code, 10, 11, GOLD)
            new = card('Rimnicu V.   220 → 418', GREEN, w=2.9, size=16).move_to(fx + DOWN * 0.62)
            self.play(Create(b), run_time=0.35)
            self.play(FadeIn(new, shift=UP * 0.1), run_time=0.3)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Timisoara enters at cost 118, with f 654.", push)

    def sc_code_bounds(self):
        self.title('Where the guess comes from')
        code = code_panel(BOUNDS_SRC).move_to(LEFT * 3.55 + UP * 0.45)
        self.play(FadeIn(code), run_time=0.5)
        fx = RIGHT * 4.2
        lp = card('LP table   388', PURPLE, w=2.9).move_to(RIGHT * 2.7 + UP * 1.05)
        alt = card('landmarks   418', GOLD, w=3.0).move_to(RIGHT * 6.0 + UP * 1.05)
        best = card('take the larger   418', GREEN, w=4.2).move_to(fx + DOWN * 0.75)

        def two():
            self.play(FadeIn(lp), FadeIn(alt), run_time=0.4)
            self.play(GrowArrow(Arrow(lp.get_bottom(), best.get_corner(UL) + LEFT * 0.2, buff=0.08,
                                      color=PURPLE, stroke_width=4)),
                      GrowArrow(Arrow(alt.get_bottom(), best.get_corner(UR) + RIGHT * 0.2, buff=0.08,
                                      color=GOLD, stroke_width=4)), run_time=0.5)
            self.play(FadeIn(best), run_time=0.4)
        self.beat("The estimate takes the maximum of two bounds.", two)

        def read_table():
            b = hl_lines(code, 1, 1)
            self.play(Create(b), Indicate(lp, color=PURPLE), run_time=0.6)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("The offline LP table supplies 388.", read_table)

        def landmarks():
            b = hl_lines(code, 4, 6, CYAN)
            self.play(Create(b), Indicate(alt, color=GOLD), run_time=0.6)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Landmark distances supply 418.", landmarks)
        self.beat("Taking 418 preserves the lower-bound guarantee.",
                  lambda: self.play(Create(hl_lines(code, 9, 9, GREEN)), run_time=0.5))

    def sc_code_table(self):
        self.title('The table is built once')
        code = code_panel(LINPROG_SRC).move_to(LEFT * 3.55 + UP * 0.35)
        self.play(FadeIn(code), run_time=0.5)
        fx = RIGHT * 4.5
        boxes = [card('map of Romania', MUTED, w=3.0, size=19).move_to(fx + UP * 2.5),
                 card('46 road arrows', CYAN, w=3.0, size=19).move_to(fx + UP * 1.55),
                 card('LP solver', PURPLE, w=3.0, size=19).move_to(fx + UP * 0.6),
                 card('table   388', GREEN, w=3.0, size=19).move_to(fx + DOWN * 0.35)]
        links = [Arrow(boxes[i].get_bottom(), boxes[i + 1].get_top(), buff=0.06,
                       color=INK, stroke_width=3) for i in range(3)]

        def pipe():
            self.play(LaggedStart(*[FadeIn(b) for b in boxes], lag_ratio=0.15),
                      LaggedStart(*[GrowArrow(a) for a in links], lag_ratio=0.15), run_time=0.7)
        self.beat("Precompute the LP bounds before searching.", pipe)

        def arrows():
            b = hl_lines(code, 1, 3)
            self.play(Create(b), Indicate(boxes[1], color=CYAN), run_time=0.6)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Encode the map as 46 weighted arrows.", arrows)

        def solve():
            b = hl_lines(code, 4, 6)
            self.play(Create(b), Indicate(boxes[2], color=PURPLE), run_time=0.6)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Minimise the cost of a fractional mixture.", solve)
        self.beat("Store results such as 388 in the table.",
                  lambda: self.play(Create(hl_lines(code, 9, 9, GREEN)),
                                    Indicate(boxes[3], color=GREEN), run_time=0.7))

    def sc_code_both(self):
        self.title('Two fronts, one answer')
        code = code_panel(BOTH_SRC).move_to(LEFT * 3.55 + UP * 0.35)
        self.play(FadeIn(code), run_time=0.5)
        fx = RIGHT * 4.5
        lc = [card('Sibiu   140', CYAN, w=2.7, size=18).move_to(fx + LEFT * 1.55 + UP * 1.55),
              card('Rimnicu   220', CYAN, w=2.7, size=18).move_to(fx + LEFT * 1.55 + UP * 0.95)]
        rc = [card('Pitesti   101', GOLD, w=2.7, size=18).move_to(fx + RIGHT * 1.55 + UP * 1.55),
              card('Fagaras   211', GOLD, w=2.7, size=18).move_to(fx + RIGHT * 1.55 + UP * 0.95)]
        badge = card('the best route   418', GREEN, w=4.2).move_to(fx + DOWN * 0.7)

        def two():
            self.play(FadeIn(label('from Arad', 19, CYAN).move_to(fx + LEFT * 1.55 + UP * 2.1)),
                      FadeIn(label('from Bucharest', 19, GOLD).move_to(fx + RIGHT * 1.55 + UP * 2.1)),
                      *[FadeIn(c, shift=UP * 0.1) for c in lc + rc], run_time=0.5)
        self.beat("Maintain a search from each endpoint.", two)

        def combine():
            b = hl_lines(code, 1, 1)
            self.play(Create(b), run_time=0.4)
            self.play(GrowArrow(Arrow(lc[1].get_bottom(), badge.get_corner(UL) + LEFT * 0.2, buff=0.1,
                                      color=CYAN, stroke_width=4)),
                      GrowArrow(Arrow(rc[1].get_bottom(), badge.get_corner(UR) + RIGHT * 0.2, buff=0.1,
                                      color=GOLD, stroke_width=4)), run_time=0.5)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Each front bounds the whole trip.", combine)

        def halt():
            b = hl_lines(code, 5, 6, GREEN)
            self.play(Create(b), run_time=0.4)
            self.play(FadeIn(badge, shift=UP * 0.08), run_time=0.4)
            self.play(FadeOut(b), run_time=0.2)
        self.beat("Stop when a bound meets the best route.", halt)

    def sc_recap(self):
        self.title('What we gained')
        self.beat("Cost alone takes 13 expansions here.", lambda: self.play(
            FadeIn(label('explore by cost', 30, PURPLE).move_to(UP * 1.2)), run_time=0.4))
        self.beat("A lower-bound estimate guides the search.", lambda: self.play(
            FadeIn(label('guide with a safe estimate', 30, GOLD).move_to(UP * 0.3)), run_time=0.4))
        self.beat("Search both ends, then certify when to stop.", lambda: (
            self.play(FadeIn(label('combine two bounds', 30, GREEN).move_to(DOWN * 0.6)), run_time=0.4),
            self.play(FadeIn(label('search both ends', 30, CYAN).move_to(DOWN * 1.5)), run_time=0.4)))
        self.beat("5 expansions, the same 418 km route.", lambda: self.play(
            FadeIn(card('13 expansions', PURPLE, w=2.8, size=22).move_to(LEFT * 2.9 + DOWN * 2.4)),
            FadeIn(label('same 418 km route', 22, INK).move_to(DOWN * 2.4)),
            FadeIn(card('5 expansions', GREEN, w=2.8, size=22).move_to(RIGHT * 2.9 + DOWN * 2.4)),
            run_time=0.5))
