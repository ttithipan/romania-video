"""Shared building blocks for the Romania pathfinding animation.

Holds the project data, the palette, the `label` text helper and the `RoadMap`
mobject. Imported by `film.py` (the film) and by the scratch scenes under
`../tmp/vizlab/`.
"""
import json
from pathlib import Path

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'project_data.json').read_text())

INK, MUTED = '#F4F1EA', '#C4C1B9'
CYAN, GOLD, GREEN, PURPLE, RED = '#55D6BE', '#F2C14E', '#8BE28B', '#B39DDB', '#F07167'
config.background_color = '#000000'
config.frame_width = 16
config.frame_height = 9


def label(text, size=25, color=INK, width=None):
    # Shape at a constant large size to reduce small-font positioning
    # quantization. The fixed scale preserves the requested font size;
    # it never depends on the length of the string.
    def typeset(value):
        # Render at a very wide Pango layout width so it never soft-wraps a
        # line. Text SVGs are cached by content (not resolution), so a wrap
        # baked at a small render size would otherwise leak into later
        # higher-resolution renders and clip subtitles unpredictably.
        pw, ph = config.pixel_width, config.pixel_height
        config.pixel_width, config.pixel_height = 10000, 10000
        try:
            return Text(value, font='Avenir Next', font_size=200,
                        color=color, disable_ligatures=True).scale(size / 200)
        finally:
            config.pixel_width, config.pixel_height = pw, ph

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
        DOWN, aligned_edge=LEFT, buff=size * .007)


class RoadMap(VGroup):
    """The Google-Maps wall map: nodes, roads and per-city labels.

    City labels are tagged `map_label` so the layout auditor can ignore them
    (an initial inside its node circle is intentional, not a collision).
    """

    def __init__(self, width=6.8, center=LEFT * 3.9 + DOWN * .2, initials=False):
        super().__init__()
        self.points_by_city = {}
        self.nodes, self.roads = {}, {}
        self.city_labels = {}
        for city, item in DATA['graph'].items():
            self.points_by_city[city] = np.array([(item['x'] - 2043) / 2540 * width,
                                                  -(item['y'] - 1254) / 2540 * width, 0]) + center
        for city, item in DATA['graph'].items():
            for edge in item['edges']:
                if city < edge['to']:
                    road = Line(self.points_by_city[city], self.points_by_city[edge['to']],
                                color='#53627A', stroke_width=2.4)
                    self.roads[frozenset([city, edge['to']])] = road
                    self.add(road)
        for city, point in self.points_by_city.items():
            node = Dot(point, radius=.16 if initials else .068, color=MUTED).set_z_index(3)
            self.nodes[city] = node
            self.add(node)
            name = 'Rimnicu V.' if city == 'Rimnicu Vilcea' else city
            city_label = label(name, 16).next_to(
                node, DOWN if city in ['Arad', 'Sibiu', 'Fagaras', 'Hirsova',
                                       'Giurgiu', 'Craiova', 'Eforie'] else UP, buff=.065)
            city_label.map_label = True
            if initials:
                city_label = label(city[0], 16, '#101010').move_to(node)
                city_label.map_label = True
            city_label.set_z_index(10)
            self.add(city_label)
            self.city_labels[city] = city_label

    def route(self, cities, color=GREEN):
        return VGroup(*[Line(self.points_by_city[a], self.points_by_city[b],
                             color=color, stroke_width=5)
                        for a, b in zip(cities, cities[1:])])
