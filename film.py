"""Render: .venv/bin/manim -qh film.py PathfindingFilm
Set CHAPTER_SELECTION=0,6,10 to render selected chapters for review.
"""
import json
import os
from pathlib import Path
import numpy as np
from manim import *
from storyboard import CHAPTERS

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT/'project_data.json').read_text())
INK, MUTED = '#F4F1EA', '#C4C1B9'
CYAN, GOLD, GREEN, PURPLE, RED = '#55D6BE', '#F2C14E', '#8BE28B', '#B39DDB', '#F07167'
config.background_color = '#101010'
config.frame_width = 16
config.frame_height = 9


def label(text, size=25, color=INK, width=None):
    # Shape at a constant large size to reduce small-font positioning
    # quantization. The fixed scale preserves the requested font size;
    # it never depends on the length of the string.
    def typeset(value):
        return Text(value, font='Avenir Next', font_size=200,
                    color=color, disable_ligatures=True).scale(size / 200)

    if width:
        lines = []
        for paragraph in text.split('\n'):
            line = ''
            for word in paragraph.split():
                candidate = f'{line} {word}' if line else word
                if line and typeset(candidate).width > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        text = '\n'.join(lines)
    # Lay out complete lines explicitly. This avoids baseline collisions
    # between wrapped and manually separated lines in Pango.
    lines = text.split('\n')
    if len(lines) == 1:
        return typeset(text)
    return VGroup(*[typeset(line) for line in lines if line]).arrange(
        DOWN, aligned_edge=LEFT, buff=size*.007)


def subscript(base, sub, size=28, color=INK):
    """Font-safe visual subscript, avoiding missing Unicode glyphs."""
    main = label(base, size, color)
    small = label(sub, size * .52, color)
    small.next_to(main, DOWN * .18 + RIGHT * .03, buff=0)
    return VGroup(main, small)


def formula(kind, equation):
    """Use semantic color tokens instead of coloring every formula cyan."""
    if kind in ('ucs', 'ucstrace', 'ucsproof'):
        return VGroup(label('priority(n) = ', 30, INK), label('g(n)', 30, PURPLE))
    if kind == 'astar':
        return VGroup(label('f(n)', 30, GREEN), label(' = ', 30, INK), label('g(n)', 30, PURPLE), label(' + ', 30, INK), label('h(n,t)', 30, GOLD))
    if kind in ('lp', 'lpproof'):
        return VGroup(label('min ', 30, INK), label('Σ αᵢ cᵢ', 30, GOLD), label('   subject to   ', 30, INK), label('Σ αᵢ vᵢ = Δ', 30, CYAN))
    if kind == 'alt':
        return VGroup(subscript('h', 'ALT', 27, GOLD), label('(n,t) = max over L of ', 27, GOLD), label('|d(L,n) − d(L,t)|', 27, INK))
    if kind == 'triangle':
        # Keep the signed-distance terms semantically colored while the
        # absolute-value and subtraction operators remain neutral.
        return VGroup(
            label('|', 28, INK), label('d(L,n)', 28, CYAN),
            label(' − ', 28, INK), label('d(L,t)', 28, GOLD),
            label('| ≤ ', 28, INK), label('d(n,t)', 28, GREEN),
        ).arrange(RIGHT, buff=.03)
    if kind == 'leaf':
        return VGroup(label('d(Giurgiu,n) − 90', 28, GOLD), label(' = ', 28, INK), label('d(Bucharest,n)', 28, GREEN))
    if kind == 'combine':
        return VGroup(label('h = max(', 29, INK), subscript('h', 'LP', 29, PURPLE), label(', ', 29, INK), subscript('h', 'ALT', 29, GOLD), label(')', 29, INK), label('  ≤  d', 29, GREEN))
    if kind == 'stop':
        return VGroup(label('max(', 29, INK), label('min fF', 29, CYAN), label(', ', 29, INK), label('min fB', 29, GOLD), label(')  ≥ ', 29, INK), label('μ', 29, GREEN))
    if kind == 'consistency':
        return VGroup(label(equation, 28, CYAN, width=6.6))
    return VGroup(label(equation, 28, CYAN, width=6.6))


def example(start='Arad',goal='Bucharest',preset='lm8'):
    return next(p for p in DATA['variants'][preset]['pairs'] if p['s']==start and p['t']==goal)


class RoadMap(VGroup):
    def __init__(self, width=6.8, center=LEFT*3.9+DOWN*.2, initials=False):
        super().__init__()
        self.points_by_city = {}
        self.nodes, self.roads = {}, {}
        self.city_labels = {}
        for city, item in DATA['graph'].items():
            self.points_by_city[city] = np.array([(item['x']-2043)/2540*width, -(item['y']-1254)/2540*width, 0])+center
        for city, item in DATA['graph'].items():
            for edge in item['edges']:
                if city < edge['to']:
                    road = Line(self.points_by_city[city],self.points_by_city[edge['to']],color='#53627A',stroke_width=2.4)
                    self.roads[frozenset([city,edge['to']])] = road
                    self.add(road)
        for city, point in self.points_by_city.items():
            node = Dot(point,radius=.16 if initials else .068,color=MUTED).set_z_index(3)
            self.nodes[city] = node
            self.add(node)
            name = 'Rimnicu V.' if city=='Rimnicu Vilcea' else city
            city_label = label(name,16).next_to(node, DOWN if city in ['Arad','Sibiu','Fagaras','Hirsova','Giurgiu','Craiova','Eforie'] else UP,buff=.065)
            city_label.add_background_rectangle(color='#101010', opacity=1, buff=.035)
            if initials:
                city_label = label(city[0],16,'#101010').move_to(node)
            city_label.set_z_index(10)
            self.add(city_label)
            self.city_labels[city] = city_label

    def route(self, cities, color=GREEN):
        return VGroup(*[Line(self.points_by_city[a],self.points_by_city[b],color=color,stroke_width=5) for a,b in zip(cities,cities[1:])])


class PathfindingFilm(Scene):
    """A question leads to a demonstration, then a name or equation."""

    def construct(self):
        selected = os.environ.get('CHAPTER_SELECTION')
        indices = [int(v) for v in selected.split(',')] if selected else list(range(len(CHAPTERS)))
        self.note = None
        self.vector_diagram = None
        timeline = []
        for index in indices:
            start = self.time
            title, kind, _, _, narration = CHAPTERS[index]
            self.begin(index, title)
            getattr(self, kind)()
            self.wait(2.4)
            # Keep exactly the same vector arrows between explanation and proof.
            keep = self.vector_diagram if kind == 'lp' and index + 1 in indices else None
            outgoing = [m for m in self.mobjects if m is not keep]
            self.play(*[FadeOut(m) for m in outgoing], run_time=.5)
            self.note = None
            timeline.append(dict(index=index + 1, kind=kind, title=title,
                                 start=round(start, 3), duration=round(self.time-start, 3),
                                 narration=narration))
        if not selected:
            (ROOT/'timeline.json').write_text(json.dumps(timeline, indent=2))
            (ROOT/'narration.md').write_text(
                '# Human narrator script\n\nCompanion to the silent video. '
                'These chapter times come from the animation, not recorded speech.\n\n' +
                '\n\n'.join(f'## {c["index"]:02} · {c["title"]}\n\n'
                             f'Start: {c["start"]:.2f}s · Visual duration: {c["duration"]:.2f}s\n\n'
                             f'{c["narration"]}' for c in timeline))

    def begin(self, index, title):
        counter = label(f'{index+1:02} / {len(CHAPTERS):02}', 16, MUTED).to_corner(UL, buff=.55)
        self.add(counter)
        self.add(label(title, 36, width=14.5).next_to(counter, DOWN, aligned_edge=LEFT, buff=.28))

    def panel(self, mob, hold=2.5):
        """One idea at a time, below the reserved title band."""
        mob.move_to(RIGHT*3.65+UP*.4)
        if mob.width > 6.6 or mob.get_top()[1] > 2.6 or mob.get_bottom()[1] < -2.8:
            raise ValueError('Explanation exceeds the reserved panel bounds')
        if self.note is not None:
            self.play(FadeOut(self.note), run_time=.3)
        self.play(FadeIn(mob), run_time=.5)
        self.note = mob
        self.wait(hold)
        return mob

    def say(self, text, color=INK, size=27):
        return self.panel(label(text, size, color, width=6.3),
                          hold=max(2, min(4.5, len(text.split()) / 3)))

    def equation(self, kind, text=''):
        parts = formula(kind, text)
        rows, row = [], VGroup()
        for part in list(parts):
            if len(row) and sum(p.width for p in row) + .08*len(row) + part.width > 6.3:
                rows.append(row.arrange(RIGHT, buff=.08))
                row = VGroup()
            row.add(part)
        if len(row):
            rows.append(row.arrange(RIGHT, buff=.08))
        self.panel(VGroup(*rows).arrange(DOWN, buff=.25), hold=3)

    def map(self):
        diagram = RoadMap(width=6.2, center=LEFT*3.5+DOWN*.1, initials=True)
        self.play(FadeIn(diagram), run_time=.8)
        return diagram

    def compact_labels(self, diagram):
        # Move the existing first glyph into the node; fade only the suffix.
        # This keeps letter shapes intact throughout the smooth transition.
        animations, replacements = [], []
        for city, old in diagram.city_labels.items():
            background = old.background_rectangle
            old.remove(background)
            self.remove(background)
            first, suffix = old[0], VGroup(*old[1:])
            initial = label(city[0],16,'#101010').move_to(diagram.nodes[city]).set_z_index(10)
            animations.extend([Transform(first, initial), FadeOut(suffix),
                               diagram.nodes[city].animate.scale(.16/.068)])
            replacements.append((city, old, first, suffix, initial))
        self.play(*animations, run_time=1.2, rate_func=smooth)
        for city, old, first, suffix, initial in replacements:
            self.remove(old, first, suffix)
            diagram.remove(old)
            diagram.add(initial)
            diagram.city_labels[city] = initial
        self.add(diagram)

    def draw_route(self, diagram, route, color=GREEN, seconds=.45):
        lines = VGroup()
        for a, b in zip(route, route[1:]):
            line = Line(diagram.points_by_city[a], diagram.points_by_city[b],
                        color=color, stroke_width=5).set_z_index(1)
            lines.add(line)
            self.play(Create(line), run_time=seconds)
        self.add(lines)
        return lines

    def journey(self):
        diagram = RoadMap(width=6.2, center=LEFT*3.5+DOWN*.1)
        endpoints = [diagram.nodes[c] for c in ('Arad', 'Bucharest')]
        names = [diagram.city_labels[c] for c in ('Arad', 'Bucharest')]
        self.play(*[FadeIn(m) for m in endpoints+names], run_time=.7)
        self.say('You are in Arad.\nYou want to reach Bucharest.')
        # Introduce the road network only after establishing the journey.
        rest = VGroup(*[m for m in diagram if m not in endpoints+names])
        self.play(FadeIn(rest), run_time=1)
        self.add(diagram)
        self.say('There is more than one way to go.')
        self.wait(1)
        self.compact_labels(diagram)
        self.wait(1)
        first = self.draw_route(diagram, ['Arad','Sibiu','Fagaras','Bucharest'], GOLD)
        self.wait(1)
        self.play(FadeOut(first), run_time=.4)
        self.draw_route(diagram, ['Arad','Sibiu','Rimnicu Vilcea','Pitesti','Bucharest'], PURPLE)
        self.say('Which route has the smallest total distance?')

    def routes(self):
        totals = []
        paths = [(['Arad','Sibiu','Fagaras','Bucharest'], GOLD, 1.15),
                 (['Arad','Sibiu','Rimnicu Vilcea','Pitesti','Bucharest'], PURPLE, -1.15)]
        for path, color, y in paths:
            points = [np.array([x,y,0]) for x in np.linspace(-6.8,-.5,len(path))]
            names = VGroup(*[label('Rimnicu V.' if c=='Rimnicu Vilcea' else c, 14)
                             .next_to(p, UP, buff=.22) for c,p in zip(path,points)])
            self.play(FadeIn(names), run_time=.5)
            costs = []
            for a,b,p,q in zip(path,path[1:],points,points[1:]):
                cost = next(e['km'] for e in DATA['graph'][a]['edges'] if e['to']==b)
                costs.append(cost)
                self.play(Create(Line(p,q,color=color,stroke_width=5)),
                          FadeIn(label(str(cost),18,color).move_to((p+q)/2+DOWN*.28)),run_time=.55)
            total = label(f'{len(costs)} roads\n'+' + '.join(map(str,costs))+f' = {sum(costs)} km',
                          25, color, width=6.3).move_to(RIGHT*3.65+UP*(.4 if not totals else -.85))
            self.play(FadeIn(total), run_time=.5)
            self.wait(2.5)
            if not totals:
                self.play(total.animate.shift(UP*.9), run_time=.65, rate_func=smooth)
            totals.append(total)
        self.wait(2)
        self.play(*[FadeOut(total) for total in totals], run_time=.5)
        self.say('Four roads can be shorter than three.')
        self.say('Can we find the best route systematically?')

    def ucs(self):
        diagram = self.map()
        ex = example()
        self.say('Start at zero.\nExtend the cheapest discovered route.')
        costs, tree = {ex['s']: 0}, {}
        for step in ex['ucs']['steps']:
            current = step['current']
            self.play(Indicate(diagram.nodes[current], color=PURPLE, scale_factor=1.4),run_time=.25)
            if current != ex['t']:
                for edge in DATA['graph'][current]['edges']:
                    neighbor = edge['to']
                    cost = costs[current]+edge['km']
                    if cost < costs.get(neighbor,float('inf')):
                        costs[neighbor] = cost
                        line = Line(diagram.points_by_city[current],diagram.points_by_city[neighbor],
                                    color=PURPLE,stroke_width=5).set_z_index(1)
                        changes = [Create(line), diagram.nodes[neighbor].animate.set_color(CYAN)]
                        if neighbor in tree:
                            changes.append(FadeOut(tree[neighbor]))
                        self.play(*changes,run_time=.35)
                        tree[neighbor] = line
            self.play(diagram.nodes[current].animate.set_color(PURPLE),run_time=.15)
        self.draw_route(diagram, ex['ucs']['path'])
        self.say('418 km.\nThe goal is now selected at minimum cost.', GREEN)
        self.say('This is uniform cost search.\nUCS', PURPLE)
        self.equation('ucs')
        self.say('g is the cost already paid.', PURPLE)

    def ucsproof(self):
        positions = [LEFT*6.5, LEFT*4, LEFT*1.5]
        for p,name in zip(positions,['start','frontier','goal']):
            self.add(Dot(p,color=PURPLE),label(name,20).next_to(p,DOWN,buff=.25))
        self.play(Create(Line(positions[0],positions[1],color=PURPLE,stroke_width=5)),run_time=.7)
        self.say('Suppose the selected goal hides a cheaper route.')
        self.play(Create(DashedLine(positions[1],positions[2],color=GREEN)),run_time=.7)
        self.say('That route must cross the frontier.')
        self.play(Indicate(Dot(positions[1],color=GREEN),color=GREEN),run_time=.7)
        self.say('With nonnegative road costs, its frontier cost would be smaller.')
        self.say('UCS would have selected it first.\nThat is the contradiction.', GREEN)

    def waste(self):
        diagram = self.map()
        self.draw_route(diagram,['Arad','Timisoara','Lugoj'],PURPLE)
        self.draw_route(diagram,['Arad','Zerind','Oradea'],PURPLE)
        self.say('Cheap first steps can lead away from our final route.')
        self.draw_route(diagram,example()['ucs']['path'],GREEN)
        self.say('UCS knows the cost so far.\nIt does not estimate the rest.')
        self.say('Could the destination guide the search?', GOLD)

    def astar(self):
        for y,text,color in [(1.5,'Already paid: 220 km',PURPLE),
                             (0,'Estimated remainder: 198 km',GOLD),
                             (-1.5,'Whole-trip estimate: 418 km',GREEN)]:
            self.play(FadeIn(label(text,25,color,width=6.1).move_to(LEFT*3.7+UP*y)),run_time=.6)
            self.wait(1.5)
        self.say('Rank each city by its estimated whole journey.')
        self.say('This is A*.', GREEN)
        self.equation('astar')
        self.say('But which estimates are safe?')

    def optimism(self):
        base = LEFT*6.8
        for y,value,color in [(1.4,198,GREEN),(0,160,GOLD),(-1.4,230,RED)]:
            bar = Rectangle(width=value/45,height=.2,fill_color=color,fill_opacity=1,stroke_width=0)
            bar.move_to(base+RIGHT*bar.width/2+UP*y)
            self.play(GrowFromEdge(bar,LEFT),
                      FadeIn(label(f'{value} km',22,color).next_to(bar,UP,buff=.15)),run_time=.7)
        self.say('True remainder: 198 km.\n160 is optimistic; 230 is too high.')
        self.panel(VGroup(label('h(n,t)',30,GOLD),label(' ≤ ',30,INK),
                          label('d(n,t)',30,GREEN)).arrange(RIGHT,buff=.08))
        self.say('Never overestimate.\nThis is admissibility.')
        self.say('Reopen a city if a cheaper route to it is found.')
        self.say('How can we build such an estimate?')

    def make_vectors(self):
        point = LEFT*6.5+DOWN*1.2
        origin = point.copy()
        arrows = VGroup()
        for vector,color in zip([RIGHT*1.45+UP*1.2,RIGHT*1.65+DOWN*.4,RIGHT*1.3+UP*1.3],
                                [CYAN,GOLD,PURPLE]):
            arrow = Arrow(point,point+vector,buff=0,color=color,stroke_width=6)
            arrows.add(arrow)
            self.play(GrowArrow(arrow),run_time=.7)
            point += vector
        direct = Arrow(origin,point,buff=0,color=GREEN,stroke_width=3)
        self.play(GrowArrow(direct),run_time=.7)
        arrows.add(direct)
        self.add(arrows)
        self.vector_diagram = arrows

    def lp(self):
        self.make_vectors()
        self.say('A route adds road displacements.')
        self.say('What if we could buy fractions of roads, even disconnected ones?')
        self.say('Keep the same total displacement.\nMinimize the cost.')
        self.say('This is a linear program: LP.')
        self.panel(VGroup(label('min Σ αᵢ cᵢ',28,GOLD),
                          label('Σ αᵢ vᵢ = Δ',28,CYAN),
                          label('0 ≤ αᵢ ≤ 1',24,INK)).arrange(DOWN,buff=.3))
        self.say('Why should this easier problem help?', GREEN)

    def lpproof(self):
        if self.vector_diagram not in self.mobjects:
            self.make_vectors()
        self.say('Keep the same arrows.\nA real route is one allowed mixture.')
        self.say('Choose each path edge once.\nIntermediate positions cancel.')
        self.say('Extra choices can only lower the minimum.')
        self.say(f'LP: {example()["lp"]:.2f} km\nTrue shortest route: 418 km', GREEN)
        self.say('The project solves these bounds offline and checks the table.')

    def landmark(self):
        diagram = self.map()
        self.play(Indicate(diagram.nodes['Giurgiu'],color=GOLD),run_time=.7)
        self.say('Choose a landmark: Giurgiu.',GOLD)
        self.draw_route(diagram,['Giurgiu','Bucharest','Pitesti','Rimnicu Vilcea','Sibiu','Arad'],CYAN)
        self.say('Giurgiu to Arad: 508 km',CYAN)
        self.draw_route(diagram,['Giurgiu','Bucharest'],GOLD)
        self.say('Giurgiu to Bucharest: 90 km',GOLD)
        self.say('508 − 90 = 418 km',GREEN)
        self.say('Why does subtracting these distances give a lower bound?')

    def triangle(self):
        points = [LEFT*6.5+DOWN,LEFT*1.5+DOWN,LEFT*4+UP*1.5]
        for p,name in zip(points,['n','t','L']):
            self.add(Dot(p,color=MUTED),label(name,25).next_to(p,UP,buff=.15))
        for a,b,color in [(0,2,CYAN),(1,2,GOLD),(0,1,GREEN)]:
            self.play(Create(Line(points[a],points[b],color=color,stroke_width=5)),run_time=.6)
        self.say('Going through t cannot beat the shortest route from L to n.')
        self.panel(VGroup(
            label('d(L,n)',28,CYAN), label(' ≤ ',28,INK),
            label('d(L,t)',28,GOLD), label(' + ',28,INK),
            label('d(t,n)',28,GREEN),
        ).arrange(RIGHT,buff=.08), hold=3)
        self.say('Swap n and t.\nRearrange both inequalities.')
        self.equation('triangle')
        self.say('Try several landmarks.\nKeep the largest lower bound.')
        self.say('This is the landmark idea behind ALT.',GOLD)

    def combine(self):
        for y,text,color in [(1,'LP: 388.21 km',PURPLE),(-.4,'ALT: 418 km',GOLD)]:
            self.play(FadeIn(label(text,29,color).move_to(LEFT*3.8+UP*y)),run_time=.6)
        self.say('Both estimate the same remaining journey.')
        self.say('Keep the larger safe estimate.\nDo not add them.')
        self.equation('combine')
        self.say('A* has guidance.\nCould we also start at the other end?')

    def ensemble(self):
        # Same graph as the combine step, but the max is now justified on one
        # concrete pair where the LP is the deciding (larger) term.
        pair = next(p for p in DATA['variants']['lm8']['pairs'] if p['s'] == 'Arad' and p['t'] == 'Craiova')
        d, lp, alt = pair['optimal'], pair['lp'], pair['alt']
        x0, y0, span = -6.5, 1.5, 6.0
        scale = span / d
        ceiling = Line([x0, y0, 0], [x0+span, y0, 0], color=INK, stroke_width=5)
        self.play(Create(ceiling), FadeIn(
            label(f'true distance d = {d:.0f} km', 20, INK).next_to(ceiling, UP, buff=.15).align_to(ceiling, LEFT)), run_time=.7)
        self.say('The ceiling is the true remaining distance.')
        for i, (name, value, color) in enumerate([('hLP', lp, PURPLE), ('hALT', alt, GOLD)]):
            y = y0 - .95 - i*.95
            bar = Rectangle(width=value*scale, height=.34, fill_color=color, fill_opacity=1, stroke_width=0)
            bar.move_to([x0+bar.width/2, y, 0])
            self.play(GrowFromEdge(bar, LEFT),
                      FadeIn(label(f'{name} = {value:.0f}', 19, color).next_to(bar, UP, buff=.08).align_to(bar, LEFT)), run_time=.6)
        self.say('Both estimates sit below the ceiling.')
        value = max(lp, alt)
        y = y0 - .95 - 2*.95
        bar = Rectangle(width=value*scale, height=.34, fill_color=GREEN, fill_opacity=1, stroke_width=0)
        bar.move_to([x0+bar.width/2, y, 0])
        self.play(GrowFromEdge(bar, LEFT),
                  FadeIn(label(f'max = {value:.0f}', 19, GREEN).next_to(bar, UP, buff=.08).align_to(bar, LEFT)), run_time=.6)
        self.say('The maximum is the taller estimate,\nstill below the ceiling.', GREEN)
        self.say('And it is never smaller than either.')
        self.say('Safe and never weaker: keep the maximum.')

    def admissible(self):
        # Empirical admissibility: every ordered pair plotted against the
        # ceiling h = d. The diagonal may be touched, never crossed.
        pairs = DATA['variants']['lm8']['pairs']
        ax = Axes(x_range=[0, 1000, 200], y_range=[0, 1000, 200], x_length=5.0, y_length=4.1,
                  tips=False, axis_config={'color': MUTED, 'stroke_width': 2, 'font_size': 16})
        ax.move_to(LEFT*3.4+DOWN*.2)
        self.play(FadeIn(ax), run_time=.6)
        self.add(label('true distance d', 18, MUTED).next_to(ax.x_axis, DOWN, buff=.28))
        self.add(label('estimate h', 18, MUTED).rotate(PI/2).next_to(ax.y_axis, LEFT, buff=.22))
        ceiling = DashedLine(ax.c2p(0, 0), ax.c2p(1000, 1000), color=GREEN, stroke_width=4)
        self.play(Create(ceiling), run_time=.7)
        self.say('The diagonal is the ceiling h = d.')
        for key, color, text in [('lp', PURPLE, 'LP alone: all 380 below the line.'),
                                 ('alt', GOLD, 'Landmarks alone: below as well.'),
                                 ('h', GREEN, 'Their maximum: none above the line,\non all 380 pairs.')]:
            dots = VGroup(*[Dot(ax.c2p(p['optimal'], p[key]), radius=.033, color=color) for p in pairs])
            self.play(FadeIn(dots), run_time=.7)
            self.say(text, color)
        self.say('Admissibility here is measured,\nnot assumed.', GREEN)

    def tightness(self):
        m = DATA['variants']['lm8']
        x0, y0, span = -6.4, 1.6, 6.2
        ceiling = Line([x0, y0, 0], [x0+span, y0, 0], color=INK, stroke_width=4)
        self.play(Create(ceiling), FadeIn(
            label('true distance = 1.0', 19, INK).next_to(ceiling, UP, buff=.12).align_to(ceiling, LEFT)), run_time=.6)
        for i, (name, value, color) in enumerate([('LP alone', m['meanLP'], PURPLE),
                                                  ('Landmarks (lm8)', m['meanALT'], GOLD),
                                                  ('Ensemble max', m['meanCombined'], GREEN)]):
            y = y0 - .9 - i*.9
            bar = Rectangle(width=value*span, height=.36, fill_color=color, fill_opacity=1, stroke_width=0)
            bar.move_to([x0+bar.width/2, y, 0])
            self.play(GrowFromEdge(bar, LEFT),
                      FadeIn(label(f'{name}: {value:.3f}', 19, color).next_to(bar, UP, buff=.08).align_to(bar, LEFT)), run_time=.6)
        self.say('Higher is tighter, and the max is\nnever below either.')
        self.say('On 4 of 380 pairs the LP is the deciding term.')
        pair = next(p for p in m['pairs'] if p['s'] == 'Craiova' and p['t'] == 'Zerind')
        self.panel(VGroup(
            label('Craiova → Zerind', 22, INK),
            label(f'LP {pair["lp"]:.0f}  >  ALT {pair["alt"]:.0f}', 22, GOLD),
            label(f'max = {pair["h"]:.0f}  ≤  d = {pair["optimal"]:.0f}', 22, GREEN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=.18))
        self.say('Two independent methods;\nsafety never rests on one.')

    def landmarks(self):
        y0, scale = -1.9, 3.8
        centers = [-5.2, -3.0, -0.8]
        ceiling = DashedLine([-6.4, y0+scale, 0], [-.1, y0+scale, 0], color=INK, stroke_width=3)
        self.play(Create(ceiling), FadeIn(
            label('true distance = 1.0', 18, MUTED).next_to(ceiling, UP, buff=.12).align_to(ceiling, LEFT)), run_time=.6)
        for preset, cx in zip(['lm2', 'lm4', 'lm8'], centers):
            m = DATA['variants'][preset]
            for dx, value, color in [(-.34, m['meanALT'], GOLD), (.34, m['meanCombined'], GREEN)]:
                bar = Rectangle(width=.52, height=value*scale, fill_color=color, fill_opacity=1, stroke_width=0)
                bar.move_to([cx+dx, y0+value*scale/2, 0])
                self.play(GrowFromEdge(bar, DOWN), run_time=.45)
            self.add(label(preset, 20, INK).move_to([cx, y0-.4, 0]))
        self.say('Gold: landmarks alone.  Green: the ensemble.', MUTED, 24)
        self.say('Two landmarks reach 0.90 of the distance;\nfour reach 0.97; eight reach 0.98.')
        self.say('More landmarks never loosen the bound,\nand never break safety.', GREEN)

    def exact(self):
        rows = [('Arad', 508, 418), ('Fagaras', 301, 211), ('Pitesti', 191, 101),
                ('Craiova', 329, 239), ('Eforie', 359, 269)]
        cols = [-6.6, -4.7, -3.0, -1.4]
        header = VGroup(label('city', 18, MUTED), label('d(Giurgiu, c)', 18, MUTED),
                        label('− 90', 18, MUTED), label('= d(Bucharest, c)', 18, GREEN))
        for item, x in zip(header, cols):
            item.move_to([x, 1.7, 0])
        self.play(FadeIn(header), run_time=.5)
        self.play(Create(Line([-6.9, 1.4, 0], [-.1, 1.4, 0], color=MUTED, stroke_width=1.5)), run_time=.4)
        for i, (city, dg, db) in enumerate(rows):
            y = 1.0 - i*.62
            self.play(FadeIn(label(city, 19, INK).move_to([-6.6, y, 0])),
                      FadeIn(label(f'{dg}', 19, CYAN).move_to([-4.7, y, 0])),
                      FadeIn(label('− 90', 19, MUTED).move_to([-3.0, y, 0])),
                      FadeIn(label(f'= {db}', 19, GREEN).move_to([-1.4, y, 0])), run_time=.35)
        self.say('Giurgiu is degree one,\nso its difference is exact.')
        self.say('On 360 of 380 pairs the estimate is exact.', GREEN)
        self.say("Exact where the landmark allows it;\nsafe everywhere else.")

    def consistency(self):
        a, b = LEFT*6.2+UP*.8, LEFT*3.4+UP*.8
        self.play(FadeIn(Dot(a, color=MUTED)), FadeIn(Dot(b, color=MUTED)), run_time=.4)
        self.add(label('Arad', 22, INK).next_to(a, UP, buff=.15),
                 label('Sibiu', 22, INK).next_to(b, UP, buff=.15))
        self.play(Create(Line(a, b, color='#53627A', stroke_width=4)),
                  FadeIn(label('140', 20, MUTED).move_to((a+b)/2+UP*.28)), run_time=.6)
        self.play(FadeIn(label('h(Arad) = 418', 22, GOLD).next_to(a, DOWN, buff=.35)),
                  FadeIn(label('h(Sibiu) = 278', 22, GOLD).next_to(b, DOWN, buff=.35)), run_time=.5)
        self.say('Along one road the estimate may rise.')
        self.say('But only by that road\'s cost:\n418 ≤ 140 + 278.', GREEN)
        self.panel(VGroup(label("h(n) ≤ c + h(n')", 26, INK)))
        self.say('Checked on every road and goal:\nzero violations.')
        self.say('The search still reopens improved states.', CYAN)
        self.say('Optimality rests on admissibility.\nStability is a measured bonus.')

    def guided(self):
        # Replay the real A*(LP+ALT) trace so the payoff is shown, not claimed.
        diagram = self.map()
        trace = DATA['demo']['algos']['astarAlt']
        costs, tree = {'Arad': 0}, {}
        for step in trace['steps'][:-1]:
            current = step['current']
            self.play(Indicate(diagram.nodes[current], color=CYAN, scale_factor=1.3), run_time=.22)
            for edge in DATA['graph'][current]['edges']:
                neighbor = edge['to']
                cost = costs[current] + edge['km']
                if cost < costs.get(neighbor, float('inf')):
                    costs[neighbor] = cost
                    line = Line(diagram.points_by_city[current], diagram.points_by_city[neighbor],
                                color=CYAN, stroke_width=4).set_z_index(1)
                    changes = [Create(line), diagram.nodes[neighbor].animate.set_color(GREEN)]
                    if neighbor in tree:
                        changes.append(FadeOut(tree[neighbor]))
                    self.play(*changes, run_time=.3)
                    tree[neighbor] = line
            self.play(diagram.nodes[current].animate.set_color(CYAN), run_time=.12)
        self.draw_route(diagram, trace['path'])
        self.say('A* with the combined estimate settles 5 cities.', GREEN)
        self.say('Uniform cost settled 13 on the same query.')
        self.say('The route is identical, and still 418 km.')

    def breadth(self):
        w = DATA['work']['lm8']['expansions']
        rows = [('UCS (uninformed)', w['ucs'], PURPLE),
                ('Greedy best-first', w['greedy'], RED),
                ('A* (LP only)', w['astar'], GOLD),
                ('A* (ALT only)', w['astarAltOnly'], CYAN),
                ('A* (LP+ALT)', w['astarAlt'], GREEN),
                ('Bidirectional A*', w['biastar'], MUTED)]
        x0, scale = -4.3, 3.6/11.0
        for i, (name, value, color) in enumerate(rows):
            y = 1.7 - i*.72
            self.add(label(name, 19, color).next_to(np.array([x0, y, 0]), LEFT, buff=.2))
            bar = Rectangle(width=value*scale, height=.32, fill_color=color, fill_opacity=1, stroke_width=0)
            bar.move_to([x0+bar.width/2, y, 0])
            self.play(GrowFromEdge(bar, LEFT),
                      FadeIn(label(f'{value:.1f}', 18, color).next_to(bar, RIGHT, buff=.15)), run_time=.4)
        self.say('Guided search expands about half\nof uniform cost search.')
        self.say(f'Greedy is fewest, but wrong on\n{DATA["work"]["lm8"]["greedySuboptimal"]} of 380 pairs.', RED)
        self.say('Every A* variant here stays optimal.', GREEN)

    def coverage(self):
        # For one goal, show both component bounds city by city; the taller bar
        # is exactly the maximum the search uses.
        pairs = {p['s']: p for p in DATA['variants']['lm8']['pairs'] if p['t'] == 'Bucharest'}
        cities = ['Arad', 'Sibiu', 'Fagaras', 'Pitesti', 'Craiova', 'Eforie']
        y0, scale = -1.9, 3.7
        centers = np.linspace(-5.6, -1.0, len(cities))
        ceiling = DashedLine([-6.4, y0+scale, 0], [.1, y0+scale, 0], color=INK, stroke_width=3)
        self.play(Create(ceiling), FadeIn(
            label('true distance = 1.0', 18, MUTED).next_to(ceiling, UP, buff=.12).align_to(ceiling, LEFT)), run_time=.6)
        for city, cx in zip(cities, centers):
            p = pairs[city]
            for dx, value, color in [(-.19, p['lp']/p['optimal'], PURPLE), (.19, p['alt']/p['optimal'], GOLD)]:
                bar = Rectangle(width=.34, height=value*scale, fill_color=color, fill_opacity=1, stroke_width=0)
                bar.move_to([cx+dx, y0+value*scale/2, 0])
                self.play(GrowFromEdge(bar, DOWN), run_time=.35)
            self.add(label(city, 16, INK).move_to([cx, y0-.42, 0]))
        self.say('Goal: Bucharest.  Purple: LP.  Gold: landmarks.', MUTED, 23)
        self.say('The maximum keeps the taller bar for each city.')
        self.say('ALT usually wins; LP still decides some pairs.', GOLD)

    def saving(self):
        pairs = DATA['variants']['lm8']['pairs']
        M = max(max(p['exp']['ucs'], p['exp']['astarAlt']) for p in pairs) + 1
        ax = Axes(x_range=[0, M, 3], y_range=[0, M, 3], x_length=4.6, y_length=4.6, tips=False,
                  axis_config={'color': MUTED, 'stroke_width': 2, 'font_size': 15}).move_to(LEFT*3.4+DOWN*.2)
        self.play(FadeIn(ax), run_time=.5)
        self.add(label('UCS expansions', 17, MUTED).next_to(ax.x_axis, DOWN, buff=.25),
                 label('A* expansions', 17, MUTED).rotate(PI/2).next_to(ax.y_axis, LEFT, buff=.2))
        self.play(Create(DashedLine(ax.c2p(0, 0), ax.c2p(M, M), color=INK, stroke_width=2)), run_time=.5)
        self.say('The diagonal means equal work.')
        dots = VGroup()
        for i, p in enumerate(pairs):
            x, y = p['exp']['ucs'], p['exp']['astarAlt']
            jx, jy = ((i*37) % 7-3)/3*.14, ((i*53) % 7-3)/3*.14
            color = GREEN if y < x else (MUTED if y == x else RED)
            dots.add(Dot(ax.c2p(x+jx, y+jy), radius=.045, color=color))
        self.play(FadeIn(dots), run_time=.8)
        self.say('Almost every pair lies below the diagonal.', GREEN)
        self.say('A* settles fewer cities on 352 of 380,\nand never more.', GREEN)

    def optimality(self):
        w = DATA['work']['lm8']['optimalCount']
        rows = [('Uniform cost (UCS)', 'ucs', PURPLE),
                ('A* (LP only)', 'astar', GOLD),
                ('A* (ALT only)', 'astarAltOnly', CYAN),
                ('A* (LP+ALT)', 'astarAlt', GREEN),
                ('Bidirectional A*', 'biastar', MUTED),
                ('Greedy best-first', 'greedy', RED)]
        self.play(FadeIn(label('optimal routes / 380 pairs', 20, MUTED).move_to([-3.6, 2.0, 0])), run_time=.4)
        self.play(Create(Line([-7.0, 1.7, 0], [-.2, 1.7, 0], color=MUTED, stroke_width=1.5)), run_time=.3)
        for i, (name, key, color) in enumerate(rows):
            y = 1.1 - i*.62
            n = w[key]
            self.play(FadeIn(label(name, 19, color).move_to([-5.2, y, 0])),
                      FadeIn(label(f'{n} / 380', 19, GREEN if n == 380 else RED).move_to([-1.2, y, 0])), run_time=.4)
        self.say('Every heuristic search is optimal\non all 380 pairs.', GREEN)
        self.say('Greedy alone falls short: 319 of 380.', RED)
        self.say('Guidance keeps the answer exact.')

    def guarantee(self):
        x0, span = -6.6, 6.2
        scale = span/450
        for name, value, color, y in [('optimal cost C*  = 418', 418, INK, 1.2),
                                       ('frontier f(n)  ≤  418', 418, GREEN, .1),
                                       ('selected goal g  =  450', 450, PURPLE, -1.0)]:
            bar = Rectangle(width=value*scale, height=.36, fill_color=color, fill_opacity=1, stroke_width=0)
            bar.move_to([x0+bar.width/2, y, 0])
            self.play(GrowFromEdge(bar, LEFT),
                      FadeIn(label(name, 19, color).next_to(bar, UP, buff=.06).align_to(bar, LEFT)), run_time=.6)
        self.say('Suppose a cheaper route C* still exists.')
        self.say('A frontier city has value no larger than C*,\nso it is expanded before the goal.', GREEN)
        self.say('That contradicts the goal being chosen.', RED)
        self.say('So an admissible estimate preserves optimality.', GREEN)

    def bidirectional(self):
        diagram = self.map()
        self.say('Start at Arad…',CYAN)
        self.play(Indicate(diagram.nodes['Arad'],color=CYAN),run_time=.6)
        self.say('…and at Bucharest.',GOLD)
        self.play(Indicate(diagram.nodes['Bucharest'],color=GOLD),run_time=.6)
        # The exported implementation alternates directions; omit its final
        # synthetic display frame. Relax edges with separate costs/parents.
        costs = [{'Arad':0},{'Bucharest':0}]
        trees = [{},{}]
        for i,step in enumerate(example()['biastar']['steps'][:-1]):
            side = i % 2
            color = [CYAN,GOLD][side]
            current = step['current']
            self.play(Indicate(diagram.nodes[current],color=color),run_time=.3)
            for edge in DATA['graph'][current]['edges']:
                neighbor = edge['to']
                candidate = costs[side][current]+edge['km']
                if candidate < costs[side].get(neighbor,float('inf')):
                    costs[side][neighbor] = candidate
                    line = Line(diagram.points_by_city[current],diagram.points_by_city[neighbor],
                                color=color,stroke_width=4).set_z_index(1)
                    animations = [Create(line)]
                    if neighbor in trees[side]:
                        animations.append(FadeOut(trees[side][neighbor]))
                    self.play(*animations,run_time=.25)
                    trees[side][neighbor] = line
        self.say('Each side uses its own A* estimate.\nThis is bidirectional A*.')
        self.say('The searches share a city.\nAre we done?')

    def meeting(self):
        diagram = self.map()
        self.draw_route(diagram,['Arad','Sibiu','Fagaras','Bucharest'],GOLD)
        self.say('Imagine finding this candidate first:\n450 km',GOLD)
        self.draw_route(diagram,example()['ucs']['path'],GREEN)
        self.say('Another journey costs 418 km.\nA first connection is not a proof.',GREEN)
        self.say('Keep the cheapest complete route found so far.')
        self.say('Call its cost μ.\nCould a cheaper route still remain?')

    def stop(self):
        for y,text,color in [(1.4,'lower bound ≤ optimum',CYAN),
                             (0,'optimum ≤ candidate μ',GOLD),
                             (-1.4,'bounds meet → answer certified',GREEN)]:
            self.play(FadeIn(label(text,25,color,width=6.1).move_to(LEFT*3.7+UP*y)),run_time=.7)
            self.wait(1.5)
        self.say('Each frontier minimum estimates the whole optimum.')
        self.say('When either lower bound reaches μ, no cheaper route remains.')
        self.equation('stop')
        self.say('Do not sum two whole-trip bounds.\nReopen improved states.')

    def metrics(self):
        ex = example()
        values = [('UCS expansions',len(ex['ucs']['steps']),PURPLE),
                  ('Bidir. expansions',len(ex['biastar']['steps'])-1,CYAN),
                  ('UCS generated',ex['ucs']['generated'],PURPLE),
                  ('Bidir. generated',ex['biastar']['generated'],CYAN)]
        for i,(name,value,color) in enumerate(values):
            y = 1.5-i*1.1
            bar = Rectangle(width=value*.27,height=.18,stroke_width=0,fill_color=color,fill_opacity=1)
            bar.move_to(LEFT*(6.8-bar.width/2)+UP*(y-.35))
            self.play(FadeIn(label(f'{name}: {value}',22,color).move_to(LEFT*3.7+UP*y)),
                      GrowFromEdge(bar,LEFT),run_time=.6)
        self.say('Same journey.\nSame optimal cost: 418 km.',GREEN)
        self.say('Fewer expansions can still mean more generated entries.')
        self.say('Preprocessing costs work too.\nThis small map cannot prove scaling.')
        self.say('UCS: explore by cost.\nA*: add an optimistic remainder.\nBidirectional A*: search both ends, then certify.',INK,25)
