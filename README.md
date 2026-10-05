# Nullovation City

A personal project tracker drawn as an isometric pixel-art city. Every project is one building: click it for a quick status bubble, or step inside for everything else. It is one self-contained HTML file that runs offline in the browser.

Your city stays in the browser you use it in. Export saves a backup file, Import restores one, and the data file keeps a copy on disk.

## Versions

Tool: 0.1.18. It's shown in small text under the side bar logo, and set in `src/VERSION`. Changes are in `CHANGELOG.md`.

## Build and test

1. `pip install -r requirements.txt`. The build needs only Python; the tests drive Google Chrome through Playwright.
2. `python build.py` writes the page, `index.html`, at the root. The repo keeps it with the source, so it always holds the current page. `python build.py <path>` writes it somewhere else.
3. `python tests/run_tests.py` builds, runs every test pass, and prints one line per pass. `python tests/run_tests.py 9 16` runs only those two. Logs go to `tests/data/logs/`, screenshots to `tests/shots/`.

GitHub Pages serves `index.html` straight from the branch: in Settings, Pages, pick Deploy from a branch, `main`, `/ (root)`. `.nojekyll` makes Pages serve the files as they are.

## What is where

- `index.html`: the page, built from `src/` by `build.py`.
- `src/`: everything the page is built from.
  - `VERSION`, `body.html`, `style.css`, and the modules in `js/`, joined in name order.
  - `buildings/`: the shipped buildings and park lots, with `meta.json` and `lots.json`.
  - `fonts/`: Pixelify Sans and Readex Pro, with their licenses.
  - `setup/`: the folder links setup for Windows, which the page hands out.
- `build.py`: joins `src/` into one HTML file. It also makes two modules in memory: `25-generics.js` from `src/buildings`, and `26-extra.js` from `src/VERSION` and `src/setup`.
- `art/`: how the buildings are drawn. Nothing here ships until it is installed into `src/buildings`.
  - `kit/`: the 256 px kit.
  - `buildings/`: one script per building. Each renders into `art/out/`.
  - `lots/`: the four park lots, with the older kit they use.
  - `canon/`: the original 128 px designs. `render.py` draws them into `canon/out/` to compare.
  - `sources/`: stills made elsewhere that a script starts from.
  - `slim_gifs.py`: shrinks the shipped GIFs, keeping each only if it decodes pixel-identical.
  - `projects/`: art for the projects in the city. It stays on this machine; git leaves it out.
- `tests/`: the test passes, `testkit.py` for their shared setup, and `run_tests.py`.
- `tools/pack.py`: the source archive that carries the work to a claude.ai chat and back.
- `docs/nullovation-city-knowledge.md`: everything about the tool: features, code, data, art, decisions and open items.
- `CLAUDE.md`: the working rules for Claude Code. It imports the knowledge file.
- `.claude/skills/`: the `nullovation-city` and `nullovation-city-builder` skills, where Claude Code loads them.

## Art

1. Draw with a script in `art/buildings/`; it renders into `art/out/`.
2. Compare, then install: copy the GIF and PNG into `src/buildings/` and the GIF into `art/unslimmed/`, and update `src/buildings/meta.json`.
3. `python art/slim_gifs.py` shrinks the GIFs. It needs gifsicle and Node on the PATH.

## Between a chat and Claude Code

- `python tools/pack.py` writes the source archive one folder up, beside this folder, to attach to a chat.
- `python tools/pack.py --apply <zip>` brings this folder up to an archive a chat delivered. Add `--dry-run` to see the changes first. It refuses an older archive unless `--force` is added.

## Credits

The fonts are Pixelify Sans and Readex Pro, from Fontsource 5.3.0, under the SIL Open Font License; the license texts are in `src/fonts/`.
