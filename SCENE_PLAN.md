# Scene plan — one theme across all 22 scenes

Audit basis: one 1920×1080 frame per scene (72% through, `/tmp/pages/`) plus the scene code.
**Caveat: only scenes 01 and 03 are rendered after the black-background commit.** Frames for
02 and 04–22 are pre-commit (`#101010`), so their "grey slab behind the subtitle" is the old
background showing through the black plate, not a defect. Re-render before judging backgrounds.

---

## A. The theme, as it now stands

| element | rule | where |
|---|---|---|
| background | `#000000` | `scene_kit.py:18`, `manim.cfg` |
| palette | INK `#F4F1EA`, MUTED `#C4C1B9`, CYAN `#55D6BE`, GOLD `#F2C14E`, GREEN `#8BE28B`, PURPLE `#B39DDB`, RED `#F07167` | `scene_kit.py:16-17` |
| title | top-left, `Write` on, size 30 | `film.py:340` |
| subtitle | size 23, text bottom 135 px above frame bottom, bottom-anchored | `film.py:48, 64-67` |
| character | 0.92 tall, bottom-left, fades in, idle bob — **absent in 01 and 03** | `film.py:311-326` |
| numbers | `counter()` with a caption above the number | `film.py:349-357` |
| stage | content centred within ±1.2 u of x=0 | measured per scene |
| scene end | fade to black, then 1.5 s of background | `film.py:299-306` |
| close-up scenes | 01 and 03 run character-free with all content at 1.3× | `film.py:471`, scene 01 constants |

Everything below is measured against that table. Two of the reference scenes are the only
1.3×, character-free ones — that is the single biggest "is this the theme or an exception?"
question, item **B2**.

---

## B. Decisions to settle first (each one resolves edits in several scenes)

**B1 — the colour key.** The film currently uses colours two ways at once. Pick one rule per row
and the listed edits follow mechanically.

| meaning | should be | conflicts found |
|---|---|---|
| cost so far (`g`) | PURPLE | `film.py:449` "cost so far" is GOLD (g is PURPLE at 533) |
| heuristic / estimate (`h`, ALT) | GOLD | `sc_landmark:695,700,704-707` paints the leftover RED; `sc_tightness`/`sc_max` use GOLD |
| UCS / explored-by-cost | PURPLE | consistent |
| A* / guided | GREEN? | GREEN at `744,774,776,789`; GOLD at `12:991`. If A* is GREEN, `sc_estimate`'s GOLD `h` bar still reads as the *estimate*, not A* — defensible, but decide |
| optimal result | GREEN | 418 is GREEN at `537` but PURPLE at `412` (scene 01 route) |
| LP result (388) | CYAN or PURPLE | CYAN at `551`, PURPLE at `620` |
| wrong / greedy | RED | consistent |
| contradiction beat | RED | RED at `501`, GREEN at `876` — same rhetorical move, opposite colour |
| code-push highlight | — | GREEN at `939`, GOLD at `12:991` |

**B2 — character policy.** 01 and 03 have no mascot and 1.3× content; the other 20 have a 0.92
sprite at 1.0×. Either the film has a "close-up" tier (then say so and scale the other 20 where
the content is small — see `sc_stop`, `sc_cutwork`), or 01/03 should go back to 1.0× with a
character. Every other per-scene edit below assumes the current split.

**B3 — chart grid.** `sc_max` (`719` line at y=1.7, stroke 4) and `sc_tightness` (`735` line at
y=1.5, stroke 3; bars at 0.8/0.0/-0.8 vs 0.6/-0.25/-0.25) are adjacent charts on different grids.
Adopt the `sc_max` grid in both.

**B4 — code-scene layout.** Panels are identical (7.6 u box) but the type size inside them is
`.scale_to_fit_width()`-driven (`film.py:83`), so the shortest source gets the biggest text:
measured line pitch ≈28 px (13) / 23 px (14) / 26 px (15). Card stacks also differ across 11/12
(width 2.6 vs 2.9, font 18 vs 16, stack top 1.65 vs 1.25, one header row vs two). Needs a helper
change (constant type size, or per-scene width), plus one card spec used by all five.

**B5 — bar-label idiom.** `sc_cutwork:790` is the only bar whose length encodes a value that its
label omits (RED bar = 5, label says only "wrong on 61").

---

## C. Per-scene plan

Impact key: ●●● changes what the scene reads as · ●● consistency fix · ● polish.

### 01 `sc_route` — reference, no changes
Compliant. One watch item: map bottom node at y=-2.78 vs subtitle text top ≈-2.7, the tightest
clearance in the film — if it ever collides, `film.py:400` `UP*0.2` → `UP*0.35`. ●

### 02 `sc_explore`
- ●● `film.py:449` `GOLD` → `PURPLE` — "cost so far" is `g`, which is PURPLE in `sc_estimate` (533).

### 03 `sc_ucsproof` — reference, no changes
Verified centred (cx −0.01) and 1.3×-scaled throughout.

### 04 `sc_estimate`
- ● Flagged only: 418 is GREEN here, PURPLE in scene 01 — same quantity, two colours (B1).
- ● Optional: `533,534,537` `6.0/450` → `9.0/450` with `x0=-2.79` → `-4.17` fills the frame; the
  current chart uses 5.6 u of 16.

### 05 `sc_twoways`
- ●● `film.py:545` — LP vector chain has no labels at all; every reference scene labels its
  elements. One `label` per vector (or one for the chain).
- ●● `film.py:551` `388` CYAN vs `film.py:620` PURPLE — resolve per B1.

### 06 `sc_lpproof`
- ●● `film.py:601-602` — Sibiu, Rimnicu V., Pitesti are bare dots while Arad/Bucharest are named.
  Append three `label(name, 17, MUTED)` entries with the existing `- normal * 0.36` offset.
- ●● same 388 colour conflict (B1).
- ● Edge colours reuse the g/h/f palette with no legend — a viewer can read GREEN as "the answer"
  on the wrong edge.

### 07 `sc_triangle`
- ●● `film.py:633` — node letters are INK here but colour-coded 20 lines later in `sc_landmark`;
  same three objects, two languages, one scene apart. Match `sc_landmark` (L/GOLD, n/CYAN, t/GREEN).
- ● Tokens GOLD (`636,643`) while GOLD means "estimate" elsewhere.

### 08 `sc_landmark`
- ●●● `film.py:653-655` shift all three vertices +0.7 in x (L −4.6→−3.9, n −2.1→−1.4, t 2.2→2.9):
  measured cx −1.27, left-heavy.
- ●● `film.py:708-710` formula to `[0.8, 3.05, 0]`, size 24 → 28: matches 07's inequality and
  clears the title (currently ~2 px of headroom).
- ● leftover painted RED (`695,700,704-707`) vs GOLD for ALT elsewhere — see B1.

### 09 `sc_max`
- ●● `film.py:719` — "true distance  d" is the only quantity on a numeric chart with no value:
  → `'true distance  d  =  418'`.
- Adopt this chart grid in 10 (B3).

### 10 `sc_tightness`
- ●● `film.py:735-742` — line `1.5`→`1.7` and stroke `3`→`4`; bars `0.8/0.0/-0.8` → `0.6/-0.25/-1.10`;
  caption y `1.72`→`1.92`. Identical chart to `sc_max` afterwards.
- ⚠ Flag: 0.73 / 0.98 do not follow from the film's own numbers (388/418 = 0.93, 418/418 = 1.00).
  Confirm these are illustrative, not a worked example.

### 11 `sc_code_search`
- ●●● `film.py:923,925` shift right: `LEFT*3.55` → `LEFT*2.90`, `RIGHT*4.4` → `RIGHT*4.75` — 3.14 u
  of empty black currently sits between the code text and its own cards (content centre −0.67).
- ●● `film.py:926` caption → `'frontier   id · cost'` (two numbers, one caption).
- ●● `film.py:941-943` cards `w=2.6`→`2.9`, add `size=16` to match 12.
- ●● push highlight GREEN (`939`) vs GOLD (`12:991`) — B1.

### 12 `sc_code_astar`
- ●●● `film.py:996` narration says "Timisoara enters at cost 118" while that beat's animation
  inserts the **Rimnicu Vilcea** card — text and visual disagree inside one beat.
- ●● same +0.65 x-shift as 11; coordinated stack move (`959,960,962,963,964,983,992`) so the top
  card lands on 11's row.
- ●● card colours GREEN/GOLD/MUTED have no key; either key them in the caption or mute two of them.

### 13 `sc_code_bounds`
- ● Panel type is the largest of the three code-up scenes — B4.
- ● Highlight colour vs card colour mismatch (`1017` GOLD line / PURPLE card; `1023` CYAN lines /
  GOLD card) — only if highlights are meant to be semantic.

### 14 `sc_code_table`
- ●● `film.py:1038` `card('table   388', GREEN)` → PURPLE, matching scene 13's LP-table card.
  (Trade-off: breaks the pipeline's colour-per-stage scheme.)
- ●● `film.py:1035-1038` drop `size=19` — only size outlier in the family.

### 15 `sc_code_both` — no changes
Cyan/gold front convention matches `sc_bothends` (`889`) exactly; columns symmetric, centre +0.03.

### 16 `sc_race`
- ●●● `film.py:775-776` counters sit at ∓1.1, a centred scoreboard ~3 u from the maps they
  describe, and the two captions merge into one band across the middle. Every other counter sits
  beside its own content (410/421, 448/449, 910/911). → `LEFT*4.1 + UP*2.75` / `RIGHT*4.1 + UP*2.75`.
- ● A* GREEN vs "GOLD = A*" — B1.

### 17 `sc_cutwork`
- ●●● `film.py:788-790` bars off the centred anchor: `0.35, x0=-2.5` → `6.0/11, x0=-3.0`, so the
  widest bar spans ±3.0 like `sc_guarantee`.
- ●● `film.py:790` label → `'greedy   5   wrong on 61'` (the only bar whose label omits its value).
- ● Bread's visible ink measures 0.6×0.6 u against the whale's 0.93×0.66 — PNG padding differs, so
  `sc_cutwork` (and 18, 19, 20, 21, 22) show a smaller mascot than the whale scenes.

### 18 `sc_complexity`
- ●● `film.py:853` the gold spur node is a 6th dot on a stage captioned "5 nodes" — add
  `tag('pruned', 16, GOLD)` beside it, or drop it.
- ●● `film.py:826-829` space-padding hack makes the two O(b^d) columns ragged (16 px skew); anchor
  name and value labels at fixed x instead.
- ● `film.py:859` chip `size=18` → `20`, matching its sibling on 858.

### 19 `sc_guarantee`
- ●● `film.py:876` split the closing line: `'contradiction'` RED + `'→ optimal'` GREEN, so it
  matches scene 03's RED contradiction instead of contradicting it.
- ●● `film.py:870-874` same split-label fix as 18 — the 450/418/418 numbers start at three
  different x positions today, which is the one comparison the scene exists to make.
- ● Optional: `6.0/450` → `9.0/450` with `x0=-4.5` (6 u of 16 in use); `DOWN*2.0` → `DOWN*1.5`.

### 20 `sc_bothends`
- ●●● `film.py:903` the punchline beat ("a meeting alone does not prove it optimal") animates
  nothing — the only scene whose closing beat leaves the frame untouched.
- ●● `film.py:891-897` both fronts `self.add(Line(...))` the same edges, so the merged middle
  reads flat GOLD and the "meet" is invisible. `split_line(a, b, CYAN, GOLD, gap=0.10)` exists for
  exactly this (used at `429`).
- ● `film.py:902` the green "fronts meet → a route" label uses the colour of the thing about to be
  qualified (B1).

### 21 `sc_stop`
- ●●● `film.py:910-911` `∓4.2` → `∓2.8` and add `size=64`: two numbers 8.4 u apart with a ~5 u void
  between them is the emptiest frame in the film, and the bound-meets-cost relationship is never
  shown.
- ●● `film.py:918` `DOWN*0.6` → `DOWN*0.15`, putting "reaches it → stop" under the two equal numbers.
- This is the only scene using `counter()` exactly right — treat it as the counter reference.

### 22 `sc_recap`
- ●●● The finale is four centred text lines: no map, no route, no counter, no motion beyond
  FadeIn — the only scene with no stage. It also never returns to the opening image.
- ●● `film.py:1106-1108` replace the two bare `FadeIn(card(...))` with `counter(...)` at
  `∓2.9 + DOWN*2.4` so the film's last movement is its own numeric device (13 → 5).
- ● Subtitle "5 expansions, the same 418 km route." repeats the on-screen "5 expansions" card.

---

## D. Order of work

1. Settle **B1** (colour key) and **B2** (character policy) — between them they decide ~15 edits.
2. Apply B3–B5 helper-level changes (`bar` labels, code panels, chart grid) once.
3. Apply the per-scene edits, ●●● first.
4. Re-render all 22 scenes, then re-measure: stage centre within ±1.2 u, subtitle text bottom
   110–160 px, `AUDIT=1` clean on every touched scene.
5. Rebuild `output/Film.mp4` last — it is currently stale and does not contain any of this.

## E. Known-good, do not "fix"

- Scenes 01/03 vertical framing (checked: line at +0.52 sits 0.08 above the band centre).
- `sc_race` map symmetry (∓4.10 u), `sc_code_both` column symmetry, `sc_recap` palette listing.
- Node initials at `#101010` (`scene_kit.py:94`) — the only off-palette colour, and justified:
  INK on a MUTED dot would not read.
- Code panels' `monokai` colours — the only non-palette colours in the film, but deliberate.
- Three different blind-search counts on screen (15 illustrative tree in 18, 13 demo UCS in 22,
  11 pair-average in 17) — all correct for their own quantity.
