# Changelog

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
