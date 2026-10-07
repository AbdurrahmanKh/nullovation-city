# Changelog

## 0.1.23 (2026-10-07)

- Street props face their own street on every side of a block: on the south-west and south-east sides we see their fronts, facing those streets; on the north-east and north-west sides their backs, as they face those streets.
  - The bus stops and billboards stood turned sideways on all four sides. The tool took every front as facing the south-west street, but PixelLab drew theirs facing the south-east one; only the vending machine's faces south-west.
  - `src/buildings/props.json` now names the street each front faces as drawn (`faces`), and the map mirrors a view only on the side it does not face. `build.py` refuses a prop without it.
  - The vending machines and bins were right already and look the same; where every prop stands is unchanged.
- Tests: test19 checks each prop's `faces`, that every prop as drawn faces its own street, and, measured on the art itself, that every bus stop, billboard and vending machine front stands with its long side along its street. It saves close-ups of a bus stop and a billboard on each side, `191-*.png`.

## 0.1.22 (2026-10-07)

- Street props round the blocks: bus stops, vending machines, holo billboards and bins, made with PixelLab and drawn at half size like the buildings.
  - Each stands on the sidewalk and faces its street: fronts on a block's south-east and south-west sides, backs on its north-east and north-west, and a tall building may hide part of one behind it.
  - Bus stops follow a fixed pattern, vending machines stand mid-block, billboards by a corner past where a zebra lands, and bins on a building's two front sides, where people walk in. At most two to a side, fixed like the street details.
  - People walk through them, drawn in front or behind by depth. They show with the traffic off too, and keep their neon by night.
  - Buses pull up to a bus stop on their side of the street and pause there for a few seconds.
- Tests: the new test19 checks the props' plan, facing, places, the bus pause, and their night colors.

## 0.1.21 (2026-10-07)

- Three new park kinds for empty plots, made with PixelLab and animated in code:
  - a playground, whose carousel orbs light in turn, with a swaying swing and a butterfly;
  - a sculpture garden of floating stones that lift off their plinths over breathing cyan glows;
  - a mini golf lagoon course with a glowing lighthouse, glints on the pond and fluttering flags.
- The glows keep shining at night. With seven kinds instead of four, every park in the city was reshuffled once.
- `art/slim_gifs.py` also slims without gifsicle, by a delta in Python, keeping the smallest exact result.
- Tests: test06 checks the seven park kinds decode at full size, the new ones animate, and no park repeats its neighbor.

## 0.1.20 (2026-10-07)

- People, still 5 px wide and drawn in code, gain variety:
  - They face the way they walk: walking toward you the face shows under the hair, walking away the head is all hair, and walking left mirrors them.
  - About half have long hair, and half of those wear a dress.
  - Some carry one thing: a courier's coral pack, a tote bag, a cap whose brim points the way they walk, or a phone.
  - The phone and the pack's screen glow cyan and keep their color by night, so the crowd twinkles after dark.
  - A few run, twice as fast, and never stop.
  - Some walk with a kid, 5 px tall, or a dog beside them.
  - 2 cyclists ride the sidewalks on a 5 by 5 map, at about three times walking speed, crossing at zebras; more as the map grows.
- Tests: test13 checks the facing, the looks and their shares, runners, kids and dogs, the cyclists, and the glow by night. test02 sets its project deadline 20 days from today instead of on 8 October 2026, which had turned into "tomorrow".

## 0.1.19 (2026-10-05)

- Open in Claude: beside every Copy for Claude, a menu opens the Claude desktop app with the same text filled in and ready to send: a new chat, a Cowork task with the project's local folders and files attached, or Claude Code in the project's first folder. The text goes on the clipboard too; one too long to fill in opens Claude empty and stays on the clipboard. The more menu also sends the builder card to a new chat.
- The README links the live page.
- Tests: neutral names instead of a work project and folder in test06 and test12, and a new pass, test18_open_in_claude. test15 and test18 read the clipboard with `\n` line ends on Windows too, where Chrome hands them back as `\r\n`.
- Art: `art/pixellab.py` sends PixelLab's Pro a prompt with a local reference image, the recipe for building stills and park lots, and downloads the result. The token comes from `PIXELLAB_SECRET`.

## 0.1.18 (2026-10-05)

- The page is `index.html` at the root: `build.py` writes it there, the repo keeps it, and GitHub Pages serves it straight from the branch, with `.nojekyll`. test17 fails if it is older than the source.
- No more `dist/` folder: the source archive goes one folder up, beside the source folder.
- The Pages workflow is gone, since Pages serves the branch.
- test13: the stop-line probe tries another car and line when a car close ahead holds the first one back, which failed one full run in seven.

## 0.1.17 (2026-10-05)

The source is laid out for GitHub. Apart from the version and the starter city, the page works as in 0.1.16.

- Layout: `src/` holds everything the page is built from, `art/` how the buildings are drawn, `tests/` the test passes, and `tools/` the chat archive. Only `build.py` stays at the root.
- The build makes `25-generics.js` and `26-extra.js` in memory and writes nothing into `src/`.
- A new city starts with one project, Nullovation City. The decision-wizard project is gone, with its links to two claude.ai chats.
- The `d-wizard` skill is no longer copied here: it has its own repo.
- Tests: named by number and topic, from `test02_map.py` to `test17_source.py`. Every browser pass starts from its own test city, so the passes no longer depend on the starter city, and test04 checks the real start. The retired test1 and test3 are gone.
- Art: one folder per job: `kit/`, `buildings/`, `lots/`, `canon/`, `projects/` and `sources/`. The scripts read and write inside the repo instead of chat folders, and `art/canon/render.py` draws the 128 px originals into their own folder instead of over the shipped art.
- `src/buildings/meta.json` gives the width, height and frame count of every building; the stale fields from the 128 px renders are gone.
- New: `requirements.txt`, this changelog, and a workflow that builds the page and publishes it to GitHub Pages.
- CLAUDE.md: Claude never pushes.

Earlier versions were not logged here.
