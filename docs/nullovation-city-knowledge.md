# Nullovation City: everything to know

State as of version 0.1.47 (October 2026). The tool file is about 2 MB. 0.1.38, one skill for the city, was built in a chat and has not reached the repo; 0.1.39 was built from 0.1.37.

## 1. What it is

Nullovation City is Abdurrahman's personal project tracker, drawn as an isometric pixel-art city. Every project is one building: click it for a quick status bubble, or step inside for everything else. It is one self-contained HTML file that runs offline in the browser, with everything stored locally. It holds his real projects, around 13 of them.

A building is a company that is always alive, whatever the project's status. Buildings never show progress or stage; the bubbles carry status. Since 0.1.31 a neglected building gathers garbage round it, on the ground, never on the building.

What Abdurrahman keeps:
- The tool: `index.html` at the root of the repo, which GitHub Pages also serves. A chat delivers it as `nullovation-city.html`.
- His data file: a JSON file on disk that the tool keeps up to date.
- Exported backups.
- The skills: `nullovation-city` and `nullovation-city-builder`, whose sources are in the source, and `d-wizard`, which has its own repo.
- The source, in a GitHub repo that Abdurrahman pushes; Claude never pushes. It travels to chats as the archive `nullovation-city-source-v<version>.zip`: code, art scripts, building animations, tests, fonts, the two skills' sources, `CLAUDE.md` for Claude Code, and a copy of this file. Section 8 covers how it moves between chats and Claude Code.

## 2. Features

### The city map

- The map is a grid of plots, 5 to 11 each way, so it can be a rectangle, such as 7 by 5. Edit City, in Settings, adds or takes off a line on any side, or a ring all round (Edit City, below). Each plot is 4 by 4 tiles, with streets between plots.
- Empty plots become parks, in seven kinds: garden, park, plaza, pond, and since 0.1.21 playground, sculpture garden, and mini golf. A park's kind comes from a hash of its place in the city, never the same as a neighbor, so adding a kind reshuffles every park once. Edit City can pick any park's kind.
- Streets vary by segment, fixed so they look the same every visit: repair patches, cracks, manholes, drains, center lines (dashed, double, none, turn arrows), sidewalk paving, crossings (zebra, stop line, none), and crossing centers (plain, manhole, yellow box, small roundabout). Like the parks and the props, they are dealt by their place in the city, so they stay beside their buildings when a line or a ring is added; the ring road round the edge is always the avenue with a double line.
- Zoom steps are 1x, 2x, 3x, 4x, 6x, and 8x. At even steps every building pixel lands on whole screen pixels. At 3x a building is first enlarged crisply to 2x, then scaled down smoothly, so it stays sharp.
- Drag to pan. Q and E jump to the previous or next building, Enter steps inside the selected one, F opens its shortcut wheel, and Esc backs out one layer at a time.
- The bar at the bottom right holds Traffic, Bubbles, Time of day, Postcard, Zoom, and a gear that opens Settings.
- Bubbles and Time of day open drop-ups: stacks of the same buttons as the bar, rising above the one clicked. Each option has its own icon, and the bar's button wears the chosen option's icon and label. The current choice shows pressed, arrow keys and Enter work, and Esc or a click outside closes.
- Time of day:
  - Auto (clock icon) follows the computer's clock, passing through dawn and dusk, at the hours set in Settings, Look: night from 19:00 and day from 06:30 by default.
  - Day (sun).
  - Dusk (a sun on the horizon) holds the halfway light. Dawn looks the same, so it is listed once.
  - Night (moon).
- Bubbles:
  - Bubbles (alert icon) shows red and yellow urgency.
  - Red only (flag).
  - Tasks (task icon) puts a near-white bubble over every building with that project's count of open tasks, 0 included.
  - No bubbles (cross).
- Hovering a building and the city's star (0.1.39, changed at 0.1.40 and 0.1.41): see Tasks on the map, below.
- Ghost tasks creeping round their blocks (0.1.47): see Ghost tasks, below.
- Postcard saves the current view as a PNG, with a caption and the date, at screen size; Settings, Look, can leave out the caption or double the size.

### Street props (0.1.22)

Bus stops, vending machines, holo billboards and bins stand round the blocks, made with PixelLab (section 4, Street props) and drawn at half size like the buildings.
- **Where:** on the sidewalk. On a block's south-east and south-west sides a prop stands near the curb and reaches back over the plot's rim; on its north-east and north-west sides it stands near the plot, behind it as seen from the camera, so a tall building may hide part of it.
- **Facing:** each faces its own street: fronts on the south-east and south-west sides, backs on the north-east and north-west.
  - A front faces one of the two near streets as PixelLab drew it: the bus stop's and billboard's the south-east, the vending machine's and the bin's the south-west. `src/buildings/props.json` records it as `faces`. The back faces the opposite street, the same diagonal turned around.
  - Mirrored, a view turns to the other street on the same side of the camera, so each view is drawn as is on the side it faces and mirrored on the other.
  - Until 0.1.23 the tool took every front as facing the south-west street, which turned the bus stops and billboards sideways on every side.
- **Which prop where:** bus stops by a fixed pattern (a fifth of block sides); vending machines mid-block; holo billboards 0.62 tiles from a corner, just past where a zebra lands; bins on a building's two front sides, where people walk in. At most two to a side, kept apart.
- **Fixed:** the plan comes from the block's place in the city and its side, like the street details, so it looks the same every visit and stays put when the map grows; planting a building only adds or takes away that block's bins.
- **Settings, City:** street props on or off, each kind on or off, How many, and Deal again (Settings, below). Off, a kind only goes; it moves nothing else.
- **People** walk through them, drawn in front or behind by depth. Props show with the traffic off too, and their neon (the billboard's screen, the bus stop's sign, the vending machine's front) keeps glowing by night.
- On the 5 by 5 test city: 51 props on 47 of 100 block sides (20 bus stops, 16 vending machines, 12 billboards, 3 bins).

### Traffic

The city has 12 cars, 2 small buses, and 2 delivery drones on a 5 by 5 map, scaled with the map's area. 20 people roam the whole city, and 2 cyclists ride its sidewalks. Settings, Life, keeps any of them in, and scales the street traffic and the walkers from a quarter to twice those counts.

- **People (0.1.20):** 5 px wide and 6 tall, drawn in code from row strings in `src/js/45-traffic.js` (`BODY`, `personRows`).
  - They face the way they move: toward you the face shows under the hair, walking away the head is all hair, and walking left mirrors the sprite.
  - Looks: about half have long hair (framing the face, and filling the back from behind), and half of those wear a dress over bare legs.
  - At most one item each: a courier's coral pack (6%), a tote bag (12%), a cap whose brim points the way they walk (15%), or a phone (10%). The phone and the pack's screen glow cyan and keep that color by night, so the crowd twinkles after dark.
  - Runners (3%): arms and legs spread, twice as fast, never stopping, with no item or companion.
  - Companions: some walk with a kid, 5 px tall (6%), or a 4 by 3 dog (5%), a step to their right; they skip the benches.
  - Cyclists: 2 on a 5 by 5 map, scaled with the map's area, kept apart from the people count. They ride the sidewalk loops at three times walking speed, cross at zebras (cars wait for them too), and never stop.

- Cars keep to the right, turn at crossings, stop at stop lines, wait at zebras, and keep a gap. They do not yet yield inside crossings, so turning paths can briefly overlap.
- Buses pull up to a bus stop on their side of the street (on their right, along their lane) and pause there for 2 to 3.5 seconds, once as they pass; cars behind them hold back.
- At night, cars and buses driving toward you show two warm headlights and a soft cone of light on the road ahead. Cars driving away show red tail lights.
- Drones hop between busy buildings.
- **Claude's drones (0.1.37):** while Claude Code works on a building (any of its sessions working), six coral drones with a warm yellow light, and no parcel, fly in high from the map's edge, settle to between 24 and 96 px up, and work round it on a loose ring 1.2 to 2.4 tiles from its middle, pausing and changing height. When no session there is working, they fly off the edge and are gone. They follow Traffic, Still, and the city's drones setting (Settings, Life), and are `cdrones` in `45-traffic.js`, checked once a second.
- **A street party (0.1.46):** when a milestone is finished, its block dances, six party drones loop over it and the nearest bus pulls up to watch (Celebrations, below). `parties` and `pdrones` in `45-traffic.js`.
- Busyness comes from a project's activity log over the past 7 days, each event fading out over the week. A building with busyness of 0.3 or more draws its own crowd.
- The crowd size is a setting in Settings, Life: None, Small, Medium, or Large, for 0, 8, 14, or 20 extra people per busy building. Medium is the default, and the whole city is capped at 150 people: the walkers stay under it, and the crowds take what room is left.
- People walk the sidewalks, cross at zebras, gather in groups and talk, sit on park benches, and go in and out of buildings.
- The Traffic button, and the Traffic switch in Settings, Life, turn all of it on or off. Motion set to Still stops it too.

### Urgency and bubbles

Each project picks an urgency system:
- **None.**
- **Work until finished:** its open tasks count.
- **One task per N days:** a pace. If no task is finished in time, the project turns red.

Due dates also count: tasks due soon or overdue jump to the top of the status bubble.

Settings, Projects, pauses the systems, never the due dates: rest days are weekdays that do not count for either system, and away until a date keeps every system quiet until that day, from which each counts afresh. Red and yellow bubbles float over buildings that need attention, showing a count, or "!" for a single item. The side bar's Urgent section lists red projects.

### Garbage (0.1.31)

A city you leave alone fills with litter, and a hover truck clears it once you are back on it. Visuals only: garbage never shows in the status card, the recap or the status brief.
- **The points, one piece of garbage each, round the building that earned them:**
  - One task per N days: yellow (one period missed) 5; red (two periods) 10, and 10 more for each period after: 20 at three, 30 at four.
  - Work until finished: red (no task finished for a day) 10, and 10 more for each day after. Its yellow, a task finished in the last 24 hours, adds nothing.
  - Each overdue task: 5 for each day late, from the day after its due date: 2 days 10, a week 35, a month 150.
  - Due within 2 days but not yet late adds nothing, though its bubble is red.
- **Rest days and away:** rest days pause the urgency points, not the late ones. Away pauses both: no building is yellow or red, so their garbage goes, and a late task keeps what it had on the day you set away, growing again from the day you are back. The city records the days away as `city.awaySpans`.
- **The ceiling:** 1,000 pieces for the whole city since 0.1.32 (500 before), none per building. Over it, every building's share shrinks in proportion, the leftovers going to the largest remainders.
- **Where:** first the building's front strip (lifted onto its plot) and front sidewalks, then its back sidewalks, the gutters of the streets beside it, the nearest park, and the sidewalks across the street, then piling up on its own ground; 1,000 spots a building since 0.1.32 (640 before), so one forgotten building can carry the whole ceiling. 1,000 pieces cost nothing measurable. Litter gathers in clusters, by corners and curbs. Each spot and its kind is dealt by the building's place in the city, so garbage stays put between visits and moves with its building.
- **The pieces:** drawn in code at double detail and shown at half size, like the props: loose paper and wrappers, sticky notes, cans and bottles with a cyan glint (which brightens at night, as the neon does), and dark, white and lying trash bags. Night colors come from the tool's palette, with no glow of their own. Now and then a loose paper hops a few pixels in the wind, never far from its spot.
- **Cleanup:** any drop calls a hover garbage truck, a partial one too.
  - It drives in from the map's edge at one end of the street on the block's south-east or south-west side (dealt by its place), faster the further it comes (3 to 7 tiles a second), and stops by the block.
  - Three of its crew, in coral with yellow caps and brooms, walk the sidewalk to spots of their own round the block and sweep for about 3.4 seconds; the pieces go with a sparkle, nearest first, and those spilled far away go when the crew are back. The truck leaves by the other end.
  - At most 3 trucks out at once; the rest wait their turn. The truck hovers with a shadow under it, bobs a pixel, and shows headlights or tail lights at night.
  - Traffic off: garbage goes with the sparkle alone. Motion on Still: it just goes. What changed while the city was closed shows as it is on load, with no truck. A ticked task, a moved building or a new day shows within a second.
- **Where it shows:** the map, the postcard, and the picture at the top of the project view, which is the map's own drawing of the building in its street. Edit City hides it.
- **The switch:** Settings, Look, Garbage, on by default and kept on this computer. Off, the city looks clean and no truck comes.

### Gus Grimsby, the Garbage Man (0.1.32)

The cleanup crew's chief, grumpy but fair, who tells you what to fix. Designed over three wizard rounds (section 6, The Garbage Man).
- **Where:** in the side bar, between This week and Urgent, while the city has garbage: on its map, or owed by the rules. He steps away once the last piece is gone and his last word has closed, and goes when the Garbage switch is off.
- **His part of the side bar:** his face, his name and title, a [-] at the top right, his last line (with a coral bar beside it), then his report. Since 0.1.33 he never says which projects are urgent or need attention: the map's bubbles show that.
  - One line for the overdue tasks: "You have 4 overdue tasks. Let's clean them up." ("You have 1 overdue task. Let's clean it up." for one); with no overdue task, no line. Overdue: a late task that makes garbage (past its due date, and not frozen by away). Until 0.1.33 the line led with "2 projects need your urgent attention, 1 project needs your attention."
  - The task to start with, the one that clears the most: "Start with Draw the beds, in Garden planner.", or "Start with any task in Home budget." when that is a project behind its pace. A late task also puts its project back on pace, so it counts both. Titles past 60 characters are cut short.
  - Every building with garbage, the most first: "Garden planner: 2 overdue tasks", "Recipe box: 1 overdue task", and for a building behind its pace with no late task, "Home budget: finish any task", since finishing any of its tasks clears it. A click goes to the building and opens its card. (Until 0.1.33: "Garden planner: urgent, 2 overdue tasks", "Home budget: needs attention".)
- **Minimized (0.1.33):** the [-] shrinks his part of the side bar to his face alone with a coral ! on it, like the Urgent tiles' badges, still between This week and Urgent. A click on the face opens him again. It stays shrunk, through new lines, reloads and his steps away, until that click; kept on this computer. His speech bubble over the map still shows while he is shrunk.
- **When he speaks up:** in a speech bubble at the map's top left, by the side bar, with his face, name and a close button; the same line shows under his face in the side bar. It closes with its button or by itself after 14 seconds. Four moments:
  - The first open of the day with garbage in it, one of three lines picked at random: "You're back. {tasks} between this city and clean streets. Start with {task}.", "Took you long enough. {tasks} waiting. {task} first.", "I cannot clean what you don't fix. {tasks}. Start with {task}." {tasks} is the tasks between the city and clean streets: every late task, plus one for each project behind its pace with no late task of its own; {task} is the task to start with, capitalized when it starts a sentence.
  - The garbage passing 50 pieces: "The city is getting dirty! We should do something about it."
  - Passing 200: "The city is filthy! This is unacceptable!"
  - The last piece going, after the truck: "Clean streets. Don't get used to it.", "Not a wrapper in sight. I'll be off, then." or "Fine. Good work. Don't make me come back."
  - Each alarm speaks once as the total climbs past it, at most once a day, and only the worst one passed speaks; nothing speaks on load but the day's first word. The days are kept in this browser.
- **Never pieces:** his lines and his report count tasks and projects, never pieces of garbage.
- **His face:** until his portrait is made, a faceless stand-in drawn in code, 28 by 22 px shown at twice the size: his yellow cap with the truck's teal badge, grey brows and walrus mustache, coral overalls with a gold band, and a broom over his shoulder, on a dark coral frame.

### Tasks on the map (0.1.39 to 0.1.41)

The first of the task ideas (section 6, Tasks), from Tasks, Round 2, M1 to M6, with Abdurrahman's changes to the star after trying it (0.1.40), and the star's colors and What is next's layout picked from mockups (0.1.41, Star and What is next, Round 1).
- **The hover (M1 to M3):** with the mouse resting on a building for 250 ms, a white bubble with its count of open tasks (0 included) joins its bubbles on the left, so the bubbles already there stay where they are, and its next task shows in one line under them, centred, in the Tasks view's near white, cut short past 40 characters with the full title as its tooltip. A pinned or starred next task carries a small pin or star. In the Tasks view, which already shows the count, only the line is added. It shows whatever Bubbles says, No bubbles included, since you asked for it; not on the selected building (its card is open), in Edit City, while planting or moving, while the shortcut wheel is open, or in the postcard. A press, a right-click or leaving the building takes it away; letting go starts it again. The building's name tip by the pointer stays as it was. The line is `#hoverTask`, placed each time the map is drawn (`placeHoverLabel` in `40-map.js`).
- **Pins (M4, M5):** a project can pin one open task as its next one. The pinned task comes first in What is next, the status card, the hover, the project's status and the summary for Claude (`nextTask` and `bubbleTodos` honor it), even from another milestone; What is next says Pinned beside its label and names the pinned task's own milestone. Pinning another task moves the pin. It clears only when its task is ticked (anywhere: the list, the card, the panel, Tick it, Claude's asked-for tick), deleted, or unpinned; reopening the task does not bring it back.
- **The star (M6):** one open task in the whole city can wear the star: a purple bubble with a gold star over its building (0.1.40 made it cyan on night blue, a misreading of the request; 0.1.41 brought the gold back, A1), beside the urgency (or Tasks) bubble and before Claude's. It shows with Bubbles, Red only and Tasks, and hides with No bubbles and in the postcard. Starring a task pins it in its project too; after that the two are separate, so unstarring keeps the pin and pinning another task keeps the star. Starring another task moves the star, with the toast "The star moved to <task>." Ticking, deleting or unstarring takes it off.
- **Where to pin and star (M4, changed at 0.1.40):** the pin is a small icon button, hollow until pressed, on every open row of the status card and of the project view (shown while the row is pointed at or has the focus, and always when pressed), and at What is next's top right, where a pressed pin says Pinned (0.1.41). The star is set only in the task panel, as Star for the city / Starred: Abdurrahman found a star on every row too much for a feature used rarely. The task panel also has Pin as next / Pinned. A starred task shows a gold Starred mark, not a button, at What is next's top right (0.1.41; a cyan star mark beside the task at 0.1.40). After a click in What is next the focus stays on its pin, even when the next task changes. A click on a pin keeps the focus on it and neither opens nor drags the task. A done task has none.
- **The starred task in the side bar (0.1.40):** while a task wears the star, a card under search, above This week, shows its building, Starred with the star, the task (two lines at most) and its project, purple with a gold edge (0.1.41; cyan at 0.1.40). A click opens the task in its project; ticking, deleting or unstarring takes the card away. `renderStar` in `70-menu.js`.
- **What is next (0.1.40, 0.1.41):** a widget of its own, a shade lighter than the project view (#2E2748) with an edge round it (0.1.40). Since 0.1.41 it is layout B (A3): the label What is next with the pin, and Starred while the task wears the star, at its top right; the task's own milestone with the due date as a chip at the right of its line ("Due Fri 23 Oct", "Due tomorrow", "2 days overdue", red when late), and nothing without a date; the task in 17 px type, red with a ! when overdue; Copy task and Open in Claude on one row; and the other overdue tasks' note under them. While its task wears the star, the box is purple (#3A2766) with a gold edge (A2).
- **Not work:** pinning and starring change neither Updated nor urgency, and write nothing in Activity. Esc in the task panel, which undoes the task's edits, leaves them alone, since they live on the project.
- **Data:** a project's `pin` and `star` hold a task id or are empty (section 3). `tidyMarks` clears any that point at a task no longer open before every save, and reading a city keeps the first star only.

### Recurring tasks and one-line adding (0.1.42)

The second of the task ideas (section 6, Tasks), from Tasks, Round 2, R1 to R4, O1 and O2, with R1 reasoned out at the build from Abdurrahman's own words. `22-repeat.js` holds the model and the reading of a typed line; `66-quickadd.js` the quick add.
- **How a repeat comes back (R1):** ticking a repeating task moves the same task on to its next date (R4) and it waits: out of the status card, What is next, the hover count, the bubbles, urgency, Due this week, Gus and the garbage, until that day, when it is back and due that day. In the project view it keeps its place in its milestone, dimmed, with its repeat sign for the square and "Back Thu 22 Oct", so it can be opened, changed or stopped; its panel says "Ticked. Back Thu 22 Oct, due that day." A nearer due date brings it back sooner. A new repeat shows at once, due on its first date. A repeat not ticked by its date stays one overdue task, garbage and all, until it is ticked; nothing piles up.
- **Undo:** a tick in the list, the card or Tick it shows a toast, "Water the beds comes back Fri 23 Oct.", with Undo; unticking in the card while the line is still struck through puts it back too. In the task panel, Esc undoes it, as it undoes every edit there; the Done line is written when the panel closes, as for any task.
- **Schedules (R2):** every day, every N days (2 to 365), weekly on chosen weekdays (the buttons run Saturday to Friday, like rest days; one stays pressed at least), monthly on a date (1st to 31st; a month without it uses its last day, and the panel says so), yearly (a day and a month; 29 February uses the 28th in other years). The task panel's Repeat row, under the due date, sets them; a task with no due date gets the schedule's first date from today; No repeat stops it, bringing back a waiting one at once. Repeats show a small repeat sign beside the date in the project view's rows and the status card.
- **The next date (R3), `nextRepeatDue`:** weekdays, monthly dates and years keep their rhythm: the first such date after the later of today and the due date, so a late tick skips what was missed and an early one does not come back the same week. Every day and every N days count from the day of the tick.
- **One task moves on (R4):** the task keeps its id, title, milestone and description; only Activity's Done line records each tick, and it counts as work for urgency. The week's recap reads Done lines, so a repeat ticked counts there, once per week by its title. Pins and the star clear on a repeat's tick, as on any tick (M5). A milestone with a repeat in it never counts as finished.
- **The one-line add (O1):** marks typed in a task's line are taken out of its title. !fri (or !friday), !today, !tomorrow, !20, !oct 20 (or !20 oct, or !2026-10-20) give the due date, the next such date that is not past. #daily, #weekly, #monthly, #yearly, #every day and #every 3 days give a repeat: #weekly on the due date's weekday, or on each weekday marked (!mon !thu #weekly); #monthly and #yearly on the due date's day; with no date a repeat starts today. @name puts it in the milestone whose name starts with it (case, Arabic letter forms, and hyphens for spaces aside), or a new milestone by that name when none fits. A word that does not read as a mark stays in the title, so "#1 priority" and "bob@mail.com" are left alone. Marks are English; the title can be in any language. Under the field, a line says what was understood before Enter ("In Launch · Due Fri 23 Oct · Repeats weekly on Fri"), or what is missing ("Type the task too", "/nope fits no project"); empty and focused, it names the marks. ^ and * (pin and star) and #repeat alone were left out (O1).
- **Where (O2):** the project view's add field under each milestone's +, which puts the task in that milestone unless @ says otherwise; a new add field at the foot of the status card's list, "Add a task", which adds to the current milestone (else the last, else a new To do), clears, and stays focused for the next one, keeping what is typed when the card redraws; and the quick add: T, anywhere outside a field and when no dialog is open, opens one line over the map, "A task, with /project !date #repeat @milestone". /name picks the project the same way @ picks a milestone; without it the task goes to the project open in the view, else the selected building, and with neither it asks for one. Enter adds it and closes, with a toast "Added to Garden planner: Weed the beds." and Open; Esc or a click elsewhere closes it. The controls guide names T.
- **Data:** a task may carry `repeat` (`{ every: 'day', n }`, `{ every: 'week', days }`, `{ every: 'month', day }` or `{ every: 'year', month, day }`) and `waiting: true` while a ticked repeat waits for its due date. Reading a city keeps a whole repeat only, and a wait only while its date is ahead; `tidyMarks` clears a wait whose day has come before every save, so a later due date cannot hide it again. A project export loaded back as a plan keeps its repeats, and a tasks file or Claude's add-tasks may carry one in the same shape.

### Reports (0.1.43 to 0.1.45)

From the fourth of the task ideas (section 6, Tasks), Tasks, Round 2, P1 to P3, built before the third at Abdurrahman's call on 19 October. `74-reports.js` holds it. The weekly review (V2 to V4) was built at 0.1.43 as a third tab and taken out at 0.1.44, after he tried it (section 6, Tasks); the productivity inspector (V1), Proxima Pace, lives at the top of Reports since 0.1.45 (below).
- **The panel (P1):** a Reports button sits beside Settings at the foot of the side bar; it, or R anywhere outside a field with no dialog open, turns the side bar into Reports, as Settings does, with the map in view and at its size. The back arrow, Esc or R again bring the lists back, with the focus on Reports. Reports and Settings share the side bar, so opening one closes the other. On a narrow window R opens the drawer on Reports. Two tabs with their names, Weeks and Records, and the arrow keys between them; the tab and Week or Month are kept in this browser, and it opens again on the tab last used (Weeks, for a browser last left on 0.1.43's Review).
- **What counts:** every count is of ticks: Activity's Done lines, less those a Reopened line took back (`taskTicks`), so a repeat counts each time it is ticked, unlike the recap's once a week. A done task whose Done line the log no longer keeps (it holds 400 lines a project) counts on the day it was finished. Claude Code's finish lines, added and removed tasks never count.
- **Weeks (P2):** "Tasks finished each week": a bar for each of the last 12 Saturday-to-Friday weeks (`weeklyTicks`), with its count over it, this week's last and hatched as so far, and three dates under them; over the bars, this week so far, the 12 weeks' total and the average a week. "By project": Week or Month, arrows back to the first week or month with a tick and on to now, and each building's tasks finished in it, the most first, with its picture and a teal bar (`ticksByProject`). It opens on this week; a bar picks its week, and that bar turns gold. A row shows the building on the map.
- **Records (P2, P3):** the streak (`streakOf`): days in a row with a task finished, with a flame, then what today does ("Finish a task today to make it 7 days.", "Today counts already.", or a day off that cannot break it) and the longest with its first and last day. Rest days and days away never break it (P3): one with no tick is passed over, one with a tick counts, and today does not break it before its first tick. The busiest building of the month (`busiestByMonth`): its picture and name in gold, and how many it finished; buildings tied share it; then each earlier month with a tick, at most 11. Milestones finished (`milestonesFinished`): every task in them done, dated by the last one, newest first, with the project; 8 show, then Show all; a click opens the project. Overdue tasks over time is for later; by weekday and best weeks were left out.
- **Kept up:** a tick anywhere redraws the open tab at once.
- **Data:** nothing new. Reports keep their tab and Week or Month in this browser (`nullovation-city:reports`).

### Proxima Pace, Productivity Inspector (0.1.45)

V1 of Tasks, Round 2, designed over two wizard rounds (section 6, The Productivity Inspector). A co-pilot who reads the city's instruments and calls out the numbers. `76-proxima.js` holds her.
- **Where (J1):** at the top of Reports, above the tabs: her face, name and title, her line (with a sky-blue bar beside it), and her three reports as tiles, Daily, Weekly and Monthly, each with the day, week or month it is on. A tile not read yet has a sky-blue dot and a sky-blue name, and the Reports button wears the same dot ("Reports (R). Proxima has a report for you."). Her line is the biggest report not read yet's first line, else the daily one's. A click opens the report. With nothing to report yet (a new city): "Her first report comes tomorrow."
- **Her reports (J3):** the daily report, on yesterday, waits in Reports and never speaks; the weekly report, on the last Saturday-to-Friday week, and the monthly one, on the last month, she brings herself on the first open after their period ends (or within a minute, while the city stays open), each once, in a speech bubble at the map's top left with her face, name, line, Read and a close button. Read opens Reports and the report. The bubble closes by itself after 14 seconds; closed unread, the report keeps its dot. With both due she brings the weekly one, then the monthly one. A report on a period that ended before the city's first record is not given.
- **Never with Gus:** she waits while Gus speaks, and when he speaks while she does, her bubble goes and she says it again after him. She waits while a report or another panel is open.
- **A report, in a panel:** her face and the report's first line, the period, then (L1):
  - in every report: Tasks finished, against the period before ("7, 4 more than the week before."); Streak, now, and how short of the longest; Milestones finished in the period, with their dates; and what the coming day, week or month holds (Today, This week, This month), from today on, with each task's date, a repeat coming back in it included.
  - weekly and monthly add: By building, the most first; Busiest building, ties shared; Nothing finished, the buildings with open tasks and no tick in the period; Overdue, with the oldest-due task to close first.
  - monthly adds: Repeats kept up, each repeat with how many times it was ticked; Notes written, with their dates.
  - From Proxima, her facts (L2): a milestone one task from done (every other task in it done, no repeat, at least two tasks), in every report; next week with nothing due, in the weekly; a repeat (weekly or more often) ticked 3 or more weeks running, in the weekly and monthly.
  - A task opens in its project, a building shows on the map, a milestone opens its project.
- **Every count is of ticks,** as in Reports (`taskTicks`), and the streak is Reports' (`streakOf`).
- **Her lines (V2), word for word:** weekly, one of "Weekly report inbound! {n} tasks landed this week." and "Copy that, week logged: {n} tasks done. Report's ready.", or with no ticks "Quiet week: no tasks landed. Next week holds {due} due."; monthly, one of "Monthly report on deck! {n} tasks in {month}." and "{month} is logged: {n} tasks, {m} milestones. Report's ready.", the second always when nothing landed; daily: "Yesterday: {n} tasks landed. Today's flight plan: {due} due."; the facts: "{milestone} is one task from done: {task}. Let's land it!", "Next week's flight plan is empty. Nothing due yet.", "{repeat}: ticked {k} weeks running. Steady hands!". A count of one reads in the singular. The same report always gets the same line (picked by `hashStr` of its kind and period).
- **Her face:** until her portrait is made, a faceless stand-in drawn in code, 28 by 22 px shown at twice the size: black hair in a high ponytail with a sky-blue tie, a white earpiece with a side mic, a sky-blue pilot shirt with a white collar and epaulettes, and a stopwatch on a lanyard, on a dark sky-blue frame (Sky crew, N2).
- **A finished milestone (0.1.46):** she announces its street party in her speech bubble, with Go to it in place of Read (Celebrations, below).
- **Data:** nothing new in the city. What was read and what she said are kept in this browser (`nullovation-city:proxima`).

### Celebrations (0.1.46)

The sixth of the task ideas (section 6, Tasks), designed in Celebrations, Rounds 1 and 2 (section 6, Celebrations). `49-celebrate.js` holds the particles, the bursts, the party and its lights; `45-traffic.js` the party's crowd, drones and bus; `76-proxima.js` her announcement.
- **A tick bursts (T1):** every tick sets off small particles round its building, never a firework: a burst like the decision wizard's when you type wizard there (26 gold stars that fly out, fall and fade over 1.5 seconds). 16 particles fly out from the building's middle (0.42 of the way from its top to its base), 24 to 50 map px with a slight lift, drift down 14 px, and twinkle out as a dot of their own color over the last fifth of 1.5 seconds. They are drawn in code at the map's scale, 3 to 7 px plus the city's 1 px dark outline, about the size of the people, in the city's colors, which they keep at night like the neon. A tick anywhere counts, through `tickTask`: the status card, the project view, the task panel, Tick it, and Claude's Apply; a repeat's tick too. Unticking plays nothing. They show over everything but the bubbles, on the map and in the project view's picture, which is the map's own drawing.
- **The kinds (T2, T3):** stars, binary 0 and 1 (cyan), gold 0 and 1, dollar signs, lightning, wizard sparkles, hearts, leaves, game buttons (four colors and a d-pad), speech bubbles, coins (which turn as they fly) and confetti (bits in seven colors). Every building starts on stars. `PARTICLE_KINDS` in `20-model.js`.
- **Picking:** the project view's Building panel, opened from the building's picture, has Particles above the generic buildings: a tile per kind, at rest with three of them, playing its burst while pointed at or focused. A click picks it, presses it, and plays it on the map. Picking is not work: Updated stays and nothing goes in Activity.
- **The street party (S1, S2):** ticking the last open task of a milestone of 2 tasks or more throws a 30 second party round its building.
  - Its particles burst every 2 seconds or so.
  - Party lights: strings across its four streets, three to a street, from sidewalk to sidewalk on two poles 11 px tall with a 3 px sag, a bulb on every other pixel in the city's colors (neon pink, butter, neon cyan, lavender, leaf), chasing along; they keep their colors at night. They are sorted by depth with the figures, so a building in front hides the ones behind it.
  - With the traffic on: those on its block dance (both arms up, one arm out, up, the other, with a hop on each up, turning now and then), and others walk over to dance, across its zebras or out of its front, up to about 20 in all, under the city's 150. Anyone walking on to the block joins in.
  - Six party drones in the colors of its particles fly in high from the map's edge, settle, and loop round it at 34 to 79 px up, rising and dipping.
  - The nearest bus drives over at 1.6 tiles a second by the shortest way to a street with the block on its right, skips its bus stops, and waits at the block's curb, mid-block, cars holding back behind it.
  - When it ends, the lights come down, the dancers walk on, the guests walk off across the first zebra (or into the building), the drones fly off the map's edge, and the bus drives on a second later.
  - With the traffic off, the party has its particles and lights only. Motion on Still shows no particles and no party.
- **Proxima announces it:** in her speech bubble, after anything already waiting, in one of two lines approved word for word, picked by the milestone: "Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!" and "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!". Go to it, in place of Read, glides the map to the building, into the open part beside the project view when it is open. She waits for Gus and for an open panel, as for her reports; several milestones are said one after another; while the project view is open her bubble sits beside it. She announces it on Still too.
- **Once a day:** a milestone throws its party once a day, so unticking and ticking again throws no second one; kept in this browser (`nullovation-city:celebrate`). A milestone with a repeat in it never finishes.
- **Data:** a project's `particles`, one of `PARTICLE_IDS`; a city without it, or with a kind the tool does not have, reads as stars.

### Ghost tasks (0.1.47)

The fifth of the task ideas (section 6, Tasks), first named Tasks as cars, designed in Ghost Tasks, Round 1 (section 6, Ghost tasks). `46-ghosts.js` holds it.
- **Which tasks haunt (C1, G1, G2):** every overdue task, and the next task of each building behind its pace: one or more periods behind under One task per N days, or a day without a tick under Work until finished. Those are the buildings that make garbage through urgency (`Garbage.breakdown(p).sys`), and overdue is Gus's (a late task that makes garbage), so the ghosts, the garbage and Gus's count agree. The next task is the one the status card puts first (`bubbleTodos`): the pinned one when there is one, else the first due soon, else the current milestone's; a task both overdue and next is one ghost, so a pinned next task that is not overdue gets a ghost of its own beside the overdue ones. At most 5 to a block, the most overdue first, then the next task; the rest come out as ghosts are ticked. Rest days and away pause the pace, never the due dates, so on them only overdue tasks haunt; a repeat waiting for its next date never haunts. `hauntOf`.
- **The ghost (L1, L1a, L2, L3, C2):** a sheet ghost drawn in code, 9 px wide and 12 tall at 1x (`SHAPE`, `HEMS`): a round head over a hem that ripples through three frames, see-through white inside its edge (`rgba(250, 244, 255, 0.62)`), and two glowing eyes 1 by 2 px. Its edge and eyes glow in its building's bubble color: red (edge #FF3D7F, eyes #E8195A) or yellow (edge #FFC81E, eyes #D98A00), and keep it at night like the neon. By day a faint dark ring round it keeps it clear on the pale sidewalk; at night that ring becomes a soft glow in its edge color. Its eyes look the way it goes: to the side it heads on screen, low coming toward you, high going away.
- **Round its block (C3, M1):** on the sidewalk ring, among the people, who walk through it; it is sorted by depth with them, so a building in front hides it. It creeps at 0.11 to 0.15 tiles a second, about half walking speed, floating 1 to 3 px above a faint shadow and bobbing. It pauses now and then (and sometimes turns back), lingers by its building's front staring in, and at a corner stops, leans round on to the new side with its eyes on it, and carries on (X1, peeks round corners). It never crosses a street. Two meeting head on: one turns back after 2 seconds.
- **Coming and going (M2):** a ghost whose task starts to haunt comes out of its building's front, fading in; when the city opens, or the ghosts show again, they are already on their rounds. A tick anywhere (through `tickTask`: the status card, the project view, the task panel, its own card, Tick it, Claude's Apply) lays it to rest at once: it rises 6 px and fades out where it is, in a second. One whose task stops haunting without a tick (a new due date, the building back on pace) leaves the same way, within a second. Its building moved, it goes round the new block.
- **The hover (X1):** resting the mouse on a ghost shows its task's title by the pointer, as a building's name does; no building is hovered.
- **Its card (C4, X1):** a click opens a small card over the ghost, with a strip in its glow: its project, the task, its due chip ("6 days overdue" in red, or the next task's date, nothing without one), Tick and Enter. The status card and the shortcut wheel close for it, and the ghost holds still while it is open. Tick ticks the task off, with the toast "Ticked off: <task>." and Undo, or moves a repeat on with its own toast. Enter steps inside the building with the task open beside it (`FullView.openTask`). Esc, its close button, a click elsewhere on the map, or a building's status card closes it. Open in Claude on the card was left out.
- **When they show (S1, S2):** Settings, Look, Ghosts, on by default and kept on this computer (`nullovation-city:ghosts`), with its dot and its tab's Reset to defaults. Traffic and No bubbles leave them. Hidden on Motion Still and in Edit City; shown on the postcard and in the project view's picture, the map's own drawing.
- **Data:** nothing new in the city.

### The status bubble

Click a building for a small card:
- the project's next 3 open tasks: the pinned one first (0.1.39), then those due soon;
- tasks can be ticked off from it, with a short animation; a repeat moves on to its next date (0.1.42);
- an add field, Add a task, with the one-line marks (0.1.42);
- when the project was last updated;
- an Enter button that steps inside.

### The project view (stepping inside)

- **Top:** the building's picture and the About: the project's description first, then What is next, with Copy task and Open in Claude for the next task. Since 0.1.39 What is next shows the pinned task when there is one; since 0.1.40 it is a widget of its own, a shade lighter than the view; since 0.1.41 it is laid out as layout B, purple with a gold edge while its task wears the star (Tasks on the map, above).
- **Milestones and tasks:** tasks are grouped by milestone. They can be reordered by dragging, and each has an optional due date, an optional repeat (0.1.42) and a description. A milestone's + opens a one-line add field with the marks (0.1.42). A task opens in a side panel, with Copy task and Open in Claude.
- **Milestone view:** clicking a milestone's name opens its rename field and its tasks as a read-only list. Done tasks are ticked and struck through, and open ones show their due date and the first line of their description. It also has Copy for Claude and Delete milestone.
- **Notes:** notes show as cards, each with its own copy button. A note opens in a panel with Copy for Claude and Delete.
- **Links:** each link shows an icon: Doc, Code, GitHub, Claude, Chat, Folder or Web. An address picks its own icon as it is typed: claude.ai and claude:// get Claude, github.com GitHub, and a Windows path Folder. With the setting on, folder links open in File Explorer. (Until 0.1.26 there were Task and Design icons; links saved with them get an icon picked from their address.)
  - **Add link** opens a panel the width of the column: the icon, the address, and the label on its own line under it, then Add to shortcuts, on by default.
  - **Paste to add (0.1.27):** Ctrl+V with an address on the clipboard, while the project view is open and no field is in use, opens Add link with it filled in, ready for a label. Text that is not an address (one line starting with a scheme and //, mailto:, www., or a Windows path) is left alone.
  - **A label from the address (0.1.27):** the label field offers a name read from the address alone, since the tool works offline: a GitHub repository's name (with #12 for an issue or pull request), a folder's or file's own name, Claude project, Claude chat or Claude, a github.io page's first folder, an app's name (Slack), or the site's name (figma.com). Tab in the empty field takes it, to edit. A link without a label keeps it empty and shows that name, on its button and in the wheel, instead of its whole address. `suggestLabel` in `20-model.js`.
  - **The same address twice (0.1.27):** an address the project already links, by `addressKey` (case, a trailing slash, www, and http or https aside), says so under the address with that link's name, and Add becomes Add anyway.
  - **Editing** the section shows each link as a row with a grip, its icon, the address over the label, a Shortcut switch, and delete. A link drags by its grip to a new place, or moves with the arrow keys on the grip; the list's order is the wheel's order. Deleting one shows a toast with Undo for 6 seconds, which puts it back in its place, while the section is open or after Done (0.1.27).
  - **Past 8 shortcuts** a note says only 8 fit in a building's wheel, so the first 8 in the list show. More are allowed.
- **The shortcut wheel (0.1.26):** a right-click on a building opens a pie of its shortcuts round the pointer, like the Sims' pie menu: its links marked as shortcuts that can be opened, in the links' order, at most 8, the first at the top and the rest clockwise. The middle is an empty round frame kept for the leader's face, and the building's name sits above. A shortcut opens like its link in the project view. Esc, a click elsewhere, scrolling, or a click on a shortcut closes it; the arrow keys move between shortcuts. A building with none says so. It does not select the building, and opens nothing on a park, while planting or moving, or in Edit City.
  - **Since 0.1.27:**
    - Its buttons fit about three words (up to 216 px), each growing outward from the ring: left-aligned on the right, right-aligned on the left, centered only near the top and the bottom.
    - Enter, a button under the wheel, steps inside the building, as the bubble's Enter does. The wheel opens with no shortcut picked, so the Enter key steps inside too; the arrow keys pick a shortcut, and Enter then opens it.
    - F, with a building selected, opens its wheel round the building, and F again closes it.
    - The wheel and the status bubble never show together: a right-click closes the bubble, and a click on a building closes the wheel and opens the bubble. The empty middle lets a click through to the building under it.
    - With the wheel open, the arrow keys and WASD leave the map still, and Q and E hop on from the wheel's building.
- **The more menu:** Copy for builder, Builder card in a Claude chat, Load plan or tasks (JSON from the nullovation-city skill), Export this project, and Delete project.
- **The building:** clicking its picture opens the building panel, which picks one of the generic buildings or uploads the project's own art as a PNG or GIF, and since 0.1.46 picks its particles (Celebrations, above). Under the picture, Mirror flips the building and Download saves it as a GIF.
- **The urgency system:** chosen per project.

### The side bar

- **Top:** the logo, with the version in very small text under it. Saving that is paused or has failed (the browser, the data file, the daily backups) shows just under it with its fix, over the lists and Settings alike, and so does a Claude folder that is paused or missing.
- **Lists:** New project, which you plant on a free plot; search, which reads names, descriptions, tasks, milestones, notes, and the links' labels and addresses (addresses since 0.1.27); the starred task, while there is one (0.1.40); This week (the weekly recap), with Copy status brief, a summary of every project for a Claude chat, and Open in Claude beside it; Gus Grimsby, the Garbage Man, while the city has garbage (0.1.32); Urgent; and Due this week.
- **The foot (0.1.43):** Reports, which turns the side bar into Reports (above), and Settings, which turns it into Settings (below), side by side.

### Settings (0.1.24)

The side bar turns into Settings, and back with its arrow, so the map stays in view and shows every change as it is made. It opens from the button at the foot of the side bar, the gear on the map's bar, or the comma key; Esc closes it, after ending Edit City. On a narrow window the gear opens the drawer on Settings.
- **The header:** the title, the back arrow, and a small ? that shows the controls guide: move, zoom, status, hop, shortcuts (right-click or F), step inside (Enter), add a task (T, since 0.1.42), Reports (R, since 0.1.43), Settings (the comma key) and Esc. It leaves out moving buildings, which Edit City's bar teaches (0.1.25).
- **Tabs:** six pixel-icon tabs, City, Life, Look, Projects, Saving and Links, with the tab's name under them; arrow keys move between them.
- **Ground rules:**
  - Changes apply at once and are saved, with no toast; actions such as Export, Download palette and Test folder links keep theirs.
  - A dot marks a setting that differs from its default, and its tab.
  - Each tab has Reset to defaults, except Saving, whose data file and backups folder are connections rather than preferences. Reset all settings, at the foot, asks first. Resets never touch the projects, the map, or the parks picked in Edit City.
  - It opens again on the tab, and at the place on the page, where it was left.
  - Traffic, Bubbles and Time of day are on the bar and in Settings, with the same choices and icons, in step.
- **City:** the map's size, with the Edit City button; street props on or off, each kind on or off, How many, from a quarter to twice today's props, and Deal again.
  - How many: each prop has its own draw, so more only adds props and fewer only takes some away; none moves. Bus stops keep their pattern up to today's amount, and above it some stand off it.
  - Deal again lays the props out anew by the same rules, kept until dealt again.
  - At today's amount with no new deal, the plan is today's.
- **Life:** Traffic; who is out: cars, buses, drones, cyclists, walkers; two sliders from a quarter to twice today's counts, Street traffic (cars, buses and drones) and Walkers (people and cyclists); and Crowds round busy buildings. Walkers kept in takes the crowds too; with bus stops off, the buses drive past.
- **Look:** Time of day; Auto's hours, when night starts (19:00) and day starts (06:30), with dusk and dawn blending over the 90 minutes before each; Bubbles; Garbage (0.1.31), on or off; Ghosts (0.1.47), on or off; Motion; Postcard, the caption on or off, as on screen or doubled; and Download palette.
  - Motion: Full; Saver, at most 30 frames a second; or Still: no traffic, every building and park on its first frame, and bubbles that do not bob. Until one is chosen it follows the system: Still when the system asks for reduced motion.
- **Projects:** rest days, picked by weekday from Saturday, and away until a date (with Clear).
  - Rest days count for neither One task per N days nor Work until finished; a building's reason says so.
  - Before the away date no system turns a building yellow or red; from that day every system counts from its start. Due dates count every day, rest or away.
  - Away also stops a late task's garbage growing (0.1.31): the city keeps the days away, from the day it is set to the day you are back, and Clear ends them today.
- **Saving:** the data file; daily backups; Export and Import; and storage use: how much of about 5 MB the projects and settings take in this browser, with a bar and a warning near the limit, and what the building art and the rest take.
  - Daily backups (Chrome and Edge): a folder picked once. The first time the city is open each day, before the day's changes, it saves `nullovation-city-daily-YYYY-MM-DD.json` there and keeps the newest 14. Only files with that name are counted and pruned, so exported backups in the same folder are never touched. One tab writes, the one the data file uses. Paused or failed shows under the logo too, with Allow or Pick the folder again.
- **Links:** folder links in File Explorer, Get the setup, and Test folder links, which opens C:\Windows through a folder link; and since 0.1.28 Claude Code at work (above).
- **Where each setting lives:** what the city is like travels in the data file and every backup: crowds, who is out, the sliders, street props, Deal again, the parks picked, Auto's hours, rest days, and away until with the days away. How this computer shows it stays in this browser: the Traffic, Bubbles and Time of day buttons, the camera, folder links, the data file, the daily backups' folder, motion, the garbage and ghosts switches, and the postcard.

### Edit City (0.1.24)

Opened from Settings, City. A bar over the map shows the size, Grow, Shrink and Done, and the map frames the whole city.
- **Lines:** each side has an arrow out that adds a line of plots on that side, while the city is under 11 plots that way, and an arrow in that takes off that side's outer line, only when the line is empty and the city is over 5 plots that way. So the city can be a rectangle, 5 to 11 plots each way. The arrows follow the map, and on a city bigger than the view they stay at its edge.
- **Rings:** Grow and Shrink, as before: a ring all round, while both ways stay within 5 to 11; Shrink only when the ring is empty.
- **Parks:** pointing at a park names its kind, and a click deals the next one. The picks travel with the city, kept by their place, so a line taken off and added back brings its picks back. Round all seven, back at the kind its place deals, the pick is dropped.
- **Buildings:** a plain drag moves one, with no hold, and a click does nothing. Outside Edit City, moving stays hold then drag.
- **Everything stays with its buildings:** a line or a ring moves the grid, not the city. Each plot keeps its place in the whole city, so parks, street details, crossings and props stay beside their buildings, and the view stays on them.
- Esc, Done, closing Settings, or planting a project ends it. Q and E do not hop in it.

### The weekly recap

The recap keeps one snapshot per Saturday-to-Friday week, and you can go back to any older week.

### Copy for Claude formats

No copy carries the project's About any more (until 0.1.26 every copy ended with it). Tasks copy with Copy task; notes and milestones still say Copy for Claude.

| Copy | Opens with | Then |
|---|---|---|
| Task (Copy task) | `# Task: <title>` | Project, milestone, due date, the repeat if any, state (open, done, or ticked and coming back on a date), and the description |
| Note | `# Note: <title>` | Project, when it was written, and the note |
| Milestone | `# Milestone: <name>` | Project and progress; every open task with its due date, repeat and full description; the repeats waiting for their next date; then the done tasks as a list |
| Builder card | `# Nullovation City builder card` | Project name and size signals (open and done tasks, milestones, notes, links), description, milestones, open and done tasks. Abdurrahman may add his own idea for the building under it. |
| Status brief | `# Nullovation City status, <date>` | Every project at once |

Since 0.1.36 every copy for Claude (a task, a note, a milestone, a project's status, the status brief) ends with `REPORT_LINE`, "When you finish, send Nullovation City an update with the nullovation-city skill." The builder card does not.

### Open in Claude

Beside every copy for Claude sits Open in Claude, wearing the Claude icon (the chat icon until 0.1.26): in the task, milestone and note panels, on What is next, beside Copy status in the project view, and beside Copy status brief in the side bar. Its menu opens the Claude desktop app through the app's `claude://` links, or Claude Code in a terminal through its own `claude-cli://` link, with the same text filled in and ready to send:
- **Chat:** a new chat.
- **Cowork:** a new task, with the project's local folders and files attached. A local link whose last part has an extension counts as a file.
- **Claude Code:** a new session in the project's first local folder. Without a folder link it stays greyed out, saying it needs one.
- **Terminal (0.1.37):** Claude Code in a new terminal (Windows Terminal first, then PowerShell, then cmd) in the project's first local folder: `claude-cli://open?q=<text>&cwd=<folder>`. Its own icon, a terminal with a prompt. Without a local folder link (a network path or one with `..` does not count) it is greyed out like Claude Code. Claude Code registers the link the first time it gets a prompt in a terminal on the computer.

Nothing is sent by itself: Claude shows the text and waits. The text also goes on the clipboard, for a computer without the app. The app fills in about 14,000 characters, so a text over 13,500 opens Claude empty and stays on the clipboard to paste; the terminal link fills in at most 5,000, so Terminal does the same past 5,000. The more menu also has Builder card in a Claude chat. Esc closes the menu before anything else.

### Claude Code at work (0.1.28)

A bubble over a building while Claude Code works in one of its folders, in the terminal, VS Code, JetBrains, or the Claude app's Code tab. Claude Code on the web (cloud sessions) does not read the user settings, so it shows nothing.
- **How it works:** hooks in Claude Code's user settings (`~/.claude/settings.json`, read by every local Claude Code) run `nullovation-city-status.py` at set moments. It writes one JSON file per session into a folder; the city reads that folder every 3 seconds while its tab shows (File System Access, Chrome and Edge). Until 0.1.35 the city only read it; since then it also writes there, for Claude to read and update the city (below).
- **The bubbles:** beside the urgency bubble (or the Tasks count), the pair centred over the building.
  - Working: coral, with Claude's spark turning between two frames.
  - Waiting for you (a permission, a question, or an MCP form): coral with a ?.
  - Finished, your turn: green with a tick. It shows until you open the building's status card, or for 12 hours.
  - Failed on an API error: grey lavender with a cross, the same way.
  - Several sessions on one building show their count; the most pressing state wins: waiting, working, failed, finished.
  - No bubbles hides them, and so does the postcard; Motion on Still holds the spark still. A click on one selects its building, like the others.
- **How long:** working goes quiet after 20 minutes without an event (an interrupt with Esc tells the hooks nothing), waiting after 8 hours, and idle sessions show nothing. An ended session shows nothing either, unless it finished and then closed (its last reply is kept, since a new prompt clears it): then it keeps its tick until you look, like any finish (0.1.29).
- **The status card:** a line under the urgency: "Claude Code is working: <task>. Started 12 minutes ago.", "needs you", "finished" or "stopped on an error", and for a finish the start of Claude's reply. The task is the title of the copy from the city that started the session, else the first line of the latest prompt. Opening the card counts as seeing a finish, kept in this browser.
  - A turn Claude Code starts by itself, such as a background task's notice, arrives as a prompt in a tag (`<task-notification>`); since 0.1.34 the city leaves it out of the card, and the hook keeps it out of `ask`, `project` and `task` while still marking the session working.
- **Tick it (0.1.34):** when a session started from a city copy finishes, the finish line offers Tick it for the task the copy named, while it is still open in the copy's project (found by title, any case). One click ticks it as a tick does: done, work for urgency, "Done: <task>" in Activity, and the toast "Ticked off: <task>." With a session still working on the building, which takes the line, each finished session's task is named, "Finished: <task>", beside its own Tick it. A copy from another project, or a task renamed or done, offers nothing.
- **A line in Activity (0.1.37):** a finish leaves "Claude Code finished: <task>" in its project's Activity (the copy's task, else the prompt's first line; "Claude Code finished" alone with neither), at the time it finished, in time order, once per session and task: the entry's `ref` is `claude:<session>:<task>`. It makes the building busier for the week, as Activity does, but does not touch Updated or urgency: only a tick counts as work. Only the tab that writes the data file writes it.
- **The tab's title (0.1.37):** "(2) Nullovation City" counts the sessions waiting for you, the finishes and errors not yet seen, and Claude's changes that ask first; with none, plain "Nullovation City".
- **Which building:** the project whose folder link holds the session's working folder, the deepest when several do, in any case or slash, and from WSL (`/mnt/c/...`) or Git Bash (`/c/...`); a file link counts by its folder. Failing that, the project named on the "Project:" line of a copy from the city. A session no building claims, closed ones included (0.1.29), is listed in Settings, Links, to link its folder.
- **The setup:** `nullovation-claude-status.py`, from Settings, Links, Get the setup, embedded in the tool like the folder links setup (also `src/setup/` in the repo). Run once: a double-click, when .py files open with Python. With no arguments it asks which folder Claude Code should write to (since 0.1.30), installs, and waits for Enter before its window closes (`--no-pause` skips that); `--help` shows the usage.
  - The folder (0.1.30): a double-click opens a folder picker (tkinter; without it, a typed path, Enter keeping the shown one), starting at the folder already set, else `~/Nullovation City/Claude`. Cancel changes nothing. Running it again moves the hooks to the folder picked. `--install --folder PATH` names it without asking, and `--install` alone keeps the folder already set. Chrome cannot open folders inside AppData.
  - It copies itself to `~/.claude/hooks/nullovation-city-status.py`, makes the folder, leaves `README-nullovation-city.txt` in it saying what it is for (0.1.30), and on Windows puts the folder's path on the clipboard for the city's picker.
  - It adds 10 hooks: SessionStart, UserPromptSubmit and PostToolUse (working), PreToolUse on AskUserQuestion, PermissionRequest, and Notification on permission_prompt or elicitation_dialog (waiting), Notification on idle_prompt (idle, ending work that never reported its end), Stop (done), StopFailure (failed), SessionEnd (ended).
  - Each runs Python with no shell (`command` is the Python that ran the install, `args` the script, `hook`, the state and the folder), in the background (`async`), so it never slows Claude down. It prints nothing, so Claude reads nothing from it, and never blocks or changes anything.
  - It keeps every other setting and hook, saves the old file as `settings.json.nullovation-backup`, replaces its own hooks rather than doubling them, and refuses a settings file that is not valid JSON. `--uninstall` takes its hooks out; `--status` lists the sessions.
- **A session file** (`<session id>.json`): `app` and `kind` (`claude-session`), `session`, `state` (working, waiting, done, failed, idle, ended), `event`, `cwd`, `project` and `task` (from a copy), `ask` (the latest prompt's first line), `reply` (the start of the last reply), `entry` (Claude Code's entry point, kept but not shown), and `at`, `since` and `started` in milliseconds. A hook never overwrites a later event, swaps the file in whole, and notes failures in `hook-errors.log` in the folder. A new session clears files older than 3 days.
- **Settings, Links, Claude Code at work:** Connect the Claude folder; then the folder, when Claude Code was last heard from and what is working or waiting now, sessions no building claims, and Stop. Watching an empty folder with no README from the setup, it warns that Claude Code does not write there (0.1.30): the hooks and the city must name the same folder, and until 0.1.30 the setup picked its own without asking. Paused (the browser holding the folder back after a restart) or a missing folder shows under the logo too, with Allow them or Pick it again. Reset to defaults leaves the connection alone.

### Claude reads and updates the city (0.1.35, 0.1.36)

Both work through the Claude folder, which the city may now write in.
- **Write access (0.1.35):** connecting the Claude folder asks for read and write. A folder connected before 0.1.35 keeps its bubbles and asks once with Let it write, in Settings, Links and under the logo ("Claude cannot read the city until it may write in <folder>").
- **The summary (0.1.35):** `city/summary.json` in the Claude folder: `{ app, kind: 'city-summary', version: 1, written, about, projects: [{ name, description, deadline, folders, urgency: { system, state, reasons }, next, milestones: [{ name, open: [{ task, description, due, repeat }], waiting: [{ task, repeat, back }], done: [] }], notes: [{ title, text, written }], links: [{ label, url }] }] }`. No art, so about a tenth of the data file. Since 0.1.42 an open task that repeats has `repeat` in words, and a milestone with ticked repeats waiting lists them under `waiting`, with `back`, the day each comes back; both appear only when there is something to say. Rewritten 1.5 seconds after a change, by the tab that writes the data file; Settings says when it was last written.
- **The config file (0.1.35):** the setup writes `~/.claude/nullovation-city.json`, `{ app, kind: 'claude-folder', folder, summary, inbox }`, so the nullovation-city skill finds the city's folder from any folder; `--uninstall` removes it. The setup has to run again once to write it.
- **The inbox (0.1.36):** Claude writes a change file into `inbox/` in the Claude folder; the tab that writes the data file picks it up within 3 seconds, in name order.
  - A change file: `{ app: 'nullovation-city', kind: 'change', version: 1, project, summary, changes: [{ do, ... }] }`. `project` is the project's name, any case. The kinds: `add-tasks` (`milestone`, `tasks: [{ text, description, due }]`), `add-note` (`title`, `text`), `add-link` (`label`, `url`), `done` (`task`), `edit-description` (`task`, `description`), `replace-plan` (`plan`, as a plan file's project).
  - Applies at once, with a toast and Undo: add-tasks (into the milestone named, a new one by that name if none has it, else the current one), add-note, add-link (not one the project already has, by address). The toast: "Claude added 2 tasks, a note and 1 link in Garden planner." Undo takes back exactly what was added. Activity logs "Claude: <summary>" and "Claude wrote a note: <title>".
  - Asks first: done, edit-description, replace-plan. Done on a repeat, once applied, moves it on to its next date (0.1.42), and the card says "Tick off: X, on to its next date". They are written to `inbox/pending/`; the building's Claude bubble shows a ? (counting them with any session waiting), and its status card shows "Claude asks first: <summary>. Sent just now." with each change ("Tick off: X", "New description for X: ...", "Replace the plan: 1 milestone, 1 task. ..."), a missing task marked "(not open in this project)", and Apply and Dismiss. Apply skips what it cannot find.
  - The file then moves to `inbox/done/`, so nothing applies twice. A file it cannot read, or a project the city does not have, moves to `inbox/rejected/` with an error toast. Done and rejected files are cleared after 14 days, checked once a day.
  - `69-inbox.js` (`ClaudeInbox`) does it; the nullovation-city skill writes the files (section 5).

### Data, storage, and backups

- A browser with nothing saved starts a new city with one project: Nullovation City, on the city hall.
- Everything lives in the browser on that computer; nothing is uploaded anywhere. The database sits in localStorage under `nullovation-city:v1` (database version 3). Uploaded art and the handles of the data file and the daily backups' folder sit in IndexedDB. Another browser or device does not see any of it.
- Export makes one JSON backup with the map, the city's settings, and every project with its uploaded art. The art is stored as text, about a third bigger than the image. Import restores them all; a backup from before 0.1.24 brings default settings.
- Daily backups keep a dated copy a day in a folder of your choosing, the newest 14 (Settings, above).
- On a new device you import the data file or a backup, then connect the data file again; a first-launch prompt was decided against for now.
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
| `nullovation-city:crowds` | Crowd size before 0.1.24; read once into the city's settings |
| `nullovation-city:explorerLinks` | Folder links setting |
| `nullovation-city:motion` | Motion, when chosen |
| `nullovation-city:postcard` | The postcard's caption and size, when not the default |
| `nullovation-city:garbage` | Garbage on or off |
| `nullovation-city:ghosts` | Ghost tasks on or off (0.1.47) |
| `nullovation-city:gus` | The days Gus last spoke: the day's first open and each alarm |
| `nullovation-city:gusMin` | Gus shrunk to his face in the side bar (0.1.33) |
| `nullovation-city:celebrate` | The day each milestone last threw its party (0.1.46) |
| `nullovation-city:settings` | Settings' tab and the place on each page |
| `nullovation-city:fileWriter` | Which tab writes the data file |
| `nullovation-city:claudeSeen` | Claude Code sessions whose finish you have seen, by session |
| `nullovation-city:ui` | Interface state |
| `nullovation-city:art`, `:dataFile`, `:dataFolder` | Art and data file storage; the daily backups' folder is the `backupDir` handle in IndexedDB, and the Claude folder the `claudeDir` handle |

### Folder links in File Explorer

A web page cannot open Explorer by itself, so a one-time setup adds a `nullovation-folder:` link type for the current Windows user.

- **The setup:** `nullovation-folder-links.ps1`, from Settings, Links, Get the setup. Test folder links there checks it once it has run. Run it from a normal PowerShell window, not admin:
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
  - `src/setup/nullovation-claude-status.py`: the Claude Code at work setup and hook script, embedded in the tool.
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
| `16-backups.js` | Daily backups: the folder, the day's copy, keeping the newest 14 |
| `20-model.js` | The world grid and its place in the city, the city's settings, projects, tasks, milestones, pins and the star (`setPin`, `setStar`, `tidyMarks`), the particle kinds (`PARTICLE_KINDS`, 0.1.46), urgency with rest days and away until, plan and tasks loading, Copy for Claude texts and `REPORT_LINE` |
| `22-repeat.js` | Recurring tasks and the one-line add (0.1.42): repeats and their next dates (`nextRepeatDue`), open and waiting (`isOpenTask`, `isWaiting`, `openTasks`), ticking anywhere (`tickTask`, `untickTask`, `repeatToast`), reading a typed line (`readDateMark`, `readTaskMarks`, `readTaskLine`, `addTaskLine`) and the line under an add field (`taskLineHint`) |
| `25-generics.js` | Made by the build in memory, never on disk: the generic buildings and lots from `src/buildings` |
| `26-extra.js` | Made by the build in memory, never on disk: `APP_VERSION`, the folder links setup and the Claude Code at work setup |
| `30-pixel.js` | The city palette, the light (day, dusk, night, Auto's hours), motion, pixel icons, and the art loader |
| `35-gif.js` | The tool's GIF decoder |
| `40-map.js` | The map: geometry, streets, parks, the street props' plan and drawing, depth sorting (the ghosts among the figures), zoom, bubbles (urgency, the star and Claude Code's), the hover's count and next task, a ghost under the pointer, drop-ups, the bar's buttons, lines and rings, Edit City, the postcard |
| `45-traffic.js` | Cars, buses and their stops, drones, Claude's drones round a building Claude Code works on, people, busyness, crowds, headlights, and a street party's dancers, party drones and watching bus (0.1.46) |
| `46-ghosts.js` | Ghost tasks (0.1.47): which tasks haunt (`hauntOf`), the ghosts round their blocks, peeking, lingering, coming out and rising away, the sprite drawn in code, the hover and the card with Tick and Enter, the switch |
| `47-garbage.js` | Garbage: the points, the ceiling, the spots, the pieces drawn in code, the wind, the truck and its crew, the sparkle, the switch |
| `48-gus.js` | Gus Grimsby, the Garbage Man: his report, his lines and when he speaks, his speech bubble, his part of the side bar, his stand-in face |
| `49-celebrate.js` | Celebrations (0.1.46): the particle kinds' art, a tick's burst, a finished milestone's street party and its lights, once a day per milestone, and the Building panel's picker |
| `50-bubble.js` | The status bubble, and `markButtons`, the pin button it shares with the project view (as a chip in What is next) |
| `60-fullview.js` | The project view: tasks, milestones, notes, links, panels, local paths |
| `62-picker.js` | The building picker |
| `64-wheel.js` | The shortcut wheel a right-click on a building, or F, opens, with its Enter |
| `65-recap.js` | The weekly recap and the status brief |
| `66-quickadd.js` | The city-wide quick add on T (0.1.42) |
| `67-claude.js` | Open in Claude: its menu, and the `claude://` and `claude-cli://` links it builds |
| `68-claudework.js` | Claude Code at work: the Claude folder and writing in it, reading the session files, which project each belongs to, the card's line and Tick it, the finish lines in Activity, the tab's title, the city summary, and its part of Settings, Links |
| `69-inbox.js` | Claude's change files in the Claude folder's `inbox/`: applying at once with Undo, asking first with Apply and Dismiss, done and rejected files |
| `70-menu.js` | The side bar's lists, the starred task among them, Export and Import |
| `72-settings.js` | Settings: the panel, its tabs, dots and resets, and storage use |
| `74-reports.js` | Reports (0.1.43, 0.1.44): the counts (`taskTicks`, `weeklyTicks`, `ticksByProject`, `streakOf`, `busiestByMonth`, `milestonesFinished`), the panel and its two tabs, and R |
| `76-proxima.js` | Proxima Pace, Productivity Inspector (0.1.45): her lines (`PROXIMA_LINES`), her reports (`proximaPeriod`, `proximaReport`, `repeatRuns`, `milestonesOneLeft`), her card at the top of Reports, a report in a panel, her speech bubble after Gus, a finished milestone's announcement (0.1.46), the dot on the Reports button, her stand-in face |
| `90-boot.js` | Start-up, Esc backing out one layer at a time (Reports after Settings), and the comma key |

### Data model (database version 3)

- **Database:** `{ app: 'nullovation-city', version: 3, world: { nu, nv, ou, ov }, city, projects: [] }`.
  - `world`: the map is `nu` plots along u (down to the right on screen) by `nv` along v (down to the left), and its plot (u, v) is the city's plot (u + ou, v + ov). Before version 3 it was `{ size }`, square, at the city's origin, and older data still reads that way.
  - `city`: the city's settings, which travel with it: `crowd`; `cars`, `buses`, `drones`, `cyclists`, `walkers`; `street` and `walk` (0.25 to 2); `props`, `busstop`, `vending`, `billboard`, `bin`, `amount` (0.25 to 2) and `deal`; `night` and `day` (HH:MM); `rest` (weekdays, 0 for Sunday) and `away` (YYYY-MM-DD); `awaySpans`, the days away as `[from, back]` pairs of YYYY-MM-DD, the last 12, which a late task's garbage does not grow on (0.1.31); and `parks`, the kinds picked in Edit City, by the city's plot as `"U,V"`. Defaults are `CITY_DEFAULTS` in `20-model.js`.
- **Project:**
  - identity: `id`, `name`, `description`, `deadline`, `progressOverride`;
  - marks (0.1.39): `pin`, the id of the task pinned as next, and `star`, the id of the city's starred task, each empty when unset; at most one project in the city has a `star`;
  - content: `todos`, `links`, `milestones`, `notes`;
  - placement and art: `plot: { u, v }`, `art: { has, includesPlot }`, `generic` (a generic building's id, or null), `flip`, `particles` (one of `PARTICLE_IDS`, 0.1.46; stars when missing);
  - history: `activity`, the log that busyness reads: `{ at, text }`, and `ref` on Claude Code's finish lines (0.1.37), which keeps each from being written twice;
  - urgency: `urgency: { system: 'none' | 'finish' | 'pace', days, lastWorked, pickedAt }`;
  - timestamps: `createdAt`, `updatedAt`.
- **Task:** `{ id, text, description, done, doneAt, due, milestoneId }`, with dates as YYYY-MM-DD; since 0.1.42 also `repeat`, when it repeats, and `waiting: true` while a ticked repeat waits for its due date (section 2, Recurring tasks and one-line adding).
- **Note:** a `title`, `text`, and `at` timestamp.
- **Link:** `{ id, label, url, icon, shortcut }`; `icon` is one of `LINK_ICONS`, and `shortcut` is true unless turned off. `MAX_SHORTCUTS` (8) is how many a wheel shows.
- **Constants:** `WORLD = { NU, NV, OU, OV, S: 4, GAP: 2, MARGIN: 2, TW: 32, TH: 16, MIN_N: 5, MAX_N: 11 }`, set from `world` by `setWorld`.

### Build

`build.py` does the following:
- concatenates the modules, CSS, and body;
- embeds the fonts;
- makes `25-generics.js` in memory from `src/buildings/meta.json`, `lots.json`, `props.json` and the GIFs and prop PNGs (`prop-<id>-front.png` and `-back.png`); it refuses a prop whose `faces` in `props.json` is not `se` or `sw`;
- makes `26-extra.js` in memory with `APP_VERSION` from `src/VERSION` and the two setup scripts (`FOLDER_SETUP_PS1`, `CLAUDE_SETUP_PY`);
- writes nothing into `src/`;
- replaces `{{VERSION}}` in the body;
- writes one self-contained HTML file: `index.html` at the root, unless given a path;
- finds the source from its own location, so it runs from any folder;
- writes UTF-8 with LF line ends, so a build on Windows is byte-identical to one in a chat.

### Tests

There are 30 passes and 1390 checks, all passing at 0.1.47. `python3 tests/run_tests.py` runs them all, and `python3 tests/run_tests.py 9 16` runs passes by number. Each browser pass runs Chrome through Playwright, prints PASS or FAIL lines and console errors, and can run alone, for example `python3 tests/test09_urgency.py`. The coverage:
- **test02_map:** zoom and the map.
- **test04_seed_data:** the data version (3), the map and the city's settings in the data file, Grow and Shrink in Edit City, and the real start: a browser with nothing saved gets one project, Nullovation City.
- **test05_bubble_art and test08_bubble_tasks:** the status bubble.
- **test06_generics:** the generic buildings decoding, and the seven park kinds: all decoded at 256 by 128, the new ones animated in 40 frames, and no park repeating its neighbor.
- **test07_project_view:** activity and the project view.
- **test09_urgency:** urgency, the bubbles, the bubbles menu, and postcards.
- **test10_sidebar:** the side bar: urgent, due this week, the week with the status brief beside it, the controls that moved into Settings, and the order of it all.
- **test11_load_plan:** loading plans and tasks.
- **test12_folder_links:** folder links.
- **test13_traffic:** traffic and crowds; the people's facing, looks and their shares, runners, kids and dogs, the cyclists, and the glow by night.
- **test14_data_file:** the data file.
- **test15_notes_milestones:** copy for notes and the milestone view.
- **test16_dropups:** the drop-ups, the Tasks view, and dusk.
- **test17_source:** the source travels: no chat paths in the scripts; the layout (only `build.py` at the root, nothing written into `src/`, git leaving out what runs make, no `dist/`, `.nojekyll` in place, nothing of the decision wizard in the tool or its tests); `index.html` matching a fresh build; what the archive holds and leaves out; a byte-identical build from a copy in another folder; and applying archives safely. It needs no browser.
- **test18_open_in_claude:** Open in Claude: the menu in every place, the links for Chat, Cowork, Claude Code and Terminal with folders and files, Arabic text, a text over each limit, the builder card, the status brief, and closing with Esc or a click elsewhere. It saves `tests/shots/oc-5-terminal.png`.
- **test19_street_props:** the street props: all four decoded front and back; at most two to a side; every one on its sidewalk; facing: each prop's `faces`, every prop as drawn facing its own street, and, measured on the art (the slope of its top edge), every bus stop, billboard and vending machine front standing with its long side along its street; bus stops by the pattern, vending machines mid-block, billboards by a corner, bins on a building's front sides; none on a zebra's landing; planting a building only adds its bins; drawn with the traffic off; the same after a reload; people in front or behind by depth; a bus pausing at a stop on its side and driving past one on the far side; the night colors and the neon. It saves close-ups at 4x of a bus stop and a billboard on each side, `tests/shots/191-*.png`, to look at.
- **test20_settings:** the panel: its three ways in and Esc, the six tabs, today's controls in their new places, the bar and Settings in step, no toast for a change while actions keep theirs, the dots, Reset to defaults and Reset all settings, reopening at the same tab and place, and the gear on a narrow window. It saves every tab, `tests/shots/200-settings-*.png`.
- **test21_city_settings:** the settings: who is out and both sliders, the 150 ceiling on 11 by 11, the crowds; street props by kind, How many (none moving) and Deal again; Auto's hours; Still and Saver; the postcard's caption and size; rest days and away until against fixed dates; Test folder links; daily backups in a folder held in memory (the day's copy, the newest 14, exported backups untouched, paused and Allow); storage use; and what a backup carries, imported into a fresh browser, with older backups bringing defaults.
- **test23_links:** the link icons and the icon an address picks, old Task and Design links picking again, the About with the description first, Copy task, the Claude icon on Open in Claude, the add panel (address over label, wider, Add to shortcuts on), the warning past 8 while adding and editing, the Shortcut switch, dragging a link by its grip and the arrow keys, copies without the About, and the wheel: its shortcuts in order and at most 8, the empty middle, its places in view without overlaps, closing by click, Esc and a click elsewhere, the arrow keys, the empty wheel, and none on a park or in Edit City. Since 0.1.27 also the suggested labels and `addressKey`, the same address twice, pasting an address (and not text, nor into a field), Undo for a deleted link, search by address, and on the wheel: Enter (the button and the key), the bubble and the wheel closing each other, F, hopping on from the wheel, the arrows leaving the map still, three-word labels whole and apart with 1 to 8 shortcuts, staying in view at the map's corner, and the controls guide. It saves `tests/shots/230-*.png` to `236-*.png`.
- **test24_claude_work:** the setup script run as Claude Code would, in a home folder made for the test: install (a hook per event and state, in the background, as Python with no shell, every other setting and hook kept, the old file saved, twice changes nothing, a broken settings file refused, `--folder`), every hook event's state (the copy's project and task, the ask, the reply, idle only ending work, a later event never overwritten, a bad event or session id), the 3-day clearing, `--status` and `--uninstall`. Then the city with a Claude folder held in memory: Get the setup and the embedded copy, connecting, a bubble without a reload and the spark turning, which building each session lands on (case and slashes, WSL, the deepest folder, a file link, the Project line, none), counts, waiting, quiet after 20 minutes, ended and idle, the tick beside a red bubble, the card's lines and seeing a finish, failed, No bubbles, Tasks, Still, seen after a reload, paused and Allow, a missing folder, Reset and Stop. Since 0.1.34 to 0.1.37 also: the tag prompt, Tick it and the cases that offer none, the config file, the summary and its update, Let it write, the inbox (at once and Undo, asking first with Apply and Dismiss, rejected files), the copy line, the finish lines in Activity (once, in time order, not as work, kept through a reload), the tab's title, and Claude's drones (six setting off, flying in, working close by at different heights, the drones setting, flying off and gone). Since 0.1.42 also Claude's done on a repeat, applied, moving it on to its next date. It saves `tests/shots/240-*.png` to `249-*.png`.
- **test22_edit_city:** lines on every side and rings, on and off again, keeping every park, crossing mark, prop, building and the ground's pixels in place; rectangles from 5 to 11; a line with a building on it staying; park picks kept by place; and Edit City itself: the arrows and when they show, framing the city and keeping the arrows in reach on 11 by 11, cycling a park, dragging a building, Grow and Shrink, and the ways out. It saves `tests/shots/220-*.png` to `224-*.png`.
- **test25_garbage:** the points (pace yellow and red by period, work until finished by day and its yellow adding nothing, late tasks by day, both together, rest days, away, and the days away with their spans set, moved and cleared in Settings, saved and read with care); the 1,000 ceiling and its shares; the 1,000 spots, their kinds, the front strip first, the lift onto the plot, the park, and the same after a reload; drawn by day and by night, the can's glint at night; the switch (kept, with a dot, clean pixels, after a reload, Reset); the postcard with and without, and the project view's picture; nothing in the status card or the brief; Edit City; Still; the truck from the map's edge with a crew of three spread round the block, the sparkle, a partial drop, at most 3 trucks, Traffic off; the city's own garbage on load with no truck, and ticking a task off. It saves `tests/shots/250-*.png` to `254-*.png`.
- **test26_garbage_man:** Gus away while the city is clean and his place between This week and Urgent; the report line in every approved case (one late task, one project two periods behind, three one period behind, Work until finished, all three at once), overdue tasks only, never urgent or attention; the rows, most garbage first, "finish any task" for a building behind its pace; the task to start with, a late task counting its project's pace too, and a long title cut short; his count of tasks; never pieces; his lines and their blanks (singular, "any task in", a capital at a sentence's start); a click on a row; the first open of the day and not the second; the speech bubble's place, its close button and going by itself; the alarms at 50 and 200, once a day, the worst only, kept in this browser; the clean city and stepping away; and the Garbage switch. Since 0.1.33 also his [-]: shrunk to his face with a ! and nothing else, the focus moving, his place kept, staying shrunk as the report changes and after a reload, his speech bubble still showing, and a click on the face opening him again. It saves `tests/shots/260-gus-says.png`, `261-gus-side.png` and `262-gus-min.png`.
- **test27_tasks_map (0.1.39 to 0.1.41):** Tasks on the map. Pins and the star in the model: one pin per project, the next task and the card's order, not work, ticking clears for good, unpinning, starring pins too, one star in the city and moving it with its toast, the two separate, deleting, reading a city (one star, no pin on a done or missing task), a reload, a backup, and the project's status. The hover: none before 250 ms, the white count and the next task after, the line's place, leaving, the bubbles already there staying put with the count on their left, the Tasks view, No bubbles, a long title cut at 40, a pinned task with its pin, a city with nothing open, the selected building and Edit City. The star with Bubbles, Red only, Tasks and No bubbles, and ticking it off. The card's pins (hidden until pointed at, pinning moves the row first, pressed, the focus kept) and no star in it; the star's gold; the side bar's starred task (what it shows, purple with a gold edge, under search, following the star, a click opening the task, going when unstarred, ticked or deleted); the project view's What is next (the Pinned chip, Starred and no star button, purple with a gold edge while starred and its own shade otherwise, the pinned task's milestone, unpinning with the focus kept, layout B's order, nothing without a due date, the due chip's text and place for 4 days, tomorrow and overdue, the actions on one row), a row's pin (not opening or dragging the task) and no row with a star, the task panel's Pin as next and Star for the city, Esc leaving them, and a done task having none. It saves `tests/shots/270-hover.png` to `277-next-overdue.png`.
- **test28_repeats (0.1.42):** Recurring tasks and one-line adding. The model: every schedule read back whole and a broken one dropped, each in words; the next date by schedule for every day, every 7 days (from the tick, late ones too), weekly on Monday and Thursday (on time, late and skipping, early), monthly on the 31st, a monthly repeat two months late, yearly on 29 February; a new repeat's first date. Ticking: one task moving on, waiting, the Done line and work; gone from the open tasks, the card, What is next and the counts; a pinned repeat's pin clearing; Copy task, the project's status, a milestone's copy and the city summary; Work until finished with only a waiting repeat; the card's line; back on its day and no longer waiting; a missed repeat overdue with its garbage, ticked late, and unticked. Reading saved data, a backup, and a project export as a plan. The marks: every date mark against a fixed Monday, and those that are not; every repeat mark; words left alone; /name only in the quick add; an Arabic title; @ and /name matching, a new milestone, and each problem. The status card's field (the line under it, adding, staying focused, a plain line, marks alone, Esc, a redraw), ticking a repeat there with its toast and Undo; the project view's field (the line, its milestone, @ to another, the focus), a repeat's row, ticking it to a waiting row with no pin and out of Due this week; the task panel (a waiting repeat, a nearer date and Esc, every schedule, the weekday buttons, Esc undoing a repeat, ticking in the panel and the Done line once, No repeat); What is next with only a waiting repeat; and the quick add on T (no project, /garden, Enter and Open, the open project view, T in a field, a selected building, Esc, a click elsewhere, the controls guide). It saves `tests/shots/280-card-add.png` to `284-quick-add.png`.
- **test29_reports (0.1.43, 0.1.44):** Reports. The counts, on made-up projects and a fixed Monday: every Done line a tick and a repeat each time, a Reopened line taking one back, a done task once, one whose Done line is gone by its day, finish lines and added or removed tasks never; the 12 weeks, Saturday to Friday, and each week's count; by project for a week and a month; the streak (today included, today not breaking it, a gap breaking it, the longest with its days, a rest day passed over and a tick on one counting, days away and the day back, none, a day off today); the busiest building of each month, empty months left out, ties shared, an empty month; milestones finished with their dates, empty ones and those with a repeat never. The panel: the Reports button beside Settings with Settings still at the bottom, the side bar turning into Reports with the map at its size, the header, two named tabs and no review left in the tool (0.1.44), the arrow keys, the back arrow and the focus, R, Esc, R again, R in a field, Reports and Settings closing each other, and R in the controls guide. Weeks: twelve bars with their counts, this week last as so far, the tallest bar, the sum line, By project on this week, a bar picking its week with the focus kept, the arrows, Month, no bar pressed on a month, the month before and the first month's limit, back to Week, and a row selecting its building. Records: the streak and today's line, the longest, the rest days note, the busiest building with its picture and the months before, no milestone, ten milestones newest first with dates and projects, Show all, and a click opening the project. Then a tick on the map redrawing the open tab, nothing new in the data, the tab kept after a reload, a browser last left on 0.1.43's Review opening on Weeks, and on a narrow window R opening the drawer on Reports with nothing past its edge. It saves `tests/shots/290-reports-weeks.png` and `291-reports-records.png`.
- **test30_inspector (0.1.45):** Proxima Pace. Her lines word for word (V2). Her reports on a fixed Monday: the daily one on yesterday, the weekly on the last full week, the monthly on the last month, each with the period before and after; a count of one in the singular; tasks finished against the period before; the streak and the longest; milestones finished in the period; what is due ahead from today on, a repeat coming back included and late tasks not; the daily report without buildings, overdue, repeats or notes; by building, the busiest, buildings with nothing finished, and overdue, weekly and monthly; repeats and notes, monthly only; her three facts where they belong; each moment's line, filled, and the same line for the same report; a quiet week and a quiet month; no report on a period before the city started; a repeat run of less than 3 weeks and a milestone with a repeat or a single task never counted. Then in the city: a new city with no report, no dot and no bubble; her card above the tabs with her name, title and face, and "Her first report comes tomorrow."; with a history, the dot on the Reports button; the weekly report brought in her bubble, the monthly waiting, the daily never speaking, each said once; giving way to Gus and waiting for him, then saying hers; Read opening Reports and the report, with her line and the week, its sections, the overdue task to close first, and nothing said over an open report; the monthly one after, the close button, the dot kept on a report closed unread; three tiles; the monthly and daily reports' sections; no dots once all are read; a building in a report going to the map; nothing said again after a reload; both brought on a fresh visit, the bubble going by itself, the daily waiting unread; and her card in the drawer on a narrow window. It saves `tests/shots/300-proxima-says.png` to `304-proxima-narrow.png`.
- **test31_celebrations (0.1.46):** Celebrations. The twelve kinds and their names, each drawn in its colors with the dark outline at the people's size; stars for every building and a new one; a kind the tool does not have read as stars. A tick's burst: 16 particles at its building, on the map in its colors, over after 1.5 seconds, a burst for every tick, nothing on unticking, the building's own kind, its colors at night, nothing on Still; from the status card and the project view, and in the project view's picture. The picker: Particles with a tile per kind, in order and named, the kind in use pressed, a tile playing its burst while pointed at and resting after, a click picking it and playing it on the map, not work, in a backup and after a reload. The party: none while a task is open, a 4-task milestone's last tick throwing it for 30 seconds, Proxima's line (one of the two, filled in, word for word) and Go to it, six drones in the particles' color, about 20 dancing, the bus heading over and waiting at the block's curb with the block on its right, twelve light strings, bursts every 2 seconds, the dance frame, Go to it bringing the building to the middle, once a day, and the end (no one dancing, the drones and guests off, the lights down, the bus on). A one-task milestone and one with a repeat never party; she waits for an open panel and says two milestones in turn; her bubble beside the project view; the traffic off; Still. It saves `tests/shots/310-burst.png` to `314-proxima-beside-view.png`.
- **test32_ghosts (0.1.47):** Ghost tasks. Which tasks haunt: none in a clean city; every overdue task, the most overdue first; red, the bubble's color; a task due today or tomorrow not until it is late; behind its pace with overdue tasks, one ghost each, and a pinned next task not overdue getting its own; not behind its pace, no pin; one period behind, its next task in yellow; two, red; rest days pausing the pace; away keeping a task late before it; Work until finished with no tick for a day, and a tick in the last day; a waiting repeat never; seven overdue making five ghosts, the five most overdue, and a tick letting the sixth out of its building's front. On their rounds when the city opens; each on the sidewalk ring 0.15 tiles out from its lot; creeping at about half walking speed, never off its block; stopping at a corner, leaning round with its eyes on the new side, and carrying on; the eyes, two of 1 by 2, to the side and up or down the way it goes. The art: 9 by 12, see-through inside its edge, red or yellow, three hem frames; on the map in its red by day and the same red at night. The hover's tip and no building hovered; a click opening its card over it, the tip making way, the status card closing and the ghost holding still; its project, task, due chip, Tick and Enter; Esc, a click elsewhere and a building's status card closing it; Tick (done, the Done line, the toast with Undo, the ghost rising and fading and gone in about a second, Undo bringing it back out of its building); a tick from elsewhere and a new due date laying it to rest; Enter stepping inside with the task open; the project view's picture showing it; a repeat ticked from its card moving on. Traffic off and No bubbles leaving them; the switch in Settings, Look (on by default, off clearing the map, the dot, kept on this computer and after a reload, Reset to defaults); back on their rounds after a reload; Still and Edit City hiding them, and back on their rounds after Still; the postcard showing them; its building moved; nothing saved in the city. It saves `tests/shots/320-ghost-day.png` to `324-ghosts-city-night.png`.

Every browser pass but test14_data_file starts from the test city in `tests/testkit.py`, written into the browser before the page first loads: the starter project as it was at 0.1.16, plus a made-up second project, Garden planner, on the research lab. So the passes do not depend on what a new city starts with. It is written once per tab and never on a reload. test14_data_file needs no projects and goes without it: with an init script in its browser context, its two-tab checks failed about one run in three.

On Windows, Chrome hands clipboard text back with `\r\n` line ends, so test15 and test18 turn them back into `\n` before comparing; the copies themselves are unchanged. The headless test browser sometimes loses a page's stored writes on reload. test09_urgency and test16_dropups detect it, print a NOTE, set the value again, and retry. The real tool is not affected. In test13_traffic, the car the stop-line probe or the zebra probe sets down can be held back by another car close ahead in its lane, as it should be; the probe then prints a NOTE and tries another car and line (the zebra probe since 0.1.26, after it failed once that way). In one full run at 0.1.44, test25_garbage's crew check saw no crew while it sampled, and passed when run again alone; nothing in the garbage had changed.

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
  - Facing: a prop faces the street it stands on. A front faces one of the two near streets as drawn, and its back the opposite one; mirrored, a view faces the other street on the same side of the camera. So look at which way a new front faces and write it in `src/buildings/props.json` as `faces`, `se` or `sw`: the bus stop's and billboard's face the south-east street, the vending machine's and bin's the south-west. A flat prop's long side runs along the street it faces, so its top edge rising to the right means `se`. The tool mirrors each view on the side it does not face.
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
  - **Four sides from two images:** the front faces the south-west street. Mirrored, it faces the south-east street. The back serves the north-east side, and mirrored, the north-west side. (This held only for the vending machine and the round bin. The bus stop's and billboard's fronts face the south-east street, so at 0.1.22 they stood sideways on every side; fixed at 0.1.23 with `faces` in `props.json`.)
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

- **`nullovation-city`** writes a tasks file or a whole plan as JSON, loaded in the tool with Load plan or tasks, or (0.1.36) sends an update straight into the city's inbox from Claude Code. Only what you know: it never invents tasks. A validator lives in its `scripts/check_plan.py`, which checks change files too.
  - Updates: it fires on "update the city" and on a copy ending with the copy line; finds the city's folder in `~/.claude/nullovation-city.json`, else in the hooks in `~/.claude/settings.json`, else falls back to a tasks file or a plan; reads `city/summary.json` for exact project and task names; writes the change file (section 2, Claude reads and updates the city) as `inbox/<YYYY-MM-DD-HHMM>-<project>.json`. Changed at 0.1.36, so the claude.ai plugin needs it reinstalled.
  - Tasks file: `{ app: 'nullovation-city', kind: 'tasks', version, milestone, tasks: [{ text, description }] }`. The tasks join a milestone chosen on loading, and nothing is replaced.
  - Plan file: `{ app: 'nullovation-city', kind: 'plan', version, project: { name, description, milestones: [{ name, tasks: [{ text, description }] }], ideas: [{ title, text }], links: [] } }`. It replaces the description, milestones, and tasks, with a warning first.
  - A link's icon is one of doc, code, github, claude, chat, folder or web (Task and Design went at 0.1.26); any other is picked from the address. Loaded links are shortcuts. The skill says a copied task carries no About, so a description has to stand on its own. Changed at 0.1.26, so the claude.ai plugin needs it reinstalled.
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

- **Status (changed 5 October 2026, then 12 October 2026):** buildings show no status, progress or stage, and bubbles carry status. Dirt on red, decided on 5 October and delayed, was dropped on 12 October for the garbage system (below), which lies on the ground round a building, never on it.
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
- **Street props (October 2026):** designed in one wizard round (`wizard-rounds/2026-10-06-street-props-round1.json`, one folder up from the source) and built at 0.1.22 (section 2, Street props). The art recipe is in section 4, PixelLab workflow. The design:
  - **Where they stand:** on the sidewalk, pushed back over the plot's rim, since every prop is wider than the 5 px sidewalk.
  - **Facing:** a prop faces the street it stands on; faces show on a block's south and east sides, backs on its north and west sides. The code names sides by the screen's diagonals: the south side is `sw` (lower left on screen), east `se` (lower right), north `ne` (upper right) and west `nw` (upper left).
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

- **Settings and Edit City (7 October 2026, two wizard rounds: `wizard-rounds/2026-10-07-settings-round1.json` and `-round2.json`, answered in `nullovation-city-settings-round-1-answers-2026-10-08.json` and `-round-2-answers-2026-10-08.json`, one folder up from the source). Built at 0.1.24; section 2, Settings and Edit City.**
  - **The panel:** opens from both a Settings button at the bottom of the side bar and a gear on the bottom bar (P1); the side bar turns into Settings, with a back arrow (P2); tabs (P3).
  - **Today's controls (P4):** Map size, crowds, folder links, Download palette, Export and Import, and the data file move into Settings; the Controls guide moves behind a small ? in the header; Copy status brief with Open in Claude stays outside, beside This week; Traffic, Bubbles and Time of day are in both places, in sync.
    - Map size: Abdurrahman asked for Edit City, which shows the old Grow and Shrink, an arrow on each side adding a line in that direction, and a click on a park cycling its kind.
  - **Ground rules (P5, all approved):** changes apply at once with no Save button; Reset to defaults per tab, and Reset all settings at the bottom behind a confirm, settings only; a dot on a setting that differs from its default; the comma key opens and closes Settings; no toast per change, while actions keep theirs; it reopens where it was left. Taken as given: Esc closes it; a setting with a bar button shares its choices and icons and stays in sync.
  - **Where settings live (S1):** the split. The city travels in the data file and backups: map size, crowds, who is out, amounts, street props, parks, Auto's hours, rest days, away until. The computer keeps the rest: the view buttons, the camera, folder links, the data file, the daily backups folder, motion.
  - **Now:** who is out (C1); amounts, as sliders to play with (C1); street props on or off and by kind, with an amount or distribution setting (C1), which became both a slider and Deal again (R1); parks, through Edit City (V1); the postcard's caption and size (V1); Auto's hours you set (V2); rest days and away until (U1); daily backups and storage use (D1); Test folder links (L1); motion (I1).
  - **Edit City (round 2):** an arrow out and an arrow in on each side, the arrow in only when the line is empty and the side longer than 5 plots (E1); in Edit City a building moves with a plain drag and a click does nothing (E2).
  - **The tabs (T1, all approved):** City (the map, Edit City, street props), Life (Traffic, who is out, the two sliders, crowds), Look (Time of day with Auto's hours, Bubbles, Motion, Postcard, Download palette), Projects (rest days, away until), Saving (the data file, daily backups, Export and Import, storage use), Links (folder links, Get the setup, Test folder links).
  - **Opening the city on a new computer (D2):** kept manual: a new browser starts a fresh city, and you import from Settings.
  - **Later:** the leader speech bubbles switch, with the leaders; a bin for deleted projects; Open in Claude options and desktop notifications, which would join the Links tab; interface size.
  - **Left out:** quiet nights, city moods, name labels, a default urgency for new projects, a calendar file, a theme, sound, and an Arabic interface.
  - **Reasoned while building (not asked in the rounds):**
    - Adding or taking off a line or a ring keeps the parks, street marks and props with their buildings, which Grow did not: it shifted every plot and dealt everything again by grid position. The map now keeps an origin, so each plot has its place in the whole city, and everything is dealt by that place.
      - Parks: round the origin each plot checks its neighbors nearer the origin, so no two neighbors share a kind and a park never depends on where the edge is. Today's cities keep every park.
      - Streets: the ring road deals its own marking too, unused, so a street that stops or starts being the ring road keeps its sidewalks. At the upgrade the ring road's sidewalks and verges, the asphalt grain and the grass under the parks were dealt once more; every park, prop and crossing mark stayed.
    - The sliders run from a quarter to twice today's counts in quarter steps, the props' slider too. Walkers off takes the crowds with them; at twice on a big map the walkers stay under the city's 150 people, and the crowds use what room is left.
    - How many props: each has its own draw, so the slider adds or takes away without moving any; a kind turned off only takes that kind away. At today's amount with no new deal, the plan is today's.
    - The park picks travel with the city, kept by their place, and no reset touches them: they are the city's layout, like the buildings' places. Back at the kind its place deals, a pick is dropped.
    - Motion follows the system's reduced motion setting until one is chosen; Still stops the traffic, holds every building and park on its first frame, and stops the bubbles bobbing. The postcard's options stay on the computer, like the view buttons.
    - Rest days and away until pause only the urgency systems; due dates count every day. From the away date every system counts from its start.
    - Daily backups: the copy is taken the first time the city is open each day, before the day's changes, and named `nullovation-city-daily-YYYY-MM-DD.json`, so pruning never touches exported backups, which are named `nullovation-city-backup-YYYY-MM-DD.json`.
    - The Saving tab has no Reset to defaults: the data file and the backups folder are connections, not preferences.
    - Paused or failed saving shows under the logo, so it stays in view over the lists and over Settings.
    - Edit City lives in Settings: closing Settings ends it, and Esc leaves Edit City first. It frames the whole city when it opens, and on a city bigger than the view its arrows stay at the view's edge.
    - The controls guide adds the comma key and Esc. At 0.1.25 Abdurrahman had Rearrange taken out of it: it read as if moving worked anywhere, and Edit City's bar teaches it.

- **Links (8 October 2026, Abdurrahman's task "Links, links, links" in Nullovation City Hall, Quick Wins). Built at 0.1.26; section 2, The project view.**
  - **Asked for:** Copy for Claude becomes Copy task; the add link panel larger, with the link and the label on two lines; the Task and Design icons out, Claude and GitHub in; Add to shortcuts, on by default; a right-click on a building opens a wheel like the Sims' pie menu with its links as shortcuts, the middle empty for the leader's face later, at most 8, with a warning when more are allowed; Open in Claude with a Claude icon, not the chat one; copies without the About part; links dragged to reorder while editing; and the About with the description before What is next.
  - **Reasoned while building:**
    - Copy task renames the copy of a task, in its panel and under What is next. Notes and milestones keep Copy for Claude.
    - The About is gone from every copy that had it: tasks, notes and milestones. Project status copies never carried it.
    - Open in Claude is one button everywhere, so it wears the Claude icon everywhere, not only in the task panel. Its menu's Chat item keeps the chat icon.
    - Past 8 shortcuts the switch still turns on, and a note says only the first 8 in the list show; dragging the links chooses which.
    - The wheel shows only links that can be opened. Its first shortcut sits at the top, the rest clockwise. The building's name sits above it. It opens nothing on a park, while planting or moving, or in Edit City, and it does not select the building.
    - Links saved with Task or Design get an icon picked from their address; loaded plan links become shortcuts too.
    - While editing, a link row has the address over the label, as the add panel does, with its Shortcut switch under them.

- **Links, round 1 (8 October 2026, `wizard-rounds/2026-10-08-links-qol-round1.json`, one folder up from the source, answered in the same file). Built at 0.1.27; section 2, The project view.**
  - **Asked for with the answers:** the wheel's buttons larger, fitting about three normal-length words.
  - **Now:** paste to add, a label from the address, the same address twice (A1); a key for the wheel, F, and search by address (B1); Enter on the wheel (C1); Undo a deleted link (D1).
    - With Enter, Abdurrahman asked for the Enter key to open the project, and for the bubble and the wheel to close each other.
  - **Later:** press, move, release on the wheel (B1).
  - **Left out:** dropping an address on a building, several links at once (A1); number keys in the wheel, shortcuts in the status bubble, a list of every link in the city (B1); Add link, Open in Claude and Copy status on the wheel (C1); editing one link alone, last opened and most used, a note per link, site icons (D1); a home folder, links on a task, links in Copy status (E1).
  - **Reasoned while building:**
    - The Enter key steps inside the building whose wheel is open, and, with no wheel, the selected building, when no button or link has the focus. The wheel opens with nothing picked, so Enter steps inside until the arrows pick a shortcut.
    - A right-click closes the bubble by ending the selection, as the bubble's close does. With the project view showing the selected project, its bubble is already hidden, so the selection stays.
    - A link left without a label stays empty and shows the suggested name wherever it shows, so the placeholder is what you get, and nothing already saved is rewritten.
    - Paste to add takes one line starting with a scheme and //, mailto:, www., or a Windows path; a bare word with a dot is too often not an address.
    - Undo restores a deleted link to its place, after Done too, and never doubles one that Esc already brought back.
    - With the wheel open, the map ignores the arrow keys and WASD; until 0.1.27 the arrows moved the map under the wheel as they moved between its shortcuts.

- **Connecting to local Claude (9 October 2026, Abdurrahman's task "Design in details, connecting to local Claude" in Nullovation City Hall, Quick Wins). The plan went to `wizard-rounds/2026-10-09-local-claude-round1.json`, one folder up from the source; its first piece, Claude Code at work, is built at 0.1.28 (section 2).**
  - **Asked for:** design in detail what Open in Claude can do to make work faster, not cosmetics; and a building that looks like it is working while Claude works on it, until Claude finishes, with a solution for Claude, Cowork, Claude Code and Claude Code in the terminal; then pick the simplest thing and build it alone.
  - **What each surface allows (checked in Anthropic's docs, 9 October 2026):**
    - Claude Code, in the terminal, VS Code, JetBrains and the Claude app's Code tab, reads hooks from `~/.claude/settings.json`; cloud sessions do not. Stop fires when Claude finishes a reply but not on an interrupt; StopFailure on an API error; PermissionRequest and the permission_prompt notification when it waits for you.
    - Cowork and chat are merging into one Claude (announced 16 September 2026, rolling out over weeks). Plugin hooks are documented to load in Cowork and to be ignored in Chat; Cowork's remote sessions run on Anthropic's servers.
    - A chat can reach this PC only through a local MCP server Claude chooses to call.
    - The desktop app's links prefill only, never send: `claude://claude.ai/new`, `claude://claude.ai/chat/<id>`, `claude://claude.ai/project/<id>`, `claude://code/new` (`q` or `prompt`, the first `folder`) and `claude://cowork/new` (`q`, `folder` and `file`, repeated); a folder in a link asks for confirmation every time. Claude Code's own `claude-cli://open?q=&cwd=` opens a terminal (Windows Terminal first), with `q` up to 5,000 characters. No documented link resumes a session.
  - **The pick:** Claude Code's hooks, the only surface with a signal that is always right, covering three of the four surfaces with one setup; the folder, the matching and the bubble are what the others would reuse.
  - **Reasoned while building:**
    - The hooks write files and the city reads them, rather than a local server: nothing keeps running, and the city already reads folders.
    - Python with no shell (exec form), from the Python that ran the install: no quoting of Windows paths, the same under Git Bash or PowerShell. In the background, so Claude never waits for them.
    - Working goes quiet after 20 minutes without an event, since an interrupt reports nothing; the idle notice, about a minute after Claude stops, ends a stretch of work that never reported its end.
    - A finish shows until you open the card, since "Claude finished" is news until you have seen it; working shows all the time it lasts.
    - The Claude bubble sits beside the urgency bubble, never over it, and hides with No bubbles like the rest.
    - The folder is `~/Nullovation City/Claude`, not under AppData, which Chrome will not open.
    - The card's line takes the copy's task title, kept for the session, so a short follow-up such as "yes" does not replace it.

- **Even better Claude connections (13 October 2026, Abdurrahman's task "Even better Claude connections" in Nullovation City Hall, Quick Wins: "Connecting to claude proved to be amazing. plan the next connection and working with claude with d-wizard." One round, `2026-10-13-claude-connections-round1.json`, delivered in the chat, replacing the unanswered `2026-10-09-local-claude-round1.json`; answered 14 October). Built at 0.1.34 to 0.1.37; section 2, Claude Code at work and Claude reads and updates the city.**
  - **A1, what Claude may change and how:** applies at once (with Undo): add-tasks, add-note, add-link. Asks first: done, edit-description, replace-plan.
  - **A2, how a session knows to report:** from the copy: a line at the end of every copy for Claude.
  - **A3, how Claude reads the city:** a summary for Claude, written by the city.
  - **B1, the task a city copy started:** offer to tick it (Tick it on the finish line). Comment: "There will be a task master, that only work with claude, showing where currently the garbage man shows, offering to tick tasks from there."
  - **B2, a finish and urgency:** only ticked tasks count.
  - **B3, more ways to see Claude at work:** Activity line, now. A crowd while it works, now: "Just drones coming and moving around that building, maybe like 6 drones." The side list, now: "We need a Claude character with a Claude mascot." The tab's title count, now. A Windows notification, later: "give me a block to paste this task into the building please" (given in the chat as a tasks file).
  - **C1, tracking Cowork:** the plugin hook test. **C2, tracking chats:** leave untracked: "lets see if I will need this later or not".
  - **D1, Open in Claude faster:** Claude Code in the terminal, now. Later: one click ("I am not sure about the UX of this."), next task to Claude, continue a session, chat links.
  - **E1, build order:** Tick it on the finish line, Claude reads the city, Claude updates the city, Open in Claude faster, new places to see Claude's work, the Cowork tracking test.
  - **Reasoned while building:**
    - The summary and the inbox live in the Claude folder the hooks already write to, so the skill finds both through one config file, and nothing new runs.
    - One tab takes inbox files and writes the summary and the finish lines: the one that writes the data file, so two tabs never apply a change twice.
    - A finish line is written once per session and task, with the finish's own time, so reloads and repeated finishes never double it; it counts for busyness (the round said it would) but not as work (B2).
    - The crowd while it works is the six drones alone, no people, as the comment asked; coral, with no parcel, so they read apart from the delivery drones, and following the same Traffic and drones settings.
    - The side list belongs to the Task Master, so it waits for the Task Master round (section 7).

- **Garbage system (12 October 2026, `wizard-rounds/2026-10-12-garbage-round1.json`, one folder up from the source, answered the same day, then two previews). Built at 0.1.31; section 2, Garbage.**
  - **Asked for:** a visual punishment for ignoring the city, tied to urgency: a building whose urgency bubble shows a number or "!" adds garbage, red more, and each overdue task more each day. A setting turns the garbage view off.
  - **The points, as settled at the build:** yellow 5; red 10, and 10 more for each period past the first red one; each overdue task 5 for each day late. They came in three steps: first 1 for yellow, 5 for red, and 5 for a late task plus 1 a day after; after the first preview, yellow 5 and red 10; at the build, 5 a day late and 10 more per extra period. The building's urgency points come only from its system's own yellow or red; due dates count only through the late-task rule, so nothing counts twice.
  - **Rules:**
    - Garbage replaces the dirt on red (R1); see Status, above.
    - A late task's garbage keeps growing on rest days and stops growing while away; what it has stays (R2). While away no building is yellow or red, so their garbage goes too.
    - No ceiling per building or per task: one ceiling on the city's total, "ridiculously high, to the point of being annoying", reached only when the city is forgotten. One fixed task can take away 30 pieces or so, so cleaning up shows quickly (R3).
  - **Look:**
    - At its building, on its plot and sidewalk, spilling into the street and the nearest park past a set size (L1).
    - Street trash in the city's colors (L2), one piece per point, with no piles or steps (L3).
    - Pieces: loose paper and wrappers, crumpled sticky notes, cans and bottles with a cyan glint that stays lit at night, and trash bags (L4).
    - All drawn in code (L5).
    - Litter blowing in the wind, and a sparkle after cleaning (L6).
    - Dropped: overflowing bins, heaps, glowing goo, boxes, robot scrap, dead holo screens, glitch cubes, weeds (L4); flies, stink lines, people stepping round piles, smaller crowds, a city haze (L6). Later: a trash critter. Goo went with a note that garbage must still show at night: it does, without a glow.
  - **Cleanup (C1):** a hover garbage truck drives to the building, its crew gets out and works a few seconds, and the building's garbage goes, the pieces spilled far away too, without the crew walking to them. After the first preview: 3 of the crew, spread round the block at random; the truck comes from the map's edge at one end of the street and always leaves by an end, in any size of city, and drives faster since it comes from far.
  - **Where it shows (W1, W2):** the map and the postcard. Not in the status card: that line belongs to the Garbage Man, Abdurrahman's feature still to be asked about, which shows it for the city, not per project. Not in the weekly recap, the status brief (garbage is visuals only), or Edit City; a city total in the side bar later. The switch is in Settings, Look, kept on this computer.
  - **Reasoned, not asked:**
    - The ceiling was 500 pieces, to tune on screen: five buildings red three periods in and five tasks two weeks late make 450. Over it, every building's share shrinks in proportion. At 0.1.32 it went to 1,000, as Abdurrahman set it (The Garbage Man, H2).
    - Work until finished counts its period as a day: red after a day with no task finished, 10, then 10 more a day. Its yellow means a task was finished in the last 24 hours, so it adds nothing.
    - Away keeps only the day you come back, so the build records the days away, `city.awaySpans`: setting away opens a span from today, changing the date moves its end, and Clear ends it today (or drops it the same day). A late task does not grow from the day after you set away up to the day you are back, so it keeps what it had.
    - Each piece has a fixed spot and kind, dealt by its building's place and its number, like the street props, so garbage stays put between visits.
    - Any drop calls the truck, a partial one too (red to yellow takes 5), and so does going away; one truck per building, at most 3 on the streets at once, the rest waiting their turn. Its crew are drawn like the people; each takes the waiting pieces nearest it, and the far ones go when all are back.
    - The street is the block's south-east or south-west one, dealt by its place. Its cruising speed is its distance to the stop over 4.5 seconds, kept between 3 and 7 tiles a second.
    - Pieces lie flat, so they skip the depth sort: those off a plot are drawn with the ground, those on a plot (a building's front strip, a park) right after it. 500 pieces cost nothing measurable.
    - With Traffic off, garbage goes with the sparkle alone; with Motion on Still it just goes. Changes made while the city was closed show as they are on load, with no truck.
    - The garbage switch and Edit City hide the trucks too. The postcard carries the garbage, since it redraws the scene and leaves out only the bubbles.
    - The project view's picture shows the garbage and the truck too: it is the map's own drawing, traffic included, pointed at a small canvas.

- **The Garbage Man (13 October 2026, three rounds, `2026-10-13-garbage-man-round1.json` to `-round3.json`, delivered in the chat and answered the same day). Built at 0.1.32; section 2, Gus Grimsby.**
  - **Who he is:** a city character with a report (G1), made like a leader: a 128 px portrait with the leader recipe, a name, a voice and lines (G1a). A name of his own, with Garbage Man as his title (G1b). Grumpy but fair (G1c).
  - **Where:** in the side bar, beside Urgent and This week (G2). He steps away while the city is clean (G5), and goes when the Garbage switch is off (G6).
  - **His report (G3):** the city's total; every building with garbage, biggest first; each building's reasons; the biggest single fix; a click on a building goes to it. The reasons need better words than red and yellow: "Red means nothing to users, need better wording". Later: a clean streak. Dropped: trucks out now, pieces cleaned. The city total kept for later in the side bar (garbage round, W1) lives in his report.
  - **When he speaks up by himself (G4):** opening the city with garbage in it; the total passing 50, with Abdurrahman's line "The city is getting dirty! We should do something about it."; around 200, with "The city is filthy! This is unacceptable!"; and the last piece going. Not when a truck clears a building.
  - **Reasoned, not asked:** opening the city means the first open of the day, as the daily backup counts it. Each alarm speaks once each time the total climbs past it, at most once a day. The last piece's line plays as he steps away.
  - **Round 2 (`2026-10-13-garbage-man-round2.json`, answered 13 October):**
    - He is Gus Grimsby, Garbage Man (H1): chief of the cleanup crew; grey walrus mustache and bushy eyebrows over a permanent squint, the crew's coral overalls with a gold band, a yellow cap with a small teal truck badge, a broom over one shoulder. Signature color coral, with yellow. Greeting: "You're back. Let's see the damage." Picked over Otto Dumpstead (the truck's teal and gold, a clipboard) and Grumbo (a lavender cleaning robot rebuilt from a bin).
    - The alarm at 200 is a second alarm, after the one at 50 (H2), and the ceiling goes to 1,000 pieces: "Actually the ceiling is 1k" (built at 0.1.32).
    - His words show in a big dismissable speech bubble at the map's top left, by the side bar, with the same line under his portrait (H3).
    - Lines kept for a clean city (H4): "Clean streets. Don't get used to it.", "Not a wrapper in sight. I'll be off, then.", "Fine. Good work. Don't make me come back." His lines never mention pieces of garbage, only tasks; "I cannot clean..." replaces "I don't clean...".
    - The report (H5): not per-building reasons with piece counts, but "something like: 2 projects need your urgent attention, 1 project needs your attention. You have 4 overdue tasks. Lets clean them. One line that covers all cases."
  - **Round 3 (`2026-10-13-garbage-man-round3.json`, answered 13 October): all approved.**
    - Gus's voice (J1): chief of the city's cleanup crew for longer than anyone remembers; rides the hover truck, knows every gutter, takes every wrapper personally. Short sentences in plain words, a grumble before the point; he raises his voice only when the city is filthy. He names the mess, then the one thing to do next; grudging praise cut short, dry asides about his crew and his truck. Obsessed with clean gutters, loose wrappers and his truck; certain, he has seen worse; a weary pride in the city. He never mentions pieces of garbage (he counts tasks), insults you, lets a mess slide, cleans what you have not fixed, or gushes. A compass, not a checklist.
    - Opening the city (J2), one picked at random: "You're back. {tasks} tasks between this city and clean streets. Start with {task}.", "Took you long enough. {tasks} tasks waiting. {task} first.", "I cannot clean what you don't fix. {tasks} tasks. Start with {task}." {tasks} counts each overdue task plus one task in each project behind its pace (finishing one task clears it); {task} is the task that clears the most, or "any task in <project>" when that is a project behind its pace. Singular forms read right.
    - The report line (J3), parts with nothing to count dropping out: "2 projects need your urgent attention, 1 project needs your attention. You have 4 overdue tasks. Let's clean them up." Approved cases: "1 project needs your urgent attention. Let's clean it up.", "3 projects need your attention. Let's clean them up.", "You have 1 overdue task. Let's clean it up.", "1 project needs your urgent attention. You have 2 overdue tasks. Let's clean them up." Urgent attention: two or more periods behind its pace, or Work until finished with no task finished for a day. Attention: one period behind. Overdue: past its due date. A task due soon but not late is not counted.
    - Under the line (J4): "Start with Draw the beds, in Garden planner." or "Start with any task in Home budget."; then a row per building, most garbage first, a click going to it: "Garden planner: urgent, 2 overdue tasks", "Home budget: needs attention", "Recipe box: 1 overdue task".
  - **Reasoned while building (0.1.32):**
    - {tasks} counts every late task and one task for each project behind its pace with no late task of its own: finishing any task in a project puts it back on pace, a late one included, so a project with late tasks adds nothing more.
    - The task to start with counts a late task's own garbage plus its project's urgency garbage, since finishing it clears both.
    - Only the worst alarm the total climbed past speaks, so a jump straight past 200 says the 200 line and not the 50 one; a mark that already spoke today stays quiet, and the milder marks passed on the way wait until the total drops below them again.
    - He stays in the side bar while pieces still lie on the map after their cause is fixed, and the clean line comes when the last of them goes, after the truck; then he steps away once his bubble closes.
    - The speech bubble closes with its button, or by itself after 14 seconds, since his line stays under his face in the side bar.
    - His face is a faceless stand-in drawn in code in his colors until the portrait is made: the leaders' design allows a silhouette in the signature color.
  - **After the build (13 October 2026, Abdurrahman's notes on 0.1.32). Built at 0.1.33:**
    - A small [-] to dismiss what he says, leaving him minimized as one picture with a ! on it. Asked where: his part of the side bar, not the map's speech bubble, which keeps its close button and its 14 seconds.
    - He no longer says what needs attention or what is urgent, since the map shows it: the J3 report line keeps only the overdue tasks, and the J4 rows drop "urgent" and "needs attention".
    - Reasoned while building: a building behind its pace with no late task keeps its row, reading "finish any task", what clears it, as "Start with any task in" already says. Shrunk, he stays shrunk until his face is clicked, and the ! shows the whole time; his speech bubble still speaks up on the map. The ! is in his coral, the Urgent tiles' badge shape, so it does not read as a red bubble.
  - **His portrait prompt** (Pro Flash at 128 px, transparent background): "Head and shoulders portrait of a grumpy old sanitation chief, looking straight at the viewer, front view: a big grey walrus mustache and bushy grey eyebrows over a permanent squint, a yellow work cap with a small teal garbage truck badge, coral work overalls with a gold band across the chest, a worn wooden broom handle resting on one shoulder, a stern but fair frown, soft light from the top left."

- **The Productivity Inspector (19 October 2026, two rounds, `2026-10-19-productivity-inspector-round1.json` and `-round2.json`, delivered in the chat and answered the same day). Built at 0.1.45; section 2, Proxima Pace.** V1 of Tasks, Round 2: "a new character the prouctivity inspector, provide daily, weekly, monthly, reports to read. and other interesting facts/suggestions." He answered the round's first version, which still asked how the review starts.
  - **Who she is (I1), in his words:** "An asian co-pilot looking, female, wearing an earphone and a side mic. Delighted in numbers, a bit energitic but cares mostly about productivity." Made like Gus: a name of her own with Productivity Inspector as her title, a stand-in face drawn in code until her 128 px portrait is made with the leader recipe.
  - **Her name (I2):** "I need you to generate bunch of names that start with p or pr [like productive Proona) or something." Asked in Round 2 (N1), with eight names in a bracket. The three Round 1 concepts (Mabel Quill, Tally, Odo Fenwick) were not picked.
  - **Where (J1):** at the top of Reports. **The review (J2):** "I cancelled the reviews."
  - **How each report arrives (J3):** the daily report, on yesterday, waits in Reports; the weekly report, on the week, and the monthly report, on the month, she brings herself, in a speech bubble with Read.
  - **What each report holds (L1):** in every report: tasks finished against the period before, the streak and how near it is to the longest, milestones finished with their dates, and what the coming day, week or month holds; in the weekly and monthly: each building's tasks finished, the most first, overdue tasks with the one to close first, buildings with nothing finished in the period, and the busiest building; in the monthly only: repeats kept up, and notes written.
  - **Facts and suggestions (L2):** yes to a milestone one task from done, next week with nothing due, and a repeat kept up; left out: streak news, round numbers, a quiet building, a building far above or below its usual month, and overdue tasks piling up in one building.
  - **Round 2 asked:** her name (N1, a bracket of eight: Proona Pace, Pippa Pulse, Presta Mei, Prue Velo, Proxima Lin, Pria Tally, Prisma Kai, Pomi Sato), her look in detail (N2: Flight deck in mint with navy, Sky crew in sky blue with white, or Night run in lime with graphite), her voice (V1), and her lines (V2) for the weekly and monthly bubbles, the daily report's first line, and the three facts.
  - **Her name (N1):** Proxima Pace, his own, from the bracket's Proxima Lin and Proona Pace.
  - **Her look (N2):** Sky crew: sky blue with white. Black hair in a high ponytail with a sky-blue tie, a white single earpiece with a slim side mic, a sky-blue pilot shirt with white epaulettes, a silver stopwatch on a lanyard.
  - **Her voice (V1), approved:** the city's productivity inspector, riding co-pilot on your work: she reads the instruments, calls out the numbers, and keeps the flight plan honest. Quick, bright and exact; short call-outs with a little cockpit talk (inbound, logged, on deck, copy that); real numbers said precisely, an exclamation when a number is good; she opens with the number and closes with the next thing to do. Driven by the count, the streak and the milestone one task from done; delighted by numbers that move; cares more about the next tick than the last. Sure of her readings, never of your excuses; upbeat, but steady when the numbers are low. She never scolds or nags (Gus's job), mentions garbage, makes up or rounds a number, praises with empty words, or crowds a report.
  - **Her lines (V2):** all nine approved as written (section 2, Proxima Pace).
  - **Reasoned while building:** the daily report is on yesterday, the weekly on the last full Saturday-to-Friday week, the monthly on the last month; each is compared with the period before it, and looks ahead to the period it was given in, from today on; a report on a period that ended before the city's first record is not given; she brings the weekly report before the monthly one; she gives way to Gus and to an open panel; reading a report before she brings it means she does not bring it; the streak in a report is the streak now; the weekly and monthly lines are picked once per report, so the same report keeps its line; "a repeat kept up" is a repeat set to weekly or more often, ticked in each of 3 or more weeks in a row up to the last full week; "a milestone one task from done" has at least two tasks and no repeat.
  - **Her portrait prompt** (Pro Flash at 128 px, transparent background): "Head and shoulders portrait of an energetic young East Asian woman, a co-pilot and productivity inspector, looking straight at the viewer, front view: black hair in a high ponytail, a sky-blue pilot shirt with white epaulettes, a white single earpiece with a slim side mic by her cheek, a silver stopwatch on a lanyard, a bright, delighted smile, soft light from the top left."

- **Star and What is next, Round 1 (19 October 2026, `2026-10-19-star-next-round1.json`, delivered in the chat with three sheets of mockups drawn from the tool, answered the same day). Built at 0.1.41; section 2, Tasks on the map.**
  - **Asked for:** "mock me bunch of different colors and let me choose. also what I wanted was changing the color of this box if the task is starred. while you are at it. please make the box better looking, it seem disorganized, maybe hide no due date, but also when there is a due date it appears in a better layout".
  - **A1, the star bubble on the map:** B1, a gold star on purple, as at 0.1.39. Shown against cyan on night blue (0.1.40), gold on night blue, pink on plum, gold on teal and cyan on purple.
  - **A2, What is next while its task wears the star:** S1, purple with a gold edge, matching B1. Shown against night blue with cyan, night blue with gold, plum with pink, teal with gold and amber. The side bar's starred card takes the same colors, and the star icon is gold everywhere.
  - **A3, What is next's layout:** B, the due date as a chip at the right of the milestone line. Shown against A (the date on its own line under the task, in words with how far off) and C (a pixel date tile on the left). All three dropped No due date, merged the pin and Pinned into one chip at the top right, showed Starred as a mark beside it, and kept Copy task and Open in Claude on one row.
  - **Reasoned while building:** the chip's date names the weekday when it is more than a day off ("Due Fri 23 Oct"), as the mockup did; the task's type was meant to be 17 px all along, but its font rule was invalid, so it fell back to the button's; a pin click in What is next keeps the focus there, falling back to What is next's own pin when the next task changes.

- **Celebrations (20 October 2026, two rounds, `2026-10-20-celebrations-round1.json` and `-round2.json`, delivered in the chat with a sheet of every kind drawn round the city hall and a GIF of the burst, answered the same day). Built at 0.1.46; section 2, Celebrations.** The details of E1 and E2 of Tasks, Round 2.
  - **T1:** every tick sets off its building's particles.
  - **T2, the kinds:** his four (binary 0 and 1, stars, dollar signs, lightning) and, of the twelve suggestions, wizard sparkles, hearts, leaves, game buttons, speech bubbles, coins and confetti. Keys left out with his note "Just make gold zero and ones", so gold 0 and 1 is a kind too. Playing cards, clouds, planes and flags left out.
  - **T3:** every building starts on stars until he picks. Not picked: a start from its building, or one dealt by its place.
  - **S1:** a milestone needs at least 2 tasks to throw a party.
  - **S2, approved:** a crowd of about 20 dances round the block; six party drones loop over it in the colors of its particles; a bus pulls up to watch; its particles all party long; party lights over its streets; the announcement with Go to it, with his note "It gets announced by proxima pace", so it is her speech bubble rather than a toast. Left out: a banner with the milestone's name.
  - **Round 2, A1, Proxima's lines for it:** approved, "Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!" and "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!"; left out, "{n} tasks, {milestone} complete! {project} is throwing a street party. Next on the flight plan: {next}." and "Touchdown! {project} landed {milestone}, all {n} tasks. Next up: {next}."
  - **Reasoned in the rounds, not asked:** the burst plays like the wizard's; particles only, no cheer from the people; particles at the map's scale with the dark outline, keeping their colors at night; a tick anywhere counts, unticking plays nothing, and Still shows none of it; the pick lives in the Building panel, a tile per kind playing its burst when pointed at, and travels with the city; a milestone throws its party once a day; with the traffic off only the particles and lights play; it shows on the map and in the project view's picture.
  - **Reasoned while building:** the burst starts 0.42 of the way down the building; a party's own bursts start 2 seconds after the tick's; the lights are three strings across each of the four streets, sorted by depth with the figures; the dance is the talking arms and a new arms-up frame, with a hop; guests come across the block's zebras and out of its front, and walk off across the first zebra afterwards, or into the building after 6 seconds without one; anyone walking on to the block joins in; the bus takes the shortest way to a street with the block on its right, at 1.6 tiles a second, skipping its stops, and drives on a second after the party ends; the party drones fly in high from the map's edge and loop at 34 to 79 px; picking particles is not work, like a pin; Go to it glides the building to the middle of the open map, and her bubble sits beside the project view while it is open; she announces on Still too; a kind the tool does not have reads as stars.

- **Ghost tasks (19 and 20 October 2026, Ghost Tasks, Round 1, `2026-10-19-ghost-tasks-round1.json`, delivered in the chat and answered the same day). Built at 0.1.47; section 2, Ghost tasks.** The details of C1 to C4 of Tasks, Round 2.
  - **G1, "building with urgency":** behind its pace: one or more periods behind under One task per N days, or a day without a ticked task under Work until finished, the same buildings that make garbage through urgency. Not picked: any red or yellow bubble, or red bubbles only.
  - **G2:** at most 5 ghosts round one block at once.
  - **M1:** on the sidewalk, among the people, who walk through it. Not picked: in the street, or along its plot's rim.
  - **M2:** a ticked ghost rises and fades. Not picked: slipping into its building, or fading where it is.
  - **L1:** a sheet ghost; **L1a:** see-through inside its glowing edge. Not picked: a note ghost, a hologram ghost; a pale solid body.
  - **L2:** its eyes and edges glow in its building's bubble color, red or yellow. Not picked: ghost cyan for all.
  - **L3:** 12 px tall at 1x, in his words: "The ghosts will be clickable/or you point over them, and you see the task."
  - **S1:** its own switch in Settings, Look, on by default and kept on this computer; Traffic and No bubbles leave them. **S2:** hidden on Motion Still; shown on the postcard and in the project view's picture.
  - **X1:** now: a due chip on its card, its task on hover, peeking round corners; later: slipping through its building's wall; left out: Open in Claude on its card, and a faint trail. On Open in Claude he asked "what do you mean by on its card, what is the card?": the small card a click on a ghost opens (C4).
  - **Reasoned in the round, not asked:** a task both overdue and next is one ghost; the next task is the one the status card puts first; on rest days and away only overdue tasks haunt; a waiting repeat never haunts; it creeps at about half walking speed with a slight bob and pauses, lingers by its building's front, never crosses a street, and nothing reacts to it; it comes out of its building's front when its task starts to haunt and is already on its round when the city opens; one that stops haunting without a tick leaves as a ticked one does; Edit City hides them; the ghost is shown at 1x and 2x, by day and night, for his approval.
  - **Reasoned while building:** the next task is `bubbleTodos`' first, so a pinned task not overdue gets its own ghost beside the overdue ones; past 5, the most overdue come out first, then the next task; the eyes look the way it goes, which also makes the peek read; the body is white at 0.62, since a fainter one read as an empty arch by day; a faint dark ring by day and a soft glow ring at night; peeking is a stop at the corner, a lean of 0.13 tiles on to the new side with its eyes there, and back; the ghost holds still while its card is open, and its card closes the status card and the wheel, as they close each other; Enter steps inside with the task open, since the card is about the task; Tick has a toast with Undo, since the card goes; a click on a ghost never starts moving the building behind it.

- **Tasks (14 and 15 October 2026, Abdurrahman's ask for a brainstorm on the whole task system: "things to improve on tasks specifically, the entire task system, any missing features and things that might increase the quality of tasks and task tracking"). A two-round brainstorm, Tasks, Brainstorm 1; a ranking round, Tasks, Round 1; and the details, Tasks, Round 2 (41 questions), all delivered in the chat. Also kept in the claude.ai project as `claude/tasks-ideas.md`.**
  - **The goal (brainstorm):** "The speed of finishing many tasks".
  - **How they get built (15 October):** one idea at a time, in the order below; Abdurrahman tests each and decides what changes before the next one starts. Each idea's section of Round 2 holds its details; testing the one before can still change them. On 19 October he chose to build idea 4 before idea 3, which was not built yet; idea 3 comes after he tests idea 4. On 20 October he had idea 6 built ahead of ideas 3 and 5, then idea 5, still ahead of idea 3.
  - **The order (Round 1, A1):** 1. Tasks on the map (built at 0.1.39); 2. Recurring tasks and one-line adding; 3. Wizard round in a task; 4. Reports and the weekly review; 5. Tasks as cars; 6. Celebrations; 7. Archiving; 8. City-wide task list; 9. Attack System.
  - **Dropped:** project sleep (ranked third, then removed: an urgency of None does it). Killed in the brainstorm: a Done list, a week laid out by the city, task sizes, glowing paths between waiting tasks, a rule against priority levels, moving tasks by dropping them on buildings, a lost and found plaza, a date when a task stops mattering, a surprise task, the skill asking what done looks like, putting the effort into milestones instead, a task in several projects, the city logging unwritten work from Claude sessions, a Start button for a first step, checklist steps, the leader's kind word, the stale task sweep, folding done lists away, the drones flying back with one Tick it card, a cap on attacks, a combo streak, ticking several tasks at once, and a report Claude writes.
  - **1. Tasks on the map (M1 to M6), built at 0.1.39 (section 2):** a white count bubble with the next task in a line under it (M1); after 250 ms (M2); with No bubbles too, on demand (M3); pins from the task's panel, a project view row, a status card row, and What is next (M4); a pin clears only when ticked or unpinned (M5); each project's pin and one city star, separate, starring pinning too (M6). After trying it (18 October 2026), Abdurrahman asked for three changes, built at 0.1.40: What is next in a slightly different color, to read as its own widget, and the star in a new color (picked: neon cyan on night blue, used nowhere else); no star on the lists, only in the task's panel, since it is rare and was too much to see all the time; and the starred task in the side bar until it is unstarred or done, with its building, as a shortcut to the task. That 0.1.40 build misread one point: Abdurrahman meant What is next itself to change color while its task is starred, not the star a new color everywhere; Star and What is next, Round 1 (below) settled it, built at 0.1.41. Reasoned while building: the hover's count joins on the left so the bubbles there stay put; pins and the star live on the project, so Esc in the task panel does not undo them; the star bubble was purple with a gold star, so it never reads as yellow urgency; the hover leaves the name tip by the pointer as it was.
  - **2. Recurring tasks and one-line adding, built at 0.1.42 (section 2):** R1, how a repeat comes back, in Abdurrahman's words: "lets say it is recurring every 7 days, when you tick the task, it will go away. after 7 days it will get re-added. so you don't see it and you can infinitely tick it. but I still don't know exactly how it works." R2: every day, every N days, weekly on chosen weekdays, monthly on a date, and yearly. R3: by schedule (weekdays, monthly dates and years keep their rhythm; every day and every N days count from the tick). R4: one task moves on (only Activity's Done line records each tick). O1: !dates, #daily/#weekly/#monthly/#yearly/#every N days and @milestone approved; ^ (pin) and * (star) left out; #repeat alone left out, with the comment "I don't understand the difference between this one and the one above it." (it was shorthand for #weekly on the due date's weekday, so #weekly covers it). O2: the one-line add in the project view, a new add field in the status card, and a city-wide quick add on a key naming the project with /project. R1 was reasoned out at the build from his words, rather than asked again: ticking moves the task on and it goes away from every list and count until its next date, when it is back, due that day; it stays visible only in the project view, dimmed in its place with when it comes back, so it can be changed or stopped; a missed one stays one overdue task; Undo after a tick, Esc in the panel. Reasoned while building too: a new repeat shows at once, due on its first date, and with no date a repeat starts today; #weekly takes every weekday marked; an @name no milestone has makes one, as Claude's add-tasks does; /name and @name match the first name that is, starts with, or has a word starting with the mark; the quick add without /name goes to the project open in the view or the selected building; the status card's field stays for the next task; T is ignored while typing in a field.
  - **3. Wizard round in a task:** W1, Open in Claude, back by the inbox; W2, the round is kept inside the task; W3, a shared wizard-rounds folder, else a download; W4, the answers go into the task, and Copy task carries them; W5, a small hat on the task's row while its round is open; W6, a new round replaces the old one.
  - **4. Reports and the weekly review:** P1, a panel like Settings; P2, now: tasks finished each week (12 weeks), by project for a week or month, the streak and its longest, the busiest building of the month, milestones finished with their dates; later: overdue tasks over time; left out: by weekday, best weeks. P3, rest days and days away never break a streak. V1, in Abdurrahman's words: "a new character the prouctivity inspector, provide daily, weekly, monthly, reports to read. and other interesting facts/suggestions." (it replaces Gus running the Saturday review). V2, the review brings up overdue tasks, then any project. V3, a task closed as dead is deleted. V4, picking a task for next week gives it a due date next week. Built at 0.1.43 (section 2) without the inspector, at Abdurrahman's call: the reports panel and the review now, the inspector through a wizard round (Productivity Inspector, Round 1, `2026-10-19-productivity-inspector-round1.json`, delivered in the chat), built after his answers, like Gus. Reasoned while building: every count is of ticks, Activity's Done lines less those a Reopened line took back, so a repeat counts each tick; the streak passes over a day off with no tick and counts one with a tick, and today does not break it before its first tick; the busiest building is shown for this month and each earlier month with a tick, ties shared; milestones finished are dated by their last task; next week is the coming Saturday-to-Friday week, or on a Saturday the one starting that day, and the review looks back on the week before it; the review runs in three steps, Look back, Close and Pick, on every task Done, Dead and Next week with its seven days, Undo on Done and Dead, Unpick for what the review picked; picking is not work; Reports open with R, beside Settings at the side bar's foot, and the two close each other; nothing new is saved in the data.
    - **After his test (19 October 2026), built at 0.1.44:** the review is taken out, in his words: "I found the review tab to be completely useless. The menu is dull, and I have no way of fixing it, the city is where to manage your tasks, and maybe it should stay that way. the look back you can see it in weeks. remove it please until I come up with a better flow (if ever) but it is not going to be the side menu." V2 to V4 wait for a better flow of his own, if any, and it will not be in the side bar. Reports keeps Weeks and Records.
    - **The inspector, built at 0.1.45:** Proxima Pace, after Productivity Inspector, Rounds 1 and 2 (below), at the top of Reports with a stand-in face.
  - **5. Tasks as cars:** C1, in his words: "overdue task + the next task of building with urgency. also, instead of cars they are ghost as in ghosted tasks, moving around the city creeping, but people doesn't see them." C2: "ghosts with glowing eyes and edges". C3, round its own block. C4, a click opens a small card with the task and its project, Tick and Enter. Designed further as ghost tasks in Ghost Tasks, Round 1 (Ghost tasks, above), and built at 0.1.47 (section 2, Ghost tasks).
  - **6. Celebrations:** E1, in his words: "I don't want a firework, just small particles around the building. like when we write wizard in decision wizard. however; in building settings you get to pick from a variaty of different particles. 0011100 is one idea we have stars, $ sign, electricity icon, you can suggest more if you know the projects in my city." E2, the milestone street party lasts 30 seconds. Designed in Celebrations, Rounds 1 and 2, and built at 0.1.46 (Celebrations, above, and section 2).
  - **7. Archiving:** A1, an Archive view (in the project's more menu, newest first, with Restore); A2, both by hand and automatically, a done task archiving itself 7 days after its tick (A2a); A3, search and the reports, recap and review still see archived work, while a milestone's Copy for Claude and the city summary leave it out.
  - **8. City-wide task list:** L1, a panel like Settings; L2, tasks with no due date after the dated ones, grouped by project.
  - **9. Attack System:** K1, sessions start by themselves after a one-time setup like the folder links one; K2, they ask as usual; K3, the map and the list feed one pick list; K4, several tasks in one project run as one session, in order; K5, the drones lift off from the city hall.

## 7. Open items

- Tasks: Celebrations, idea 6, is built at 0.1.46, and ghost tasks, idea 5, at 0.1.47, both ahead of idea 3 at Abdurrahman's call, and both wait for his test. Idea 3, Wizard round in a task, is next. Ghost tasks, later: a ghost slipping through its building's wall now and then (X1). The weekly review was taken out at 0.1.44 and waits for a flow Abdurrahman may come up with, not in the side bar. The productivity inspector, Proxima Pace, is built at 0.1.45 with a stand-in face, waiting for Abdurrahman's test; her portrait is made later with the leader recipe (the prompt is in section 6, The Productivity Inspector, 6 generations a try). The questions the Round 2 answers opened were settled in each idea's own rounds: ghost tasks instead of cars (C1, C2) in Ghost Tasks, Round 1, and particles picked per building (E1) in Celebrations, Rounds 1 and 2.
- 0.1.38, one skill for the city, built in a chat on 14 October, is not in the repo: the builder still lives in its own skill there. Its archive, if kept, needs merging with 0.1.39 rather than applying over it, since `tools/pack.py --apply` refuses an older archive.
- Leaders: build the leader card this month. The seven leaders are picked through a wizard round, then their portraits are made (6 generations a try).
- Abdurrahman names the projects that get the new buildings (bus depot, drone port, apartment block, cafe, library). The drone port is finished; the other four have their designs picked and wait until he says (20 generations each).
- The Garbage Man: built at 0.1.32 with a stand-in face. His portrait is next (the prompt is in section 6, The Garbage Man, 6 generations a try); once made, it ships in the tool in place of the stand-in. Later: a clean streak, and a trash critter (section 6, Garbage system).
- The month's list: all six PixelLab tests are done, so the bulk work can start.
- Links, later: press, move, release on the wheel (section 6, Links, round 1).
- The Task Master: round 1 (`2026-10-14-task-master-round1.json`, delivered in the chat) asks who it is and its mascot (three original concepts, since Claude's own mascot is Anthropic's), when it shows, how it shares the side bar with Gus, what else its panel holds, when it speaks, and where the mascot shows. Already decided for it: Gus's place in the side bar, the list of sessions each going to its building, and Tick it. After the answers: its voice and lines, then the build, with a stand-in face until its portrait.
- The Cowork tracking test (Even better Claude connections, C1): ship the hooks in the claude.ai plugin and try one Cowork task running on the PC; build on it only if session notes arrive. Needs to know how the plugin is put together, since the hooks ship as part of a plugin, not as a skill.
- Even better Claude connections, later: a Windows notification, one click on Open in Claude, the next task to Claude, continuing a session, chat links. Chats stay untracked for now.
- After 0.1.37 lands on the PC: run the Claude Code setup again once (it writes `~/.claude/nullovation-city.json` and keeps background notices out of the card), click Let it write once, and reinstall the nullovation-city skill in the claude.ai plugin.
- Repeats, later if wanted: a line in the nullovation-city skill on how repeats show in the summary (`repeat` on an open task, `waiting` with `back`) and that done moves a repeat on (a cloud session cannot write in `.claude/`, so it waits for Claude Code on the PC); Claude's skill writing repeats into tasks files and add-tasks (the city already reads them), and a replace-plan from Claude keeping repeats (it carries them only when the plan says so). The week's recap counts a repeat once per week by its title, however often it was ticked; Reports (0.1.43) count each tick.
- Claude Code at work: on 9 October 2026 the setup ran on Abdurrahman's PC, and a fresh terminal session wrote its note (prompt, reply, ended), so the hooks work. A session already open before the setup wrote nothing. That first session ran in the folder above the repo, so a link to the repo did not match it; linking `D:\Storage\Work\_Projects\Nullovation-City` covers the repo and everything beside it. On 12 October the city watched `Nullovation City data\Claude-Hooks` beside the data file, which Abdurrahman picked, while the hooks wrote to the folder the setup had made by itself; he wants Claude-Hooks used, so 0.1.30's setup asks for the folder and he runs it again to pick Claude-Hooks. Whether `claude://cowork/new` still works after Cowork merged into Claude is untested.
- Settings, later: the leader speech bubbles switch, a bin for deleted projects, Open in Claude options, desktop notifications, and interface size (section 6, Settings and Edit City).
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
