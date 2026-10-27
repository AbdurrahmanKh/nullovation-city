# The city on a phone

A report for the task "Improve the phone experience" in Nullovation City Hall, UX Mastery, written 27 October 2026 on 0.1.73.

How it was checked: the built page opened in Chrome as a phone, in a private headless browser, with a copy of the city from the data file of 24 October imported (19 projects, the leaders and the art). Three sizes: 390 by 844 at 3x with touch (an everyday phone), 360 by 740 (a small Android phone), and 844 by 390 (a phone on its side). Every screen was looked at, and what sits off the screen, the size of every button and the type size of every field were measured.

Not checked, since it needs a real phone: the on-screen keyboard, Safari's own ways on an iPhone, the installed app's window, and how the gestures feel under a finger.

## Bad: broken on a phone

1. **The map's bar runs off the left edge.** It needs about 440 px; on 390 px, Traffic and Bubbles are off the screen and cannot be reached, and Time of day is cut in half.
2. **The project view's top is cut off on the right.** The building picture, the leader card's Change, the About and What is next run about 50 px past the edge: their column keeps the picture's 440 px and never shrinks. The lists under them fit.
3. **The Menu button covers what is under it.** The status card's title, when its building sits near the top; and every speech bubble (Gus, Proxima, a leader's news) opens over the button, so the menu cannot be reached until the bubble closes.
4. **Speech bubbles cover the drawer.** With Proxima's bubble showing, Reports and the Leaders panel open under it.
5. **Toasts sit on the map's bar.**
6. **The shortcut wheel runs off the screen.** A shortcut on its right sat at 353 to 456 px on a 390 px phone.
7. **On its side, a phone keeps the side bar docked.** It takes 300 of 844 px, the project view gets 544 by 390, and the task panel covers half of it.
8. **iPhone: fields under 16 px make Safari zoom the page in when tapped.** Search and Find a task 15 px, Add a task 14, the sync fields 13, a task's description 15, a leader's name and role 15, Settings' times and dates 14.

## Missing: no way to do it on a phone

1. **Stepping inside with a double tap.** Two taps only select the building (the double-click counts with a mouse only); the way in is the card's Enter.
2. **The one-line add over the map.** Enter or T only; there is no button for it.
3. **The shortcut wheel.** Right-click or F only, and a long press lifts the building instead (Clunky 1).
4. **Esc.** Backing out one layer at a time, and the task panel's undo ("Esc undoes everything since it opened"), have no button. Android's back gesture leaves the city rather than closing the open panel.
5. **Hopping between buildings** (Q and E).
6. **Open in Claude on a phone.** Cowork, Code and Terminal open the desktop app, so on a phone they cannot work; whether the Claude phone app takes the city's Chat link is untested.

## Clunky

1. **A long press on a building lifts it to move it,** after 380 ms, as hold then drag does with a mouse. A finger resting on a building and then sliding a little moves it to another plot.
2. **Small targets.** Pins, copy and Claude icons are 24 px, checkboxes 18 px, and a news face's dismiss 20 px, on the face's own corner, so opening a leader's news can dismiss it. A finger is comfortable at 40 to 48 px.
3. **The status card moves after a tap,** as the map glides the building into view, so a quick second tap can land on another button: in the test, a tap meant for Add a task landed on I worked!
4. **All tasks shows "Shift: Create Think Errand" under every untagged row** on a touch screen, since nothing can point at a row to reveal them: here 166 of 173 open tasks, which makes the list about half again as long.
5. **Keyboard words on a phone:** the one-line add's head ("Enter adds · Shift+Enter adds and stays · Ctrl+Enter adds and opens"), the task panel's foot ("Esc undoes everything since it opened"), and the controls guide behind Settings' ?, which lists keys only.
6. **The speech bubbles are big for a phone.** Gus's first word of the day, with his 100 px face and his report, fills the top half of the screen; a leader's news or Proxima's report a third.
7. **The zoom reads 0.7x on opening,** since the city fits the screen at whole screen pixels and a phone has three of them to a point.

## Works well

- The drawer, Settings, Reports, the Leaders panel and a leader's editor, All tasks, the task panel, Open in Claude's panel and the one-line add (opened from code) fit 390 px.
- Drag to pan and pinch to zoom on the map; the drawer and the panels scroll.

## The work, in order

1. **Built in 0.1.74, what was plainly broken:** Bad 1 to 8; a double tap steps inside (Missing 1, the double-click Rethink the One-Line Add E1 asked for, on a touch screen); no words for keys on a touch screen (Clunky 5, but the controls guide); and a speech bubble that opens by itself waits while the project view covers a phone's map, where it had opened out of sight.
2. **Decided in The City on a Phone, Round 1** (`wizard-rounds/2026-10-27-phone-round1.json` in the Claude folder, attached to the task), **built in 0.1.75:** G1 a long press opens the shortcut wheel, and on a phone buildings move in Edit City only (Clunky 1, Missing 3); G2 Android's back closes one layer at a time, keeping what was typed (Missing 4); B2 bigger tap areas with the same look (Clunky 2); B4 Open in Claude is Copy only on a phone (Missing 6); L2 a 64 px face in the speech bubbles on a phone (Clunky 6); S1 a phone's own controls guide (Clunky 5); S2 the zoom in screen pixels (Clunky 7). Kept as they were: G3 no undo in the task panel on a phone, B3 a news face's dismiss on its corner, L1 the shift tags in All tasks. Waiting for a pick in the chat: B1, where a phone opens the one-line add (Missing 2).
3. **Left as it is:** the card moving while the map glides (Clunky 3) lasts 0.4 s, and a person waits for it to settle; only the test's instant second tap hit another button. Hopping between buildings (Missing 5): on a phone, a drag and a tap do it.
4. **On a real phone, once 0.1.74 is pushed:** the keyboard over the status card's Add a task and the task panel, and how a double tap and a pinch feel.
