# Changelog

## 0.1.37 (2026-10-14)

New places to see Claude's work, and Open in Claude in the terminal (Even Better Claude Connections, Round 1, B3 and D1, the items marked Now):
- Activity: a finish leaves "Claude Code finished: <task>" in its project's Activity, at the time it finished, once per session and task (the copy's task, or the prompt's first line without one). It makes the building busier for the week, as Activity does, but it is not work for urgency: only a tick is (B2). The tab that writes the data file writes it.
- Claude's drones: while Claude Code works on a building, six coral drones fly in from the map's edge, settle, and work round it at different heights; when the work stops, they fly off. They follow Traffic, Still, and the city's drones setting.
- The tab's title counts what waits for you: "(2) Nullovation City" while sessions need you, finished or stopped without you seeing it, or Claude's changes ask first.
- Open in Claude has a fourth item, Terminal: Claude Code in a new terminal in the project's first folder, with the text filled in, through Claude Code's own claude-cli:// link. It fills in up to 5,000 characters (longer goes by clipboard), and works once Claude Code has had a prompt in a terminal on this computer.
- Tests: test18 checks the Terminal item; test24 checks the Activity line, the title count and the drones.

## 0.1.36 (2026-10-14)

Claude updates the city (Even Better Claude Connections, Round 1, A1 and A2):
- Claude drops a change file into `inbox/` in the Claude folder, and the city picks it up within a few seconds, with no Load plan or tasks. A change names the project by name (any case) and its tasks by title, and the file then moves to `inbox/done/`, so nothing applies twice.
  - Applies at once, with a toast and Undo (6 seconds): adding tasks (into the milestone named, a new one if no milestone has that name, else the current one), adding a note, adding a link (not one the project already has). Activity says what Claude did.
  - Asks first: ticking tasks, a new description for a task, replacing the plan. They wait in `inbox/pending/`; the building's Claude bubble shows a ?, and its status card lists each change with Apply and Dismiss. Apply skips what it cannot find, such as a task no longer open.
  - A change for a project the city does not have, or a file it cannot read, goes to `inbox/rejected/` with a message. Done and rejected files are cleared after 14 days. One tab takes new files: the one that writes the data file.
- Every copy for Claude (a task, a note, a milestone, a project's status, the status brief) ends with "When you finish, send Nullovation City an update with the nullovation-city skill." The builder card does not.
- The nullovation-city skill sends updates: it finds the city's folder in `~/.claude/nullovation-city.json` (or the hooks in Claude Code's settings), reads the summary for exact names, and writes the change file; without the city's folder, it writes a tasks file or a plan as before. `check_plan.py` checks change files too. Reinstall the skill in the claude.ai plugin, so Claude Code has it in every folder.
- Tests: test24 checks applying at once and Undo, asking first with Apply and Dismiss, rejected files, and the copy line.

## 0.1.35 (2026-10-14)

Claude reads the city (Even Better Claude Connections, Round 1, A3: a summary for Claude):
- The city keeps `city/summary.json` in the Claude folder: every project with its description, folders, urgency, what is next, milestones with their open tasks (with descriptions and due dates) and done ones, notes and links. No building art, so it is about a tenth of the data file. It is rewritten a moment after every change, by the tab that writes the data file.
- Connecting the Claude folder asks to let the city write there too. A folder connected before 0.1.35 keeps its bubbles and asks once: Let it write, in Settings, Links and under the logo.
- The setup writes the folder down in `~/.claude/nullovation-city.json`, with the summary's and the inbox's paths, for the nullovation-city skill to find from any folder. Run the setup again once to write it.
- Tests: test24 checks the note the setup writes, the summary, its update after a change, and asking to write.

## 0.1.34 (2026-10-14)

The first piece of "Even better Claude connections" (Nullovation City Hall, Quick Wins), from Even Better Claude Connections, Round 1 (B1):
- Tick it: when a Claude Code session started from a city copy finishes, the status card's finish line offers Tick it for the task the copy named, while that task is still open. One click ticks it off as a tick does: done, work for urgency, a line in Activity, and the garbage it held goes.
  - The task is found by its title in the copy's project; a copy from another project, or a task renamed or already done, offers nothing.
  - With a session still working on the building, which takes the line, each finished task is named beside its Tick it.
- A turn Claude Code starts on its own, such as a background task's notice, no longer shows as `<task-notification>`: the city leaves it out of the card, and the hook no longer records it as the latest ask (that part needs the setup run again).
- Tests: test24 checks Tick it, the cases that offer none, and the tag prompts.

## 0.1.33 (2026-10-13)

From Abdurrahman's notes on Gus Grimsby:
- A [-] at the top right of his part of the side bar shrinks him to his face alone, with a coral ! on it, between This week and Urgent. A click on the face opens him again. He stays shrunk until then, kept on this computer; his speech bubble over the map still shows.
- He no longer says which projects are urgent or need attention, since the map's bubbles show it. The report line keeps only the overdue tasks ("You have 4 overdue tasks. Let's clean them up."), and the rows drop "urgent" and "needs attention": "Garden planner: 2 overdue tasks", and "Home budget: finish any task" for a building behind its pace with no late task.
- Tests: test26 checks the [-], the small face and opening it again, and the new report and rows.

## 0.1.32 (2026-10-13)

Gus Grimsby, the Garbage Man, designed over three wizard rounds (Garbage Man, rounds 1 to 3): the cleanup crew's grumpy but fair chief, who tells you what to fix.
- He lives in the side bar, between This week and Urgent, while the city has garbage: his face, his last line, one report line ("2 projects need your urgent attention, 1 project needs your attention. You have 4 overdue tasks. Let's clean them up."), the task to start with ("Start with Draw the beds, in Garden planner." or "Start with any task in Home budget."), and every building with garbage, most first ("Garden planner: urgent, 2 overdue tasks"). A click on a building goes to it.
  - Urgent: two or more periods behind its pace, or Work until finished with no task finished for a day. Needs attention: one period behind. Overdue: past its due date.
  - The task to start with is the one that clears the most; a late task also puts its project back on pace.
- He speaks up by himself in a speech bubble at the map's top left, with the same line under his face: the first open of the day with garbage in it ("You're back. 3 tasks between this city and clean streets. Start with Save a plan as a file." and two more), past 50 pieces ("The city is getting dirty! We should do something about it."), past 200 ("The city is filthy! This is unacceptable!"), and when the last piece goes ("Clean streets. Don't get used to it." and two more), before he steps away. Each alarm speaks once as the total climbs past it, at most once a day, and only the worst one passed speaks. The bubble closes with its button or by itself after 14 seconds.
- He never mentions pieces, only tasks. The Garbage switch sends him away with the garbage.
- Until his portrait is made, a faceless stand-in drawn in code takes its place: his yellow cap with the truck's teal badge, grey walrus mustache, coral overalls with a gold band, and a broom.
- The garbage ceiling is 1,000 pieces (was 500), and a building has 1,000 spots, so one forgotten building can carry it all. 1,000 pieces cost nothing measurable.
- Tests: the new test26 checks Gus; test25 checks the new ceiling.

## 0.1.31 (2026-10-12)

The garbage system, designed in the garbage round (`wizard-rounds/2026-10-12-garbage-round1.json`) and two previews: a city you leave alone fills with litter, and a hover truck clears it once you are back on it.
- One piece of garbage per point, round the building that earned it:
  - One task per N days: yellow (one period missed) 5; red (two periods) 10, and 10 more for each period after.
  - Work until finished: red (no task finished for a day) 10, and 10 more for each day after. Its yellow, a task finished today, adds nothing.
  - Each overdue task: 5 for each day late.
- Rest days pause the urgency points, not the late ones. Away pauses both: no building is yellow or red, and a late task does not grow on the days away. The city now records the days you set away, `city.awaySpans` in the data file.
- One ceiling for the whole city, 500 pieces; over it, every building's share shrinks in proportion.
- Where: the building's front strip and sidewalks first, then the gutters, the nearest park and the sidewalks across the street, then piling up. Each piece has a fixed spot and kind (paper, sticky notes, cans, bags), dealt by the building's place, so it stays put between visits. Loose papers hop in the wind now and then.
- Cleanup: any drop calls a hover garbage truck. It drives in from the map's edge at one end of the street, drops 3 of its crew who spread round the block and sweep, the pieces go with a sparkle, and it leaves by the other end. At most 3 trucks out at once. With Traffic off the garbage goes with the sparkle alone; on Still it just goes; what changed while the city was closed shows as it is on load.
- Shows on the map and the postcard; not in the status card, the recap, the status brief or Edit City.
- Settings, Look, Garbage: on by default, kept on this computer. Off, the city looks clean.
- Tests: the new test25 checks the points, the ceiling, the spots, the truck and its crew, the switch, and where garbage shows.
## 0.1.30 (2026-10-12)

From the second test on the PC: the hooks wrote to the folder the setup made by itself, `Nullovation City\Claude` in the user folder, while the city watched Claude-Hooks, the folder Abdurrahman picked, so nothing ever showed.
- The setup asks: a double-click opens a folder picker, starting at the folder already set, and the hooks write to the folder picked. Running it again moves them; Cancel changes nothing. `--install` alone keeps the folder already set instead of going back to the default.
- The setup leaves `README-nullovation-city.txt` in the folder, saying what the folder is for.
- Settings, Links warns when the city watches an empty folder with no README in it: Claude Code does not write there, so double-click the setup again and pick it.
- Tests: test24 checks the question, keeping the folder, the README, and the warning.

## 0.1.29 (2026-10-09)

From the first test on the PC: a Claude Code session in the terminal finished and closed within half a minute, and the city showed nothing.
- A session that finished and then closed keeps its green tick until you open the building's card, as a finish does; closed in the middle of work, it still shows nothing.
- Settings, Links lists a closed session too when no building claims its folder, so a folder that is not linked shows up there.
- Tests: test24 checks both.

## 0.1.28 (2026-10-09)

The first piece of "Design in details, connecting to local Claude" (Nullovation City Hall, Quick Wins): knowing when Claude Code is at work.
- Claude Code at work: a bubble over a building while Claude Code works in one of its folders, beside its urgency bubble.
  - A coral bubble with Claude's spark, turning while it works; a ? when it waits for you (a permission or a question); a green tick when it has finished; a cross when it stopped on an API error. Several sessions on one building show their count.
  - The status card says so in a line under the urgency: what Claude Code works on (the copy's task, or the first line of the prompt), since when, and for a finished session the start of its reply. Looking at the card counts as seeing a finish, so its tick goes.
  - Working goes quiet after 20 minutes without a word (an interrupt with Esc tells the hooks nothing), waiting after 8 hours, and a finish you never looked at after 12.
  - A session belongs to the project whose folder link holds its working folder, the deepest when several do, in any case or slash and from WSL; a file link counts by its folder. Failing that, the "Project:" line of a copy from the city places it.
  - No bubbles hides them, like the others, and so does the postcard; Still holds the spark still.
- The setup, `nullovation-claude-status.py`, from Settings, Links, Get the setup: a double-click (or `python nullovation-claude-status.py --install`) adds background hooks to Claude Code's user settings, which the terminal, VS Code, JetBrains and the Claude app's Code tab all read, and makes `Nullovation City\Claude` in the user folder for the session files. It keeps every other setting, saves the old file beside it, never doubles its hooks, and `--uninstall` takes them out. The hooks print nothing and block nothing.
- Settings, Links, Claude Code at work: Connect the Claude folder, what it last heard, and any session no building claims, to link its folder. Paused or a missing folder shows under the logo with its fix, like the data file.
- Tests: the new test24 runs the script as Claude Code would (install, uninstall, every hook event) and checks the city reading the folder.

## 0.1.27 (2026-10-08)

From the links round (Nullovation City Links, Round 1):
- The shortcut wheel:
  - Its buttons are larger and fit about three words; each grows outward from the ring, like a pie menu.
  - Enter under the wheel steps inside the building, and so does the Enter key while the wheel is open.
  - F opens the selected building's wheel round it, and closes it again.
  - The wheel and the status bubble close each other: a right-click closes the bubble, a click closes the wheel.
  - The arrow keys in the wheel no longer move the map under it, and Q and E hop on from the wheel's building.
- Enter steps inside the selected building, unless a button or a link has the focus.
- Links:
  - A label from the address: the label field offers a name, such as the repository for GitHub, the folder's own name, Claude, or the site; Tab takes it. A link without a label shows that name instead of its whole address.
  - Ctrl+V with an address, in the project view with no field in use, opens Add link with it filled in.
  - Adding an address the project already links says so, and Add becomes Add anyway.
  - Deleting a link shows a toast with Undo for 6 seconds.
- Search in the side bar also reads the links' addresses.
- The controls guide lists F and Enter.
- Tests: test23 grows by 34 checks.

## 0.1.26 (2026-10-08)

- Links:
  - Add link opens a larger panel: the address, then the label on its own line, and Add to shortcuts, on by default.
  - The icons are Doc, Code, GitHub, Claude, Chat, Folder and Web: Task and Design went, and links saved with them pick an icon from their address. claude.ai and claude:// links get the Claude icon, github.com the GitHub one.
  - While editing, each link drags by its grip to a new place (or moves with the arrow keys on it), shows the address over the label, and has a Shortcut switch.
- The shortcut wheel: a right-click on a building opens its shortcuts round the pointer, at most 8, the middle kept for the leader's face. Past 8, the links section says only the first 8 show.
- Copy for Claude on a task is now Copy task, and no copy carries the project's About any more.
- Open in Claude wears the Claude icon.
- The About shows the description first, then What is next.
- The nullovation-city skill lists the new icons and no longer says a copied task carries the About; reinstall it in the claude.ai plugin.
- Tests: the new test23 covers all of it; test13's zebra probe tries another car when one is held back, as the stop-line probe does.

## 0.1.25 (2026-10-08)

- The controls guide behind the ? in Settings no longer lists Rearrange: moving a building is taught by Edit City's bar, where a plain drag does it.
- Tests: test10 checks the guide leaves it out.

## 0.1.24 (2026-10-08)

- Settings, as designed over two rounds on 7 October 2026. The side bar turns into Settings, with a back arrow, from a Settings button at its foot, a gear on the map's bar, or the comma key; Esc closes it.
  - Six tabs: City, Life, Look, Projects, Saving and Links. Changes apply at once with no toast, a dot marks what differs from its default, each tab has Reset to defaults, and Reset all settings asks first. It opens again on the same tab and place.
  - The map's size, crowds, folder links, Download palette, Export and Import, and the data file moved in; the controls guide sits behind a small ? in its header. Copy status brief and Open in Claude stay outside, under This week. Traffic, Bubbles and Time of day are on the bar and in Settings, in step.
  - New: who is out (cars, buses, drones, cyclists, walkers), sliders for street traffic and walkers, street props on or off by kind with a slider for how many and Deal again, Auto's hours, motion (Full, Saver, Still), the postcard's caption and size, rest days, away until, daily backups keeping the last 14, storage use, and Test folder links.
  - The city's settings travel in the data file and backups; how this computer shows the city stays in this browser. The database is version 3; older backups import with default settings.
- Edit City, from Settings, City: an arrow on each side adds a line of plots there and another takes the outer line off when it is empty, so the city can be a rectangle, 5 to 11 plots each way; Grow and Shrink work as before; a click on a park deals its next kind; a building moves with a plain drag.
- Lines and rings keep everything with its buildings: parks, street details and props are dealt by their place in the city. Today's parks, props and crossing marks stay exactly as they were; the ring road's sidewalks and verges and the asphalt grain were dealt once more.
- Tests: three new passes, test20 (the panel), test21 (the settings) and test22 (Edit City), and the passes that used the old side bar find the controls in Settings.

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
