#!/usr/bin/env python3
"""Checks a Nullovation City tasks file or plan before it is handed over.

Errors are things the user would notice or the tool would drop: fix all of them.
Warnings are judgment calls: read them and fix what applies.

Usage: python3 check_plan.py <tasks-or-plan.json>
"""
import datetime, json, sys

LIMITS = {'name': 120, 'description': 8000, 'milestone': 120, 'task': 500, 'task_description': 8000, 'idea_title': 200}
ICONS = {'doc', 'code', 'github', 'claude', 'chat', 'folder', 'web'}
DASHES = {'\u2014': 'em dash', '\u2013': 'en dash'}
STATUS_WORDS = ['currently', 'current work', 'right now', 'in progress', 'working on', 'next step', 'this week', 'upcoming', 'so far', 'at the moment', 'status']


def main(path):
    errors, warnings = [], []
    try:
        data = json.load(open(path, encoding='utf-8'))
    except Exception as e:
        print(f'ERROR: not valid JSON: {e}')
        return 1

    def walk(x, where):
        if isinstance(x, str):
            for ch, name in DASHES.items():
                if ch in x:
                    errors.append(f'{where}: contains an {name}; use a comma, colon, semicolon, or hyphen')
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, f'{where}.{k}')
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f'{where}[{i}]')
    walk(data, 'plan')

    if data.get('kind') == 'tasks':
        return check_tasks(data, errors, warnings)
    if data.get('app') != 'nullovation-city' or data.get('kind') != 'plan' or data.get('version') != 1:
        errors.append('the top level needs "app": "nullovation-city", "kind": "plan" or "tasks", "version": 1')
    p = data.get('project')
    if not isinstance(p, dict):
        errors.append('the plan needs a "project" object')
        return report(errors, warnings, None)
    if 'name' in p and (not isinstance(p['name'], str) or not p['name'].strip()):
        errors.append('project.name, when present, must be a non-empty string; leave it out to keep the name')
    if isinstance(p.get('name'), str) and len(p['name']) > LIMITS['name']:
        errors.append(f'project.name is over {LIMITS["name"]} characters')
    desc = p.get('description')
    if not isinstance(desc, str) or not desc.strip():
        errors.append('project.description (the About) is missing; the project view opens with it')
    else:
        if len(desc) > LIMITS['description']:
            errors.append(f'project.description is over {LIMITS["description"]} characters')
        if len(desc) > 900:
            warnings.append(f'the About is {len(desc)} characters; an About should be one to three sentences')
        hits = [w for w in STATUS_WORDS if w in desc.lower()]
        if hits:
            warnings.append(f'the About mentions {hits}; it should hold only facts unlikely to change, never current work or status')
    ms = p.get('milestones')
    if not isinstance(ms, list) or not ms:
        errors.append('project.milestones must be a non-empty list')
        ms = []
    if len(ms) > 6:
        warnings.append(f'{len(ms)} milestones; plans usually need two to five, so check for groups that could merge')
    seen, first_open, n_tasks = {}, None, 0
    for i, m in enumerate(ms):
        where = f'milestone {i + 1}'
        if not isinstance(m, dict) or not isinstance(m.get('name'), str) or not m['name'].strip():
            errors.append(f'{where} has no name')
            continue
        where = f'milestone "{m["name"]}"'
        if len(m['name']) > LIMITS['milestone']:
            errors.append(f'{where}: the name is over {LIMITS["milestone"]} characters')
        tasks = m.get('tasks')
        if not isinstance(tasks, list) or not tasks:
            errors.append(f'{where} has no tasks')
            continue
        if len(tasks) > 10:
            warnings.append(f'{where} has {len(tasks)} tasks; check that each is needed, or split the milestone')
        for j, t in enumerate(tasks):
            tw = f'{where}, task {j + 1}'
            if not isinstance(t, dict) or not isinstance(t.get('text'), str) or not t['text'].strip():
                errors.append(f'{tw} has no title ("text")')
                continue
            n_tasks += 1
            tw = f'task "{t["text"][:50]}"'
            if len(t['text']) > LIMITS['task']:
                errors.append(f'{tw}: the title is over {LIMITS["task"]} characters')
            elif len(t['text']) > 90:
                warnings.append(f'{tw}: the title is long; aim for under about 80 characters')
            key = t['text'].strip().lower()
            if key in seen:
                errors.append(f'{tw} appears twice, also in {seen[key]}')
            seen[key] = where
            d = t.get('description')
            if not isinstance(d, str) or not d.strip():
                errors.append(f'{tw} has no description; every task needs one to be ready to work on')
            else:
                if len(d) > LIMITS['task_description']:
                    errors.append(f'{tw}: the description is over {LIMITS["task_description"]} characters')
            due = t.get('due')
            if due not in (None, ''):
                try:
                    datetime.date.fromisoformat(due)
                except Exception:
                    errors.append(f'{tw}: due must be YYYY-MM-DD, not {due!r}')
            if 'done' in t and not isinstance(t['done'], bool):
                errors.append(f'{tw}: done must be true or false')
            if first_open is None and not t.get('done'):
                first_open = t['text']
    for i, idea in enumerate(p.get('ideas') or []):
        if not isinstance(idea, dict) or not (str(idea.get('title') or '').strip() or str(idea.get('text') or '').strip()):
            errors.append(f'idea {i + 1} is empty')
        elif len(str(idea.get('title') or '')) > LIMITS['idea_title']:
            errors.append(f'idea {i + 1}: the title is over {LIMITS["idea_title"]} characters')
    for i, link in enumerate(p.get('links') or []):
        if not isinstance(link, dict) or not isinstance(link.get('url'), str) or not link['url'].strip():
            errors.append(f'link {i + 1} has no url')
        elif link.get('icon') not in ICONS:
            warnings.append(f'link {i + 1}: icon {link.get("icon")!r} is not one of {sorted(ICONS)}; the tool picks one from the address')
    summary = f'{len(ms)} milestones, {n_tasks} tasks, {len(p.get("ideas") or [])} ideas, {len(p.get("links") or [])} links. What is next: {first_open or "nothing open"}'
    return report(errors, warnings, summary)


def check_task(t, tw, errors, warnings, seen, where):
    if not isinstance(t, dict) or not isinstance(t.get('text'), str) or not t['text'].strip():
        errors.append(f'{tw} has no title ("text")')
        return False
    tw = f'task "{t["text"][:50]}"'
    if len(t['text']) > LIMITS['task']:
        errors.append(f'{tw}: the title is over {LIMITS["task"]} characters')
    elif len(t['text']) > 90:
        warnings.append(f'{tw}: the title is long; aim for under about 80 characters')
    key = t['text'].strip().lower()
    if key in seen:
        errors.append(f'{tw} appears twice')
    seen[key] = where
    d = t.get('description')
    if not isinstance(d, str) or not d.strip():
        errors.append(f'{tw} has no description; every task needs one, even a short one')
    elif len(d) > LIMITS['task_description']:
        errors.append(f'{tw}: the description is over {LIMITS["task_description"]} characters')
    due = t.get('due')
    if due not in (None, ''):
        try:
            datetime.date.fromisoformat(due)
        except Exception:
            errors.append(f'{tw}: due must be YYYY-MM-DD, not {due!r}')
    return True


def check_tasks(data, errors, warnings):
    if data.get('app') != 'nullovation-city' or data.get('version') != 1:
        errors.append('the top level needs "app": "nullovation-city", "kind": "tasks", "version": 1')
    ms = data.get('milestone')
    if ms is not None and (not isinstance(ms, str) or len(ms) > LIMITS['milestone']):
        errors.append(f'milestone, when present, must be a name of up to {LIMITS["milestone"]} characters')
    tasks = data.get('tasks')
    if not isinstance(tasks, list) or not tasks:
        errors.append('a tasks file needs a non-empty "tasks" list')
        tasks = []
    seen = {}
    n = sum(1 for j, t in enumerate(tasks) if check_task(t, f'task {j + 1}', errors, warnings, seen, 'this file'))
    return report(errors, warnings, f'{n} tasks' + (f' for the milestone "{ms}"' if ms else ', milestone picked when loading') + '.')


def report(errors, warnings, summary):
    for e in errors:
        print('ERROR:', e)
    for w in warnings:
        print('WARNING:', w)
    if summary:
        print('SUMMARY:', summary)
    print('OK' if not errors else f'{len(errors)} errors to fix')
    return 1 if errors else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
