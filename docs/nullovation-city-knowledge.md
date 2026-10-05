# Nullovation City: everything to know

State as of version 0.1.18 (October 2026). The tool file is about 1.4 MB.

## 1. What it is

Nullovation City is Abdurrahman's personal project tracker, drawn as an isometric pixel-art city. Every project is one building: click it for a quick status bubble, or step inside for everything else. It is one self-contained HTML file that runs offline in the browser, with everything stored locally. It holds his real projects, around 13 of them.

A building is a company that is always alive, whatever the project's status. Buildings never show progress or stage; the bubbles carry status.

What Abdurrahman keeps:
- The tool: `index.html` at the root of the repo, which GitHub Pages also serves. A chat delivers it as `nullovation-city.html`.
- His data file: a JSON file on disk that the tool keeps up to date.
- Exported backups.
- The skills: `nullovation-city` and `nullovation-city-builder`, whose sources are in the source, and `d-wizard`, which has its own repo.
- The source, in a GitHub repo that Abdurrahman pushes; Claude never pushes. It travels to chats as the archive `nullovation-city-source-v<version>.zip`: code, art scripts, building animations, tests, fonts, the two skills' sources, `CLAUDE.md` for Claude Code, and a copy of this file. Section 8 covers how it moves between chats and Claude Code.

## 2. Features

### The city map

- The map is an N by N grid of plots, from 5 by 5 up to 11 by 11, grown or shrunk one ring at a time from the side bar. Each plot is 4 by 4 tiles, with streets between plots.
- Empty plots become parks, in four kinds: garden, park, plaza, and pond.
- Streets vary by segment, fixed so they look the same every visit: repair patches, cracks, manholes, drains, center lines (dashed, double, none, turn arrows), sidewalk paving, crossings (zebra, stop line, none), and crossing centers (plain, manhole, yellow box, small roundabout).
- Zoom steps are 1x, 2x, 3x, 4x, 6x, and 8x. At even steps every building pixel lands on whole screen pixels. At 3x a building is first enlarged crisply to 2x, then scaled down smoothly, so it stays sharp.
- Drag to pan. Q and E jump to the previous or next building, and Esc backs out one layer at a time.
- The bar at the bottom right holds Traffic, Bubbles, Time of day, Postcard, and Zoom.
- Bubbles and Time of day open drop-ups: stacks of the same buttons as the bar, rising above the one clicked. Each option has its own icon, and the bar's button wears the chosen option's icon and label. The current choice shows pressed, arrow keys and Enter work, and Esc or a click outside closes.
- Time of day:
  - Auto (clock icon) follows the computer's clock, passing through dawn and dusk.
  - Day (sun).
  - Dusk (a sun on the horizon) holds the halfway light. Dawn looks the same, so it is listed once.
  - Night (moon).
- Bubbles:
  - Bubbles (alert icon) shows red and yellow urgency.
  - Red only (flag).
  - Tasks (task icon) puts a near-white bubble over every building with that project's count of open tasks, 0 included.
  - No bubbles (cross).
- Postcard saves the current view as a PNG.

### Traffic

The city has 12 cars, 2 small buses, and 2 delivery drones on a 5 by 5 map, scaled with the map's area. 20 people roam the whole city.

- Cars keep to the right, turn at crossings, stop at stop lines, wait at zebras, and keep a gap. They do not yet yield inside crossings, so turning paths can briefly overlap.
- At night, cars and buses driving toward you show two warm headlights and a soft cone of light on the road ahead. Cars driving away show red tail lights.
- Drones hop between busy buildings.
- Busyness comes from a project's activity log over the past 7 days, each event fading out over the week. A building with busyness of 0.3 or more draws its own crowd.
- The crowd size is a setting under Tools: None, Small, Medium, or Large, for 0, 8, 14, or 20 extra people per busy building. Medium is the default, and the whole city is capped at 150 people.
- People walk the sidewalks, cross at zebras, gather in groups and talk, sit on park benches, and go in and out of buildings.
- The Traffic button turns all of it on or off.

### Urgency and bubbles

Each project picks an urgency system:
- **None.**
- **Work until finished:** its open tasks count.
- **One task per N days:** a pace. If no task is finished in time, the project turns red.

Due dates also count: tasks due soon or overdue jump to the top of the status bubble. Red and yellow bubbles float over buildings that need attention, showing a count, or "!" for a single item. The side bar's Urgent section lists red projects.

### The status bubble

Click a building for a small card:
- the project's next 3 open tasks, with those due soon first;
- tasks can be ticked off from it, with a short animation;
- when the project was last updated;
- an Enter button that steps inside.

### The project view (stepping inside)

- **Top:** the building's picture and the About, which is the project's description.
- **Milestones and tasks:** tasks are grouped by milestone. They can be reordered by dragging, and each has an optional due date and a description. A task opens in a side panel, with Copy for Claude.
- **Milestone view:** clicking a milestone's name opens its rename field and its tasks as a read-only list. Done tasks are ticked and struck through, and open ones show their due date and the first line of their description. It also has Copy for Claude and Delete milestone.
- **Notes:** notes show as cards, each with its own copy button. A note opens in a panel with Copy for Claude and Delete.
- **Links:** links show icons: doc, task, design, code, chat, folder, web. A Windows path pasted as a link is detected as a folder. With the setting on, folder links open in File Explorer.
- **The more menu:** Load plan or tasks (JSON from the nullovation-city skill), Copy for builder, and the building panel. The building panel picks one of the generic buildings, uploads the project's own art as a PNG or GIF, or flips the building.
- **The urgency system:** chosen per project.

### The side bar

- **Top:** the logo, with the version in very small text under it, and New project, which you plant on a free plot.
- **Lists:** search, This week (the weekly recap), Urgent, and Due this week.
- **Map size:** grow or shrink the grid.
- **Tools:**
  - Copy status brief, a summary of every project for a Claude chat.
  - Download palette, the city palette as a PNG.
  - Crowds round busy buildings.
  - Folder links open in File Explorer, with "Get the setup".
- **Backup and data file:** Export, Import, and the data file connection.
- **Controls:** a short guide to the controls.

### The weekly recap

The recap keeps one snapshot per Saturday-to-Friday week, and you can go back to any older week.

### Copy for Claude formats

Every copy ends with the project's About, cut to its first 900 characters.

| Copy | Opens with | Then |
|---|---|---|
| Task | `# Task: <title>` | Project, milestone, due date, state, and the description |
| Note | `# Note: <title>` | Project, when it was written, and the note |
| Milestone | `# Milestone: <name>` | Project and progress; every open task with its due date and full description; then the done tasks as a list |
| Builder card | `# Nullovation City builder card` | Project name and size signals (open and done tasks, milestones, notes, links), description, milestones, open and done tasks. Abdurrahman may add his own idea for the building under it. |
| Status brief | `# Nullovation City status, <date>` | Every project at once |

### Data, storage, and backups

- A browser with nothing saved starts a new city with one project: Nullovation City, on the city hall.
- Everything lives in the browser on that computer; nothing is uploaded anywhere. The database sits in localStorage under `nullovation-city:v1` (database version 2). Uploaded art and the data file's handle sit in IndexedDB. Another browser or device does not see any of it.
- Export makes one JSON backup with every project and its uploaded art. The art is stored as text, about a third bigger than the image. Import restores both.
- **The data file:** a JSON file on disk, picked once, that the tool rewrites on every change (File System Access API).
  - A busy file gets quiet retries after 1, 3, and 8 seconds.
  - Failures name their cause: "moved or deleted" offers Pick the file again; "busy" offers Try again; ended permission becomes "paused" with Allow.
  - Only one tab writes at a time: the one in use. Other tabs stand by.
  - The tool never reads the data file back by itself. On a new device you import it.
- Storage keys:

| Key | Holds |
|---|---|
| `nullovation-city:v1` | The database |
| `nullovation-city:light` | Time of day choice |
| `nullovation-city:bubbles` | Bubbles choice |
| `nullovation-city:traffic` | Traffic on or off |
| `nullovation-city:crowds` | Crowd size |
| `nullovation-city:explorerLinks` | Folder links setting |
| `nullovation-city:fileWriter` | Which tab writes the data file |
| `nullovation-city:ui` | Interface state |
| `nullovation-city:art`, `:dataFile`, `:dataFolder` | Art and data file storage |

### Folder links in File Explorer

A web page cannot open Explorer by itself, so a one-time setup adds a `nullovation-folder:` link type for the current Windows user.

- **The setup:** `nullovation-folder-links.ps1`, from Tools, Get the setup. Run it from a normal PowerShell window, not admin:
  - Install: `powershell -ExecutionPolicy Bypass -File .\nullovation-folder-links.ps1`
  - Remove: add `-Uninstall`.
  - It waits for Enter before closing, so the result stays on screen; `-NoPause` skips that.
- **The helper:**
  - It reads paths forgivingly.
  - It opens a folder, or a file's folder with the file selected, and never runs anything.
  - When it cannot open something, it shows a popup saying why.
  - It records each click in `%LOCALAPPDATA%\Nullovation City\last-link.txt`.
  - It tries to bring the Explorer window to the front.
- **Checking it from PowerShell:** `Test-Path 'HKCU:\Software\Classes\nullovation-folder'` should print True, and `Start-Process 'nullovation-folder:C%3A%5CWindows'` should open C:\Windows.

## 3. The code

### Source tree (unpacked at `/home/claude/nc` in a chat, or the git repo on the PC for Claude Code)

The root keeps only `build.py`, the docs and the config; everything else sits in a folder by its job.

- `build.py`: builds the tool. `python3 build.py [output]`, with the default output `index.html` at the root.
- `index.html`: the page, built from `src/`. The repo keeps it with the source and GitHub Pages serves it from the branch; test17 fails if it is older than the source.
- `src/`: everything the page is built from, and nothing else.
  - `src/VERSION`: the version, the one source for it.
  - `src/body.html`, `src/style.css`, and `src/js/*.js`, concatenated in name order.
  - `src/buildings/`: the shipped building and lot animations and stills, with `meta.json` (id, title, footprint, width, height, frames) and `lots.json`.
  - `src/fonts/`: the five Pixelify Sans and Readex Pro files the build embeds, with their licenses.
  - `src/setup/nullovation-folder-links.ps1`: the folder links setup, embedded in the tool.
- `art/`: the art pipeline (section 4). Nothing in it ships until it is installed into `src/buildings/`.
- `tests/`: the passes; `testkit.py` for their shared paths, fixtures and test city; and `run_tests.py`, which builds, then runs every pass in order with one line per pass: `python3 tests/run_tests.py [9 16 ...]`.
- `tools/pack.py`: writes the source archive, and applies one back over a folder (section 8).
- `CLAUDE.md`: the working rules for Claude Code. It imports `docs/nullovation-city-knowledge.md`, the copy of this file that travels with the source.
- `CHANGELOG.md`: one entry per version, from 0.1.17. `requirements.txt`: the Python packages for the tests and the art.
- `.claude/skills/`: the sources of the `nullovation-city` and `nullovation-city-builder` skills, where Claude Code loads project skills.
- `.nojekyll`: makes GitHub Pages serve the files as they are.
- Made by runs, kept by neither git nor the archive: `tests/shots/` (screenshots), `tests/data/` (generated fixtures, logs, files the passes write), `art/out/` and `art/canon/out/` (renders).
- Kept on this machine and in the archive, but not in git: `art/unslimmed/` and `art/projects/`.

### Modules (`src/js`)

| File | Role |
|---|---|
| `00-util.js` | Dates and small helpers |
| `10-store.js` | IndexedDB storage for art and the data file handle |
| `15-datafile.js` | The data file: saving, retries, named causes, one writer across tabs |
| `20-model.js` | The world grid, projects, tasks, milestones, urgency, plan and tasks loading, Copy for Claude texts |
| `25-generics.js` | Made by the build in memory, never on disk: the generic buildings and lots from `src/buildings` |
| `26-extra.js` | Made by the build in memory, never on disk: `APP_VERSION` and the folder links setup |
| `30-pixel.js` | The city palette, the light (day, dusk, night), pixel icons, and the art loader |
| `35-gif.js` | The tool's GIF decoder |
| `40-map.js` | The map: geometry, streets, drawing, depth sorting, zoom, bubbles, drop-ups, the bar's buttons |
| `45-traffic.js` | Cars, buses, drones, people, busyness, crowds, headlights |
| `50-bubble.js` | The status bubble |
| `60-fullview.js` | The project view: tasks, milestones, notes, links, panels, local paths |
| `62-picker.js` | The building picker |
| `65-recap.js` | The weekly recap and the status brief |
| `70-menu.js` | The side bar |
| `90-boot.js` | Start-up, and Esc backing out one layer at a time |

### Data model (database version 2)

- **Database:** `{ app: 'nullovation-city', version: 2, world: { size }, projects: [] }`.
- **Project:**
  - identity: `id`, `name`, `description`, `deadline`, `progressOverride`;
  - content: `todos`, `links`, `milestones`, `notes`;
  - placement and art: `plot: { u, v }`, `art: { has, includesPlot }`, `generic` (a generic building's id, or null), `flip`;
  - history: `activity`, the log that busyness reads;
  - urgency: `urgency: { system: 'none' | 'finish' | 'pace', days, lastWorked, pickedAt }`;
  - timestamps: `createdAt`, `updatedAt`.
- **Task:** `{ id, text, description, done, doneAt, due, milestoneId }`, with dates as YYYY-MM-DD.
- **Note:** a `title`, `text`, and `at` timestamp.
- **Constants:** `WORLD = { N: 5, S: 4, GAP: 2, MARGIN: 2, TW: 32, TH: 16, MIN_N: 5, MAX_N: 11 }`.

### Build

`build.py` does the following:
- concatenates the modules, CSS, and body;
- embeds the fonts;
- makes `25-generics.js` in memory from `src/buildings/meta.json`, `lots.json` and the GIFs;
- makes `26-extra.js` in memory with `APP_VERSION` from `src/VERSION` and the setup script;
- writes nothing into `src/`;
- replaces `{{VERSION}}` in the body;
- writes one self-contained HTML file: `index.html` at the root, unless given a path;
- finds the source from its own location, so it runs from any folder;
- writes UTF-8 with LF line ends, so a build on Windows is byte-identical to one in a chat.

### Tests

There are 15 passes and 376 checks, all passing at 0.1.18. `python3 tests/run_tests.py` runs them all, and `python3 tests/run_tests.py 9 16` runs passes by number. Each browser pass runs Chrome through Playwright, prints PASS or FAIL lines and console errors, and can run alone, for example `python3 tests/test09_urgency.py`. The coverage:
- **test02_map:** zoom and the map.
- **test04_seed_data:** the data version, and the real start: a browser with nothing saved gets one project, Nullovation City.
- **test05_bubble_art and test08_bubble_tasks:** the status bubble.
- **test06_generics:** the generic buildings decoding.
- **test07_project_view:** activity and the project view.
- **test09_urgency:** urgency, the bubbles, the bubbles menu, and postcards.
- **test10_sidebar:** the side bar.
- **test11_load_plan:** loading plans and tasks.
- **test12_folder_links:** folder links.
- **test13_traffic:** traffic and crowds.
- **test14_data_file:** the data file.
- **test15_notes_milestones:** copy for notes and the milestone view.
- **test16_dropups:** the drop-ups, the Tasks view, and dusk.
- **test17_source:** the source travels: no chat paths in the scripts; the layout (only `build.py` at the root, nothing written into `src/`, git leaving out what runs make, no `dist/`, `.nojekyll` in place, nothing of the decision wizard in the tool or its tests); `index.html` matching a fresh build; what the archive holds and leaves out; a byte-identical build from a copy in another folder; and applying archives safely. It needs no browser.

Every browser pass but test14_data_file starts from the test city in `tests/testkit.py`, written into the browser before the page first loads: the starter project as it was at 0.1.16, plus a made-up second project, Garden planner, on the research lab. So the passes do not depend on what a new city starts with. It is written once per tab and never on a reload. test14_data_file needs no projects and goes without it: with an init script in its browser context, its two-tab checks failed about one run in three.

The headless test browser sometimes loses a page's stored writes on reload. test09_urgency and test16_dropups detect it, print a NOTE, set the value again, and retry. The real tool is not affected. In test13_traffic, the car the stop-line probe sets down can be held back by another car close ahead in its lane, as it should be; the probe then prints a NOTE and tries another car and line.

Every pass builds its paths from the source folder through `tests/testkit.py`, which also draws the files the passes upload on first use: a JPEG, a 700 px PNG, a still PNG, a 128 px block PNG, an 8-frame GIF with set margins, and a version 1 backup for test04. Before 0.1.16 those files existed only in one chat's sandbox, so a fresh chat could not run test2, test4, test5, test6 or test11.

## 4. Art

### Standards

- **Size and plot:** building art is 256 px wide; the map shows it at half size. The plot is drawn into the art: its surface is a flat 2:1 diamond spanning the full width, with its front corner at the bottom edge, centered. There are no empty margins.
- **Style:** true pixel art with hard edges, 2:1 isometric, lit from the top left (left faces lit, right faces in shade), a 1 px dark outline round every shape, and a transparent background. The palette is the city's own, with about 18 to 46 colors per building.
- **Character:** pastel sci-fi in SNES-era style. Colorful with one lead color, never white on white, with soft sci-fi shapes and a little strangeness. The city hall is the standard to reach.
- **Lots:** each lot has its own design: paving, lawns, paths, pools, shrubs. Not every lot needs a ring of grey tiles.
- **Motion:** calm. Slow and uneven, with no visibly repeating pattern; only small things may move fast. A typical building is 40 frames at 200 ms. Motion over open sky, such as steam, cranes, drones, or a swinging dish, needs full frames.
- **Night:** the tool computes night colors itself. Lit windows, neon, and glows keep shining, so every building should give some light at night.
- **GIF rules:** at most 256 colors per frame. Every GIF must decode pixel-identical in the tool's own decoder (`src/js/35-gif.js`).

### Pipeline

1. Draw with a building script in `art/buildings/` (the kit is in `art/kit/`: `kit.py` with Canvas, Layer, prism, rounded_rect, circle, composite, ramp, save, tree; plus `shapes.py` for domes and vaults, `lot.py` for lots, `parks.py` for benches and lamps). It renders to `art/out/`, made when missing.
2. Show it for approval with side-by-side comparisons: the original, the current version, the new one.
3. Install: copy the GIF and PNG into `src/buildings/` under the building's id, and the GIF into `art/unslimmed/` too. Update its width, height, and frames in `src/buildings/meta.json`.
4. Optimize: `python3 art/slim_gifs.py` (needs gifsicle and Node) runs gifsicle -O3 and keeps a file only if the tool's decoder reproduces every frame exactly and it is smaller.
5. Build, bump the version, and run the tests.

The original 128 px designs, the canon, live in `art/canon/generics.py` with `art/canon/kit.py`. `python3 art/canon/render.py` draws all eleven into `art/canon/out/` with a contact sheet, for the side-by-side comparisons. The park lots come from `art/lots/lots.py`, which still uses the first 256 px kit, `art/lots/lots_kit.py`. At 0.1.17 every code-drawn building and lot re-renders pixel-identical to the shipped art. The city hall animates Abdurrahman's PixelLab still: `art/buildings/city_hall.py` needs scipy and that still in `art/sources/city-hall.png`.

### The generic buildings

| Building | Design |
|---|---|
| City hall | Abdurrahman's own building: pink-trimmed teal glass under a dome holding a tiny city, lit windows. The standard. |
| Worksite | Rising floors with scaffolding, a tower crane with a swinging jib and a red warning light, a site cabin |
| Habitat pod | A lavender banded pod and dome, glowing portholes, airlock, solar panel, flickering hologram, cyan hover glow |
| Research lab | A white block with sky-blue trims and rounded corners, ribbon windows, a neon ticker over the door, a sweeping dish, a rooftop AC unit, and a bench |
| Data tower | A tall glass tower with lit windows and a cyan strip |
| Hangar | A peach and coral vault with a skylight strip, a glowing bay door, chevron lights, a hovering tug |
| Greenhouse dome | The original's tall glass dome with plants and grow lights, a vestibule, and the original lot's water pool |
| Power station | A floating orb in a turning cage with a gold ring, energy arcs, sparks, and steaming vents |
| Comms spire | A tall banded violet needle with beacons, a glowing antenna ring, and an equipment shed |
| Workshop | A white block with a coral band, a half-open bay door with a warm glow, an angled roof crane with a swaying hook, a cart rolling across the yard, and crates |
| Kiosk | A striped awning, a neon sign whose glyphs flicker and half fail, a steaming cup |
| Home | A pink gabled house at the original's size, chimney, lit windows, fence, mailbox, tree, on the original lawns and path |

The four park lots are `lot-garden`, `lot-park`, `lot-plaza`, and `lot-pond`.

### Art made for projects (delivered as files, not generics)

- **Generals and Diplomats:**
  - The Situation Tower: a stepped teal glass HQ with a helipad and drone, a situation room map in six player colors, an uplink dish, and flags.
  - The Projection Court: an amphitheater with a holographic Earth showing real continents from the `global-land-mask` package, each continent in a player's color, plus a spire, flags, and a gold-lined lot. Two passes; the second takes details from Abdurrahman's reference image, in slightly darker colors.
  - The theme is modern and a little futuristic, not old-world.
- **Handheld building:** Abdurrahman's PixelLab art, a giant game console, animated. The hut charges the console along its cable, the hero hops on the screen, the side lights fill. The still has 12,284 colors and a lot skewed 7 px off center.
- **Ring tower:** his art, animated. Three glyph rings turn at their own speeds behind a fixed plaque column, the lockers' keyholes blink, and a cloud beacon pulses.
- **Where their scripts are:** `art/projects/`, which git leaves out: `situation_tower.py`, `projection_court.py` and `projection_court2.py` for Generals and Diplomats, `animate_handheld.py`, and `animate_vault.py` for the ring tower. The last two read their stills from `art/projects/sources/` (`HandHeld-Building.png` and `ring-tower.png`). All of them render into `art/out/`.

### Image services

- No image model runs inside Claude here. Images are drawn in code, or made by Abdurrahman in a service such as PixelLab from the builder skill's prompts.
- PixelLab: the Pro tool is recommended over Pro Flash for prompts over 2,000 characters. Animation tools (PixMiniMax, skeleton v3) need Tier 1 or higher, even through the API, and API calls draw from the same monthly pool as the web app. Pro Flash allows custom sizes up to 256 px (beta); Bitforge is limited to 200 by 200.

## 5. Skills

- **`nullovation-city`** writes a tasks file or a whole plan as JSON, loaded in the tool with Load plan or tasks. Only what you know: it never invents tasks. A validator lives in its `scripts/check_plan.py`.
  - Tasks file: `{ app: 'nullovation-city', kind: 'tasks', version, milestone, tasks: [{ text, description }] }`. The tasks join a milestone chosen on loading, and nothing is replaced.
  - Plan file: `{ app: 'nullovation-city', kind: 'plan', version, project: { name, description, milestones: [{ name, tasks: [{ text, description }] }], ideas: [{ title, text }], links: [] } }`. It replaces the description, milestones, and tasks, with a warning first.
- **`nullovation-city-builder`** designs a project's building.
  - The rewrite, decided in a wizard round:
    - three concepts, two grounded and one wild;
    - each a one-line pitch, then a card: name, idea, why it fits, look, signature, supporting pieces, lot, motion, size, and leader;
    - three copyable prompts per concept: a subject-only prompt for services with style settings such as PixelLab, a full prompt with the style words, and an animation prompt describing the motion;
    - delivered in chat;
    - service settings, such as size, live in its `references/services.md` and are only given when asked.
  - The organization's plugin now loads the rewrite. Checked at 0.1.16: the installed copy matches the source except for quotes around its name.
- **`d-wizard`** writes decision rounds as JSON, named `YYYY-MM-DD-topic-roundN.json`, and reads the answers JSON back (`meta.tool` is `decision-wizard`). It has its own repo, and nothing of it lives in this one: Claude Code gets it from the personal skills folder (`~/.claude/skills/d-wizard/`, copied from that repo), chats and Cowork from the claude.ai plugin.
- **Where the sources live:** `.claude/skills/` in the source holds the two city skills, so Claude Code loads them there. The claude.ai plugin is installed separately; after changing a skill's source, it gets reinstalled there.

## 6. Decisions (settled)

- **Status:** buildings never show status, progress, or stage; bubbles do.
- **Art fidelity:** refining keeps the original design, size, and proportions, and adds detail and character. All 12 generics are now ported from their originals at 256 px.
- **Lots:** every lot is its own design, not a grey tile ring.
- **Versioning:** the tool started at 0.1.0. Every small fix or UI change bumps the patch (0.1.1, 0.1.2, and so on), and 1.0.0 waits for production. The version shows in very small text under the side bar logo.
- **Zoom:** includes 3x, drawn sharp.
- **Drop-ups:** the same buttons as the bar, each option with its own icon, the current one pressed.
- **The Tasks bubble view:** counts open tasks, showing 0 too.
- **Crowds and lights:** a crowd-size setting with a ceiling of 150, and headlights and tail lights at night.
- **Copies and the milestone view:** Copy for Claude for tasks, notes, and milestones. The milestone view lists its tasks read-only.
- **The data file:** quiet retries, named causes, one writer across tabs.
- **Folder links:** the `nullovation-folder:` link type plus the one-time setup.
- **Repo layout (0.1.17):** `src/` holds everything the page is built from, `art/` how the buildings are drawn, `tests/` the passes, `tools/` the chat archive; only `build.py` and the page it builds, `index.html`, stay at the root besides the docs and config. The build writes nothing into `src/`.
- **Nothing of the decision wizard in this repo:** it has its own. A new city starts with only Nullovation City.
- **Pushing:** Abdurrahman creates the GitHub repo and pushes. Claude never pushes or touches the remote; Claude Code may commit.
- **The page in the repo (0.1.18):** `index.html` at the root is built and committed with every change, and GitHub Pages serves it straight from the branch. There is no `dist/` folder; the chat archive goes one folder up, beside the source folder.
- **The traffic tonight round:** cars yielding in crossings, a speed check on a 7 by 7 city, and cleaning the handheld's colors were skipped.
- **Leaders:** designed over two wizard rounds and not built yet (design only). The design:
  - **Who:** one leader per project now, a crew later. A leader is created with a new project's building through the builder skill, or on its own. A redesign keeps the leader. Leaders and notes are separate things.
  - **What a leader holds:** name, role, look (two or three visual traits), a one-line personality, greeting, short bio, signature color, a square portrait (uploaded like building art, from any source), and lines.
  - **Voice:** a written voice, one free text in the shape of Abdurrahman's Shop Town Dooter character voice reference. That means who they are, how they sound, core and secondary patterns, obsessions, confidence, dominant feeling, and what they would never do, plus its usage rules: the profile is a compass, not a checklist. It is mainly for writing lines, and a leader works without it. A spoken voice comes later.
  - **Lines:** written by the art builder skill with the leader, and edited by Abdurrahman. They can be fixed or have blanks the tool fills from the project, such as the next task. Any number per moment, one picked at random.
  - **When they speak:** on opening the project view (a greeting with the next task), when the building turns red or yellow, and when a milestone is finished. The greeting comes first, then red or yellow, then the milestone. Not in the week recap.
  - **Where they show:**
    - a leader card in the project view, beside the About: portrait, or a silhouette tinted in their signature color, picked once and kept; name; role; the current line;
    - a big dismissable speech bubble over the building for red, yellow, and milestone moments, with the same line repeated in the card;
    - the builder card;
    - Copy for Claude, which carries name, role, the full voice, and their assigned projects;
    - not the status bubble;
    - a small figure on the map, later.
  - **Unanswered:** whether "assigned projects" means one leader can run several projects.

## 7. Open items

- Leaders: the design is ready. Building it waits for Abdurrahman, along with the unanswered question above.
- Opening the city on another device, such as a first-launch prompt to open the data file: needs design.
- Cars yielding inside crossings, the 7 by 7 speed check, and the handheld's palette: skipped for now.
- Later: the leader figure on the map, a leader crew, and a spoken voice.
- An idea Abdurrahman mentioned: connecting PixelLab to Claude Code through MCP, to send prompts and save files automatically. It needs an active PixelLab subscription.
- GitHub: whether the repo is public is open. Until it is decided, `art/projects/` stays out of git; a public repo would also show this file's project names and the work folder path in test12. Pages needs to be set once: Deploy from a branch, `main`, `/ (root)`.
- The stills behind three animations are not in the source: `art/sources/city-hall.png` for the city hall, and the handheld and ring tower stills in `art/projects/sources/`. Those scripts cannot run until Abdurrahman adds them.

## 8. Working across chats and Claude Code

- **In claude.ai:** Nullovation City chats run in the Nullovation City project, which holds this file and the instructions. Each chat needs the newest source archive attached, since project knowledge takes documents but not zip archives, and a chat cannot write back to project files. The chat unzips it into `/home/claude`, which makes `/home/claude/nc`, works there, and delivers the built HTML, a new archive, and this file when it changed, to replace the project's copy.
- **In Claude Code:** Claude Code works in the git repo on the PC, or in an `nc` folder unzipped anywhere. Started there, it reads `CLAUDE.md`, which imports `docs/nullovation-city-knowledge.md`, and loads the two city skills from `.claude/skills/`; `d-wizard` comes from the personal skills folder. It runs natively on Windows, best with Git for Windows installed, or in WSL. On Windows, `python` replaces `python3` in every command.
- **Between them:** `python tools/pack.py` writes `nullovation-city-source-v<version>.zip` one folder up, beside the source folder, to attach to a chat. `python tools/pack.py --apply <zip>` brings the folder up to an archive a chat delivered: it writes changed files, removes files the archive no longer has, keeps what runs make and `.git/`, refuses an older archive unless `--force` is added, and shows the changes first with `--dry-run`.
- **Which copy wins:** `docs/nullovation-city-knowledge.md` in the newest archive is the current knowledge file. If the project's copy is older, the archive's copy wins.
- **What the archive leaves out:** `tests/shots/`, `tests/data/`, `art/out/`, `art/canon/out/`, `__pycache__/`, `.git/`, and Claude Code's local settings. It carries `index.html`, and keeps `art/unslimmed/` and `art/projects/`, which git leaves out.
- **GitHub:** the repo is the home of the source. Abdurrahman pushes; Claude never does. GitHub Pages serves `index.html` from the branch, so a push publishes the page.
