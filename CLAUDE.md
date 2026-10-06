# Nullovation City

Abdurrahman's personal project tracker, drawn as an isometric pixel-art city. Every project is one building: click it for a quick status bubble, or step inside for everything else. It is one self-contained HTML file that runs offline in the browser.

@docs/nullovation-city-knowledge.md

The file imported above is the knowledge file: features, code, data, art, skills, decisions and open items. Read it before answering anything about the tool, and treat its Decisions section as settled. Build on what was decided; do not re-argue it unless Abdurrahman reopens it. Verify against the source, not memory: read the code, data or files before stating how something works or what was decided.

## Where things go

- `src/`: everything the page is built from, and nothing else: `VERSION`, `body.html`, `style.css`, the modules in `src/js/`, the shipped buildings and lots in `src/buildings/`, the fonts, and the folder links setup in `src/setup/`.
- `art/`: how the buildings are drawn. `art/kit/` is the 256 px kit, `art/buildings/` has one script per building, `art/lots/` the park lots, `art/props/` the street props, `art/canon/` the original 128 px designs, `art/sources/` the stills a script starts from, and `art/projects/` the art for Abdurrahman's own projects, which git leaves out. Scripts render into `art/out/`.
- `tests/`: the passes, `tests/testkit.py` and `tests/run_tests.py`. `tools/`: `tools/pack.py`.
- The root keeps `build.py`, `index.html` (the page it builds), the docs and the config. New files go in their folder, never the root.

## Setup, once per machine

- `pip install -r requirements.txt`: Pillow, NumPy and Playwright. The tests drive Google Chrome; if it is not installed, run `python -m playwright install chrome`.
- Node on the PATH, only for `art/slim_gifs.py`; it also uses gifsicle when that is on the PATH.
- scipy, only for `art/buildings/city_hall.py`; global-land-mask, only for the Projection Court scripts in `art/projects/`.
- On Windows, use `python` where these notes say `python3`.

## Build and test

- Build: `python3 build.py` writes the page to `index.html` at the root. The repo keeps it and GitHub Pages serves it, so rebuild it with every change; test17 fails when it is older than the source.
- Test: `python3 tests/run_tests.py` builds, then runs every pass in order and prints one line per pass. `python3 tests/run_tests.py 9 16` runs only those. Logs go to `tests/data/logs/`, screenshots to `tests/shots/`.
- The passes are named by number and topic, from `tests/test02_map.py` to `tests/test18_open_in_claude.py`. `tests/testkit.py` holds their shared paths, draws the files they upload, and sets up the test city every browser pass starts from, so the passes do not depend on what a new city starts with.

## Every change to the tool

- Bump the patch in `src/VERSION`: 0.1.19, 0.1.20, and so on, and add the version to `CHANGELOG.md`. Never go to 1.0.0 before production. The version shows as very small text under the side bar logo.
- Back every change with tests: run all passes, add checks for new behavior, and fix or explain every failure before calling the work done.
- Look before presenting: open the screenshots of what changed, and for art, show side-by-side comparisons.
- Keep `docs/nullovation-city-knowledge.md` true: the version line, features, code, decisions and open items.
- Never branch, commit or push, and never add or change a remote: Abdurrahman does all of git himself. Work in the folder and leave the changes for him to commit; end with a short summary he can use as the commit message.
- Report briefly: what changed, the new version, and the test count.

## Moving between Claude Code and claude.ai chats

The source travels as `nullovation-city-source-v<version>.zip`, with one `nc/` folder inside. Chats in the Nullovation City project on claude.ai unzip it into `/home/claude`, which makes `/home/claude/nc`, and work there.

- To continue in a chat: `python3 tools/pack.py` writes the archive one folder up, beside this folder. Abdurrahman attaches it to the chat, and replaces the project's knowledge file with `docs/nullovation-city-knowledge.md` when it changed.
- When a chat delivers a new archive: once Abdurrahman has committed his work, run `python3 tools/pack.py --apply <path to the zip> --dry-run` to see what changes, then the same without `--dry-run`. It refuses an archive older than this folder. Then build, run the tests, and hand him the chat's report as the commit message.

## Decisions

- Ambiguous design, UI or content questions go to a decision wizard round through the `d-wizard` skill. When the answer can be reasoned out, reason it out directly instead of asking.
- When answers come back, report on them by question id, act on what was decided, and draft a follow-up round only for questions the answers opened.
- When Abdurrahman corrects something, rebuild it properly rather than patching around it.
- Only what you know: never invent tasks, facts, features or decisions. Plans and tasks hold only what was actually discussed.

## Writing

- Never use the em dash or the en dash, in anything: replies, files, code comments, UI text. Use a comma, colon, semicolon or hyphen. `build.py` refuses to build if one reaches the tool.
- Keep replies short, plain and direct, with concrete numbers and names.
- UI text is short and plain, in the voice the tool already uses.

## Art

- Art fidelity over reinvention: when refining a building, keep its original design, size and proportions, and add detail, color and character. Never simplify, shrink, or swap in a different design unless asked.
- The style: pastel sci-fi in SNES-era pixel art, colorful with a lead color, never white on white, a little strange. The city hall, Abdurrahman's own building, is the standard to reach.
- Building art is 256 px wide, true pixel art, 2:1 isometric, lit from the top left, with a 1 px dark outline, drawn on the plot geometry in the knowledge file. Animations are GIFs with calm motion.
- Every GIF must decode exactly in the tool's own decoder. Optimize with `art/slim_gifs.py`, which keeps a file only if it decodes pixel-identical and smaller.
- Show redesigns and new buildings for approval before installing them in the tool.
- No image model runs here. Images are drawn in code, or made by Abdurrahman in a service such as PixelLab from the builder skill's prompts.

## Skills

The project's skills are in `.claude/skills/`, where Claude Code loads them:

- `nullovation-city`: writes a tasks file or a whole plan as JSON, which the tool loads with Load plan or tasks.
- `nullovation-city-builder`: designs a project's building as three concepts, each with a subject-only image prompt, a full prompt and an animation prompt.

They are also the sources of the skills in Abdurrahman's claude.ai plugin. After changing one here, it gets reinstalled there.

`d-wizard`, for decision rounds, is not part of this repo: it has its own. Claude Code gets it from the personal skills folder (`~/.claude/skills/d-wizard/`), chats and Cowork from the claude.ai plugin.
