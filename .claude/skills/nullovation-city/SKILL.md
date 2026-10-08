---
name: nullovation-city
description: Write tasks, or a whole plan, for a project in Nullovation City, the user's pixel-city project tracker, as a JSON file the tool loads with Load plan or tasks in the project view's more menu. Use this skill whenever the user says "create nullovation tasks", "nullovation tasks", "add this to nullovation", or "nullovation-city"; asks to build, plan, set up, or restructure a project for Nullovation City or for their city; or pastes a Nullovation City project export (app "nullovation-city", kind "project"). It decides from the request whether to write a few tasks or a whole plan. Do not use it for a project's building art or leader, which is nullovation-city-builder; for changes to the city tool's own code; for Asana tasks, which is create-asana-task; or for to-do lists that are not meant for the city.
---

# Nullovation City: tasks and plans

Nullovation City shows every project as a building. Inside, a project has an About, milestones with tasks, notes, and links. This skill writes one of two JSON files for it:

- **A tasks file** adds one or a few tasks to a project. The user picks the milestone they go into when loading it, and nothing already in the project changes. This is the common case: dropping the tasks a conversation produced into the project it belongs to.
- **A plan** sets up or restructures a whole project: its About, milestones, tasks, and ideas. Loading it replaces the project's About, milestones, and tasks, after a warning, and adds its ideas to the notes.

Choose from the request. "Create nullovation tasks", "add this as a task", or anything about one or a few tasks means a tasks file. "Build", "plan", "set up", or "restructure the project" means a plan. When it is unclear, write a tasks file: it is the smaller change, and it never replaces anything.

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

## Hand it over

On claude.ai, save the file to `/mnt/user-data/outputs/` and present it. In Claude Code, write it where the user asked, or in the working directory, and give the path.

In the chat, keep it short. For tasks, list their titles. For a plan, list the milestones with their task counts and say how many ideas there are. Do not paste the JSON unless the user asks; the file is the deliverable. Then say how to load it: open the project in Nullovation City, press the more button, choose Load plan or tasks, then choose the file or paste its text.
