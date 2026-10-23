---
name: nullovation-city
description: Write tasks, or a whole plan, for a project in Nullovation City, the user's pixel-city project tracker, as a JSON file the tool loads with Load plan or tasks in the project view's more menu, or send an update straight into the city's inbox from Claude Code. Use this skill whenever the user says "create nullovation tasks", "nullovation tasks", "add this to nullovation", "update the city", or "nullovation-city"; whenever a copy from the city ends with "When you finish, send Nullovation City an update"; asks to build, plan, set up, or restructure a project for Nullovation City or for their city; or pastes a Nullovation City project export (app "nullovation-city", kind "project"). It decides from the request whether to write a few tasks, a whole plan, or an update. Do not use it for a project's building art or leader, which is nullovation-city-builder; for changes to the city tool's own code; for Asana tasks, which is create-asana-task; or for to-do lists that are not meant for the city.
---

# Nullovation City: tasks and plans

Nullovation City shows every project as a building. Inside, a project has an About, milestones with tasks, notes, and links. This skill writes one of two JSON files for it:

- **A tasks file** adds one or a few tasks to a project. The user picks the milestone they go into when loading it, and nothing already in the project changes. This is the common case: dropping the tasks a conversation produced into the project it belongs to.
- **A plan** sets up or restructures a whole project: its About, milestones, tasks, and ideas. Loading it replaces the project's About, milestones, and tasks, after a warning, and adds its ideas to the notes.

Choose from the request. "Create nullovation tasks", "add this as a task", or anything about one or a few tasks means a tasks file. "Build", "plan", "set up", or "restructure the project" means a plan. When it is unclear, write a tasks file: it is the smaller change, and it never replaces anything.

In Claude Code on the user's PC, the city can also take an **update** straight into its inbox, with nothing to load: see Sending an update straight to the city, below. Use it when a copy from the city ends with "When you finish, send Nullovation City an update", or when the user asks you to update the city.

## The rule: only what you know

Write only what the user said, asked for, or agreed to: in this conversation, in the Claude project's files, or in something they pasted. Do not predict tasks, add steps nobody mentioned, or turn your own suggestions into tasks unless the user agreed to them. Do not pull items from memory or older chats unless the user points you to them. If the conversation produced two tasks, the file has two tasks.

The rule holds inside every task too: each detail in a description comes from the context. A short description that is all true beats a full one that is partly guessed. When something you need is missing, such as which project the tasks are for, ask one short question instead of guessing.

## Task descriptions

In the tool, every task has Copy task. It copies the task's title, project, milestone, due date, and description, without the project's About, so the task can be pasted into a fresh chat and worked on. Write each description for that reader, as plain text, so it stands on its own, using these lines:

```
<One or two sentences: what to do, and what it produces.>
Why: <what this unlocks or fixes>
Done when: <a checkable end state>
Where: <the files, pages, links, tools, or people involved>
Notes: <decisions already made, constraints, what not to do>
```

Keep only the lines the context can fill truthfully, and drop the rest. Never invent file names, steps, people, or criteria.

A description written this way, for a made-up project:

```
Write the one-page rules for Clan Cup: sign-up, bracket size, match windows, and no-shows.
Why: scheduling cannot be sized until the rules are fixed.
Done when: the rules page answers what happens when a clan misses its match window.
Notes: brackets are 8 or 16 clans, single elimination.
```

Start each task title with a verb, and keep it under about 80 characters.

## Plans

**The About.** Only facts that are unlikely to change: what the project is, and its main features. One to three sentences. Never the current work, status, progress, plans, or dates, and no incidental details. This is the bar:

```
The Decision Wizard is a single-file HTML tool plus the d-wizard Claude skill. Claude writes open decisions as a questions JSON round; the user answers it in the browser and exports an answers JSON back, which Claude acts on and reports per question id.
```

**Milestones.** Only the groups the known tasks fall into, in the order the user described, each named by the outcome it delivers. Do not create a milestone for work nobody mentioned.

**Tasks.** The known tasks, and nothing more. Mark a task "done": true only when the user said it is finished.

**Ideas.** Only what the user called an idea, a maybe, or something for later. Each becomes a note with a title and a short text. Never copy the project's existing notes into ideas; loading never deletes them.

**Links and due dates.** Only real addresses and dates the user gave.

**Restructuring a pasted export.** Keep the user's tasks and wording unless they asked for changes. Regroup, merge, or move a task into ideas only as asked, and say in your summary what moved, so nothing disappears silently.

## Writing

Never use an em dash or an en dash anywhere in the file; use a comma, colon, semicolon, or hyphen instead. The user reads every line of it in their tool.

## The files

A tasks file:

```json
{
  "app": "nullovation-city",
  "kind": "tasks",
  "version": 1,
  "milestone": "Optional: a milestone the user named. The tool preselects it when a milestone by that name exists.",
  "tasks": [
    { "text": "Start with a verb, under about 80 characters", "description": "The description lines above", "due": "Optional, YYYY-MM-DD" }
  ]
}
```

A plan:

```json
{
  "app": "nullovation-city",
  "kind": "plan",
  "version": 1,
  "project": {
    "name": "Optional. Renames the project; leave it out to keep its name.",
    "description": "The About",
    "milestones": [
      { "name": "The outcome this group delivers", "tasks": [
        { "text": "Start with a verb", "description": "The description lines above", "due": "Optional, YYYY-MM-DD", "done": false }
      ] }
    ],
    "ideas": [{ "title": "A short title", "text": "What and why" }],
    "links": [{ "label": "Short name", "url": "https://...", "icon": "doc, code, github, claude, chat, folder, or web" }]
  }
}
```

Limits: names and milestone names up to 120 characters, task titles up to 500, descriptions up to 8000, idea titles up to 200. The tool clips anything longer and ignores fields it does not know. Complete examples are in `references/example-tasks.json` and `references/example-plan.json`.

Name the file after the project: `<project>-tasks.json` or `<project>-plan.json`. If Python is available, check it and fix every error it reports:

```
python3 scripts/check_plan.py <the-file>
```

## Sending an update straight to the city

Every copy from the city (a task, a note, a milestone, a project's status, the status brief) ends with "When you finish, send Nullovation City an update with the nullovation-city skill." When the work is finished, or the user asks you to update the city, write one change file into the city's inbox. The city picks it up within a few seconds.

**Find the city.** Read `~/.claude/nullovation-city.json` (on Windows, `%USERPROFILE%\.claude\nullovation-city.json`). It names `summary`, the city as it is now, and `inbox`, the folder to write to. If it is missing, look in `~/.claude/settings.json` for the hooks whose `args` hold `nullovation-city-status.py`: the folder is the fourth argument, the summary is `city/summary.json` in it, and the inbox is `inbox/` in it. If neither exists, or you cannot reach the user's files (as on claude.ai), write a tasks file or a plan as above instead, and say how to load it.

**Read the summary first.** `summary.json` lists every project with its milestones, open tasks (with descriptions and due dates), done tasks, notes, links and folders. Use its names exactly: the city matches the project by name and a task by its title. If the work is not clearly about one project, or a task you mean is not in the summary, ask rather than guess.

**What to send, only what you know.** The rule above holds here too.
- `done`: a task the work finished. Only when it is really finished; the user approves it before it counts.
- `add-note`: a short note on what was done, decided or found, when it is worth keeping. Its title says what it is about.
- `add-tasks`: work that is left, only what the user asked for or agreed to, or what they said is still to do. Each task has a description written as above.
- `edit-description`: a task's description brought up to date, such as what is done and what is left. The user approves it first.
- `add-link`: a real address of something made, such as a document or a pull request.
- `replace-plan`: a whole new plan, only when the user asked for one. The user approves it first.
- `add-round`: a decision wizard round or a brainstorm for a task, when a copy from the city asks for one (below).

Adding tasks, notes, links and a round applies at once, with an Undo; ticking tasks, editing descriptions and replacing the plan wait on the building for the user to apply. Send one file per update, for one project.

```json
{
  "app": "nullovation-city",
  "kind": "change",
  "version": 1,
  "project": "The project's name, exactly as in the summary",
  "summary": "One line: what this update is about",
  "changes": [
    { "do": "done", "task": "The task's title, exactly" },
    { "do": "add-note", "title": "A short title", "text": "What was done, decided or found" },
    { "do": "add-tasks", "milestone": "Optional: a milestone's name; a new name makes a new milestone", "tasks": [{ "text": "Start with a verb", "description": "The description lines above", "due": "Optional, YYYY-MM-DD" }] },
    { "do": "edit-description", "task": "The task's title, exactly", "description": "The whole new description" },
    { "do": "add-link", "label": "Short name", "url": "https://...", "icon": "doc, code, github, claude, chat, folder, or web" },
    { "do": "replace-plan", "plan": { "description": "The About", "milestones": [{ "name": "...", "tasks": [{ "text": "...", "description": "..." }] }], "ideas": [], "links": [] } },
    { "do": "add-round", "task": "The task's title, exactly", "file": "2026-10-22-draw-the-beds-round1.json" }
  ]
}
```

Leave out the changes you have nothing for. Name the file `<YYYY-MM-DD-HHMM>-<project>.json`, write it into the inbox folder (make the folder if it is missing), and check it with `python3 scripts/check_plan.py <the-file>` when Python is available. Then tell the user in one line what you sent, and that adding applied at once while ticks and edits wait on the building.

## A wizard round or a brainstorm for a task

A copy from the city made with Think, in Open in Claude, ends with "Plan this task further with a decision wizard round" instead of the update line. Write the round with the d-wizard skill, asking only what the copy leaves open: a copy may already carry an earlier round's answers, which are settled.

With Make a brainstorming round ticked, it ends with "Explore this task with a brainstorm" instead. Write a brainstorm with the d-wizard skill, as its brainstorm reference says: its round 1, or, when the copy carries a brainstorm whose round 1 is answered, its round 2 from those answers. A brainstorm attaches exactly as a round does, and its round 2 replaces its round 1 on the task. Name its files as the d-wizard skill names brainstorms.

Then attach it to the task:

- **In Claude Code, with the city found as above:** write the round as `wizard-rounds/<YYYY-MM-DD>-<topic>-round<N>.json` in the city's folder (the folder that holds `inbox/`; make `wizard-rounds/` if it is missing), not in the project's own `wizard-rounds/`. In its `config`, set `project` to `Nullovation City` and `folder` to the full path of that `wizard-rounds` folder, as the d-wizard skill describes. Then send a change file with `{ "do": "add-round", "task": "<the task's title, exactly>", "file": "<the round's file name>" }`. The city attaches it to the task at once, with an Undo; the user answers it in their wizard, which saves the answers into the same file, and the city reads them back into the task. A new round replaces the task's old one.
- **Anywhere else, as on claude.ai:** deliver the round as a file, and tell the user to drop it on the task's panel in the city.

A copy of a task with a round carries it under "Wizard round", or "Brainstorm, round 1" or "round 2": in Claude Code it names the round's file, so read the questions or cards and their answers there; in a chat the answers are written in. Act on the answers as the d-wizard skill says: what was picked, typed or noted is decided. In the city summary, a task's `round` has `kind`, `round` or `brainstorm`.

## Hand it over

On claude.ai, save the file to `/mnt/user-data/outputs/` and present it. In Claude Code, write it where the user asked, or in the working directory, and give the path.

In the chat, keep it short. For tasks, list their titles. For a plan, list the milestones with their task counts and say how many ideas there are. Do not paste the JSON unless the user asks; the file is the deliverable. Then say how to load it: open the project in Nullovation City, press the more button, choose Load plan or tasks, then choose the file or paste its text.
