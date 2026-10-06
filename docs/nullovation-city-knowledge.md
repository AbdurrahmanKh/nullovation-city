# Nullovation City: everything to know

State as of version 0.1.21 (October 2026). The tool file is about 1.6 MB.

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
- Empty plots become parks, in seven kinds: garden, park, plaza, pond, and since 0.1.21 playground, sculpture garden, and mini golf. A plot's kind comes from a hash of its position, never the same as the plot above or to its left, so adding a kind reshuffles every park once.
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

The city has 12 cars, 2 small buses, and 2 delivery drones on a 5 by 5 map, scaled with the map's area. 20 people roam the whole city, and 2 cyclists ride its sidewalks.

- **People (0.1.20):** 5 px wide and 6 tall, drawn in code from row strings in `src/js/45-traffic.js` (`BODY`, `personRows`).
  - They face the way they move: toward you the face shows under the hair, walking away the head is all hair, and walking left mirrors the sprite.
  - Looks: about half have long hair (framing the face, and filling the back from behind), and half of those wear a dress over bare legs.
  - At most one item each: a courier's coral pack (6%), a tote bag (12%), a cap whose brim points the way they walk (15%), or a phone (10%). The phone and the pack's screen glow cyan and keep that color by night, so the crowd twinkles after dark.
  - Runners (3%): arms and legs spread, twice as fast, never stopping, with no item or companion.
  - Companions: some walk with a kid, 5 px tall (6%), or a 4 by 3 dog (5%), a step to their right; they skip the benches.
  - Cyclists: 2 on a 5 by 5 map, scaled with the map's area, kept apart from the people count. They ride the sidewalk loops at three times walking speed, cross at zebras (cars wait for them too), and never stop.

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
- **Milestones and tasks:** tasks are grouped by milestone. They can be reordered by dragging, and each has an optional due date and a description. A task opens in a side panel, with Copy for Claude and Open in Claude.
- **Milestone view:** clicking a milestone's name opens its rename field and its tasks as a read-only list. Done tasks are ticked and struck through, and open ones show their due date and the first line of their description. It also has Copy for Claude and Delete milestone.
- **Notes:** notes show as cards, each with its own copy button. A note opens in a panel with Copy for Claude and Delete.
- **Links:** links show icons: doc, task, design, code, chat, folder, web. A Windows path pasted as a link is detected as a folder. With the setting on, folder links open in File Explorer.
- **The more menu:** Copy for builder, Builder card in a Claude chat, Load plan or tasks (JSON from the nullovation-city skill), Export this project, and Delete project.
- **The building:** clicking its picture opens the building panel, which picks one of the generic buildings or uploads the project's own art as a PNG or GIF. Under the picture, Mirror flips the building and Download saves it as a GIF.
- **The urgency system:** chosen per project.

### The side bar

- **Top:** the logo, with the version in very small text under it, and New project, which you plant on a free plot.
- **Lists:** search, This week (the weekly recap), Urgent, and Due this week.
- **Map size:** grow or shrink the grid.
- **Tools:**
  - Copy status brief, a summary of every project for a Claude chat, with Open in Claude beside it.
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

### Open in Claude

Beside every Copy for Claude sits Open in Claude: in the task, milestone and note panels, on What is next, beside Copy status in the project view, and beside Copy status brief in the side bar. Its menu opens the Claude desktop app through the app's `claude://` links, with the same text filled in and ready to send:
- **Chat:** a new chat.
- **Cowork:** a new task, with the project's local folders and files attached. A local link whose last part has an extension counts as a file.
- **Claude Code:** a new session in the project's first local folder. Without a folder link it stays greyed out, saying it needs one.

Nothing is sent by itself: Claude shows the text and waits. The text also goes on the clipboard, for a computer without the app. The app fills in about 14,000 characters, so a text over 13,500 opens Claude empty and stays on the clipboard to paste. The more menu also has Builder card in a Claude chat. Esc closes the menu before anything else.

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
| `67-claude.js` | Open in Claude: its menu, and the `claude://` links it builds |
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

There are 16 passes and 424 checks, all passing at 0.1.21. `python3 tests/run_tests.py` runs them all, and `python3 tests/run_tests.py 9 16` runs passes by number. Each browser pass runs Chrome through Playwright, prints PASS or FAIL lines and console errors, and can run alone, for example `python3 tests/test09_urgency.py`. The coverage:
- **test02_map:** zoom and the map.
- **test04_seed_data:** the data version, and the real start: a browser with nothing saved gets one project, Nullovation City.
- **test05_bubble_art and test08_bubble_tasks:** the status bubble.
- **test06_generics:** the generic buildings decoding, and the seven park kinds: all decoded at 256 by 128, the new ones animated in 40 frames, and no park repeating its neighbor.
- **test07_project_view:** activity and the project view.
- **test09_urgency:** urgency, the bubbles, the bubbles menu, and postcards.
- **test10_sidebar:** the side bar.
- **test11_load_plan:** loading plans and tasks.
- **test12_folder_links:** folder links.
- **test13_traffic:** traffic and crowds; the people's facing, looks and their shares, runners, kids and dogs, the cyclists, and the glow by night.
- **test14_data_file:** the data file.
- **test15_notes_milestones:** copy for notes and the milestone view.
- **test16_dropups:** the drop-ups, the Tasks view, and dusk.
- **test17_source:** the source travels: no chat paths in the scripts; the layout (only `build.py` at the root, nothing written into `src/`, git leaving out what runs make, no `dist/`, `.nojekyll` in place, nothing of the decision wizard in the tool or its tests); `index.html` matching a fresh build; what the archive holds and leaves out; a byte-identical build from a copy in another folder; and applying archives safely. It needs no browser.
- **test18_open_in_claude:** Open in Claude: the menu in every place, the links for Chat, Cowork and Claude Code with folders and files, Arabic text, a text over the limit, the builder card, the status brief, and closing with Esc or a click elsewhere.

Every browser pass but test14_data_file starts from the test city in `tests/testkit.py`, written into the browser before the page first loads: the starter project as it was at 0.1.16, plus a made-up second project, Garden planner, on the research lab. So the passes do not depend on what a new city starts with. It is written once per tab and never on a reload. test14_data_file needs no projects and goes without it: with an init script in its browser context, its two-tab checks failed about one run in three.

On Windows, Chrome hands clipboard text back with `\r\n` line ends, so test15 and test18 turn them back into `\n` before comparing; the copies themselves are unchanged. The headless test browser sometimes loses a page's stored writes on reload. test09_urgency and test16_dropups detect it, print a NOTE, set the value again, and retry. The real tool is not affected. In test13_traffic, the car the stop-line probe sets down can be held back by another car close ahead in its lane, as it should be; the probe then prints a NOTE and tries another car and line.

Every pass builds its paths from the source folder through `tests/testkit.py`, which also draws the files the passes upload on first use: a JPEG, a 700 px PNG, a still PNG, a 128 px block PNG, an 8-frame GIF with set margins, and a version 1 backup for test04. Before 0.1.16 those files existed only in one chat's sandbox, so a fresh chat could not run test2, test4, test5, test6 or test11.

## 4. Art

### Standards

- **Size and plot:** building art is 256 px wide; the map shows it at half size. The plot is drawn into the art: a flat 2:1 diamond with its front corner at the bottom edge, centered. On a building the plot, outline included, spans x 5 to 250 of the 256 px (the kit's `TW = 245 / 4`), the same in every shipped building; a park lot fills the full 256 by 128 with no slab. There are no empty margins above or below. (Checked 7 October 2026 against every shipped GIF; until then this file said the building plot spans the full width, which was wrong.)
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
4. Optimize: `python3 art/slim_gifs.py` (needs Node; uses gifsicle when it is on the PATH) tries gifsicle -O3 and a delta written in Python (each frame after the first keeps only its changed pixels, the rest see-through), and keeps the smallest result the tool's decoder reproduces exactly, only if it is smaller than the file already there. Name files to slim only those. Since 0.1.21 it works without gifsicle, which is not installed on Abdurrahman's PC.
5. Build, bump the version, and run the tests.

The original 128 px designs, the canon, live in `art/canon/generics.py` with `art/canon/kit.py`. `python3 art/canon/render.py` draws all eleven into `art/canon/out/` with a contact sheet, for the side-by-side comparisons. The park lots come from `art/lots/lots.py`, which still uses the first 256 px kit, `art/lots/lots_kit.py`. At 0.1.17 every code-drawn building and lot re-renders pixel-identical to the shipped art. The city hall animates Abdurrahman's PixelLab still: `art/buildings/city_hall.py` needs scipy and that still in `art/sources/city-hall.png`. Art that starts from a PixelLab still keeps the still in `art/sources/` and its script beside the code-drawn ones: `art/buildings/drone_port.py` (with the lot check in `art/kit/fixlot.py`), `art/lots/playground.py` (with the edge fill in `art/kit/filllot.py`), `art/lots/sculpture_garden.py` and `art/lots/mini_golf.py` (laid on the park lawn from `art/lots/lots.py`, since Pro drew them no ground), and `art/props/props.py` for the street props. Each re-renders byte-identical from its still.

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

The seven park lots are `lot-garden`, `lot-park`, `lot-plaza` and `lot-pond`, drawn in code by `art/lots/lots.py`, and since 0.1.21 `lot-playground`, `lot-sculpture-garden` (the floating stones) and `lot-mini-golf` (the lagoon course), made with PixelLab Pro and animated by `art/lots/playground.py`, `sculpture_garden.py` and `mini_golf.py`. The new three weigh 40 to 41 KB each after slimming, against 3 to 7 KB for the code-drawn ones.

### Art made for projects (delivered as files, not generics)

- **Generals and Diplomats:**
  - The Situation Tower: a stepped teal glass HQ with a helipad and drone, a situation room map in six player colors, an uplink dish, and flags.
  - The Projection Court: an amphitheater with a holographic Earth showing real continents from the `global-land-mask` package, each continent in a player's color, plus a spire, flags, and a gold-lined lot. Two passes; the second takes details from Abdurrahman's reference image, in slightly darker colors.
  - The theme is modern and a little futuristic, not old-world.
- **Handheld building:** Abdurrahman's PixelLab art, a giant game console, animated. The hut charges the console along its cable, the hero hops on the screen, the side lights fill. The still has 12,284 colors and a lot skewed 7 px off center.
- **Ring tower:** his art, animated. Three glyph rings turn at their own speeds behind a fixed plaque column, the lockers' keyholes blink, and a cloud beacon pulses.
- **Council hall (Council of Fun Masters, October 2026):** the first building made with the settled recipe (section 4): Pro at 256 by 256, the city hall as the style image, from Abdurrahman's prompt, 20 generations. A council hall shaped like a game controller lying flat, with a D-pad skylight, four button domes, thumbstick turrets, a drum of arched windows under a teal dome, six gaming-chair pods floating round a gold cartridge hologram, a mast with a coral beacon, an arcade cabinet, and a cream star plaza.
  - Its lot came out centered but steeper than 2:1 (0.61), so in the city its side corners floated above the ground.
    - A code-drawn flat lot under it did not work: the hall is drawn at the same steep angle, so its controller wings reached past the flatter lot's edges.
    - `council_hall.py` squashes the whole still to 2:1 instead, hall and plaza together, about 18% shorter, so it sits flat on its plot.
    - The cream plaza stays as drawn. At night the tool turns it brown; Abdurrahman kept it over a city-colored plaza, whose night is right but whose day is pale on pale.
  - Animated in code, a 10-second loop of 40 frames at 250 ms:
    - the cartridge turns once on its axis and bobs;
    - the pods brighten one at a time, each bobbing a pixel on its own rhythm;
    - two figures walk past the drum's windows inside, seen as shadows on the glass;
    - the buttons light up in no fixed order, as if pressed;
    - the beacon blinks and the arcade screen flickers.
  - The tool draws an animation as its first frame plus what each later frame changes: a later frame can add pixels but never clear them, so the turning cartridge first showed twice in the city.
    - The GIF therefore opens with a 20 ms frame of only what is solid in every frame, and every later frame only adds to it.
    - The same trick serves any building whose pieces move over open sky.
  - 256 by 185, 180 colors, 422 KB, decoding exactly in the tool.
- **Half Cards' salad diner (October 2026):** made with the settled recipe from Abdurrahman's prompt (Pro at 256, the city hall as the style image, 20 generations): a white diner with a mint roof, a coral rim, SALAD, FRESH and DINER card signs, a golden counter of salad bowls, a teal glass drum of greens, a tomato greenhouse, an order kiosk, two parasol tables and planters on lavender tiles. Its lot came out the city's plot exactly.
  - Abdurrahman wanted the diner small, like the kiosk, keeping the design; the props could stay their size.
    - A first Pro redraw at 96 px (20 generations) came back barely smaller and cropped.
    - What worked: Pro at 84 by 84, which returns 16 candidates (billed 25), with a box-shrunk copy of the diner as the first reference (size and framing), the full diner as the second (design), and a crop of the original as the style image, detail off. Candidate 9 was the only one with its wall whole under the window.
    - PixelLab copies a reference's flaws exactly: the references had a parasol cleared by a box (most candidates lost the wall there) and a greenhouse sliver cleared by column (candidate 9's roof corner and drum stopped in a straight cut). Clear neighbors by their own pixels, never by a box or a column. `half_cards.py` mends the cut: the drum's outline flush with its band, the roof corner closed in the right side's shaded corals.
  - `half_cards.py` takes the big diner off the lot, refills the tiles from the lot's own 14 px lattice and its back outline from its own run, carries the path to the new door, and sets the small diner at the back (about 70 px wide) with a new drum shadow. 256 by 138.
  - Animated in code, 40 frames at 200 ms: the window glow breathes, the door's glass lights once, the drum's grow light swells once, the signs glow warm white (SALAD dims, DINER stutters), the kiosk screen glows cyan with a scanline and its top light blinks, and a glint crosses the greenhouse. 195 colors, 43 KB: each frame keeps only its changed pixels, the rest transparent. It decodes exactly in the tool and uploads as 40 frames.
  - A server walking behind the counter was tried: the counter and bowls hide all but scraps of the figure.
  - At night the cream path turns dark red (the tool maps every cream through a peach); a street grey path (#908BA5) was shown as the other choice. Abdurrahman kept the cream for now (7 October 2026) and will fix it later.
- **Where their scripts are:** `art/projects/`, which git leaves out: `situation_tower.py`, `projection_court.py` and `projection_court2.py` for Generals and Diplomats, `animate_handheld.py`, `animate_vault.py` for the ring tower, `council_hall.py`, and `half_cards.py`. The last four read their stills from `art/projects/sources/` (`HandHeld-Building.png`, `ring-tower.png`, `council-hall.png`, and `half-cards-pixellab.png` with `half-cards-small-diner.png`). All of them render into `art/out/`.

### Image services

- No image model runs inside Claude itself. Images are drawn in code, made by Abdurrahman in a service such as PixelLab from the builder skill's prompts, or, since October 2026, sent to PixelLab by Claude Code.
- **The account:** Tier 1 (Pixel Apprentice), 2,000 generations a month, refilled on the 5th. A daily bonus of 5, up to 20, is spent only once the monthly pool is empty. The MCP, the API and the web app all draw from the same pool, and animation tools (PixMiniMax, skeleton v3) need Tier 1 or higher.
- **Claude Code and PixelLab:** the PixelLab MCP is connected in Claude Code. It takes images only as URLs or inline base64, so it cannot read a local file; `art/pixellab.py` sends local images to the v2 API (`https://api.pixellab.ai/v2`) instead. Its token comes from the `PIXELLAB_SECRET` environment variable and is never written to a file, and downloads go to `art/out/pixellab/`, which git and the archive leave out.
  - `python art/pixellab.py balance` prints the generations left.
  - `pro "prompt" --style REFERENCE.png --size 256x256 --name NAME` is the recipe for building stills (256x256) and park lots (256x128). It sends Pro (`/generate-image-v2`) the prompt with a local image of the city's own art as its style reference, then downloads the result.
  - `job ID --name NAME` waits for any job and downloads its images.
  - Everything the settled recipes do not use was taken out at 0.1.19: PixMiniMax's `animate`, the `gif` fitting, and a generic `call`.
- **PixMiniMax** (animate with text): animates any image from a motion description. Frames up to 256 by 256, 4 to 40 frames in multiples of 4. It returns the frame count plus one: index 0 is the input unchanged. Priced by generation time: 6 generations for a 40-frame clip; at 64 by 64, 4, 8, 16 and 40 frames cost 1, 1, 2 and 6. Sizes just above 64 or 128 px cost less than just below. Enhance prompt adds 0.05. The docs say 1 to 6 minutes. Subject, pose, view and facing left out are read off the image by a model, which can decline; the job then fails asking for them.
  - The first real run (October 2026): the city hall at 256 by 192, 40 frames, billed 5 generations and took 10 minutes. It redraws the whole building every frame, not only what moves: 5,000 to 13,800 pixels differ from the still in each frame, outlines shimmer, the palette jumps lighter halfway, and a magenta burst appears at the drone pad. The fitted GIF has 173 colors and weighs 385 KB, against 15 KB for the shipped one. It was not installed.
- **Pro Flash:** one image per call, prompts up to 2,000 characters (the Pro tool is recommended for longer ones), with an optional style image.
  - Create: native sizes 16 (experimental), 24, 32, 32 by 48, 48, 64, 96 by 64, 96 and 128; custom sizes from 16 to 256 px in steps of 4 (beta). Provisional cost: 6 generations at 128 by 128, 9 at 256 by 192 or 256 by 256.
  - Edit and inpaint: from 32 to 256 px, at the source's size; the canvas never grows. Inpaint keeps every unmasked pixel exactly. Edit is quoted at 9 generations at 256 by 192.
  - Object and character: up to 256 px, with 1 or 8 directions. Saving an existing image as a one-direction object is free; eight views charge only the rotations.
  - Quotes come free from the MCP's `get_pro_flash_capabilities` with an operation and size; the bill on completion is what counts.
- Bitforge is limited to 200 by 200.

### PixelLab workflow

A testing phase (from October 2026): nothing is made in bulk until each kind of art has a recipe Abdurrahman approved. One small test at a time, each announced with what it tests, the tool, the settings and the quoted cost, with the balance checked before and after. The cheapest settings that answer the question; testing stops at 300 generations unless he raises it. Nothing is installed or added to the app; results are shown beside what they are compared with, and map art also in a city screenshot at 1x and 2x. Each recipe below is marked testing until he approves it, then settled. The tests, in order: building motion, leader portrait, street props, citizen, building still, park lot. When all six are settled, the month's list starts.

The testing phase ended on 6 October 2026: five recipes settled and citizens cancelled, for 135 generations spent on tests.
- Everything the tests made sits in `_extras/pixellab-tests/`, one folder up from the source and outside git, with a note in `_extras/README.txt`.
- The scripts that made the city screenshots, and the two lot fixes, are in its `helpers/` folder.

**1. Building motion (settled, October 2026): the code animation.**
- **The recipe:** a script in `art/buildings/` changes existing pixels of the still: windows, twinkles, rotors, a glint. It costs no generations. The city hall changes about 400 pixels per frame (at most 607) and weighs 15 KB after `art/slim_gifs.py`. The still can come from PixelLab; the motion is drawn in code.
- **Tried and not picked: PixMiniMax with cleanup** (5 generations, test 1):
  - Tool and settings: PixMiniMax (`/animate-pixminimax`, run by a command `art/pixellab.py` dropped at 0.1.19), 40 frames, with all four caption fields (subject, pose, `--view "high top-down"`, `--direction south`) and a seed. Prompt shape: "Calm ambient loop. The building, walls, dome and plot stay perfectly still, with no camera movement and no shaking. Only small lights change:", then each light and what it does.
  - Raw, it was not usable: it redrew the whole building every frame (about 13,500 pixels), the palette jumped lighter halfway, outlines shimmered, and a magenta burst appeared at the drone pad.
  - A local cleanup (keep the still's silhouette, snap pixels within 72 of the still back to it, map the rest to the still's colors) brought it to about 850 changed pixels per frame, but still left stray marks to fix by hand.
  - It cost 5 generations and about 10 minutes for 256 by 192 at 40 frames. The API's `drift_threshold` color de-flicker was not tried.
  - Files: `test1-compare.gif`, `test1-sheet.png`, and the city shots `test1-city-*` in `_extras/pixellab-tests/`.

**2. Leader portrait (settled, October 2026): Pro Flash at 128 px.**
- **The recipe:**
  - Design the leader with the builder skill.
  - Tool: `create_image_pro_flash` at 128 by 128, transparent background. 128 px only; the tool can show it at half size.
  - Prompt shape: subject only. "Head and shoulders portrait of ... facing the viewer:", then hair, clothing, the one or two props that tie the leader to the building, expression, and "soft light from the top left". Pro Flash has no facing setting, so when the pose matters, say it firmly: "looking straight at the viewer, front view".
  - Cleanup: none needed. The alpha comes back hard.
  - Cost per finished piece: 6 generations and about 30 seconds per try. Each call gives one image, so a miss costs another 6.
- **Why not the others:** Pixen (1 generation) had the city's crisp look but no shoulders. Pro (20 per call, 4 candidates at 128 px, so about 5 each) followed the brief most closely, but costs more per finished piece.
- **Why models differ on one prompt:** only Pixen has a facing setting; Pro Flash and Pro read the pose from the words alone, and a seed does not carry across models.
- **First use of the recipe, Ines redesigned** (6 generations, 20 seconds): Abdurrahman kept the concept but asked for a dark-haired, mysterious woman with a poker face.
  - Prompt: "Head and shoulders portrait of a mysterious woman, a cipher keeper, looking straight at the viewer, front view:", then a sleek dark chin-length bob with a faint violet sheen, a high pale lavender stand-up collar edged with gold glyphs, the keyhole loupe over her left eye, the cloud pin, "an unreadable poker face with calm half-lidded eyes and a closed neutral mouth", and light from the top left.
  - Result: front view as asked, the expression unreadable, and every concept piece kept. 33 colors, hard alpha, the figure about 83 by 95 px on the canvas.
  - File: `test2-ines-redesign.png` (before and after, at 1x and 3x on light and dark), and the `test2-proflash-128-ines2` folder.

**The test, in full:** SwiftCoder's leader, Ines Tumbler, Cipherwright and keeper of the rings, designed with the builder skill to belong to the Ring tower: mint-silver hair swept up like its dome, a lavender collar ringed with gold glyphs, a brass loupe with a keyhole lens, a sky-blue cloud pin for the Gist sync. Signature color lavender, with gold.
- **Pixen, first run** (2 generations):
  - Tool: `create_image_pixen` through the MCP.
  - Settings: 64 by 64 and 128 by 128, transparent background, facing south, single-color black outline, one seed for both.
  - Prompt shape: subject only. "Head and shoulders portrait of a calm cipher keeper facing the viewer:", then hair, collar, loupe, pin and expression, and "soft light from the top left".
  - Cleanup: none needed. The alpha is already hard, with a dark outline; 31 colors at 64 px, 67 at 128 px.
  - Cost per finished piece: 1 generation per size, about 30 seconds each.
  - The 128 px reads well: the keyhole loupe, the glyph collar and the cloud pin all show.
  - Two faults:
    - The collar came out as a deep plum ring the head sits inside, with no shoulders.
    - The 64 px is a different person (long hair, a handled magnifier), so one seed does not hold a leader across sizes.
- **Pro Flash, same prompt and seed** (11 generations):
  - Tool: `create_image_pro_flash` through the MCP, at 64 by 64 and 128 by 128 with a transparent background. It has no outline or facing settings, and a style image is optional; none was used.
  - Cost: 5 generations at 64 px and 6 at 128 px, about 30 seconds each, billed as quoted.
  - The result is a real head and shoulders: a plum coat with a stand-up glyph collar, a brass keyhole loupe, and the cloud pin. 40 colors at 64 px, 75 at 128 px; the alpha is hard.
  - Against Pixen: better composition and more character, but darker and muddier colors, a softer outline that is missing in places, and spiky silver hair instead of the swept mint crest.
  - The 64 px is again a different person: grey hair, a violet eye, a blue coat.
- **Both tools:** one prompt and one seed do not keep a leader the same across sizes. The recipe must make one size from the other, or use a reference image.
- **128 px only:** Abdurrahman dropped the 64 px size after the first two runs. A 128 px portrait can show at 64 the way the map shows 256 px buildings at half size.
- **Pro, same prompt and seed, 128 px** (20 generations):
  - Tool: `create_image_pro` through the MCP, the API's `/generate-image-v2`. One call returns 16 candidates at 43 to 85 px and 4 at 86 to 170 px. It takes up to 4 labelled reference images and a style image; none was used.
  - Cost: quoted 20 to 40 per call, with no quote tool; billed 20 for 4 candidates, about 2 minutes.
  - It followed the brief most closely: a pale lavender stand-up collar with gold glyphs, the swept mint-silver crest, the keyhole loupe, and the cloud pin. All four candidates are the same person, so a pick is about pose and framing.
  - About 30 colors each, close to the city's own count per building; the alpha is hard.
  - Three of the four sit small in the frame (about 65 to 75 px wide); candidate 4 fills it (93 by 126). The look is older and sterner than the other tools'.
- Files: `test2-compare-128.png` (Pixen, Pro Flash and Pro's 4 candidates at 1x and 3x, on light and dark), `test2-compare.png`, `test2-portraits.png`, and the `test2-pixen-*`, `test2-proflash-*` and `test2-pro-128` folders, in `_extras/pixellab-tests/`.

**3. Street props (settled, October 2026): a Pixflux front and a Pro Flash back, mirrored for the other two sides.**
- **The recipe:**
  - Front: `create_image_pixflux` with isometric on, high top-down view, transparent background, single-color black outline, and the city's 32 colors forced as the palette. 1 generation.
  - Back: `create_object_pro_flash` with the front as its first frame, 8 directions, high top-down view. 1 generation.
  - Prompt shape: "A small <prop>:", then its parts and colors, then "Pastel sci-fi street furniture, isometric view, light from the top left."
  - Cleanup: pick the true back by eye (the same diagonal, turned around), then `python art/props/props.py`: it snaps both views to the 32 city colors (read from `CITY_PALETTE` in `src/js/30-pixel.js`, nearest by the redmean distance), clears each still's known flaws and any stray speck, adds a 1 px dark outline where Pixflux left none, and sets the back on the front's canvas, standing on the same spot.
  - Sizes: art at double detail, shown at half size, like buildings. Bus stop and billboard 64 by 64, vending machine 32 by 48, bin 32 by 32. Abdurrahman approved the size.
  - Facing: a prop faces the street it stands on. The front faces the south-west street, and mirrored the south-east; the back serves the north-east side, and mirrored the north-west.
  - Cost per finished prop: 2 generations, for all four sides.
- **The finished set (approved 7 October 2026, in the missing art round, with the lavender billboard):**
  - The stills are in `art/sources/props/`, a front and a back per prop. `art/props/props.py` writes `art/out/props/<prop>-front.png` and `-back.png`, and `props-sheet.png` with the stills beside the finished four sides on dark and light.
  - The bus stop, vending machine and bin are the test 3 props, finished for free: the vending machine's teal patch and the bench ghost behind the bus stop are gone. The script clears flaws by box and color in each still's own pixels (`FLAWS`), and drops pieces under 8 px, or under a twentieth of the prop.
  - The test billboard had no dark outline at all, and its back was a plain white slab. A second billboard was made with the same recipe (2 generations): seed 2106, the prompt "a slim lavender post on a round pale base, holding a rounded lavender frame around a glowing translucent cyan hologram panel ...". It came out with a lavender frame, a pink top and the cyan screen, still without an outline; its back is the rotation's `north` view. It is outlined in code. Abdurrahman picked it over the test billboard, which is left in `_extras/pixellab-tests/test3/`.
  - City shots, with the props round a park block at 1x and 2x: `props-city-1x.png` and `-2x.png`.
- **Placement on the map:** decided in the street props round; see section 6, Street props. Not built.

**The test, in full:** a bus stop, a vending machine, a holo billboard (icons, no words) and a bin, as one styled set.
- **Scale:** props are drawn like buildings, at double detail and shown at half size. Art sizes: bus stop and billboard 64 by 64, vending machine 32 by 48, bin 32 by 32. People on the map are 5 by 7 px sprites.
- **Prompt shape:** "A small <prop>:", then its parts and colors, then "Pastel sci-fi street furniture, isometric view, light from the top left." The shared phrase ties the set together.
- **Pixflux** (4 generations, 1 each, about 15 to 30 seconds):
  - Settings: `create_image_pixflux` with isometric on, high top-down view, transparent background, single-color black outline, one seed, and the city's 32 colors forced as the palette (`_extras/pixellab-tests/test3/city-palette.png`, read from `CITY_PALETTE`).
  - Every color is a city color (13 to 25 per prop), so the props get the tool's hand-picked night colors, and the angles are true 2:1 isometric.
  - The detail is rough: the bus stop's sign is a red and teal smudge, the billboard's icons blur and it reads as a plain screen rather than a hologram, and the vending machine has a stray teal patch at its foot.
- **Pro Flash** (20 generations, 5 each, 20 seconds to 2 minutes):
  - Settings: `create_image_pro_flash`, transparent background, one seed. The bus stop came first; the billboard used it as its style image (by `source_image_id`), and the vending machine and bin a 32 by 32 crop of it, since a style image must fit inside the target canvas.
  - The result is crisp and charming and reads as one set: the same outline, shading and finish. The billboard is a real hologram showing a star, a heart and an arrow.
  - No color is a city color (29 to 50 per prop), and the angles are front or three-quarter views rather than true 2:1 isometric, which shows beside the buildings.
- **Pro Flash snapped to the city's colors** (free, local): each color mapped to the nearest of the 32. It keeps the Pro Flash look with 12 to 22 colors per prop, and gains the night colors.
- **At real size:** all three sets read at 2x. At 1x the props are small smudges of color, the bus stop and billboard still recognizable. The props come out larger than real life beside 7 px people (the bin stands about two people tall), so smaller canvases may be needed.
- **Abdurrahman's read:** Pixflux leads, since its props look more isometric, and the size is right.
- **The facing rule (decided):** a prop faces the street it stands on. On a block's south and east sides we see its face; on its north and west sides, its back. So each prop needs a front and a back view.
- **Back views, Pro Flash object rotations** (4 generations, 1 per prop, 2 to 2.5 minutes):
  - Tool: `create_object_pro_flash` with the Pixflux image as `first_frame_base64`, `n_directions` 8, view "high top-down", and the prop's prompt. Starting from an existing image charges only the rotations, 1 generation per prop. The 8 views download as a zip from `/mcp/objects/<object id>/download`.
  - The tool takes the given image as its "south" view and draws the other 7. The true back is the original turned around on the same diagonal: the "north" view for the bus stop and billboard, but "north-east" for the vending machine, whose "north" came out flat-on. So the back is picked by eye per prop. The bin is round, so any view serves.
  - The views add colors outside the city's (up to 36 per view), so they are snapped to the 32 city colors after, free and local. The vending machine's stray teal patch carries into every view.
  - **Four sides from two images:** the front faces the south-west street. Mirrored, it faces the south-east street. The back serves the north-east side, and mirrored, the north-west side.
  - Mocked round a park block at 1x and 2x, with two props per side: faces on the south sides, backs on the north sides. Every prop reads as facing its own street. Front-side props overlap the lot behind them, the way isometric depth works.
- Files (test 3): `test3-rotations.png` (each prop's 8 views), `test3-backs.png` (the back candidates), `test3-block-1x.png`, `test3-block-2x.png` and `test3-block-2x-close.png` (props round a park block), `test3-props.png` (both sets at 1x and 4x, on light and dark), `test3-city-1x.png`, `test3-city-2x.png` and `test3-city-2x-close.png` (Pixflux, Pro Flash and snapped on the sidewalk by the city hall, pasted onto screenshots), and the prop folders in `_extras/pixellab-tests/test3/`.

**4. Citizen (cancelled, October 2026): citizens stay code-drawn.**
- Abdurrahman loved the courier, but at 16 px on the map they looked like giants walking round the city. The old 5 by 7 px people are the right size, and their abstraction is part of their charm.
- So PixelLab is not used for citizens. Any improvement to the people is drawn in code, at their size.
- **What the test found, for any later sprite work:**
  - 2 directions plus mirrors are enough on this map.
  - `size` is the canvas, not the figure.
  - A citizen with walk, talk and sit costs 7 generations.

**The test, in full:** the courier, a delivery courier in a mint jacket and a pale lavender cap, with a boxy coral parcel pack showing a small glowing cyan screen, and light sneakers.
- **How many directions:** people on the map only move along the two diagonals. Sidewalks, zebra crossings and the walk into a building all run along the plot edges. So only the four diagonal views are ever seen, never straight up, down, left or right. Today's code-drawn people do not face any way at all.
- **The courier** (1 generation, about 1 minute):
  - Tool: `create_character` in standard mode, 8 directions, `size` 48, view "high top-down", single-color black outline, basic shading, medium detail.
  - Standard mode costs 1 generation for 4 or 8 directions alike.
  - `size` sets the canvas, not the figure: it came back on a 68 px canvas with the figure about 46 px tall, about 23 px on the map. Abdurrahman chose about 16 px, so the next try asks for about 32.
  - 25 to 27 colors per view; the alpha is hard.
- **The walk on the 4 diagonals** (4 generations, 1 per direction, 1.5 to 2 minutes each):
  - Tool: `animate_character` with the template `walking-8-frames`, 8 frames.
  - The north-west job failed once ("heavy load") and was not charged. It was retried into the same group with `animation_group_id`.
- **4 real directions against 2 plus mirrors:** the courier is close to symmetric, so a mirrored south-east walk is hard to tell from the real south-west one, and the same holds for north-east and north-west. Walking round a park block at 1x and 2x, the two versions look the same.
  - With mirroring, a walk costs 2 generations instead of 4 (or 8 for every direction).
  - A lopsided design, such as a bag on one shoulder, would swap sides when mirrored.
- **Approved:** 2 directions plus mirrors, at about 16 px tall on the map.
- **The courier at 16 px, with walk, talk and sit** (7 generations):
  - The courier: `create_character` as before, but `size` 32. It came back on a 48 px canvas with the figure 31 to 33 px tall, so 16 px on the map, as chosen. 1 generation, under a minute.
  - Same concept, but without the dark outline (that setting is only a hint) and in softer colors than the first courier.
  - Walk: the `walking-8-frames` template on south-east and north-east, 8 frames. 1 generation each.
  - Talk: `animate_character` in mode "v3" with "standing in place, talking calmly and gesturing with one hand", 8 frames plus the reference frame. 1 generation each, 1 to 3 minutes. One arm sweeps out and back; it reads as talking.
  - Sit: mode "v3" with "sitting down on a low bench and staying seated, hands resting on knees", 8 frames plus the reference. 1 generation each. It is a sit-down move that ends seated, not a loop, so on the map its last frame is held while someone sits.
  - The animations carry 26 to 37 colors.
  - In the city at 1x and 2x on the plaza: a pair talking face to face on a sidewalk (south-east and mirrored north-west), couriers walking two sidewalks, and one sitting on the plaza's bench seat (mirrored to face south-west). Everything reads at 2x; at 1x the figures are small but readable.
- **The recipe it would have been:**
  - The character: standard mode, `size` 32 for a 16 px figure, 1 generation.
  - The walk: the template, 1 per direction.
  - Talk and sit: v3, 1 per direction.
  - 2 directions drawn, 2 mirrored, 7 generations in all.
  - The 16 px courier also lacked the dark outline.
- Files: `test4-courier-views.png` (the first courier's 8 views), `test4-walk-compare.gif` (each real diagonal beside the mirrored other), `test4-city-1x.gif` and `test4-city-2x.gif` (4 real directions against 2 plus mirrors), `test4-courier32-views.png` (the first and the 16 px courier), `test4-courier32-actions.gif` (walk, talk and sit, real and mirrored), `test4-courier32-frames.png` (every talk and sit frame), `test4-life-1x.gif`, `test4-life-2x.gif` and `test4-life-2x-close.png` (life on the plaza), and the courier files in `_extras/pixellab-tests/test4/`.

**5. Building still (settled, October 2026): Pro at 256 px with a reference building, then a lot fix in code.**
- **The recipe:**
  - Tool: Pro at 256 by 256 with a transparent background: `python art/pixellab.py pro "prompt" --style src/buildings/city-hall.png --name NAME`.
  - Reference: one of the city's good buildings as `style_image` (image, size, and a usage line asking to match its palette, outline, shading and detail). The city hall is the standard, and the reference must fit inside the canvas.
  - Prompt shape: the builder skill's full prompt: the hero structure, the supporting pieces and the lot in plain colors, then "Isometric pixel art, 2:1 isometric view, standing on a square isometric plot, light from the top left, 1 px dark outline."
  - Cleanup, the lot check: `art/kit/fixlot.py` measures the lot against the city hall's plot (x 5 to 250). An exact match is kept as drawn; the drone port and Half Cards came out exact. A 2:1 lot of another size or a little off center is redrawn on the city's plot in its own colors, with the original's surface and building laid on it, the ground carried out along the tile joints to the new rim, and the original's rim, slab and outline left out. A lot that is not 2:1 (a turned camera, such as the council hall's at slope 0.59) is refused. Free.
  - Motion: drawn in code on the still, a script per building in `art/buildings/`.
  - Cost per finished building: 20 generations (quoted 20 to 40) and about a minute. Abdurrahman makes few buildings, so 20 each is fine.
- **Why not the others:**
  - Pixflux (1 generation) is clean and cheap but draws at a different scale: big windows and a person-sized door make it read as a small two-room building beside the city hall's tower, and it cannot take a reference.
  - Pro Flash (9) gives Abdurrahman odd results, and here drew the lot with a steeper, turned camera.
- **The first lot fix was a mistake:** it stretched the drone port's plot to the full 256 px, about 5 px wider on each side than every other building, and its two leftovers (a faint double line on the back-left edge, and a strip without tile joints along the new rim) came from that stretch. The Pro lot already matched the city's plot. The old helper, `_extras/pixellab-tests/helpers/fixlot.py`, is replaced by `art/kit/fixlot.py`.
- **The finished drone port (approved 7 October 2026; held out of the app):** `art/buildings/drone_port.py` reads `art/sources/drone-port.png` (the test 5 Pro still), checks its lot, and writes `art/out/drone-port.gif` and `.png`: 256 by 189, 40 frames at 250 ms, 98 colors, 80 KB, up to 835 pixels changed per frame, decoding exactly in the tool. Not slimmed: `art/slim_gifs.py` works only on `src/buildings/`, and the drone port is held out of the app.
  - Motion: a slow uneven chase round the pad's 8 lights, which glow at night; 3 side lights breathe; the drone's 4 rotors spin; its nav lights take turns; the tower's pink beacon blinks 3 times a loop; the hangar door's glow and its light on the paving breathe; 3 locker lights come on now and then. Two wall shades were nudged so the walls do not glow at night.
  - By night the butter-cream walls turn a strong brick brown, the way the tool darkens warm colors.
  - Shown in `art/out/drone-port-sheet.png` (the still, its lot against the city hall's plot, frames by day and by night), `drone-port-preview.gif`, and the city shots `drone-port-city-1x` and `-2x`.
- **The test, in full:**

The drone port, picked from the held buildings (bus depot, drone port, apartment block, cafe, library), none of which had a design on file.
- **The design:** a rounded two-storey hub of pale panels with mint trims, the lead color. A round rooftop landing pad ringed with glowing mint lights holds a small white drone. Around it: a control-tower pod with teal glass and a pink beacon, a glowing hangar door, a lavender parcel-locker wall and coral parcels. The lot is pale paving with two gold-ringed landing pads and a lawn strip with shrubs.
- **The prompt shape:** the builder skill's full prompt: the hero structure, the supporting pieces and the lot in plain colors, then "Isometric pixel art, 2:1 isometric view, standing on a square isometric plot, light from the top left, 1 px dark outline."
- **Pixflux** (1 generation, about 30 seconds):
  - Settings: 256 by 256, isometric on, the city colors forced, single-color black outline.
  - It ignored the transparent-background setting at this size and came back on solid lavender, which was keyed out afterwards (a free flood fill from the corners).
  - Plainer and boxier, all 30 colors city colors, and its lot is a small square, not the full-width plot.
- **Pro Flash with the city hall as style image** (9 generations, about 30 seconds):
  - Sent with a one-off script (in the extras' `helpers/`) as the API's nested `style_image` (image, size and usage). The MCP's style image takes only a URL, inline base64 or an owned image ID.
  - It reads as part of the city. Every design piece is there, with 54 colors (none of them city colors) and hard alpha.
- **The lot is skewed:** the Pro Flash lot's front corner sits 9 px right of center, its left corner is 13 px higher than its right, its two front edges differ in length (134 and 116 px), and they slope at about 1.6 to 1, not 2 to 1. The image uses a slightly different camera, so warping it cannot fix the lot without smearing the pixels. At 2x in the city the lot reads as slightly turned on its plot.
- **Abdurrahman's read:**
  - He first took Pro Flash for buildings, but on seeing it alone he preferred the Pixflux building's proper look, though he liked the Pro Flash design idea more.
  - Pro Flash often gives him odd results, and he usually makes buildings with Pro (20 to 40 generations), so Pro is tested next.
  - Using a good building as the reference stays: the city hall is the standard. A reference must fit inside the canvas, so at 256 by 256 the data tower (314 px tall) and the comms spire (329) cannot serve.
- **Pro, same prompt, seed and city hall reference** (20 generations, about 1 minute):
  - Tool: the API's `/generate-image-v2`, with the same nested `style_image` as Pro Flash; `art/pixellab.py pro` now sends exactly this request. At 256 px it returns one image; it billed 20 of the quoted 20 to 40.
  - The result is a butter-cream hub with mint trims, the rooftop pad and drone, the control tower with its pink beacon, a glowing hangar door, the lavender lockers, coral parcels, two gold chevron pads on lavender tiles, and shrubs. 57 colors, hard alpha.
  - Its lot is the plot's shape: the front corner at the center, both front edges sloping 0.51, and 245 px wide. The test read that as 5 px short on each side; in fact it is exactly the city hall's plot (see the first lot fix, above).
  - In the city at 2x it sits flat on its plot like the city hall.
  - For comparison, Pixflux's lot slopes 0.54 and is a little lopsided, and Pro Flash's slopes about 0.63 and is turned.
- **Why Pixflux looked plainer:** it is PixelLab's fast 1-generation model, and at 256 px it simplifies. The round hub became a box and the lockers were dropped, it had no reference image, and the forced 32 colors leave little room for glow and shading. Its isometric setting and the city colors give it the clean, proper look.
- **The plot to match:** a 2:1 diamond spanning x 5 to 250 with its outline, a 5 px slab under the two front edges, and the front corner at the bottom center (`art/kit/kit.py`, `art/kit/lot.py`).
- **Next:** a lot fix. Two ways:
  - Free: lift the building off and set it on a lot drawn in code.
  - 9 generations: Pro Flash inpaint over an exact code-drawn lot, so the lot is right from the start.
- Files: `test5-pro-lotfix.png` (Pro before and after the lot fix), `test5-city-pro-fixed-1x/2x` (the fixed drone port in the city), `test5-compare-pro.png` (Pixflux, Pro Flash and Pro), `test5-city-2x-all.png` (the city hall and the three drone ports on one plot at 2x), `test5-city-pro-1x/2x`, `test5-proflash-alone.png` (Pro Flash with the plot outlined), `test5-compare.png` (the city hall, Pixflux and Pro Flash), `test5-city-proflash-1x/2x` and `test5-city-pixflux-1x/2x` (each drone port on the city hall's plot), `test5-city-2x-close.png` (the three plots side by side), and `_extras/pixellab-tests/test5/`.

**6. Park lot (settled, October 2026): Pro at 256 by 128 with a park lot as reference, then an edge fill.**
- **The recipe:**
  - Tool: Pro at 256 by 128 with a transparent background: `python art/pixellab.py pro "prompt" --style <a park lot PNG> --size 256x128 --name NAME`.
  - Reference: the first frame of one of today's park lots (`src/buildings/lot-*.gif`) as `style_image`, asking to match its palette, outline, shading, scale and detail.
  - Prompt shape: the lot's ground, then its pieces in plain colors, then "Everything small and low, seen from above. Isometric pixel art, 2:1 isometric view, flat ground tile, light from the top left, 1 px dark outline."
  - Cleanup: `art/kit/filllot.py`. `fill_lot` fills every empty pixel inside the diamond today's lots cover (columns 0 to 255) from its nearest neighbor; `trim_lot` clears the 1 to 2 px ragged strips outside it, keeping tree tops, as today's lots have them. Free.
  - Motion: drawn in code on the still, 40 frames at 200 ms like the other lots.
  - Cost per finished lot: 20 generations.
- **The finished playground (approved 7 October 2026, in the tool since 0.1.21):** `art/lots/playground.py` reads `art/sources/lot-playground.png` (the test 6 Pro still), fills and trims it, and writes `art/out/lot-playground.gif` and `.png`: 256 by 128, 35 colors, 68 KB, 7 to 45 pixels changed per frame, decoding exactly in the tool.
  - Motion: the carousel's six cyan orbs light one after another so it seems to turn (shifting its pixels was not clean at about 22 px wide); the front swing seat sways a pixel at uneven times; a glint runs down each slide once a loop; a butterfly drifts on a closed path.
  - The orbs now use the city's glow cyan, so they shine at night. The sand and swing-frame cream was made a touch paler, since the tool lit it like a lamp at night.
  - Shown in `art/out/lot-playground-compare.png` and the city shots `lot-playground-city-1x`, `-2x` and `-2x-night`.
  - Installing a park kind reshuffles every park: a plot's kind is a hash of its position modulo the number of kinds (`lotVariant` in `src/js/40-map.js`).
- **The sculpture garden and mini golf concepts (7 October 2026, made as stills for Abdurrahman to pick):** three concepts each from the missing art round, all six made at once with the recipe (120 generations, 20 each, seed 2106), each with the closest of today's lots as its style image: lot-garden for the garden of forms, lot-plaza for the reflecting court, lot-pond for the lagoon course, lot-park for the floating stones, windmill course and planet course.
  - Pro drew no ground under three of them: the floating stones covered 26% of the diamond, the windmill and lagoon courses 57%, with their pieces on transparency. Filling from neighbors would smear the pieces, so they were laid on today's park lawn drawn in code (`ground` in `art/lots/lots.py`), leaving out the dark rim Pro drew round the windmill course's edge. So the recipe's cleanup becomes: when the lot covers less than 90% of the diamond, lay it on the code lawn; otherwise fill the edge.
  - The garden of forms, reflecting court and planet course came out with their own ground (96.6 to 100%). The planet course's ground is dark lavender with stars, the darkest plot in the city.
  - Files in `art/out/parks/`: one PNG per concept, `parks-sheet.png` (today's four lots and the six concepts), and `parks-city-1x.png` and `-2x.png`, a page copy whose park kinds are today's four plus the six. The script that made them was a one-off in the session scratchpad.
  - Abdurrahman picked the floating stones and the lagoon course, installed at 0.1.21 with the playground:
    - `art/lots/sculpture_garden.py` (still `art/sources/lot-sculpture-garden.png`): Pro drew six stones, not five. Each lifts 1 px off its plinth at its own slow pace and drops back, each plinth's glow breathes through four cyan levels on its own curve, and a pink butterfly drifts. The glows use the city's glow cyan, so they stay lit at night, and the gold stone glows too. 38 colors, 39 to 548 pixels changed per frame.
    - `art/lots/mini_golf.py` (still `art/sources/lot-mini-golf.png`): the lighthouse lantern glows warm three times a loop, glints drift on both halves of the pond, and each of the four flags ripples now and then. The flags' pale gold was nudged so the tool's night does not light it. 39 colors, 10 to 48 pixels changed per frame. The tiny windmill stays still: too small to turn cleanly.
    - Both lay Pro's pieces whole on the code lawn; neither needed the dark rim rule or the trim (which would clip the mini golf's flag tips).
- **The test, in full:** the playground, picked from playground, sculpture garden and mini golf.
- **Today's park lots:** flat 256 by 128 diamonds with no slab, filling the canvas, with small things on them (trees about 30 px tall, benches, a shed). They live in `src/buildings/lot-*.gif`, 40 frames each.
- **The design:** lawn with pale paths. In the middle, a patch of mint and coral rubber surface holds a small lavender dome tower with a curving pink slide, a gold swing set, a round sandbox and a little carousel with glowing cyan orbs. Two benches, and small trees and shrubs at the corners. The prompt ends with "Everything small and low, seen from above. Isometric pixel art, 2:1 isometric view, flat ground tile, light from the top left, 1 px dark outline."
- **Pixflux** (1 generation): 256 by 128, isometric on, the city colors forced, dark outline. Cute and bold, but at the bigger scale again: the slide is huge, the paths are yellow, and the lot covers only 77% of the plot diamond. In the city it floats on a smaller lot.
- **Pro with today's park lot as reference** (20 generations, about 1 minute):
  - The canvas is 256 by 128, and the reference is the first frame of `lot-park.gif`.
  - It copied today's lawn, scale and finish: 31 colors, hard alpha, and every design piece present. It covers 97.9% of the diamond, with a 1 to 2 px ragged edge at the corners. The pixels outside the diamond are tree tops, as on today's lots.
  - The fix: fill the empty diamond pixels from their nearest neighbors (then `_extras/pixellab-tests/helpers/filllot.py`, now `art/kit/filllot.py`; free; 352 px here).
  - In the city it blends in with the other parks.
- Files: `test6-compare.png` (today's park lot, Pixflux and Pro), `test6-city-2x-close.png` (both playgrounds on the city hall's plot at 2x), `test6-city-pro-1x/2x`, `test6-city-pixflux-1x/2x`, and `_extras/pixellab-tests/test6/`.

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
- **What Claude Code also loads:** the skills enabled on the claude.ai account, synced to `~/.claude/skills/synced/<id>/` and listed with the `anthropic-skills:` prefix. Its `manifest.json` names each skill's source:
  - Anthropic's file skills: pdf, pptx, docx, xlsx.
  - Anthropic's example skills: docs, morning, skill-creator, import-memory.
  - The plugin: nullovation-city, nullovation-city-builder, d-wizard.
  - The folder is rewritten on each sync, so skills are turned off in claude.ai, not deleted there.
  - Checked October 2026: the synced city skills match the source, except for quotes around the builder's name.
  - The personal skills folder also holds a stray `nullovation-city.skill` file, which Claude Code does not load.

## 6. Decisions (settled)

- **Status (changed 5 October 2026):** buildings show one status: dirt while their project's urgency is red. The build is delayed, including how the dirt is drawn and how it clears, so until it ships no building shows status, progress or stage, and bubbles carry status. Section 1 and the builder skill still say buildings never show status; update both when the dirt ships.
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
- **Connect to local Claude (0.1.19):** Open in Claude beside every Copy for Claude, offering Chat, Cowork and Claude Code through the desktop app's `claude://` links. The text is filled in, never sent.
- **Repo layout (0.1.17):** `src/` holds everything the page is built from, `art/` how the buildings are drawn, `tests/` the passes, `tools/` the chat archive; only `build.py` and the page it builds, `index.html`, stay at the root besides the docs and config. The build writes nothing into `src/`.
- **Nothing of the decision wizard in this repo:** it has its own. A new city starts with only Nullovation City.
- **Git:** Abdurrahman does all of it: branches, commits and pushes. Claude works in the folder and never branches, commits, pushes or touches the remote.
- **The page in the repo (0.1.18):** `index.html` at the root is built and committed with every change, and GitHub Pages serves it straight from the branch. There is no `dist/` folder; the chat archive goes one folder up, beside the source folder.
- **The traffic tonight round:** cars yielding in crossings, a speed check on a 7 by 7 city, and cleaning the handheld's colors were skipped.
- **PixelLab month (decided 5 October 2026 over two wizard rounds, PixelLab Month 1 and 2; updated by the tests on 6 October):**
  - **Where:** Claude Code generates through PixelLab's MCP, plus `art/pixellab.py` in the art pipeline for what the MCP cannot do, such as sending a local image.
  - **Plots:** PixelLab draws a building and its lot together; the pipeline redraws the lot whenever it misses the plot standard (section 4, the lot fix).
  - **Motion:** PixMiniMax was tested against code animation on the city hall, which Abdurrahman calls Nullovation hall. Code animation won (section 4, building motion).
  - **Priorities:** high for leader portraits and street props. Low for project buildings, new generics, building variants, vehicles, animals, lot props and park kinds. Not this month: micro building icons and UI art. Citizens, planned at medium, were cancelled (below).
  - **New buildings:** bus depot, drone port, apartment block, cafe, library. Made, then held out of the app until Abdurrahman says; he will use them as custom buildings. The drone port is finished from its test 5 still, waiting for approval (section 4, Building still); the other four wait for their designs.
  - **Street props:** bus stop, vending machine, holo billboard (icons, no words), bin. The sprite layer draws them where city life needs them, such as stops where the buses halt; the placement design is the street props decision below.
  - **Citizens:** planned as courier, scientist, engineer, robot citizen, dawn jogger, dusk lamplighter bot, and a street food vendor whose noodle hover-cart parks where crowds gather, with moves matching what people already do (walk, talk in groups, sit on benches). Cancelled after test 4: people stay code-drawn (below).
  - **Park kinds to add:** playground, sculpture garden, mini golf.
  - **Tool work this month:** a sprite layer for people, traffic and street props (people stay code-drawn at their size); the leader card; more park kinds. Later: a variant swap.
  - **Kept, not this month:**
    - pigeons and night fireflies (low priority);
    - The Nullovation Times, the weekly recap as a newspaper front page, which waits on UI art;
    - interiors for the project view;
    - city hall's dome showing the real city;
    - a Saturday parade of last week's busiest buildings, to be reworked;
    - a shy pond creature;
    - for leaders: living portraits, an expression per moment, the map figure, and a coffee break at the plaza.
  - **Dropped:**
    - building variants (brand new, holiday lights, rooftop garden, weather, mural bot);
    - a clinic, an observatory and a walking house;
    - delivery lockers and charging posts;
    - an alien visitor;
    - a skate bowl and a holo cinema;
    - a monorail, rooftop life, window cleaners and a planting moment;
    - a sky whale, UFO tick-off, sky islands and milestone critters;
    - a mayor portrait from a photo;
    - tool work for weather, prop placement and micro icons in the lists.
- **Citizens stay code-drawn (October 2026):** the 5 by 7 px people in `src/js/45-traffic.js` keep their size and abstraction. A 16 px PixelLab courier looked like a giant on the map, so PixelLab test 4 was cancelled.
- **Street props (October 2026):** designed in one wizard round (`wizard-rounds/2026-10-06-street-props-round1.json`, one folder up from the source) and not built yet (design only). The art recipe is in section 4, PixelLab workflow. The design:
  - **Where they stand:** on the sidewalk, pushed back over the plot's rim, since every prop is wider than the 5 px sidewalk.
  - **Facing:** a prop faces the street it stands on; faces show on a block's south and east sides, backs on its north and west sides.
  - **Behind buildings:** props stand on all four sides; a tall building partly hiding one on its north or west side is fine.
  - **Where each prop belongs:**
    - bus stop: anywhere, spread by a fixed pattern;
    - vending machine: mid-block, along a block side;
    - holo billboard: at a block corner, by the crossing (never on a zebra's landing);
    - bin: beside a building, where people walk in.
  - **How many:** up to two per block side.
  - **Fixed:** fixed per street segment, like the street details, so they look the same every visit; they do not follow activity.
  - **People:** walk through props, drawn in front or behind by depth.
  - **Buses:** pause at bus stops on their side of the street.
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
  - **Several projects (5 October 2026):** one leader can run several projects. Leaders live in a Leaders section in the side bar, and in a picker in each project's more menu.
  - **Portraits:** head and shoulders on a transparent background; the leader card sets the signature color behind. The art recipe is in section 4, PixelLab workflow.
- **The missing art round (7 October 2026, `wizard-rounds/2026-10-07-missing-art-round1.json`, one folder up from the source):**
  - Approved: the street props with the new lavender billboard, the drone port, and the playground.
  - Park kinds: the sculpture garden is the floating stones, and the mini golf is the lagoon course. All three new kinds go into the tool together, so the parks reshuffle once.
  - Held buildings, designs picked: the bus depot is the charging arcade, the apartment block the balcony stack, the cafe the neon cup corner, the library the book stack. Not made yet: Abdurrahman said no buildings for now. The prompts are in the round file.
  - Project buildings: Decision Wizard, Omar Khallouf Website, Game Analysis Frameworks, Local AI, Trips App, Sync and My Home keep their generic buildings; Shop Town Dooter, Congratulations You Exist, My Talks and Give and Grow get theirs later.
  - Leaders now for seven projects: Nullovation City Hall, My Retro Life, Generals and Diplomats, Half Cards, Council of Fun Masters, Decision Wizard and Omar Khallouf Website; the rest later. Concepts are in `leaders/2026-10-07-leader-concepts.md`, one folder up from the source; they are picked through a wizard round before any portrait is made.

## 7. Open items

- Street props on the map: the design and the art recipe are settled, and building them waits. The approved set is rendered by `art/props/props.py` into `art/out/props/` (section 4, Street props); placing it on the map is the tool work still to do.
- Leaders: build the leader card this month. The seven leaders are picked through a wizard round, then their portraits are made (6 generations a try).
- Abdurrahman names the projects that get the new buildings (bus depot, drone port, apartment block, cafe, library). The drone port is finished; the other four have their designs picked and wait until he says (20 generations each).
- Dirt on red: decided, and delayed (section 6, Status).
- The month's list: all six PixelLab tests are done, so the bulk work can start.
- Opening the city on another device, such as a first-launch prompt to open the data file: needs design.
- Cars yielding inside crossings, the 7 by 7 speed check, and the handheld's palette: skipped for now.
- Later: the leader figure on the map, a leader crew, and a spoken voice.
- The stills behind three animations are not in the source: `art/sources/city-hall.png` for the city hall, and the handheld and ring tower stills in `art/projects/sources/`. Those scripts cannot run until Abdurrahman adds them.

## 8. Working across chats and Claude Code

- **In claude.ai:** Nullovation City chats run in the Nullovation City project, which holds this file and the instructions. Each chat needs the newest source archive attached, since project knowledge takes documents but not zip archives, and a chat cannot write back to project files. The chat unzips it into `/home/claude`, which makes `/home/claude/nc`, works there, and delivers the built HTML, a new archive, and this file when it changed, to replace the project's copy.
- **In Claude Code:** Claude Code works in the git repo on the PC, or in an `nc` folder unzipped anywhere. Started there, it reads `CLAUDE.md`, which imports `docs/nullovation-city-knowledge.md`, and loads the two city skills from `.claude/skills/`; `d-wizard` comes from the personal skills folder. It runs natively on Windows, best with Git for Windows installed, or in WSL. On Windows, `python` replaces `python3` in every command.
- **Between them:** `python tools/pack.py` writes `nullovation-city-source-v<version>.zip` one folder up, beside the source folder, to attach to a chat. `python tools/pack.py --apply <zip>` brings the folder up to an archive a chat delivered: it writes changed files, removes files the archive no longer has, keeps what runs make and `.git/`, refuses an older archive unless `--force` is added, and shows the changes first with `--dry-run`.
- **Which copy wins:** `docs/nullovation-city-knowledge.md` in the newest archive is the current knowledge file. If the project's copy is older, the archive's copy wins.
- **What the archive leaves out:** `tests/shots/`, `tests/data/`, `art/out/`, `art/canon/out/`, `__pycache__/`, `.git/`, and Claude Code's local settings. It carries `index.html`, and keeps `art/unslimmed/` and `art/projects/`, which git leaves out.
- **GitHub:** the repo, github.com/AbdurrahmanKh/nullovation-city, is public and the home of the source. Abdurrahman pushes; Claude never does. GitHub Pages serves `index.html` from the branch at https://abdurrahmankh.github.io/nullovation-city/, so a push publishes the page. `art/projects/` stays out of git. The public repo shows this file's project names; the tests use neutral names since 0.1.19.
