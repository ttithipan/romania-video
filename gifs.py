"""Animated GIFs for the romania-web guide sidebar.

Mirrors the *schematic* Romania map (same COORDS as ``src/romania.ts`` via
``project_data.json``) and the app's design tokens, so each loop reads as "the
same map" the sidebar describes.  Seven scenes, one per spec in
``romania-web/requests.txt``:

    UCSRings               output/gifs/ucs-cost-rings.gif
    AStarVsUCS             output/gifs/astar-vs-ucs.gif
    AdmissibleConsistent   output/gifs/admissible-consistent.gif
    LPVectorDecomposition  output/gifs/lp-vector-decomposition.gif
    ALTTriangleInequality  output/gifs/alt-triangle-inequality.gif
    EnsembleMax            output/gifs/ensemble-max.gif
    EnsemblePerformance    output/gifs/ensemble-performance.gif

Render everything with ``./render_gifs.sh`` (writes the GIFs into
``output/gifs/``; ``PUBLISH=1 ./render_gifs.sh`` also copies them into
``../romania-web/public/gifs/``).  Preview one scene in-process:

    .venv/bin/manim render -r 720,460 --fps 13 --format mp4 gifs.py UCSRings
"""
import heapq
import json
from pathlib import Path

import numpy as np
from manim import *
from manim.utils.color import interpolate_color

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'project_data.json').read_text())
GRAPH = DATA['graph']
DIST = DATA['distances']
UCS = DATA['demo']['algos']['ucs']
ASTAR = DATA['demo']['algos']['astarAlt']

# ── Palette: mirrored from romania-web/src/{App,index}.css tokens ──────────
SURFACE = '#faf9f5'
INK     = '#08060d'
MUTED   = '#6b6375'
PURPLE  = '#aa3bff'   # lane A accent / current
TEAL    = '#0e7490'   # lane B accent
AMBER   = '#d97706'   # frontier
GREY    = '#9ca3af'   # visited
PATHC   = '#16a34a'   # path + start marker
ROADC   = '#cfcdc4'   # road / neutral
GOALC   = '#dc2626'   # goal marker
MONO    = 'Menlo'

config.background_color = SURFACE
config.frame_width = 7.2
config.frame_height = 4.6


# ── text ───────────────────────────────────────────────────────────────────
def txt(s, size=20, color=INK, width=None):
    """Monospace label. Text is shaped at a small fixed base size and scaled;
    the final geometry is independent of the base, but a small base keeps the
    720px Pango canvas from wrapping long strings (manim wraps Text at the
    pixel width of the scene)."""
    base = 48
    # Bump the geometric size so labels stay legible when the 720px GIF is shown
    # at the sidebar's ~330px width (keeps the bigger annotations near 12px).
    boost = 1.25

    def typeset(value):
        return Text(value, font=MONO, font_size=base, color=color,
                    disable_ligatures=True).scale(size * boost / base)

    if width:
        lines = []
        for paragraph in s.split('\n'):
            line = ''
            for word in paragraph.split():
                candidate = f'{line} {word}' if line else word
                if line and typeset(candidate).width > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        s = '\n'.join(lines)
    lines = s.split('\n')
    if len(lines) == 1:
        return typeset(s)
    return VGroup(*[typeset(l) for l in lines if l]).arrange(
        DOWN, aligned_edge=LEFT, buff=size * .02)


# ── map ────────────────────────────────────────────────────────────────────
def build_map(width=5.2, center=ORIGIN, node_r=0.075, letters=True,
              letter_size=11, road_w=1.8, road_color=ROADC, node_color=GREY):
    pt = {}
    for city, item in GRAPH.items():
        pt[city] = np.array([(item['x'] - 2043) / 2540 * width,
                             -(item['y'] - 1254) / 2540 * width, 0]) + center
    group, nodes, roads, labels = VGroup(), {}, {}, {}
    for city, item in GRAPH.items():
        for edge in item['edges']:
            if city < edge['to']:
                road = Line(pt[city], pt[edge['to']], color=road_color,
                            stroke_width=road_w).set_z_index(0)
                roads[frozenset([city, edge['to']])] = road
                group.add(road)
    for city, p in pt.items():
        node = Dot(p, radius=node_r, color=node_color).set_z_index(3)
        nodes[city] = node
        group.add(node)
        if letters:
            tag = txt(city[0], letter_size, INK).move_to(p).set_z_index(4)
            labels[city] = tag
            group.add(tag)
    return dict(group=group, pt=pt, nodes=nodes, roads=roads, labels=labels)


def route_lines(m, cities, color=PATHC, sw=4.0, z=2):
    return VGroup(*[Line(m['pt'][a], m['pt'][b], color=color,
                         stroke_width=sw).set_z_index(z)
                    for a, b in zip(cities, cities[1:])])


def shortest_path(s, t):
    """Dijkstra over the road graph, returning the city list."""
    seen = {s: 0}
    pq = [(0, s, [s])]
    while pq:
        cost, node, path = heapq.heappop(pq)
        if node == t:
            return path
        if cost > seen.get(node, 1e9):
            continue
        for edge in GRAPH[node]['edges']:
            nxt, c = edge['to'], cost + edge['km']
            if c < seen.get(nxt, 1e9):
                seen[nxt] = c
                heapq.heappush(pq, (c, nxt, path + [nxt]))
    return [s, t]


def dotted_path(m, cities, color, sw=2.4):
    return VGroup(*[DashedLine(m['pt'][a], m['pt'][b], color=color,
                               stroke_width=sw, dash_length=0.09)
                    .set_z_index(2)
                    for a, b in zip(cities, cities[1:])])


def pair(preset, s, t):
    return next(p for p in DATA['variants'][preset]['pairs']
                if p['s'] == s and p['t'] == t)


def mix(a, b, t):
    """interpolate_color needs ManimColor instances, not hex strings."""
    return interpolate_color(ManimColor(a), ManimColor(b), t)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-1 · UCS expands in expanding cost rings — blind to the goal.
# ═══════════════════════════════════════════════════════════════════════════
class UCSRings(Scene):
    def construct(self):
        m = build_map(width=5.2, center=LEFT * 0.5 + DOWN * 0.35)
        self.add(m['group'])

        sring = Circle(radius=0.17, color=PATHC, stroke_width=3).move_to(m['pt']['Arad']).set_z_index(6)
        gring = Circle(radius=0.17, color=GOALC, stroke_width=3).move_to(m['pt']['Bucharest']).set_z_index(6)
        self.play(Create(sring), Create(gring), run_time=0.3)
        self.add(txt('Arad', 12, PATHC).next_to(sring, DOWN, buff=0.07).set_z_index(20),
                 txt('Bucharest', 12, GOALC).next_to(gring, DOWN, buff=0.07).set_z_index(20))

        title = txt('UCS \u2014 blind to the goal', 15, INK)
        title.to_corner(UL, buff=0.16).set_z_index(20)
        self.play(FadeIn(title), run_time=0.3)

        rmax = float(np.linalg.norm(m['pt']['Bucharest'] - m['pt']['Arad']))
        tracker = ValueTracker(0.0)

        def ring():
            v = tracker.get_value()
            return Circle(radius=max(v * rmax, 1e-3), color=mix(AMBER, GREY, v),
                          stroke_width=2.2, stroke_opacity=0.6)\
                .move_to(m['pt']['Arad']).set_z_index(1)

        contour = always_redraw(ring)
        self.add(tracker, contour)

        counter = txt('expanded   0', 14, PURPLE).to_corner(UR, buff=0.18).set_z_index(20)
        self.add(counter)

        for i, step in enumerate(UCS['steps']):
            cur = step['current']
            gcur = DIST['Arad'][cur]
            anims = [tracker.animate.set_value(min(gcur / 418.0, 1.0))]
            for city in step['visited']:
                if city not in ('Arad', 'Bucharest'):
                    anims.append(m['nodes'][city].animate.set_color(GREY))
            for city in step['frontier']:
                if city != 'Bucharest':
                    anims.append(m['nodes'][city].animate.set_color(AMBER))
            if cur not in ('Arad', 'Bucharest'):
                anims.append(m['nodes'][cur].animate.set_color(PURPLE))
            anims.append(Transform(counter, txt(f'expanded {i + 1:3d}', 14, PURPLE)
                                   .to_corner(UR, buff=0.18).set_z_index(20)))
            self.play(*anims, run_time=0.14)

        self.play(Indicate(m['nodes']['Bucharest'], color=GOALC, scale_factor=1.8), run_time=0.4)
        self.remove(contour, tracker)

        route = route_lines(m, UCS['path'], PATHC, sw=5)
        self.play(LaggedStart(*[Create(l) for l in route], lag_ratio=0.35), run_time=0.7)
        self.add(route)
        self.play(FadeIn(txt('418 km \u00b7 optimal', 15, PATHC)
                         .move_to([-0.3, 1.45, 0]).set_z_index(20)), run_time=0.35)
        self.wait(0.3)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-2 · A* uses h to head for the goal; UCS can't.
# ═══════════════════════════════════════════════════════════════════════════
class AStarVsUCS(Scene):
    def construct(self):
        left = LEFT * 1.85
        right = RIGHT * 1.85
        mL = build_map(width=3.0, center=left + DOWN * 0.05, node_r=0.05,
                       letter_size=8, road_w=1.4)
        mR = build_map(width=3.0, center=right + DOWN * 0.05, node_r=0.05,
                       letter_size=8, road_w=1.4)
        self.add(mL['group'], mR['group'])
        self.add(DashedLine(UP * 2.3, DOWN * 2.3, color=ROADC, stroke_width=1.4))

        for mm, x in ((mL, left), (mR, right)):
            for city, col in (('Arad', PATHC), ('Bucharest', GOALC)):
                self.add(Circle(radius=0.10, color=col, stroke_width=2.4)
                         .move_to(mm['pt'][city]).set_z_index(6))

        self.add(txt('UCS', 16, AMBER).move_to(left + UP * 1.62).set_z_index(20),
                 txt('A*  (LP+ALT)', 16, PURPLE).move_to(right + UP * 1.62).set_z_index(20))
        cL = txt('expanded  0', 13, AMBER).move_to(left + DOWN * 1.42).set_z_index(20)
        cR = txt('expanded  0', 13, PURPLE).move_to(right + DOWN * 1.42).set_z_index(20)
        self.add(cL, cR)
        self.wait(0.1)

        for i, step in enumerate(UCS['steps']):
            anims = []
            cur = step['current']
            for city in step['visited']:
                if city not in ('Arad', 'Bucharest'):
                    anims.append(mL['nodes'][city].animate.set_color(GREY))
            for city in step['frontier']:
                if city != 'Bucharest':
                    anims.append(mL['nodes'][city].animate.set_color(AMBER))
            if cur not in ('Arad', 'Bucharest'):
                anims.append(mL['nodes'][cur].animate.set_color(PURPLE))
            anims.append(Transform(cL, txt(f'expanded {i + 1:3d}', 13, AMBER)
                                   .move_to(left + DOWN * 1.42).set_z_index(20)))

            if i < len(ASTAR['steps']):
                astep = ASTAR['steps'][i]
                acur = astep['current']
                for city in astep['visited']:
                    if city not in ('Arad', 'Bucharest'):
                        anims.append(mR['nodes'][city].animate.set_color(TEAL))
                if acur not in ('Arad', 'Bucharest'):
                    anims.append(mR['nodes'][acur].animate.set_color(PURPLE))
                anims.append(Transform(cR, txt(f'expanded {i + 1:3d}', 13, PURPLE)
                                       .move_to(right + DOWN * 1.42).set_z_index(20)))
            self.play(*anims, run_time=0.20)

        for mm in (mL, mR):
            route = route_lines(mm, ASTAR['path'], PATHC, sw=3.6)
            self.play(LaggedStart(*[Create(l) for l in route], lag_ratio=0.3), run_time=0.6)
            self.add(route)

        note = txt('same 418 km  \u00b7  ~55% fewer expansions', 13, INK)
        note.move_to(DOWN * 2.05).set_z_index(20)
        self.play(FadeIn(note), run_time=0.4)
        self.wait(0.4)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-3 · admissible = h <= h*;  consistent = h(n) <= c + h(n')
# ═══════════════════════════════════════════════════════════════════════════
class AdmissibleConsistent(Scene):
    def construct(self):
        # ── Beat 1: admissibility ──
        base = Line(LEFT * 3.2 + DOWN * 0.8, RIGHT * 3.2 + DOWN * 0.8, color=MUTED, stroke_width=2)
        ceiling = DashedLine(LEFT * 3.2 + UP * 0.9, RIGHT * 3.2 + UP * 0.9, color=INK, stroke_width=2.5)
        cap = txt('h*  (true remaining cost)', 13, INK).next_to(ceiling, UP, buff=0.08).align_to(ceiling, LEFT)
        self.add(base, ceiling, cap)

        xs = [-2.6, -1.7, -0.8, 0.1, 1.0, 1.9]
        hs = [0.95, 1.4, 0.75, 1.95, 1.15, 1.5]
        bars = VGroup()
        bad_bar = None
        for x, h in zip(xs, hs):
            bad = (x == 0.1)   # the single over-estimate
            col = GOALC if bad else TEAL
            bar = Rectangle(width=0.52, height=h, fill_color=col, fill_opacity=1, stroke_width=0)
            bar.move_to([x, -0.8 + h / 2, 0])
            self.play(GrowFromEdge(bar, DOWN), run_time=0.14)
            bars.add(bar)
            if bad:
                bad_bar = bar
        label1 = txt('h(n) \u2264 h*(n)  \u2014  never overestimate', 15, INK).move_to(DOWN * 1.55)
        self.play(FadeIn(label1), run_time=0.3)

        self.play(Indicate(bad_bar, color=GOALC, scale_factor=1.15), run_time=0.4)
        c = bad_bar.get_center()
        cross = VGroup(Line(c + LEFT * 0.28 + UP * 0.28, c + RIGHT * 0.28 + DOWN * 0.28, color=GOALC, stroke_width=5),
                       Line(c + LEFT * 0.28 + DOWN * 0.28, c + RIGHT * 0.28 + UP * 0.28, color=GOALC, stroke_width=5))
        self.play(Create(cross), run_time=0.22)
        self.play(FadeOut(bad_bar), FadeOut(cross), run_time=0.25)
        self.wait(0.15)
        self.play(*[FadeOut(m) for m in bars], FadeOut(label1), FadeOut(base),
                  FadeOut(ceiling), FadeOut(cap), run_time=0.35)

        # ── Beat 2: consistency ──
        n = LEFT * 2.4 + UP * 0.7
        npnt = RIGHT * 0.7 + UP * 0.7
        road = Arrow(n, npnt, buff=0.12, color=MUTED, stroke_width=4)
        self.play(FadeIn(Dot(n, color=INK)), FadeIn(Dot(npnt, color=INK)), run_time=0.25)
        self.add(txt('n', 20, INK).next_to(n, UP, buff=0.12),
                 txt("n'", 20, INK).next_to(npnt, UP, buff=0.12))
        self.play(Create(road), FadeIn(txt('c', 16, MUTED).move_to((n + npnt) / 2 + UP * 0.2)), run_time=0.35)

        bbase = -1.3
        hn = Rectangle(width=0.5, height=1.35, fill_color=PURPLE, fill_opacity=1, stroke_width=0)
        hn.move_to([n[0], bbase + 1.35 / 2, 0])
        hnp = Rectangle(width=0.5, height=0.8, fill_color=TEAL, fill_opacity=1, stroke_width=0)
        hnp.move_to([npnt[0], bbase + 0.8 / 2, 0])
        self.play(GrowFromEdge(hn, DOWN), run_time=0.3)
        self.play(GrowFromEdge(hnp, DOWN), run_time=0.3)
        self.add(txt('h(n)', 14, PURPLE).next_to(hn, DOWN, buff=0.08),
                 txt("h(n')", 14, TEAL).next_to(hnp, DOWN, buff=0.08))

        # The road cost c slides down to stack on h(n').
        cb = Rectangle(width=0.5, height=0.6, fill_color=AMBER, fill_opacity=1, stroke_width=0)
        cb.move_to((n + npnt) / 2 + UP * 0.2)
        self.add(cb)
        self.play(cb.animate.move_to([npnt[0], bbase + 0.8 + 0.3, 0]), run_time=0.55)
        self.add(txt('c', 16, AMBER).next_to(cb, RIGHT, buff=0.1))
        self.play(FadeIn(txt("h(n) \u2264 c + h(n')", 18, INK).move_to([0.3, -1.9, 0])), run_time=0.4)
        self.wait(0.4)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-4 · the chord rewritten as a combination of road vectors; LP prices it.
# ═══════════════════════════════════════════════════════════════════════════
class LPVectorDecomposition(Scene):
    def construct(self):
        width = 4.8
        center = LEFT * 0.1 + DOWN * 0.15
        cities = ['Arad', 'Sibiu', 'Rimnicu Vilcea', 'Pitesti', 'Bucharest']
        pt = {c: np.array([(GRAPH[c]['x'] - 2043) / 2540 * width,
                           -(GRAPH[c]['y'] - 1254) / 2540 * width, 0]) + center
              for c in cities}
        a, b = pt['Arad'], pt['Bucharest']
        dhat = (b - a) / np.linalg.norm(b - a)
        normal = np.array([-dhat[1], dhat[0], 0])
        if normal[1] < 0:
            normal = -normal

        self.add(VGroup(*[Dot(pt[c], radius=0.055, color=INK).set_z_index(5) for c in cities]))
        self.add(txt('a', 15, INK).move_to(pt['Arad'] + normal * 0.24),
                 txt('b', 15, INK).move_to(pt['Bucharest'] + normal * 0.24),
                 txt('Arad', 11, MUTED).move_to(pt['Arad'] - normal * 0.26),
                 txt('Bucharest', 11, MUTED).move_to(pt['Bucharest'] - normal * 0.26))

        chord = DashedLine(a, b, color=AMBER, stroke_width=3).set_z_index(2)
        self.play(Create(chord), run_time=0.4)
        self.add(txt('chord_ab', 14, AMBER).move_to((a + b) / 2 + normal * 0.68))

        # Real route: a tip-to-tail chain of road vectors; the LP pulls it taut
        # onto the chord and prices the cheapest spanning combination.
        pairs = list(zip(cities, cities[1:]))
        km = [next(e['km'] for e in GRAPH[u]['edges'] if e['to'] == v) for u, v in pairs]
        colors = [TEAL, AMBER, PURPLE, TEAL]
        tracker = ValueTracker(0.0)

        def endpoints(u, p):
            proj = np.dot(pt[p] - a, dhat) * dhat
            return a + (pt[p] - a) * (1 - u) + proj * u

        def chain():
            u = tracker.get_value()
            arrows = VGroup()
            for (p, q), col in zip(pairs, colors):
                arrows.add(Arrow(endpoints(u, p), endpoints(u, q), buff=0,
                                 color=col, stroke_width=4).set_z_index(3))
            return arrows

        def labels():
            u = tracker.get_value()
            g = VGroup()
            for (p, q), k, col in zip(pairs, km, colors):
                mid = (endpoints(u, p) + endpoints(u, q)) / 2 + normal * 0.28
                g.add(txt(str(k), 12, col).move_to(mid).set_z_index(6))
            return g

        self.add(always_redraw(chain), always_redraw(labels))
        self.wait(0.2)
        readout = txt('real route: 140 + 80 + 97 + 101 = 418 km', 13, INK)
        readout.move_to(DOWN * 1.8).set_z_index(20)
        self.play(FadeIn(readout), run_time=0.4)

        lp_text = txt('LP: min \u03a3 \u03b1\u1d62 km\u1d62 = 388.21 km', 13, PURPLE)
        lp_text.move_to(DOWN * 1.8).set_z_index(20)
        self.play(tracker.animate.set_value(1.0),
                  Transform(readout, lp_text), run_time=2.0, rate_func=smooth)
        self.add(txt('0 \u2264 \u03b1\u1d62 \u2264 1', 12, MUTED).move_to(DOWN * 2.12).set_z_index(20),
                 txt('the chord is never measured directly (SLD)',
                     11, MUTED).to_edge(UP, buff=0.12).set_z_index(20))
        self.wait(0.8)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-5 · triangle inequality via a landmark; more landmarks => tighter.
# ═══════════════════════════════════════════════════════════════════════════
class ALTTriangleInequality(Scene):
    def construct(self):
        m = build_map(width=4.9, center=LEFT * 0.5 + DOWN * 0.15)
        self.add(m['group'])

        n, goal = 'Arad', 'Craiova'
        green = route_lines(m, shortest_path(n, goal), PATHC, sw=4.5)
        self.play(LaggedStart(*[Create(l) for l in green], lag_ratio=0.3), run_time=0.7)
        self.add(green)
        self.add(txt('366 km', 12, PATHC).move_to([0.4, -0.4, 0]))

        def landmark(city):
            star = Star(n=5, outer_radius=0.15, color=AMBER, fill_opacity=1).move_to(m['pt'][city])
            return star, txt(city, 12, AMBER).next_to(star, UP, buff=0.06)

        star1, lab1 = landmark('Oradea')
        self.play(GrowFromCenter(star1), FadeIn(lab1), run_time=0.3)
        ref1 = dotted_path(m, shortest_path('Oradea', n), TEAL)
        ref2 = dotted_path(m, shortest_path('Oradea', goal), AMBER)
        self.play(Create(ref1), Create(ref2), run_time=0.6)
        self.add(txt('146', 12, TEAL).move_to(m['pt']['Oradea'] + RIGHT * 0.62),
                 txt('377', 12, AMBER).move_to(m['pt']['Oradea'] + RIGHT * 0.62 + DOWN * 0.24))
        ineq = txt('|377 \u2212 146| = 231  \u2264  366', 14, INK).move_to(DOWN * 2.05)
        self.play(FadeIn(ineq), run_time=0.35)

        star2, lab2 = landmark('Timisoara')
        self.play(GrowFromCenter(star2), FadeIn(lab2), run_time=0.3)
        ref3 = dotted_path(m, shortest_path('Timisoara', n), TEAL)
        ref4 = dotted_path(m, shortest_path('Timisoara', goal), AMBER)
        self.play(Create(ref3), Create(ref4), run_time=0.6)
        self.add(txt('118', 12, TEAL).move_to(m['pt']['Timisoara'] + RIGHT * 0.66 + UP * 0.1),
                 txt('376', 12, AMBER).move_to(m['pt']['Timisoara'] + RIGHT * 0.66 + DOWN * 0.14))
        self.play(Transform(ineq, txt('|376 \u2212 118| = 258  \u2192  max = 258', 14, PATHC)
                            .move_to(DOWN * 2.05)), run_time=0.5)
        self.play(FadeIn(txt('more landmarks \u21d2 tighter bound (never looser)', 13, MUTED)
                         .to_edge(UP, buff=0.14)), run_time=0.35)
        self.wait(0.5)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-6 · each bound certifies "at least this much"; the max keeps the best.
# ═══════════════════════════════════════════════════════════════════════════
class EnsembleMax(Scene):
    def construct(self):
        header = txt('each bound \u2264 truth; the max is strongest', 15, INK)
        header.to_edge(UP, buff=0.16)
        self.add(header)
        nodes = [('Arad \u2192 Bucharest', 'Arad', 'Bucharest'),
                 ('Arad \u2192 Craiova', 'Arad', 'Craiova'),
                 ('Fagaras \u2192 Lugoj', 'Fagaras', 'Lugoj')]
        x0, span = -3.2, 5.2
        for label_text, s, t in nodes:
            p = pair('lm8', s, t)
            opt, lp, alt = p['optimal'], p['lp'], p['alt']
            scale = span / opt
            panel = VGroup()
            ceiling = DashedLine([x0, 0.95, 0], [x0 + span, 0.95, 0], color=INK, stroke_width=2)
            title = txt(label_text, 15, INK).next_to(np.array([x0 - 0.1, 1.55, 0]), RIGHT, buff=0)
            panel.add(ceiling, title,
                      txt(f'true = {opt:.0f} km', 12, MUTED).next_to(ceiling, UP, buff=0.08).align_to(ceiling, LEFT))
            self.play(FadeIn(panel), run_time=0.25)

            lp_bar = Rectangle(width=lp * scale, height=0.42, fill_color=PURPLE, fill_opacity=1, stroke_width=0)
            lp_bar.move_to([x0 + lp * scale / 2, 0.35, 0])
            alt_bar = Rectangle(width=alt * scale, height=0.42, fill_color=TEAL, fill_opacity=1, stroke_width=0)
            alt_bar.move_to([x0 + alt * scale / 2, -0.35, 0])
            self.play(GrowFromEdge(lp_bar, LEFT), GrowFromEdge(alt_bar, LEFT), run_time=0.35)
            panel.add(lp_bar, alt_bar,
                      txt(f'hLP {lp:.0f}', 12, PURPLE).next_to(lp_bar, UP, buff=0.05).align_to(lp_bar, LEFT),
                      txt(f'hALT {alt:.0f}', 12, TEAL).next_to(alt_bar, UP, buff=0.05).align_to(alt_bar, LEFT))

            tall = lp_bar if lp >= alt else alt_bar
            bracket = txt('max', 13, PATHC).next_to(tall, RIGHT, buff=0.08)
            self.play(FadeIn(bracket), run_time=0.15)
            winner = max(lp, alt)
            max_bar = Rectangle(width=winner * scale, height=0.42, fill_color=PATHC, fill_opacity=1, stroke_width=0)
            max_bar.move_to([x0 + winner * scale / 2, -1.05, 0])
            max_label = txt(f'h = max = {winner:.0f}', 12, PATHC).next_to(max_bar, UP, buff=0.05).align_to(max_bar, LEFT)
            self.play(GrowFromEdge(max_bar, LEFT), FadeIn(max_label), run_time=0.35)
            panel.add(bracket, max_bar, max_label)
            self.wait(0.2)
            self.play(*[FadeOut(m) for m in panel], run_time=0.25)

        stamp = VGroup(
            txt('both \u2264 h*', 15, INK), txt('\u21d2', 15, INK),
            txt('max \u2264 h*', 15, INK), txt('\u2713 admissible', 15, PATHC),
        ).arrange(RIGHT, buff=0.22).move_to(DOWN * 0.1)
        self.play(FadeIn(stamp), run_time=0.5)
        self.wait(0.2)


# ═══════════════════════════════════════════════════════════════════════════
# GIF-7 · informedness rises / expansions fall; the ensemble tops it off.
# ═══════════════════════════════════════════════════════════════════════════
class EnsemblePerformance(Scene):
    def construct(self):
        series = ['LP only', 'ALT lm2', 'ALT lm4', 'ALT lm8', 'LP+ALT']
        informed = [0.683, 0.872, 0.972, 0.985, 0.986]
        expanded = [2316, 2191, 1984, 1924, 1922]
        cols = [mix(PURPLE, TEAL, i / (len(series) - 1)) for i in range(len(series))]
        xs = np.linspace(-2.5, 2.5, len(series))

        # ── Chart A: informedness (0..1) ──
        top_base, a_h = 0.72, 0.92
        self.add(txt('mean h / road  (higher = tighter)', 13, INK).move_to([0, 2.06, 0]))
        self.add(Line([-3.0, top_base, 0], [3.0, top_base, 0], color=MUTED, stroke_width=2))
        a_bars = VGroup()
        for x, v, col in zip(xs, informed, cols):
            bar = Rectangle(width=0.55, height=v * a_h, fill_color=col, fill_opacity=1, stroke_width=0)
            bar.move_to([x, top_base + v * a_h / 2, 0])
            a_bars.add(bar)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in a_bars], lag_ratio=0.12), run_time=0.8)
        for x, v, col in zip(xs, informed, cols):
            self.add(txt(f'{v:.3f}', 10, col).move_to([x, top_base + v * a_h + 0.14, 0]))

        # ── Chart B: expansions (all pairs) ──
        bot_base, b_h, vmax = -1.95, 0.92, 2400.0
        self.add(txt('nodes expanded  (all pairs)', 13, INK).move_to([0, -0.30, 0]))
        self.add(Line([-3.0, bot_base, 0], [3.0, bot_base, 0], color=MUTED, stroke_width=2))
        b_bars = VGroup()
        for x, v, col in zip(xs, expanded, cols):
            bar = Rectangle(width=0.55, height=v / vmax * b_h, fill_color=col, fill_opacity=1, stroke_width=0)
            bar.move_to([x, bot_base + v / vmax * b_h / 2, 0])
            b_bars.add(bar)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in b_bars], lag_ratio=0.12), run_time=0.8)
        for x, v, col in zip(xs, expanded, cols):
            self.add(txt(f'{v}', 10, col).move_to([x, bot_base + v / vmax * b_h + 0.13, 0]))
        for x, name, col in zip(xs, series, cols):
            self.add(txt(name, 8, MUTED).move_to([x, bot_base - 0.17, 0]))

        # UCS reference: far past the scale -> clamp with an arrow.
        ucs_top = bot_base + b_h + 0.26
        self.play(Create(DashedLine([-3.0, ucs_top, 0], [3.0, ucs_top, 0], color=GOALC, stroke_width=2)),
                  run_time=0.4)
        arrow = Arrow([2.9, ucs_top + 0.02, 0], [2.9, ucs_top + 0.32, 0], buff=0, color=GOALC, stroke_width=4)
        self.play(GrowArrow(arrow),
                  FadeIn(txt('UCS 4180 \u2191', 10, GOALC).next_to(arrow, UP, buff=0.02)), run_time=0.5)

        note = txt('vs ALT lm8 alone:  +0.0005 informedness,  \u22122 expansions.\n'
                   'Mostly robustness \u2014 the margin is thin.', 10, MUTED)
        note.move_to([0, 0.08, 0])
        self.play(FadeIn(note), run_time=0.5)
        self.wait(0.5)
