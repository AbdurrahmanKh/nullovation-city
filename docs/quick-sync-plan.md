# Quick Sync: the plan

Every city that syncs keeps the same city through one shared copy in a private GitHub repository, until production's database. Written 27 October 2026, when Abdurrahman picked the private repository (Quick Sync, Round 2, S1), "maybe that is the way until production". Nothing of it is built.

What was decided, and where:
- **S1 (27 October, in the chat):** a private GitHub repository.
- **S2 (Round 1):** an open city checks every 15 seconds while in view, and when it opens or comes back into view; it sends 3 seconds after the last change.
- **J1 (Round 1):** the installed app on the PC, the local copy he tests builds with, the phone and a second computer sync; a borrowed browser does not. The token stays in its browser, never in the data file, a backup or an export.
- **C1 (Round 1):** the newest change wins, with no question; the backups and the repository's history are the way back.
- **R1 (Round 1):** reports read, what Gus and Proxima said today and the day's parties travel; Claude Code at work and Claude's changes that ask first stay on the PC.
- **M1 (Round 1):** a change made in another city plays as if done here: the burst, the party, the truck, the ghost rising away.
- **O1 (Round 1):** the app first (built at 0.1.67), then sync.

Everything else below is reasoned, not asked, and marked so where it matters.

## 1. Why GitHub, and what it costs

Without a server or a database, a page on GitHub Pages needs a store it can write to from the PC and the phone, with a sign-in that does not run out every hour. GitHub's API does that: the page writes through it with a token, and GitHub makes each commit. The better ways all need a server or a database, which is what production brings.

What it costs, and how the plan handles each:
- **A commit for every send:** a few dozen to a couple of hundred a day. Each send changes only the projects that changed (section 2), so a commit is small, and the history is a version of the city for every send.
- **The token sits in the browser:** any page on abdurrahmankh.github.io can read it, the wizard included. It is a fine-grained token for that one repository, with Contents only, so at worst it can read and write the city.
- **Not instant:** a change shows in another open city within about 15 seconds, and in a closed one when it opens.
- **GitHub is not a database:** one person's use is far under its limits (5,000 requests an hour for a token; a check that finds nothing new does not count).

## 2. The shared copy

A private repository, `AbdurrahmanKh/nullovation-city-data` unless he names another, on its `main` branch:

| File | Holds |
|---|---|
| `city.json` | `{ app, kind: 'shared-city', format: 1, data: 3, wrote, at, world, city, leaders }`: the map, the city's settings, the leaders with their portraits named by fingerprint; `data` is the database version, `wrote` the version of the city that wrote it |
| `projects/<id>.json` | One per project, as the database holds it, its art named by fingerprint (`art.file`) |
| `art/<fingerprint>.<png, gif, jpg or webp>` | Each picture once, as its own bytes, named by its SHA-256 |
| `heard.json` | What travels from this browser's own keys (section 5) |

- A project per file keeps each commit to what changed: ticking a task writes one project file, not the whole city.
- Pictures go as files, not as text, so they take their own size, not a third more, and each goes once: a building moved or renamed sends no picture again.
- A deleted project's file goes from the repository; a picture nobody names any more stays (the history has it anyway).
- The repository's README says what it is, written by the first city.

## 3. Setting it up, once

On github.com:
1. **The repository:** New repository, named `nullovation-city-data`, Private, with Add a README ticked, so it has a `main` branch from the start.
2. **A token per device:** Settings, Developer settings, Personal access tokens, Fine-grained tokens, Generate new token. Name it for the device ("City on the phone"); the longest expiry it offers; Repository access, Only select repositories, the city's repository; Repository permissions, Contents, Read and write. Each device having its own means the phone's can be taken back alone.

In each city, Settings, Saving, Sync: the repository's name and the token, then Connect. The order:
1. **The app on the PC first:** the repository has only its README, so this city starts the shared copy from itself.
2. **Then the phone, the local copy and a second computer:** each saves a backup of itself first (a download, `nullovation-city-backup-before-sync-YYYY-MM-DD.json`), then takes the shared copy in place of its own city.

Connect checks before it writes anything: the token works, it can write the repository, and the repository is private. A public one is refused, since the city holds every project, note, link and folder path.

## 4. How a city syncs

The tab that syncs is the one in use, as with the data file today (`nullovation-city:fileWriter`); the others stand by.

- **The base:** each city keeps the shared copy as it was at the commit it last synced, with that commit's id, in IndexedDB (a new `sync` store, so the database opens at version 3).
- **Checking:** every 15 seconds while in view, and on opening and coming back into view, it asks GitHub for `main`'s latest commit, naming the one it has (`If-None-Match`), so an answer of "nothing new" is quick and free. It asks with the browser's cache off, since GitHub lets a browser keep an answer for 60 seconds.
- **Receiving:** a new commit is read (the files that changed since the base), merged with this city (below), and applied in place; the new commit becomes the base.
- **Sending:** 3 seconds after the last change, when the city differs from its base, it writes the files that changed and any new picture as one commit on top of the base, then moves `main` to it. GitHub refuses that move when another city wrote since; the city then receives, merges and sends again. So a send made on an old version is never lost.
- **Hidden or offline:** going out of view sends what is waiting at once. A phone that closes the page first, or is offline, keeps its changes in the city, and they go on the next open: late, never lost. While offline it waits and says so under the logo only after a few minutes.
- **A read older than its own send** (GitHub's copies can lag a second behind a write) is passed over.

### The merge (reasoned)

Three ways, thing by thing: this city, the base, and the shared copy now.
- **The things:** each project's own fields (name, description, deadline, plot, building, flip, particles, leader, urgency, pin, star, art), each task, milestone, note and link by its id, each leader, each city setting, and the map.
- **Changed on one side only:** that side's version.
- **Changed on both:** the newer one wins (C1). Newer is decided by the time: this city's last change against the shared commit's time. No new times are kept in the city.
- **Deleted on one side:** gone, unless the other side changed it later.
- **Order** (tasks in their milestones, links, milestones): the order from the side that changed it, else the shared copy's; what is new goes where its side had it.
- **Activity:** both sides' lines kept, in time order, 400 a project as today.
- **Kept the larger:** a project's `updatedAt` and `lastWorked`.
- **Then the usual tidying,** as a backup gets when read: one star in the city (the newer), plots that clash, pins and leaders that point at nothing.

### Applying a received city (reasoned)

- In place, with no reload: the database is replaced, then the map, the side bar, the status card and any open view redraw, as Import does today, without its question and without dropping the pictures.
- What is open stays open while its thing is still there: the selected building, the project view, a task's panel. One whose thing is gone closes.
- While you are typing in a field, receiving waits until you leave it, so nothing changes under the caret.
- A picture whose fingerprint changed is fetched and stored, then the building redraws.

### Another tab of the same city

Today two tabs of one browser do not read each other's saves. With sync, a tab holding an older city would send it as if it were new. So first: a tab reads the city again when another tab saves it (the `storage` event on `nullovation-city:v1`), as News already does for its own key.

## 5. What else travels, and what stays

- **Travels in `heard.json` (R1):** Proxima's reports read and what she said (`nullovation-city:proxima`), the days Gus spoke (`nullovation-city:gus`), the day each milestone threw its party (`nullovation-city:celebrate`), and the leaders' news heard (from `nullovation-city:news`). Merged by putting both together, the later day kept.
- **Stays in each city:** Claude Code at work and Claude's reports, the changes that ask first (they live in the Claude folder's `inbox/pending`), the bar's buttons, the camera, motion, the garbage and ghosts switches, the postcard, folder links, the wizard's address, and the sync token.
- **The PC's jobs (reasoned):** the data file, the daily backups, the summary for Claude and Claude's inbox belong to the city they are connected in; connect them in the app. Two cities taking the same inbox would apply a change twice, and the twice would sync, so the city that takes the inbox writes `inbox/.city` with its id every 3 seconds, and another city takes the inbox only once that file is 15 seconds old. The summary is written by the same city.

## 6. A change from another city (M1)

What arrives while the city is open and in view plays here:
- **A tick:** its building's burst.
- **The last task of a milestone of 2 or more:** the street party and Proxima's announcement, unless this city threw that party today.
- **The ghost** of a ticked task rises away, and **the truck** comes for garbage that went: both already follow the city's state within a second.

What arrives as the city opens shows as it is, with no burst, party or truck, as garbage does today.

## 7. In the city

- **Settings, Saving, Sync,** after The app:
  - Off: "Keep this city the same on your PC and your phone, through a private GitHub repository." The repository and the token, Connect, and How to set it up, which unfolds section 3's steps.
  - On: "Synced with AbdurrahmanKh/nullovation-city-data. Checked 12 seconds ago.", with Pause sync and Disconnect. Disconnect forgets the token and leaves the city as it is.
  - Pause sync (reasoned): for the local copy while testing a build he does not trust yet; a paused city neither sends nor receives, and says so under the logo.
- **Under the logo, as saving trouble shows today:** "Sync stopped: GitHub refused the token. Paste a new one.", "Sync is waiting for the network.", "Sync stopped: the shared copy is from a newer city. Reload to update." (a city whose database version is older than the shared copy's stops sending until it reloads, and the app loads the newest version on reload).
- **Kept in this browser:** `nullovation-city:sync`, `{ repo, token, paused }`; never in the database, the data file, a backup or an export, which the tests check.
- **The code:** `18-sync.js` (`Sync`): the checks, the sends, the merge (as plain functions, tested alone), applying in place, `heard.json`; `persistNow` in `20-model.js` tells it of every change, as it tells the data file. Its part of Settings in `72-settings.js`, the inbox's lease in `69-inbox.js`.

## 8. Tests

- **test44_sync:** a fake GitHub in the test (Python, like test42's server) answering only what the city asks: the branch's latest commit with "nothing new", commits, files, writing a commit, moving `main` and refusing a move on an old version, a refused token and a public repository.
- **What it checks:**
  - Connect: its checks, starting the shared copy, and the backup before taking it.
  - Two browsers as two cities: a change in one showing in the other, on each side.
  - The merge alone, every case above: one side, both sides, deleted against changed, order, Activity, the star.
  - A send on an old version refused, merged and sent again.
  - Pictures once by fingerprint.
  - Applying in place with a panel open, and waiting while typing.
  - Offline and back; the version guard; Pause and Disconnect.
  - A second tab following; the inbox's lease; M1's burst and party.
  - No token anywhere it must not be.
- **Never the real GitHub:** the passes stay off it, since their fresh browsers hold no token and the fake answers in its place.

## 9. Build order

1. **Sync, part 1, the shared copy:** a second tab following, Settings' Sync with Connect and its checks, the shared copy, checking, sending, the merge, applying in place, pictures, the trouble lines, Pause and Disconnect, test44.
2. **Sync, part 2, what travels and plays:** `heard.json` (R1), a change from another city playing (M1), and the inbox's lease.

Each is built, then tested by him before the next. Part 1 on its own already keeps the PC and the phone the same.

The task "Sync the cities through a shared copy on GitHub" is done when a change made on the phone shows on the PC within about 15 seconds, and the other way round.

## 10. Later, not in this plan

- Restoring a city from the repository's history, from inside the city.
- Working with Claude from the phone (R1: "for later, I want to be able to work from my phone").
- Moving to production's database, which replaces all of this.
