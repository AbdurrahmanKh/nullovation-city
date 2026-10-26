# Changelog

## 0.1.70 (2026-10-27)

Wizard rounds dropped by hand write in Activity too, after Abdurrahman's yes in the chat: rounds belong in Activity.
- A round dropped on a task writes "Attached a wizard round to <task>: <title>", and the same round dropped again with nothing new answered writes "Updated the wizard round of <task>: <title>".
- Answers dropped on a task, or brought by a round file, write "Answers in for <round>: 3 of 8".
- The drop's Undo takes its lines back out.
- Tests: test37_task_rounds checks the lines and their Undo.

## 0.1.69 (2026-10-27)

Leader Bubbles, Round 2: every trigger of a leader's bubble designed on its own, after Abdurrahman asked to decide again what bubbles and what leaves a note. 21 of the 31 triggers stay as they were; these are the 10 that change.
- Quill, the Pocket Wizard, is the city's voice for wizard rounds, like Gus for the garbage and Proxima for the reports. He says a round Claude attached with no finish to sit under, and a round's answers coming in, for every building, with his own face in News. His portrait ships with the city, and a leader of the city's own named Quill is him, so one Quill shows.
- A wizard round reads in a small popup: where it stands, each question with its answer so far, and Open in wizard. It opens from Read in Quill's bubble, on the status card and the leader card, and from Show the answers in the task panel, which no longer unfolds the answers in place.
- On a leader's status card or leader card, a line Quill says starts with his small face and his name.
- A finish says "Claude handed <task> back to you.", since whether the task is done is yours to say.
- Claude writes nothing in Activity but a wizard round it attaches: no finish line, no summary, and no lines for the tasks, milestones, notes and links it adds. Undo on a round takes its line back out. A tick you give from Claude's ask still writes its Done line.
- A round's answers coming in write "Answers in for <round>: 7 of 8" in Activity.
- A task going overdue writes "Overdue: <task>" in Activity, dated the day after its due date, once per due date. It draws no crowd round the building.
- The leader card in the project view says what the status card says, with the same buttons: Claude at work, waiting, stopped, finished and what it asks, and the building's news. A building with no leader has Proxima say it there, with Pick a leader.
- Fixed: a change Claude asked about, once applied or dismissed, and a session that was waiting for you, once it moves on, no longer linger on a card that read them.
- Tests: test44_leader_bubbles checks Quill, the popup, the cards, the Activity lines and the overdue line. test17, test24, test37, test39, test40 and test43 follow the new lines.

## 0.1.68 (2026-10-24)

Claude's news as one report, from Claude's News on the Status Card, Round 1 (Abdurrahman's task "Improve how leaders deliver Claude's news and asks on the status card" in Nullovation City Hall, UX Mastery): A1, A2, B3 and C2. B1, B2 and C1 came back as questions and are not built.
- An update Claude sends is one report, said by the building's leader under the finish of the task it reports on: the finish with its time, Claude's summary in its own words, then a short line for each part with its own buttons. It is one item in News and in the leader's bubble, not three.
- An update from a session still at work waits for that session's finish, so the report opens once, whole. One with no finish to sit under is said on its own, as before.
- What Claude added has Read, a small panel with the notes, tasks and links whole, beside Undo.
- Each change that asks first has its own line and buttons: Tick it and Dismiss for a tick, Read, Apply and Dismiss for a description or a plan. Read shows a new description whole, over the one it would replace. A change file waits until its last change is applied or dismissed.
- Tick it shows when Claude asks to tick the task off, and on a finish with no update; a finish whose update does not ask has none, since work is left.
- What asks first names the change itself, never Claude's summary. Every report has one time. What Claude added is named, not only counted. Cut titles end with an ellipsis. The start of a reply shows without its markdown, on one line.
- The nullovation-city skill names the task an update reports on (`task`), and check_plan.py checks it.
- Tests: test43_claude_report checks the report held until its finish, its lines and buttons, Read, Undo, Apply, Tick it, a finish alone, an update alone, and the checker. test24_claude_work and test37_task_rounds follow the new lines.

## 0.1.67 (2026-10-24)

The city installs as an app, the first of the two Quick Sync builds (Abdurrahman's task "Make the city an installable app" in Nullovation City Hall, Quick Wins). Sync comes after it.
- The hosted city installs like the Decision Wizard: its own window and icon, from the PC or the phone. It opens offline from a copy it keeps, and online the newest version always loads.
- Settings, Saving starts with The app: Install the app when the browser offers it, else where the browser's menu has it, and inside the app, that you are in it. Installed from a browser, the app opens that browser's city.
- The icon is the city hall's glass dome with the tiny city inside, on night violet, drawn from the city hall's art by `art/app/icons.py`.
- The service worker is built to sw.js beside the page, since a worker only looks after the pages in its own folder; the manifest and the icons are in src/app/. It handles only the page and the app's own files.
- A local copy of the page, opened from a file, installs nothing and says where the hosted city is.
- The app's window has the side bar's dark title bar.
- Tests: test42_app checks the manifest, the icons and sw.js, the local copy, and the city served over http: the worker keeping the page, the newest version loading online, the copy opening offline, Install, and Chrome offering the install in a real profile. test17_source checks sw.js against a fresh build and the archive carrying the app's files.

## 0.1.66 (2026-10-24)

Wizard it, after Abdurrahman's second test: from Maxthon, the link still opened a tab, since a link clicked in one browser never reaches an app installed from another, and his wizard app is installed from Chrome.
- Wizard it opens the installed wizard app through a web+dwizard: link, which the app registers with Windows, so it opens from any browser. The link names the round by its file and title, and the app opens the round's file in the Claude folder's wizard-rounds. It needs wizard 0.11.2.
- Settings, Links: Wizard it opens rounds in the Wizard app or a Browser tab. The app is the default; it needs the Claude folder, and a tab opens with an address of your own or with no Claude folder.
- The toast offers Open in a tab, for a computer without the app, or before the app knows the link.
- Tests: test37_task_rounds checks the link, what it names and its length, the toast and Open in a tab, and the setting with its dot and Reset.

## 0.1.65 (2026-10-24)

Wizard it, after Abdurrahman's test: it opened the wizard in a browser tab, on whatever round the wizard had open last.
- Wizard it opens the wizard through a link rather than a window the page opens itself, so Chrome and Edge open it in the installed Decision Wizard app, in the window it already has. Without the app it opens in a tab.
- The link carries the task's round, its file's name and its answers so far, so the wizard opens that round whatever it had open. It needs wizard 0.11.1, which reads the round from the link and keeps the app to one window.
- With no Claude folder the round no longer downloads: it arrives in the link, and its answers file is dropped back on the task as before.
- Tests: test37_task_rounds checks the link, what it carries, Arabic in it, and that nothing downloads.

## 0.1.64 (2026-10-23)

SideBar Cleanup, Abdurrahman's task in Nullovation City Hall, UX Mastery: the side bar is level 0, and what holds too much for it opens at level 1, a panel docked on the map's left like the project view.
- This week: each number has a small icon beside it, a tick for tasks done, a note for notes and a flag for milestones. "Open the week" is gone; the card still opens the week.
- Status brief: one button, Status brief. Its panel starts with Copy status brief, then Chat, Cowork, Code and Terminal.
- Due this week: the copy button on each task is now the Claude icon, which opens Open in Claude with Build it, Think and Copy, as a task's does anywhere else. All tasks' rows have it too, in place of Copy task.
- The four buttons at the side bar's foot, All tasks, Leaders, Reports and Settings, are all one size, two by two.
- All tasks opens as a large panel on the map, 880 px wide like the project view, and the side bar keeps its lists beside it. The dated tasks and the undated ones sit side by side. A task opened from it opens the project view over it, and All tasks is back as it was once the view closes, the focus on the row. L or its button bring it to the front, or close it. Reports and Settings no longer close it; Esc closes it before them.
- A leader's editor opens at level 1 on the map, with the Leaders list still in the side bar and the leader's row marked. The face and portrait sit beside the name, role and color, and the buildings it leads under them. It opens over the project view or All tasks, which are back once it closes.
- A building selected while a panel is on the map glides into the open part beside it, and the leaders' and Proxima's bubbles sit beside All tasks as they do beside the project view.
- On a narrow window All tasks and a leader's editor cover the map, and the drawer closes.
- Tests: test10_sidebar checks the week's icons, Status brief, Due this week's Claude icon and the foot; test35_all_tasks and test34_leaders follow the panels onto the map; test18_open_in_claude follows the status brief's panel; test29_reports no longer stops on a Saturday before the week's first tick.

## 0.1.63 (2026-10-23)

Open in Claude becomes a panel, from Open in Claude Panel, Round 1, and Abdurrahman's notes and diagram.
- Open in Claude opens a panel in place of its menu: tiles for Chat, Cowork, Code and Terminal, then Copy, and under them the folder they open in. Chat says "no folder". Cowork has its own icon.
- One folder: "Folder: <path>". A building with several folder links shows > beside it, which lists them; the one picked is kept for that building in this browser. Cowork gets that one folder now, plus the round's file for a task with a round, rather than every folder and file link.
- Copy, in the panel, takes the place of the separate copy buttons (A1): Copy status, Copy status brief, Copy task in What is next, the task panel and an archived task, a milestone's Copy for Claude and a note's are gone. Copy copies the text and says so, as they did.
- A task's panel has two tabs: Build it, the default, which sends the task to do it, and Think, which asks Claude for a wizard round about it (A2: tasks only). Think replaces the Make a wizard round row.
- Think has "Make a brainstorming round": ticked, it asks for a brainstorm, the wizard's two rounds through the six hats, in place of a wizard round.
- A brainstorm attaches to its task like a round (A3): dropped on its panel or sent by Claude Code with add-round. Its card says "Brainstorm, round 1" or "round 2" and counts the cards seen; it counts as answered once its last card is seen. Round 2 replaces round 1. A copy for a chat writes its answers in, card by card; the city summary says which kind a round is.
- Tick it, under a finished Claude Code session, is said by the building's leader in its toast, as the one-line add's is (D1).
- The nullovation-city skill knows Think and brainstorms, and its check accepts a brainstorm in add-round.
- Tests: test18_open_in_claude rewritten for the panel; the passes that copied with the old buttons copy through the panel; test37_task_rounds checks Think and brainstorms; test40_leader_news checks Tick it's leader.

## 0.1.62 (2026-10-23)

The leaders come alive, the fifth and last piece of the leader UX (Leader UX, Round 1 E1).
- A breathing face: wherever a leader's face shows, it rises a pixel and back every few seconds, each leader on its own slow rhythm, its faces in step. The picture rests a pixel low in its frame, so no gap opens under it.
- Talking in its bubble: the line types out, a long one in under 2 seconds, while the face bobs, then it settles and breathes. The bubble keeps its size from the first letter, a screen reader hears the line whole, and the task stays a link.
- Proxima breathes and talks the same way while she brings a building's news in the leaders' place. Gus, and Proxima's own bubble, are as they were.
- Motion on Still holds both: the faces rest and a line shows whole at once. It follows the system's reduced motion too, as the map does.
- Tests: test41_leaders_alive, new; test40_leader_news shows its lines whole.

## 0.1.61 (2026-10-23)

The Leaders panel, the fourth piece of the leader UX (Leader UX, Round 1 C1 and Round 4 L3).
- The Leaders section leaves the side bar. A Leaders button, with its own pixel icon, sits at the side bar's foot beside All tasks, over Reports and Settings.
- It turns the side bar into the Leaders panel, as All tasks, Reports and Settings do, and opening any of the four closes the others: every leader with its face, its name in its color, its role, and the buildings it leads; New leader at its top; "No leaders yet." with none.
- A click on a leader opens the editor there, in the list's place, the map still in view: the same editor as before, which was a dialog over the city. Done, Add leader, Cancel and Delete leader go back to the list, the focus on the leader; the back arrow and Esc do too, and Esc again closes the panel.
- New leader and Edit in the picker beside the project view open the editor in the panel too.
- On a narrow window the panel opens in the drawer.
- Fixes a stray "null" beside Upload portrait while a leader had no portrait.
- Tests: test34_leaders follows the panel.

## 0.1.60 (2026-10-23)

Fixes and links in the leaders' news, from Abdurrahman's first test of 0.1.59.
- A leader's bubble that opened as the city loaded showed the leader's silhouette, and its building as a generic one, because the portraits and the building's own art load a moment later. The bubble and the faces in News now draw again as soon as they load.
- The task a leader's line names is a link, in its own gold color: a click opens the task in its project. From the bubble it counts as reading the news, and the bubble closes, as Open does; the rest waits with its leader. The status card and the leader card in the project view link it the same way.
- The building named in the bubble is a button: a click goes to it on the map, as Go to it does, without opening it.
- Tests: test40_leader_news checks the links and the pictures that load late.

## 0.1.59 (2026-10-23)

The leaders' news, the third piece of the leader UX (Leader UX, Rounds 1 to 4: A1, B1 to B3, C1, N1 to N3, T1, P1, P2, M1, G1, D1, X1).
- A News section in the side bar takes the place of Urgent and of Gus's part, between This week and Due this week. Gus shows there while the city has garbage, then each leader with news waiting, then Proxima for the buildings with no leader: a face with its name, and ! for one item or a count for several.
- A click on a leader's face opens its bubble at the map's top left, where Gus and Proxima speak: the face at 100 px, the name in its color, the building, lit on the map while it shows, and Go to it. Several items share one bubble, 1 of N with Next, the most pressing first.
- Falling behind its pace, tasks due today (on the day's first open), a milestone one task from done, Claude's additions and wizard rounds, Claude waiting, asking first or stopped on an error open the bubble by themselves, after Gus and Proxima. It closes after 14 seconds and leaves the news waiting with its leader; once used, or opened by a click, it stays until closed. Claude finishing, a round's answers and the week wait with their leader.
- An item is read once its bubble showed it and was closed, or Next went past it. Each waiting face has its own dismiss. News that stops being true (back on pace, nothing due today any more, a session no longer waiting) goes by itself.
- The buttons by moment: Undo for Claude's additions and rounds, Apply and Dismiss for what Claude asks first, Tick it for a finished task still open, Open for a round's answers.
- Claude's inbox toast and the answers-in toast are now the leader's news. Toasts for your own actions stay.
- The status card's leader line says its building's news and Claude's lines in the leader's voice: working, waiting, finished with Tick it and the start of Claude's reply, stopped, and asking first with Apply and Dismiss. A building with no leader has Proxima say them. Opening the card reads the news it says.
- The leader card in the project view says its building's news when it has some, else its greeting.
- Gus's report moved into his bubble: a click on his face opens it, with his line, the overdue tasks, Start with, and his building rows; it stays until closed. His [-] is gone.
- Reports show the leader's face beside each building's row in By project, and in Proxima's By building.
- What was heard is kept in this browser; nothing new is saved in the city.
- Tests: test40_leader_news; test10, test24, test26 and test37 follow the News section, the leader's voice and Gus's bubble.

## 0.1.58 (2026-10-23)

The leaders' lines, the second piece of the leader UX (Leader UX, Rounds 1 to 4: A2, V1, L1 to L3).
- Every leader shares one set of lines, one per moment, approved word for word: falling behind its pace, a task due today, a milestone one task from done, Claude's work and changes, a wizard round's answers, the week, and the greeting. A line speaks for its building as "we" and never names it. Proxima will say the same lines for a building with no leader.
- The leader card in the project view now says its greeting under the name and role, in a quote with a bar in the leader's color: "Welcome back. Next up: <task>.", the pinned task first, or "Nothing open here yet. Add the next task." It follows ticks and pins.
- A task's title in a line is cut short past 60 characters, the full title as the line's tooltip; a count of one reads in the singular.
- The other moments' lines wait for the next piece, the bubbles and the News section. Nothing new is saved in the city.
- Tests: test39_leader_lines.

## 0.1.57 (2026-10-23)

Clearer leader faces, the first piece of the leader UX: Abdurrahman's task "Think the leader UX" in Nullovation City Hall, designed in Leader UX, Rounds 1 to 4 (D1, D2, and B1's note).
- The leader card in the project view shows the leader's face at 96 px, from 64.
- The status card's leader line shows the face at 48 px, from 32.
- Every speech bubble at the map's top left shows its face at 100 px, from 80: Gus's and Proxima's now, the leaders' when they speak.
- The side bar, the wheel's middle and the toast keep their sizes. Faces are framed and shrunk smooth as before: no head crop and no second picture (D1).
- Tests: test26, test30 and test34 check the new sizes, and test34 the framing at 96 and 48 px.

## 0.1.56 (2026-10-23)

The one-line add over the map, rethought: Abdurrahman's task "Rethink 1 line task add", designed in Rethink the One-Line Add, Round 1, with the leader's toast asked in the chat.
- Enter on the map opens the line, on the selected building's project when one is selected; T still opens it anywhere (E1). With the wheel open, Enter still steps inside its building.
- A double-click on a building steps inside it; F then Enter does too (E1).
- Every mark suggests as it is typed, in a list under the line: / the projects, @ the line's milestones, ! dates, # repeats, + shifts. Up and Down move, Tab or a click picks, Esc closes the list first, and Enter adds the task with the highlighted pick (P1).
- / lists the projects added to most recently first, with each one's picture and open tasks, and finds a name by its letters in order (/gp finds Garden planner). @ lists the line's milestones, the one a task lands in first and those in the archive last, offers a new one by the name typed, and asks for a project first when the line has none (P2).
- ! offers today, tomorrow and the next five days with their dates; # offers the repeats, each saying when it starts; + offers the shifts.
- Each kind of mark shows in its own color as it is typed, a shift in its own color.
- The three shift tags sit under the line, the one picked pressed; a click picks one or takes it off (S1).
- The line's building lights up on the map.
- With no project open or selected, the line starts on the project last added to.
- Shift+Enter adds and keeps the line open on the same project; Ctrl+Enter adds and opens the task in its panel.
- The building's leader says it in the toast: their face, name and building, and "Task added: <task>." With Open and Undo; Undo takes the task back out and reopens the line with what was typed. A building with no leader keeps its toast, with Undo too.
- Only the line over the map suggests; the add fields in the project view and the status card stay as they were (W1).
- A name with a hyphen or two spaces now matches a mark written with hyphens, in every add field.
- The controls guide: Enter on the map adds a task, and a double-click or F then Enter steps inside.
- Tests: test38_quick_add; test23 and test28 know the new Enter and the line's start.

## 0.1.55 (2026-10-22)

Wizard rounds in a task, the third of the task ideas (Tasks, Round 2, W1 to W6), designed in Wizard Rounds in a Task, Rounds 1 to 3.
- A task can keep one decision wizard round: its questions, its answers as they come, and its file in `wizard-rounds` inside the Claude folder, which the city and the wizard share (W2, F1). A new round replaces the old one (W6).
- Make a wizard round: a second row in a task's Open in Claude menu, under Chat, Cowork, Claude Code and Terminal, with the same four (M1). Each sends the task's copy ending with a line asking Claude for a round with the d-wizard skill, sent back with the nullovation-city skill, and not to start the task yet. Code and Terminal need a folder link, as above them.
- Back from Claude Code: the skill writes the round into `wizard-rounds` and sends an `add-round` change, which applies at once with Undo, a toast and a line in Activity (W1). From a chat: drop the round file Claude gives you on the task's panel; a line lights up only while a file is dragged over it (P2).
- The card, under Pin and Star in the task panel (P1): its hat, Wizard round, where it stands ("Waiting: 3 of 8 answered", "Answered: 8 of 8", "Answered: 3 of 8, 5 skipped"), its title and file, Wizard it (Open in wizard once answered), Mark answered, Remove, and the answers, folded until Show the answers (P1a).
- Wizard it opens your wizard in a tab of its own and makes sure the round's file is in `wizard-rounds`; the wizard, given that folder once, opens it by itself and saves the answers into it. With no Claude folder it downloads the file, and its answers file is dropped back on the task. Settings, Links, has the wizard's address, the hosted wizard when empty.
- The answers come back into the task as the wizard saves them, read with the rest of the Claude folder, and a toast says "Answers in for Draw the beds: 7 of 8." with Open once they stop arriving.
- A round counts as answered when nothing is open, or when you press Mark answered, which counts the open questions as skipped on purpose, with Undo (A1, S1).
- The hat: the wizard's own, flat and in one color (H1), gray while its round waits for answers and teal once answered (A2). It shows on an open task's rows in the project view, the status card and All tasks, in the hover's next-task line, and in What is next as a chip, "4 of 8" or "Answered" (X1). A click on it is Wizard it.
- Copy task names the round with where it stands, and points to its file; a copy sent to a chat writes its answers in, since a chat cannot read the file (A2, C1). A milestone's copy names it; the city summary gives each open task's round.
- Remove takes the round off the task with Undo; its file stays in the folder. Dropping, answering, marking and removing are not work: Updated, urgency and Activity stay. Claude's add-round writes its line in Activity, as its other changes do.
- The nullovation-city skill writes the round and the `add-round` change; `check_plan.py` checks it. The claude.ai plugin needs it reinstalled.
- Data: a task may carry `round` (title, file, folder, questions, answers, marked). `21-rounds.js` holds the model, `61-rounds.js` the card, hats, files and answers.
- Tests: test37_task_rounds, 122 checks. test17_source no longer forbids the word wizard in the tool: it checks that no copy of the d-wizard skill or the wizard is in the repo, that a new city has no Decision Wizard project, and that the wizard opens at its own address.

## 0.1.54 (2026-10-22)

Abdurrahman's task "Turn tasks into Ideas(Notes)", in Task Improvements: some tasks are better kept as open ideas, and links come before notes.
- Turn into a note, at the foot of a task's panel, left of Delete task: the task becomes a note, its title the note's title and its description the note's text. Its milestone, due date, repeat, shift, pin and star go with the task. The note opens in the panel in the task's place.
- Turn into a task, at the foot of a note's panel, left of Delete note: the note becomes a task where a task added without @ goes (the current milestone, else the last, else a new To do), named by its title, or by its first line when it has none, the rest its description. The task opens in the panel in the note's place. An empty note has nothing to turn, so the button waits for words.
- Each shows a toast, "Turned Water the beds into a note." or "Turned Seed library into a task in First release.", with Undo, which puts back exactly what was there: the task in its place with its date, repeat, shift, pin and star, or the note with its date, and its panel again.
- A task's title longer than a note's 200 characters is not cut: the note opens with it.
- Activity says "Turned into a note: ..." or "Turned into a task: ...". Neither is work, so urgency stays; Updated moves, as for any new task or note. The week's recap counts a note turned into a task as a task added.
- An archived task is to read, so it has no Turn into a note until it is restored. A done task has one.
- Links now sit above Notes in the project view, level with Todos.
- The note panel's foot is laid out like the task panel's: Turn into a task on the left, Delete note on the right, and when it was written under them.
- Fixed: opening a note while a task's or a milestone's panel was open skipped closing that panel, so a tick or an edit made there wrote no line in Activity.
- Tests: test36_notes_tasks, 65 checks.

## 0.1.53 (2026-10-21)

All tasks, the eighth of the task ideas, designed in All tasks, Rounds 1 to 3, with shifts, and built ahead of the third at Abdurrahman's call.
- Shifts: a task can have one of three, or none: Create (at the screen and the keyboard, in work hours: code, art, testing), Think (pen and paper will do: design, writing, a decision) and Errand (away from the screen: daily tasks, buying, a call). They are fixed; none can be added (K3, K4).
- +create, +think or +errand in a task's line sets it, or just the start of one (+c, +t, +e); a + word that names none stays in the title. The line under an add field says the shift it read, and names the mark when empty.
- The tag shows on the project view's rows, the status card's rows and in What is next; the task panel has a Shift row with the three, a click on the pressed one taking it off, and Esc undoing it as any edit there. Setting a shift is not work: Updated and Activity stay.
- Copy task and a milestone's copy say "Shift: Create"; the city summary for Claude has each open task's `shift`; tasks files, plans and Claude's add-tasks may carry one.
- All tasks: a button at the side bar's foot, before Reports and Settings, or L, or Due this week's "and N more" line, turns the side bar into every open task in the city, with the map in view. The three panels close each other; the back arrow, Esc or L again close it; on a narrow window it opens the drawer.
- At its top: "13 open, 1 overdue, 2 due this week", for what it shows; a words field that finds a task by its title, description, project or milestone; a chip for each shift with its count, and No shift; and a tile for each building with its count of the shift picked. A click on a chip or a tile shows only that, a second click everything.
- The list: the starred task first, in a purple card with a gold edge; then the dated tasks in day groups (Overdue, Today, Tomorrow, Rest of this week, Next week, Later), each row with its shift, its day and its project and milestone; then the undated ones by building, the ones behind their pace first, 3 each in the project's own order and Show all.
- Sorting: under No shift, pointing at a row shows the three shifts, and one click tags it; the focus goes on to the next.
- A row works like the status card's: the square ticks it, struck through for a moment, its particles bursting; the text opens it in its project; the pin and Copy task show while it is pointed at. Pointing at a row lights its building on the map. The arrow keys move between rows, Enter opens one and Space ticks it.
- It opens on everything each time: opening on the last shift picked was left out.
- Data: a task may carry `shift`, one of `create`, `think` or `errand`. `73-alltasks.js` holds the panel; `SHIFTS` and `setShift` live in `20-model.js`, the mark in `22-repeat.js`.
- Tests: test35_all_tasks; test28 knows the longer hint line.

## 0.1.52 (2026-10-21)

After Abdurrahman's first leaders: Kryptos's portrait showed far smaller than the rest, since it was drawn small on a big see-through canvas (Pro Flash at 128 px, the figure 83 by 95 with 16 px clear under it), while the others fill their 256 px canvas.
- Every leader's portrait is now framed by its figure: a square round its drawn pixels, the foot on the frame's foot and the figure 97% of its height, centred. A portrait that already fills its canvas, like Gus's, stays as it was.
- The file is never changed: the art store keeps it as uploaded, and an animated GIF keeps playing, framed by its first frame. A picture with no see-through pixels is cropped square, from the top when it is tall.
- A face shown larger than the portrait's own pixels grows in whole pixels; smaller, it shrinks smooth as before.
- Portraits already in the city are framed on the next open.
- Tests: test34_leaders, 9 more checks.

## 0.1.51 (2026-10-20)

Leaders, first part: picking a leader for each building, from Abdurrahman's Leaders round of 20 October (L1 to L3). Talking comes later.
- A leader holds a name, a role, a signature color and a portrait (L2). One leader per building, and one leader can lead several.
- A Leaders section in the side bar, after Due this week, shows each leader's face and name, with New leader. A click on a face edits it.
- The leader panel: the portrait (Upload, Replace, Remove; a PNG, GIF, JPEG or WebP up to 1024 px and 3 MB), name, role, twelve signature colors and one of your own, and the buildings it leads. A new leader is added with Add leader, or Enter in the name or role; editing applies each change at once. Delete leader asks first and leaves its buildings without one.
- Without a portrait, a leader shows a silhouette on its signature color.
- Picking: Pick a leader in the project's more menu (it names the leader once there is one), or the leader card in the project view, open a picker beside the view with No leader, each leader (saying where else it leads), New leader and Edit. Picking is not work: Updated and Activity stay.
- Where the face shows (L1): the leader card under the building's picture in the project view, a line under the building's name in the status card, and the shortcut wheel's middle, kept for it since 0.1.26.
- Claude knows the leader (L3): Copy task, a note's and a milestone's copies, the project's status and the status brief carry "Leader: name, role"; the city summary lists the leaders with what they lead, and each project's leader.
- Backups and the data file carry the leaders with their portraits inline; importing a backup replaces them. Export this project carries its leader; importing it uses the city's leader of the same name, or adds it.
- Data: the database gains `leaders` (`{ id, name, role, color, portrait, createdAt }`) and a project `leader`, a leader's id or empty; portraits sit in the art store under `leader:` and the id. `23-leaders.js` holds the model, `63-leaders.js` the side bar, panel, picker and faces.
- Tests: test34_leaders, 93 checks; test07, test21 and test29 know the new menu item and the leaders in the data.

## 0.1.50 (2026-10-20)

After Abdurrahman's first look at the archive: its milestones fold.
- Each milestone in the Archive view has a fold toggle before its flag, as in the task list. They all start open; a click, or Enter on the toggle, folds one to its name and count, and again opens it. The focus stays on the toggle.
- The fold is the archive's own: folding a milestone there leaves it as it is in the list, and the other way round. It is kept on the milestone, `archiveCollapsed`, and travels with the city like the list's fold. The group with no milestone keeps its fold while the page is open.
- Opening the archive at a milestone, from the count at its foot, or at a task, with Esc or Back to the archive, unfolds that milestone to show it.
- Folding is not work: Updated and Activity stay.
- Tests: test33_archive, 8 more checks.

## 0.1.49 (2026-10-20)

Archiving, the seventh of the task ideas, designed in Archiving, Round 1, and built ahead of the third at Abdurrahman's call.
- A done task goes to its project's archive by itself 7 days after its tick (A2, A2a). On the first open with archiving, every done task ticked a week or more ago goes at once (D1). It is checked on opening and when the day changes; a done task with no tick on record counts its 7 days from the day the city first sees it.
- By hand (A1): an archive button on each done row in the project view, shown while the row is pointed at, like the pin on open rows; Archive in a done task's panel; and Archive done tasks in the milestone view, for every done task in it. Each with a toast and Undo.
- A milestone whose every task is archived goes to the archive with them (B1), and comes back when one of them is restored or a task is added to it with @name.
- The Archive, first in the project's more menu with its count, "Archive (12)" (E1), opens beside the project view: archived tasks by milestone, the milestone with the newest task first, its tasks newest first (C3), each with the day it was ticked and Restore. A milestone that went to the archive with its tasks says so.
- A click on an archived task opens it in the same task panel, to read, with Restore, Back to the archive, Copy task, Open in Claude and Delete task (C2). Esc goes back to the archive. Deleting the last task of a milestone in the archive takes the milestone with it.
- Restore brings a task back done, in its old place in its milestone, with a toast and Undo, and it archives itself again 7 days later (C1). Dragging tasks, or moving them with Alt and an arrow, keeps every archived task's place.
- At a milestone's foot, the count of its archived tasks with the archive's icon and no words (E1); a click opens the Archive at that milestone. The milestone view lists its archived tasks dimmed, with the icon, under the rest.
- A milestone's count, the project's progress and its copies still count archived tasks as done (B2). Search, Reports, the recap, Proxima and the builder card still see them, while the project view's lists, a milestone's Copy for Claude and the city summary leave them out (A3). Copy task on an archived task says it is in the archive.
- A plan loaded over a project leaves its archive alone, and a project export loaded as a plan leaves its own archive out. Claude's edit-description never touches an archived task, and Claude's add-tasks skips a milestone in the archive unless it names it.
- Archiving and restoring are tidying, not work: Updated and urgency stay, and nothing goes in Activity.
- Data: a done task may carry `archived: true` with `archivedAt`, and `archiveFrom`, the day its 7 days count from after a restore. `24-archive.js` holds the model.
- Tests: test33_archive, 77 checks.

## 0.1.48 (2026-10-20)

Gus's and Proxima's portraits, Abdurrahman's 256 px pixel art, in place of the faceless stand-ins drawn in code since 0.1.32 and 0.1.45.
- Gus Grimsby's portrait in his part of the side bar, on his shrunk face with its !, and in his speech bubble; Proxima Pace's on her card at the top of Reports, at the top of each report, and in her speech bubble.
- They show in their frames of dark coral and dark sky blue: 64 by 64 in the side bar and Reports (the stand-ins were 56 by 50), and 80 by 80 in the speech bubbles. Shrunk smooth, as the map shrinks its buildings.
- The portraits live in `src/portraits/` (`gus.png`, `proxima.png`), saved as palette PNGs with every pixel as drawn, and the build carries them in the page as `PORTRAITS`, a module it makes in memory, `27-portraits.js`.
- Tests: test26_garbage_man and test30_inspector check each face (the portrait, its size on screen and in its frame, smooth, its frame's color) and that each portrait decodes pixel for pixel; test17_source checks both PNGs (256 by 256, a hard see-through background), the page carrying them, and the archive holding them: 16 new checks.

## 0.1.47 (2026-10-20)

Ghost tasks, the fifth of the task ideas (first named Tasks as cars), designed in Ghost Tasks, Round 1, and built ahead of the third at Abdurrahman's call.
- Every overdue task, and the next task of each building behind its pace, creeps round its building's block as a ghost (C1, G1). Behind its pace means the buildings that make garbage through urgency, so the ghosts agree with the garbage and Gus's count. The next task is the one the status card puts first, the pinned one when there is one; a task both overdue and next is one ghost. At most 5 to a block, the most overdue first (G2); the rest come out as ghosts are ticked. Rest days and away pause the pace, never the due dates, and a repeat waiting for its next date never haunts.
- A sheet ghost 9 px wide and 12 tall at 1x (L1, L3), drawn in code: a round head over a rippling hem, see-through white inside a glowing edge (L1a), with its eyes and edge in its building's bubble color, red or yellow, kept at night like the neon (L2). Its eyes look the way it goes. A faint dark ring keeps it clear on the sidewalk by day, and becomes a soft glow at night.
- It goes round its block on the sidewalk (C3, M1) at about half walking speed, floating and bobbing; the people walk through it. It pauses now and then, lingers by its building's front, and at a corner stops and leans round before carrying on (X1). It never crosses a street. A ghost whose task starts to haunt comes out of its building's front; when the city opens they are already on their rounds.
- A tick anywhere lays it to rest (M2): it rises a few pixels and fades out where it is, in about a second. One whose task stops haunting without a tick leaves the same way.
- Resting the mouse on a ghost shows its task by the pointer (X1). A click opens its card (C4): its project, the task, its due chip (X1), Tick and Enter, while the ghost holds still. Tick ticks the task off with Undo, or moves a repeat on; Enter steps inside the building with the task open. Esc, a click elsewhere, or a building's status card closes it.
- Ghosts in Settings, Look, on by default and kept on this computer (S1); Traffic and No bubbles leave them. Hidden on Motion Still and in Edit City; shown on the postcard and in the project view's picture (S2).
- Nothing new in the city's data.
- Tests: test32_ghosts, 71 checks.

## 0.1.46 (2026-10-20)

Celebrations, the sixth of the task ideas, designed in Celebrations, Rounds 1 and 2, and built ahead of the third and fifth at Abdurrahman's call.
- Every tick sets off small particles round its building (T1), never a firework: a burst like the decision wizard's when you type wizard there. 16 particles fly out from the building's middle, drift down and twinkle out over 1.5 seconds. They are pixel art at the map's scale, about the size of the people, with the city's 1 px dark outline, and keep their colors at night like the neon. A tick anywhere counts: the status card, the project view, the task panel, Tick it, and Claude's Apply; a repeat's tick too. Unticking plays nothing. The burst shows on the map and in the project view's picture of the building.
- Twelve kinds (T2): stars, binary 0 and 1, gold 0 and 1, dollar signs, lightning, wizard sparkles, hearts, leaves, game buttons, speech bubbles, coins (which turn as they fly) and confetti. Every building starts on stars (T3).
- The Building panel, opened from the building's picture in the project view, has Particles: a tile per kind, which plays its burst while pointed at. A click picks it and plays it on the map. Picking is not work: Updated stays, and nothing goes in Activity. The pick travels with the city, in the data file and backups.
- A milestone of 2 tasks or more (S1) throws a 30 second street party round its building when its last task is ticked (S2): its particles burst every 2 seconds or so, and strings of party lights in the city's colors hang across its four streets, chasing and glowing at night. With the traffic on, about 20 people dance round the block (those already there, and others who walk over across its zebras or step out of its front), six party drones in the colors of its particles fly in from the map's edge and loop over it, and the nearest bus drives over and waits at the block's curb, cars holding back behind it. When it ends, the dancers walk on, the guests walk off, the drones fly away and the bus drives on.
- Proxima Pace announces it, in one of her two new lines, approved word for word and picked by the milestone, with Go to it, which brings the building to the middle of the map. She waits for Gus and for an open panel as she does for her reports, says several milestones one after another, and sits beside the project view while it is open. She announces it on Still too.
- A milestone throws its party once a day; one with a repeat in it never finishes. Motion on Still shows no particles and no party; with the traffic off, the party has its particles and lights only.
- Tests: test31_celebrations, 59 checks. test30_inspector checks her two new lines word for word, and test17_source lets the tool name the Wizard sparkles kind while keeping out the decision wizard itself.

## 0.1.45 (2026-10-19)

Proxima Pace, Productivity Inspector, V1 of the fourth task idea, designed in Productivity Inspector, Rounds 1 and 2.
- Her card at the top of Reports, above the tabs (J1): her face, name and title, her latest line, and her three reports as tiles, Daily, Weekly and Monthly, with the period each is on. A report not read yet has a sky-blue dot, and so does the Reports button.
- Her reports (L1), in a panel with her line first: tasks finished against the period before, the streak against the longest, milestones finished, and what the coming day, week or month holds. The weekly and monthly add each building's tasks finished, the busiest building, buildings with nothing finished, and the overdue task to close first; the monthly adds repeats kept up and notes written. A task, building or milestone in a report opens it.
- Her facts (L2): a milestone one task from done, next week with nothing due, and a repeat ticked 3 or more weeks running.
- How they arrive (J3): the daily report, on yesterday, waits in Reports. The weekly and monthly reports she brings herself on the first open after their week or month ends, in a speech bubble at the map's top left with Read, which opens the report. Each is said once. She never speaks with Gus: she waits for him, and says hers again if he cuts in. She waits while a report is open.
- Her voice and lines (V1, V2), word for word as approved; the same report always gets the same line.
- Her face, until her portrait is made: a stand-in drawn in code in Sky crew colors (N2), sky blue with white, with a ponytail, an earpiece with a side mic, and a stopwatch.
- Nothing new in the city's data: what was read and said is kept in this browser.
- Tests: test30_inspector, 62 checks.

## 0.1.44 (2026-10-19)

After trying 0.1.43, Abdurrahman found the Review tab useless: the side bar is dull for it and has no way to fix a task, and the city is where tasks are managed. The look back is already in Weeks.
- The Review tab is gone, with its three steps and everything on its task rows (Done, Dead, Next week and its days, Unpick). Reports keeps Weeks and Records, in two tabs with their names.
- A browser that last left Reports on Review opens it on Weeks.
- The Reports button's tip says Reports (R).
- Tests: test29_reports, now 71 checks: two tabs and no review left in the tool, and the old Review tab opening on Weeks.

## 0.1.43 (2026-10-19)

Reports and the weekly review, the fourth of the task ideas (Tasks, Round 2, P1 to P3, V2 to V4), built before the third at Abdurrahman's call. The productivity inspector (V1), who will run the review, waits for his own wizard round.
- Reports (P1): a Reports button beside Settings at the foot of the side bar, or R, turns the side bar into Reports, as it does into Settings, with the map in view; the back arrow, Esc or R again bring the lists back. Opening one of Reports and Settings closes the other. Three tabs: Weeks, Records and Review. The controls guide names R.
- Weeks (P2): tasks finished each week, a bar for each of the last 12 Saturday-to-Friday weeks, this week's hatched as so far, with this week's count, the 12 weeks' total and the average a week. Under it, By project: each building's tasks finished for a week or a month, the most first, with arrows back to the first one with a tick; a bar picks its week. A row shows the building on the map.
- Records (P2, P3): the streak, days in a row with a task finished, with what today does for it and the longest with its days; rest days and days away never break it, and a tick on one counts. The busiest building of the month with its picture, and each earlier month's, ties shared. Milestones finished, newest first, with their dates and projects; 8 show, then Show all; a click opens the project.
- Every count is of ticks: Activity's Done lines, less those a Reopened line took back, so a repeat counts each time it is ticked; a done task whose Done line the log no longer keeps counts on the day it was finished.
- The review, in three steps. Look back: the week before next week, in numbers and by project, with its milestones and the streak, and Open the week for the recap. Close (V2): every overdue task, the latest first, then any project's other open tasks. Pick (V4): what next week already holds, then each project's open tasks.
- On every task in the review: Done ticks it (a repeat moves on); Dead deletes it (V3), and it never counts; Next week shows the coming week's days, Saturday first, and a day gives it that due date, so Due this week, urgency and garbage follow it. Done and Dead have Undo; a task the review picked can be unpicked, back to the date it had. Picking is not work. Finish the review sums up what it did.
- Next week is the coming Saturday-to-Friday week, or on a Saturday the one starting that day.
- Nothing new in the data: the review keeps its steps in memory, and Reports keep their tab and Week or Month in this browser.
- Tests: test29_reports, 111 checks.

## 0.1.42 (2026-10-19)

Recurring tasks and one-line adding, the second of the task ideas (Tasks, Round 2, R1 to R4, O1, O2).
- How a repeat comes back (R1, reasoned out from Abdurrahman's own words): ticking a repeating task moves the same task on to its next date, and it goes away from the status card, What is next, the hover count, the bubbles, urgency, Due this week, Gus and the garbage until that day, when it is back, due that day. In the project view it keeps its place, dimmed, with its repeat sign and when it comes back ("Back Thu 22 Oct"), so it can be opened, changed or stopped. A repeat not ticked by its date stays one overdue task until it is ticked.
- After a tick, a toast says when it comes back, with Undo; in the task panel, Esc undoes it.
- Schedules (R2): every day, every N days, weekly on chosen weekdays, monthly on a date (a month without it uses its last day), and yearly, set in the task panel's new Repeat row. A task with no date gets the schedule's first one.
- The next date (R3): weekdays, monthly dates and years keep their rhythm, so a late tick skips what was missed; every day and every N days count from the tick.
- One task moves on (R4): only Activity's Done line records each tick, and it counts as work. Pins and the star clear on a repeat's tick, as on any tick.
- The one-line add (O1): !fri, !today, !tomorrow, !20 or !oct 20 for the due date; #daily, #weekly, #monthly, #yearly or #every 3 days for a repeat; @name for the milestone. A line under the field says what it understood before Enter. Words that are not marks stay in the title.
- Where (O2): the project view's add field; a new Add a task field in the status card, which stays for the next task; and T, anywhere outside a field, for a quick add over the map, where /name picks the project. The controls guide names T.
- Claude: Copy task, a milestone's copy, a project's status and the city summary say which tasks repeat and which repeats wait for their next date. Claude's done on a repeat, once applied, moves it on.
- Data: a task may carry `repeat` and `waiting`. They travel in the data file, the daily backups, Export, and a project export loaded back as a plan.
- Tests: test28_repeats, 107 checks; test24_claude_work checks Claude ticking a repeat.

## 0.1.41 (2026-10-19)

The star and What is next, from a round of mockups (Star and What is next, Round 1):
- A1: the star bubble on the map is a gold star on purple again, as at 0.1.39. 0.1.40's cyan was a misreading of the request.
- A2: while the next task wears the star, What is next turns purple with a gold edge, and says Starred at its top right. The side bar's starred card takes the same purple and gold, and the star icon is gold everywhere again.
- A3, layout B: What is next is the label with the pin at its top right (a pressed pin says Pinned), the task's milestone with the due date as a chip at the right of its line ("Due Fri 23 Oct", "Due tomorrow", "2 days overdue"), the task in larger type, then Copy task and Open in Claude on one row. Without a due date nothing shows: "No due date" is gone.
- A pin click in What is next keeps the focus there, even when the next task changes; it used to jump to the task's row in the list.
- Removed leftover styles from What is next's old field, and the star mark the 0.1.40 box used.
- Tests: test27_tasks_map, now 85 checks: the gold star, the starred box and card colors, the layout's order, no due date showing nothing, the due chip's text and place for 4 days, tomorrow and overdue, one row of actions, and the pin chip.

## 0.1.40 (2026-10-18)

The star, after trying 0.1.39:
- The star has its own color, neon cyan, which nothing else in the tool uses: on the map a cyan star on a night blue bubble (it was gold on purple), and the same cyan everywhere else it shows.
- The star is set only in the task's panel (Star for the city / Starred). The status card's rows, the project view's rows and What is next keep only the pin. What is next shows a cyan star mark beside a starred task.
- The side bar shows the starred task under search, until it is unstarred, ticked or deleted: its building, Starred, the task and its project. A click opens the task in its project.
- What is next is a widget of its own, a shade lighter than the project view with an edge round it. The old What is next field's leftover styles are gone.
- Tests: test27_tasks_map, now 76 checks: no star in the card or the rows, the star mark, What is next's color, the side bar card (what it shows, its place, following the star, a click opening the task, going when unstarred, ticked or deleted), and the star's color.

## 0.1.39 (2026-10-15)

Tasks on the map, the first of the task ideas, built alone so it can be tried before the next (Tasks, Round 2, M1 to M6). 0.1.38, one skill for the city, was built in a chat and has not reached this repo; this build starts from 0.1.37.
- Hovering a building: after a quarter of a second (M2), a white bubble with its open tasks joins its bubbles on the left, so the ones already there stay where they are, and its next task shows in one line under them, cut short past 40 characters (M1). In the Tasks view, which already shows the count, only the line is added. It shows with No bubbles too (M3), but not on the selected building, in Edit City, while planting or moving, or in the postcard.
- Pins: a project can pin one open task as its next one, from the task's panel (Pin as next), a task row in the project view, a row in the status card, or What is next (M4). The pinned task comes first in What is next, the status card, the hover, the project's status and the summary for Claude. What is next says Pinned and names the pinned task's own milestone. A pin clears only when its task is ticked, deleted or unpinned, and reopening the task does not bring it back (M5).
- The star: one open task in the whole city can wear the star, a purple bubble with a gold star over its building, beside the others; No bubbles and the postcard leave it out. Starring a task pins it in its project too, and the two are separate after that (M6). Starring another task moves the star, and a toast says where it went.
- The pins and stars are small icon buttons, hollow until pressed, that show while their row is pointed at. They are not work: Updated and urgency stay as they were, and Esc in the task panel leaves them alone.
- Data: a project keeps `pin` and `star`, each a task id or empty, so they travel in the data file, the daily backups and Export. Reading a city keeps one star at most.
- Tests: test27_tasks_map, 60 checks.

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
