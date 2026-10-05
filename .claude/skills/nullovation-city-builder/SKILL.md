---
name: nullovation-city-builder
description: Design the building for a project in Nullovation City, the user's isometric pixel-art project city, as three concepts to choose from, each with a subject-only image prompt, a full image prompt for any service, and an animation prompt. Use this skill whenever the user pastes a Nullovation City builder card, asks for a building, block, or block art for one of their projects, wants a project's building redesigned, or describes the building they want, even if they never name the skill. Do not use it for changes to the city tool's own code, or for a project's tasks or plan, which is nullovation-city.
---

# Nullovation City builder

Nullovation City shows every project as one building on an isometric pixel map. Each building is a company that is always alive, whatever the project's status. This skill works out what a project's building should be and writes three concepts for the user to choose from. The user takes the chosen concept's prompts to an image service; Claude does not draw the building.

## 1. Understand the project

Read everything available: a builder card if the user pasted one, the conversation, the Claude project's files, and anything the user describes. When sources disagree, what the user describes wins. With nothing about the project at all, ask one short question and stop.

A builder card comes from the project's Copy for builder in the tool. It starts with `# Nullovation City builder card` and holds the project's name, its size signals (open and done tasks, milestones, notes, links), its description, its milestones, and its tasks. The user may add their own idea for the building under it.

Read for meaning: what the project is, who it is for, what kind of work it holds. The building shows what the company is. It never shows progress, stage, or status; those live in the tool's bubbles.

## 2. Write three concepts

Write three by default, or as many as the user asks for: two grounded ideas that read at once as this project, and one wild one that surprises. Make each a real building, not a variation of the others.

Every concept has a one-line pitch, then its card:

- **Name**: a short name for the building.
- **Idea**: what the building is, in one line.
- **Why it fits**: how it says what this project is.
- **Look**: the silhouette, the main colors, the materials.
- **Signature**: the one thing it is remembered by, such as a dome holding a tiny city, an orb floating in a cage, or a neon sign that half fails.
- **Supporting pieces**: up to two on the lot, such as a shed, a tank, a landing pad, a table under a parasol.
- **Lot**: the ground it stands on: paving, lawns, paths, an apron, flower beds, water. Every lot is its own; not every lot needs a ring of tiles.
- **Motion**: what moves, in plain words.
- **Size**: how big and tall it stands on its plot: small for a few tasks and one narrow goal, medium for most projects, a landmark only for the user's biggest, long-running work. The plot itself never changes size.
- **Leader**: who runs the building: a name, a role, and two or three visual traits.

The pitch and the card are what the user reads to choose, so they must make sense without the prompts.

## 3. The city's style

Every concept lives in the same city. Keep to this:

- Pastel sci-fi in SNES-era pixel art: white and pale panels with pastel trims, teal glass, soft glows, neon. Lean into the sci-fi and the strange; a building should never be plain.
- Color with intent: every building carries real color (lavender, coral, gold, pink, mint, sky), never white on white. One signature color leads.
- Detail that rewards a close look, and a silhouette that reads at the smallest zoom.
- 2:1 isometric, no perspective; light from the top left, so left faces are lit and right faces in shade; a 1 px dark outline round every shape.
- Soft sci-fi shapes: rounded corners, domes, pods, rings; no spikes or armor.
- The city hall is the standard to reach: a pink-trimmed building of teal glass under a dome that holds a tiny city, with lit windows. Aim for that level of color and character without needing it as a reference image.

## 4. Motion

Decide what moves from the building and its lot: lights, signs, water, a fan, a small vehicle, a glow. Keep the city's motion calm: slow and irregular, no pattern that visibly repeats, and only small things may move fast. Motion that crosses open sky, such as steam or a swinging crane, makes the file much larger, so use it only when it makes the building.

## 5. The three prompts

Under each concept's card, give three prompts, each in its own code block so it copies cleanly:

1. **Subject-only prompt.** The building, its supporting pieces, and its lot, with materials and colors in plain words, and where the glow sits. No style words and no sizes. This is for services such as PixelLab that set the style, outline, and size in their own settings.
2. **Full prompt.** The same subject, plus the style it needs where no settings carry it: isometric pixel art, 2:1 perspective, no perspective distortion, true pixels with hard edges, a 1 px dark outline, light from the top left, standing on a square isometric plot, transparent background. Without "isometric" and "2:1", most services draw a side view.
3. **Animation prompt.** A motion description for animating the finished still: what moves, how much, and how calmly, then that everything else stays perfectly still, and that it loops seamlessly. Animation tools read one start frame and a description of the motion, not a frame-by-frame plan.

In every prompt, describe colors in plain words, such as "pale pink trims" or "soft teal glass", never hex codes or palette names. Describe the subject in the order it is seen: the hero structure, its supporting pieces, then the lot.

## 6. Hand it over

Reply in the chat, never as a file. Write the three concepts in order, each as its pitch, its card, and its three prompt blocks. Nothing follows: each concept already carries what the user needs.

Do not remind the user of service settings such as the image size. When the user asks how to set up a service, what size to use, or how to animate, read `references/services.md` and answer from it.

Never use an em dash or an en dash in anything you write; use a comma, colon, semicolon, or hyphen instead.
