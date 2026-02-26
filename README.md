# Learn

> A full-stack classroom and live-coding platform built with Django, Django Channels, CodeMirror, and Vite.
> Deployed at: **https://nwte-capstone-ba87c892eb74.herokuapp.com**

---

## Table of contents

1. [Project overview](#project-overview)
2. [Tech stack](#tech-stack)
3. [User roles](#user-roles)
4. [Features](#features)
5. [UX design](#ux-design)
6. [Data model](#data-model)
7. [Project structure](#project-structure)
8. [Local development](#local-development)
9. [Heroku deployment](#heroku-deployment)
10. [Agile project management](#agile-project-management)
11. [Testing documentation](#testing-documentation)
12. [AI reflection](#ai-reflection-lo8)
13. [Credits and third-party licences](#credits-and-third-party-licences)

---

## Project overview

**Learn** is a web-based classroom management and live coding platform built as a personal course project. It connects teachers and students in a shared, role-driven environment where:

- An admin sets up subjects, class groups, and student enrolments.
- Teachers create and manage tasks for their assigned groups, grade submissions, and run live coding sessions.
- Students complete tasks in an in-browser code editor, submit their work, and receive graded feedback.
- During a live task session a teacher can observe any connected student's editor in real time over a WebSocket connection.
- Any two users can exchange direct messages with instant delivery via WebSocket.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 |
| Async / WebSocket | Django Channels 4 + Daphne |
| Channel layer | Redis (channels-redis) |
| Database (production) | PostgreSQL via dj-database-url |
| Database (local) | SQLite |
| Frontend bundler | Vite + django-vite |
| Code editor | CodeMirror 6 (lang-python, lang-javascript, theme-one-dark, search) |
| In-browser Python | Pyodide (CDN, lazy-loaded) |
| Static files | WhiteNoise |
| Deployment | Heroku (Node + Python buildpacks) |
| Auth | Django built-in + custom Profile model |

---

## User roles

### Student
- Views assigned task list, filterable by group, teacher, graded/ungraded, submitted/unsubmitted.
- Opens tasks in the CodeMirror editor; work autosaves every few seconds and is backed up in localStorage.
- Runs Python code directly in the browser via Pyodide (no server-side execution).
- Submits final work and views graded feedback with score and teacher comment.
- Sees a "Teacher is watching" indicator during a live session and can send a help-request notification.
- Sends and receives direct messages with other users in real time.
- Manages own profile (display name, bio, phone).

### Teacher
- Creates tasks (text or Python type) with optional starter code for groups they are assigned to.
- Edits and deletes their own tasks; toggles a task live/inactive.
- Opens the live task room to observe connected students' editors in real time.
- Receives help-request notifications from students.
- Grades final submissions with a numeric score and written comment.
- Views group announcements and student lists for their groups.
- Posts announcements to class groups.
- Sends and receives direct messages.
- Manages own profile.

**Note:** Teachers cannot create subjects or class groups, and cannot enrol students. These actions are performed exclusively by the admin.

### Admin (superuser)
- Logs in and is redirected directly to the site admin dashboard at `/admin-site/`.
- The admin dashboard is a self-contained area; the regular site navigation is not shown to admin users.
- Creates and manages subjects, assigns teachers to subjects.
- Creates and manages class groups linked to subjects.
- Enrols and removes students from groups.
- Views and edits all user accounts and profiles.
- Views platform-wide statistics (user counts, groups, tasks, submissions).

---

## Features

### Authentication
- Register with username, password, and role (student/teacher).
- Login redirects to the role-specific dashboard automatically; admins go to `/admin-site/`.
- `@login_required` protects all authenticated views; `@role_required` blocks cross-role access (HTTP 403).
- `post_save` signal auto-creates a Profile for every new User.

### Classroom management (admin only)
- Subjects link a topic name to a teacher profile.
- Class groups are linked to a subject and contain students via GroupMembership.
- Admin can add/remove students from groups, rename groups, reassign subjects, or delete groups.

### Assignments and submissions
- Tasks have a title, description, type (text/python), optional starter code, and a live flag.
- First visit to a task auto-creates a Submission and TaskDocument.
- Content autosaves every few seconds; localStorage backs up unsaved changes.
- Manual Save creates a TaskDocumentVersion snapshot.
- Students submit with a Submit button which creates a FinalSubmission record.
- Teachers grade via a form that saves a numeric score and comment.

### Live code editor (WebSocket)
- CodeMirror 6 editor with Python/JavaScript highlighting, One Dark theme, and search.
- Each task page connects to a WebSocket room keyed by task ID.
- Teacher opens `/editor/room/<task_id>` to see the connected student list.
- Clicking a student sends a `watch_student` broadcast; the teacher's editor syncs to that student's content.
- The watched student receives a `being_watched` message and sees a badge.
- Students have a floating help button that sends a `help_request` to the teacher.
- Connection indicator (green = Connected, red = Offline) shows WebSocket state.

### In-browser Python execution (Pyodide)
- Python-type tasks show a Run button.
- Pyodide loads from CDN on first Run click (lazy).
- stdout, return values, and tracebacks are shown in an output panel.

### Direct messaging
- DM threads between any two users at `/editor/messages/<user_id>/`.
- Message history shown on page load; new messages delivered instantly via WebSocket.
- Unread counts shown in the sidebar badge.

### Admin site dashboard
- Self-contained area at `/admin-site/` for superusers only.
- View all users, create/edit/delete subjects and groups, enrol students.
- Platform-wide statistics on the dashboard home.

---

## UX design

### Design principles
- **Role-aware navigation**: sidebar links differ per role; irrelevant actions are hidden.
- **Minimal friction**: first visit to a task auto-creates the submission record.
- **Live feedback**: autosave indicator, connection dot, and watching badge give ambient feedback.
- **Dark mode**: single colour scheme used throughout.

### Colour palette

| Token | Value | Used for |
|---|---|
| `--bg-900` | `#06070a` | Page background |
| `--bg-800` | `#0f1724` | Sidebar |
| `--accent` | `#7c5cff` | Primary actions, links |
| `--accent-2` | `#39d1a2` | Success states, badges |
| `--muted` | `#98a0b3` | Secondary text |
| `--border` | `rgba(255,255,255,0.06)` | Card edges |

### Wireframes

#### Base layout

```
+----------------+----------------------------------+
|   SIDEBAR      |   MAIN CONTENT                   |
|                |                                  |
|  [Avatar]      |  Page header + actions           |
|  Username      |  -------------------------------- |
|  ----------    |                                  |
|  Nav links     |  Cards / tables                  |
|  Logout        |                                  |
+----------------+----------------------------------+
```

#### Task editor (student)

```
+--------------------------------------------------+
|  Task: Title                    [Save] [Submit]  |
|  > Description (collapsible)                     |
+--------------------------------------------------+
|  +---------------------------+  +-----------+    |
|  |  CodeMirror editor        |  | Task info |    |
|  |                           |  | Group     |    |
|  |  def solve():             |  | Teacher   |    |
|  |      ...                  |  | [Run]     |    |
|  +---------------------------+  +-----------+    |
|  [o] Connected   Saved 12:34                     |
+--------------------------------------------------+
```

#### Mobile (<900px)

```
+-------------------------+
| [=]  Learn              |  burger button
+-------------------------+
|  Full-width content     |
|  Tables scroll horiz.   |
+-------------------------+
```

### Design decisions

| Decision | Rationale |
|---|---|
| Dark mode only | Reduces fatigue during long coding sessions |
| Role-aware sidebar | Users only see actions relevant to their role |
| Collapsible task description | Maximises editor space |
| Auto-create Submission on task open | Removes setup step for students |
| Tables with horizontal scroll on mobile | Preserves density on desktop, usable on mobile |

### Responsiveness

- Breakpoints: `900px` (tablet) and `600px` (mobile).
- Below `900px`: sidebar slides in from left behind a burger button; content is full width.
- Tables wrapped in `overflow-x: auto` containers to allow horizontal scroll instead of breaking layout.
- Grids collapse to single column; form rows stack vertically.
- Tested in Chrome DevTools at 375px, 768px, and 1280px.

---

## Data model

```
User (Django built-in)
 +-- Profile          role: student | teacher

Subject              teacher -> Profile
 +-- ClassGroup
      +-- GroupMembership  student -> Profile
      +-- Announcement     created_by -> Profile
      +-- Task             created_by -> Profile, type: text | python
           +-- Submission  student -> Profile, grade, comment
           |    +-- FinalSubmission
           +-- TaskDocument  student -> Profile, content
                +-- TaskDocumentVersion  author -> Profile

DirectMessage        sender -> User, recipient -> User, read
LiveTaskSession      document -> TaskDocument, user -> Profile
```

---

## Project structure

```
DjangoProject/      Settings, ASGI config, root URLs
accounts/           Registration, login, profile
assignments/        Task and submission models + views
classrooms/         Subject, ClassGroup, GroupMembership, Announcement
editor/             WebSocket consumer, TaskDocument, DirectMessage
pages/              Dashboards, task CRUD, group views, analytics, admin views
templates/          HTML templates
static/css/         Stylesheets
static/js/          base.js (CodeMirror + WebSocket), editor.js (entry point)
static_build/       Vite production build output
vite.config.js      Vite config
package.json        npm scripts
Procfile            Heroku: daphne ASGI
requirements.txt    Python dependencies
```

---

## Local development

### Prerequisites

- Python 3.11+, Node.js 20+, Redis

### Setup

```bash
git clone https://github.com/nwtes/DjangoProject.git
cd DjangoProject
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
npm install
```

Create `env.py` in the project root (never commit this):

```python
import os
os.environ['SECRET_KEY'] = 'your-local-secret-key'
os.environ['DEBUG'] = 'True'
```

```bash
python manage.py migrate
redis-server                    # separate terminal
npm run dev                     # Vite on :5173
python manage.py runserver      # Django on :8000
```

Visit `http://localhost:8000`.

---

## Heroku deployment

### Buildpacks (order matters)

```bash
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
```

### Add-ons

```bash
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini
```

### Environment variables

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | Yes | Must be `False` in production |
| `DATABASE_URL` | Auto | Set by Postgres add-on |
| `REDIS_URL` | Auto | Set by Redis add-on |
| `DJANGO_VITE_DEV_MODE` | Yes | Must be `False` in production |

```bash
heroku config:set SECRET_KEY="..." DEBUG="False" DJANGO_VITE_DEV_MODE="False"
```

### Deploy

```bash
git push heroku main
heroku run python manage.py migrate
```

The Node buildpack runs `npm run heroku-postbuild` (Vite build), then the Python buildpack runs `collectstatic`. Daphne serves both HTTP and WebSocket via the ASGI entry point in `Procfile`.

---

## Agile project management

This project was planned and tracked using **GitHub Projects (v2)**. All user stories were created as GitHub Issues, labelled by epic and MoSCoW priority, and assigned to sprint milestones.

**Board:** https://github.com/users/nwtes/projects/1
**Issues:** https://github.com/nwtes/DjangoProject/issues

### Project goals

| ID | Goal |
|---|---|
| G1 | Provide admin tools to manage subjects, groups, and enrolments |
| G2 | Provide teachers with task creation, grading, and live session tools |
| G3 | Provide students with an in-browser coding and submission workflow |
| G4 | Enable real-time communication between teachers and students |
| G5 | Ensure secure, role-based access throughout the platform |
| G6 | Deploy a production-ready application accessible via the web |

### Epics

| Epic | Goals |
|---|---|
| E1 - Authentication & Profiles | G5 |
| E2 - Classroom Management (admin) | G1 |
| E3 - Assignments & Submissions | G2, G3 |
| E4 - Live Code Editor | G3, G4 |
| E5 - Direct Messaging | G4 |
| E6 - Deployment & Infrastructure | G6 |

### User stories

#### E1 - Authentication & Profiles

| ID | Story | Priority | Status |
|---|---|---|---|
| US-01 | As a new user I can register with a username, password and role | Must Have | Done |
| US-02 | As a returning user I can log in and be redirected to my role dashboard | Must Have | Done |
| US-03 | As a logged-in user I can view my profile page | Should Have | Done |
| US-04 | As a logged-in user I can edit my display name and bio | Should Have | Done |
| US-05 | As an unauthenticated user I am redirected to login on protected pages | Must Have | Done |
| US-06 | As a student I cannot access teacher-only views | Must Have | Done |

#### E2 - Classroom Management

| ID | Story | Priority | Status |
|---|---|---|---|
| US-07 | As an admin I can create a subject and assign a teacher to it | Must Have | Done |
| US-08 | As an admin I can create a class group linked to a subject | Must Have | Done |
| US-09 | As an admin I can enrol students into a group | Must Have | Done |
| US-10 | As an admin I can remove students from a group | Must Have | Done |
| US-11 | As a teacher I can post an announcement to a class group | Should Have | Done |
| US-12 | As a student I can view announcements and classmates in my group | Should Have | Done |

#### E3 - Assignments & Submissions

| ID | Story | Priority | Status |
|---|---|---|---|
| US-13 | As a teacher I can create a task with title, description and starter code | Must Have | Done |
| US-14 | As a teacher I can edit an existing task | Should Have | Done |
| US-15 | As a teacher I can delete a task | Should Have | Done |
| US-16 | As a student I can view my assigned tasks with filters | Must Have | Done |
| US-17 | As a student my work autosaves and is backed up in localStorage | Must Have | Done |
| US-18 | As a student I can submit my final answer | Must Have | Done |
| US-19 | As a teacher I can grade a submission and leave a comment | Should Have | Done |
| US-20 | As a student I can view my graded submission with feedback | Should Have | Done |

#### E4 - Live Code Editor

| ID | Story | Priority | Status |
|---|---|---|---|
| US-21 | As a student I can write code in a CodeMirror editor | Must Have | Done |
| US-22 | As a student I can run Python code in the browser via Pyodide | Should Have | Done |
| US-23 | As a teacher I can open a live session and see connected students | Must Have | Done |
| US-24 | As a teacher I can click a student to view their code in real time | Must Have | Done |
| US-25 | As a student I see a watching indicator when a teacher observes me | Should Have | Done |
| US-26 | As a student I can send a help request to the teacher | Could Have | Done |
| US-27 | As a student my unsaved content is preserved in localStorage on refresh | Could Have | Done |

#### E5 - Direct Messaging

| ID | Story | Priority | Status |
|---|---|---|---|
| US-28 | As a user I can open a DM thread with another user | Must Have | Done |
| US-29 | As a user I can send a message that appears instantly | Must Have | Done |
| US-30 | As a user I can see full message history when I open a thread | Must Have | Done |
| US-31 | As a user messages are marked as read when I open the thread | Should Have | Done |

#### E6 - Deployment & Infrastructure

| ID | Story | Priority | Status |
|---|---|---|---|
| US-32 | As a developer I can deploy to Heroku with a single git push | Must Have | Done |
| US-33 | As a developer static files are collected and served correctly | Must Have | Done |
| US-34 | As a developer environment secrets are not in source code | Must Have | Done |
| US-35 | As a developer WebSocket connections work in production | Must Have | Done |

### MoSCoW summary

| Priority | Count |
|---|---|
| Must Have | 22 |
| Should Have | 11 |
| Could Have | 2 |

### Definition of Done

A story is Done when: code is committed, existing tests pass, the feature works on Heroku, and relevant templates/URLs/migrations are included.

---

## Testing documentation

### Running tests

```bash
python manage.py test                  # all tests
python manage.py test --verbosity=2   # verbose
python manage.py test accounts         # single app
```

All 66 tests run against an isolated SQLite test database created and destroyed automatically.

### Results summary

| App | Tests | Result |
|---|---|---|
| accounts | 16 | PASS |
| assignments | 18 | PASS |
| classrooms | 9 | PASS |
| editor | 8 | PASS |
| pages | 15 | PASS |
| **Total** | **66** | **All pass** |

### Python test procedures

#### accounts

| # | Test | Expected | Result |
|---|---|---|---|
| 1 | Profile auto-created on user creation | Profile exists with role='student' | PASS |
| 2 | Profile default role is student | role == 'student' | PASS |
| 3 | Profile str returns username | 'charlie' | PASS |
| 4 | Profile role can be set to teacher | role == 'teacher' | PASS |
| 5 | display_name optional, can be set | Saves correctly | PASS |
| 6 | bio optional, can be set | Value persisted | PASS |
| 7 | Register page loads | 200 OK | PASS |
| 8 | Register creates student user | Redirect + student role | PASS |
| 9 | Register creates teacher user | Teacher role set | PASS |
| 10 | Register invalid - missing username | 200 with form errors | PASS |
| 11 | Teacher redirected to teacher dashboard on login | Redirect to /teacher/dashboard | PASS |
| 12 | Student redirected to student dashboard on login | Redirect to /student/dashboard | PASS |
| 13 | Profile requires login | 302 to login | PASS |
| 14 | Profile loads when logged in | 200 OK | PASS |
| 15 | Edit profile GET | 200 OK | PASS |
| 16 | Edit profile POST updates display_name | display_name saved in DB | PASS |

#### assignments

| # | Test | Expected | Result |
|---|---|---|---|
| 17 | Create Task, check str and is_live default | Saved, is_live=False | PASS |
| 18 | Default task_type is text | task_type == 'text' | PASS |
| 19 | Task with task_type=python | task_type == 'python' | PASS |
| 20 | starter_code defaults to None | None | PASS |
| 21 | Create Submission, submitted=False | Saved and linked | PASS |
| 22 | Duplicate submission raises IntegrityError | IntegrityError | PASS |
| 23 | FinalSubmission str contains student | String correct | PASS |
| 24 | Task view requires login | 302 redirect | PASS |
| 25 | Task view loads for student | 200 + title visible | PASS |
| 26 | First task visit creates TaskDocument and Submission | Both rows exist | PASS |
| 27 | Autosave saves content | saved=true, content stored | PASS |
| 28 | Autosave rejects GET | 400 error | PASS |
| 29 | Submit creates FinalSubmission | FinalSubmission row exists | PASS |
| 30 | Student tasks list view | 200 + title visible | PASS |
| 31 | Student tasks filter by group | 200 OK | PASS |
| 32 | Teacher tasks list view | 200 + title visible | PASS |
| 33 | Grading view GET | 200 OK | PASS |
| 34 | Grading view POST saves grade and comment | grade=85, comment saved | PASS |

#### classrooms

| # | Test | Expected | Result |
|---|---|---|---|
| 35 | Subject str | 'History' | PASS |
| 36 | ClassGroup str | 'BioGroup' | PASS |
| 37 | Duplicate GroupMembership raises IntegrityError | IntegrityError | PASS |
| 38 | Announcement str | 'Exam' | PASS |
| 39 | Multiple groups per subject | count == 2 | PASS |
| 40 | Student can join multiple groups | count == 2 | PASS |
| 41 | Create announcement requires login | 302 redirect | PASS |
| 42 | Create announcement GET | 200 OK | PASS |
| 43 | Create announcement POST | Announcement saved | PASS |

#### editor

| # | Test | Expected | Result |
|---|---|---|---|
| 44 | TaskDocument created with content | Saved, str correct | PASS |
| 45 | Duplicate TaskDocument raises IntegrityError | IntegrityError | PASS |
| 46 | Default content is empty string | content == '' | PASS |
| 47 | TaskDocumentVersion created | Saved with correct content | PASS |
| 48 | Multiple versions per document | count == 2 | PASS |
| 49 | Create DM, read=False | All fields correct | PASS |
| 50 | Messages ordered by sent_at | First created appears first | PASS |
| 51 | Mark message read | read=True after reload | PASS |

#### pages

| # | Test | Expected | Result |
|---|---|---|---|
| 52 | Home view public | 200 OK | PASS |
| 53 | Student dashboard redirects when not logged in | 302 | PASS |
| 54 | Student dashboard loads when logged in | 200 OK | PASS |
| 55 | Teacher dashboard redirects when not logged in | 302 | PASS |
| 56 | Teacher dashboard blocked for student | 403; teacher gets 200 | PASS |
| 57 | Student group view loads with announcements | 200 + content visible | PASS |
| 58 | Teacher task detail page loads | 200 OK | PASS |
| 59 | Teacher create task GET | 200 OK | PASS |
| 60 | Teacher create task POST | Redirect + task in DB | PASS |
| 61 | Student cannot create task | 403 Forbidden | PASS |
| 62 | Teacher group view loads | 200 OK | PASS |
| 63 | Teacher analytics view loads | 200 OK | PASS |
| 64 | Teacher can edit task | Title updated in DB | PASS |
| 65 | Teacher can delete task | Task no longer exists | PASS |
| 66 | Student submission view loads | 200 OK | PASS |

### JavaScript test procedures (manual)

Browser tests performed in Chrome and Firefox.

| # | Component | Steps | Expected | Result |
|---|---|---|---|---|
| JS-1 | CodeMirror init | Open task page as student | Editor renders with syntax highlighting | PASS |
| JS-2 | Python syntax mode | Open Python-type task | def, return highlighted | PASS |
| JS-3 | Autosave | Type in editor, wait 2s | "Saved" indicator appears | PASS |
| JS-4 | Manual save | Click Save button | "Saving..." then timestamp shown | PASS |
| JS-5 | WebSocket connect | Open live task as student | Indicator turns green | PASS |
| JS-6 | Teacher sees student | Open /editor/room/<id> as teacher | Student in sidebar list | PASS |
| JS-7 | Live sync | Click student in teacher view | Editor updates to student content | PASS |
| JS-8 | Help request | Student clicks "?" button | Toast appears on teacher page | PASS |
| JS-9 | Watching indicator | Teacher clicks student | Badge appears on student page | PASS |
| JS-10 | Offline indicator | Kill server | Indicator turns red | PASS |
| JS-11 | localStorage fallback | Type, reload without saving | Content restored | PASS |
| JS-12 | Pyodide run | Write print("hello"), click Run | Output shows hello | PASS |
| JS-13 | Pyodide error | Write bad syntax, click Run | Error shown in output | PASS |
| JS-14 | DM send | Type message, press Enter | Appears instantly | PASS |
| JS-15 | DM receive | Other browser sends DM | Appears in first browser instantly | PASS |
| JS-16 | Mobile sidebar | Resize <768px, click burger | Sidebar opens; burger hides | PASS |

### Notes

- Test isolation: every TestCase uses its own setUp with fresh users, profiles, groups, and tasks.
- Access control tests verify HTTP 302 for unauthenticated and HTTP 403 for wrong-role requests.
- Integrity constraint tests assert IntegrityError on duplicate creation.
- View side-effect tests reload the object from the database to confirm persistence.
- Bugs found during testing: missing @login_required on student_task_view (AnonymousUser AttributeError); hardcoded group id=1 fallback in teacher_group_view causing 404; missing @login_required on create_announcement.

---

## AI reflection (LO8)

This project was developed with **GitHub Copilot** as the primary AI assistant.

### 8.1 Code generation

- **Django views**: Copilot generated initial CRUD view structures (create/edit/delete task, grading, submission views). Decorator protection and docstrings were added manually.
- **WebSocket consumer**: Initial EditorConsumer class generated from Channels documentation patterns. Group broadcast and help_request handler debugged manually.
- **CodeMirror setup**: initEditor function in base.js generated from requirements. Required manual fixes for the drawSelection import error and duplicate @codemirror/state instance error.
- **Model definitions**: Fields, __str__ methods, unique_together constraints, and the post_save Profile signal were Copilot-generated.
- **Test cases**: Initial test skeletons for all 5 apps generated from descriptions; setUp methods and assertions reviewed and corrected.

### 8.2 Debugging

- **FieldError on duration_minutes**: After Task fields were removed in migration 0008, Copilot identified all remaining references in views.py and generated the fix.
- **CORS / Vite dev mode**: Cross-origin errors traced to DJANGO_VITE_DEV_MODE setting; Copilot identified root cause.
- **Missing @login_required**: Systematic audit via Copilot found 8 views missing authentication decorators across 4 apps.
- **NoReverseMatch**: URL pattern mismatch between path("group") and template tag identified and corrected with Copilot.

### 8.3 Optimisation and UX

- **Context processor**: Copilot suggested centralising badge counts (ungraded, pending tasks, unread DMs) into a single context processor, removing repeated query logic from 10+ views.
- **QuerySet annotations**: annotate() with Count and Exists suggested to replace Python-level loops causing N+1 queries.
- **localStorage fallback**: Copilot suggested storing editor content on every keystroke and restoring on reconnect.
- **Sequence numbers**: seq field on WebSocket updates suggested to discard stale out-of-order messages.

### 8.4 Unit tests

Copilot generated initial test versions for all 5 apps. Key manual corrections:
- Added profile.role = 'teacher' / 'student' + .save() after user creation (Copilot omitted role assignment, causing PermissionDenied).
- Corrected assertRedirects URLs to match actual URL patterns.
- Added ownership guard tests after identifying students could access other students' submissions.

### Summary

AI tools accelerated boilerplate generation and systematic audits (decorator coverage, field references). Query optimisation suggestions (N+1 detection, annotation patterns) and test generation were the highest-value contributions. All generated code was reviewed, tested, and adjusted before committing.

---

## Credits and third-party licences

The following open-source libraries are used in this project. Their licences are reproduced here as required.

| Library | Version | Licence | Notes |
|---|---|---|---|
| Django | 5.2 | BSD 3-Clause | Copyright (c) Django Software Foundation and contributors |
| Django Channels | 4.x | BSD 3-Clause | Copyright (c) Django Software Foundation and contributors |
| Daphne | 4.x | BSD 3-Clause | Copyright (c) Django Software Foundation and contributors |
| channels-redis | 4.x | BSD 3-Clause | Copyright (c) Django Software Foundation and contributors |
| asgiref | 3.x | BSD 3-Clause | Copyright (c) Django Software Foundation and contributors |
| dj-database-url | 0.5 | BSD 2-Clause | Copyright (c) Kenneth Reitz |
| psycopg2 | 2.9 | LGPL 3.0 | Copyright (c) Federico Di Gregorio, Daniele Varrazzo |
| WhiteNoise | 6.x | MIT | Copyright (c) David Evans |
| django-vite | 3.x | MIT | Copyright (c) MrBin99 |
| django-environ | 0.x | MIT | Copyright (c) joke2k |
| sqlparse | 0.5 | BSD 3-Clause | Copyright (c) Andi Albrecht |
| Vite | 5.x | MIT | Copyright (c) 2019-present Evan You and Vite contributors |
| CodeMirror 6 | 6.x | MIT | Copyright (c) 2018-2021 by Marijn Haverbeke and others |
| Pyodide | 0.x | MPL 2.0 | Copyright (c) Pyodide contributors. Used unmodified from CDN; no source changes made. |

**Licence summaries:**

- **MIT / BSD 2-Clause / BSD 3-Clause** — Permission is granted to use, copy, modify, and distribute the software, provided the copyright notice and permission notice are preserved. These libraries are used without modification.
- **LGPL 3.0 (psycopg2)** — Used as an unmodified library linked at runtime. No modifications to psycopg2 source have been made.
- **MPL 2.0 (Pyodide)** — Used unmodified, loaded from the official Pyodide CDN. No MPL-covered files have been modified. The full MPL 2.0 licence text is available at https://www.mozilla.org/en-US/MPL/2.0/.

