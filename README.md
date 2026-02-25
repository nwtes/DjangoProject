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

---

## Project overview

**Learn** is a web-based classroom management and live coding platform built as a personal course project. It connects teachers and students in a shared, role-driven environment where:

- Teachers create subjects, class groups, and assignments — including tasks that students complete entirely in the browser.
- Students join groups, write and run code in an embedded editor, submit work, and view their graded feedback.
- During a **live task session**, a teacher can observe any connected student's editor in real time over a WebSocket connection, while students can send a help-request notification without interrupting the class.
- Any two users can send **direct messages** to each other with instant delivery via WebSocket — no page refresh needed.

The project demonstrates full-stack Django development including async consumers, a Vite-bundled frontend, in-browser Python execution (Pyodide), responsive dark-mode UI, and a Heroku production deployment.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend framework | Django 5.2 |
| Async / WebSocket | Django Channels 4 + Daphne |
| Channel layer | Redis (channels-redis) |
| Database (production) | PostgreSQL (via psycopg2 + dj-database-url) |
| Database (local dev) | SQLite |
| Frontend bundler | Vite + django-vite |
| Code editor | CodeMirror 6 (view, commands, lang-python, lang-javascript, theme-one-dark, search) |
| In-browser Python | Pyodide (loaded from CDN at runtime) |
| Static files | WhiteNoise |
| Deployment | Heroku (Node + Python buildpacks) |
| Auth | Django built-in auth + custom `Profile` model |

---

## User roles

The platform has three distinct roles enforced by the `Profile.role` field and the `role_required` decorator.

### Student
- Registers and is automatically given the `student` role (default).
- Joins class groups assigned by teachers or admins.
- Views their task list (filterable by group, teacher, graded/ungraded, submitted/unsubmitted).
- Opens tasks in the in-browser CodeMirror editor; work is auto-saved every few seconds and backed up in `localStorage`.
- Runs Python code directly in the browser via Pyodide without any server-side execution.
- Submits final work; views their graded submission with the teacher's score and comment.
- Sees a **"Teacher is watching"** indicator when a teacher is observing their live session.
- Can send a **help request** (floating `?` button) to the teacher during a live task.
- Sends and receives direct messages with any other user in real time.
- Manages their own profile (display name, bio, phone).

### Teacher
- Registers and selects the `teacher` role at signup.
- Creates subjects and class groups; enrolls students into groups.
- Posts announcements to class groups.
- Creates tasks of type **text** or **Python**, with optional starter code.
- Edits and deletes their own tasks.
- Opens the **live task room** (`/editor/room/<task_id>`) to see all connected students; clicks any student to view their code in real time.
- Receives help-request notifications from students during live sessions.
- Grades final submissions with a numeric score and written comment.
- Views per-group analytics (submission counts, average grades, task statistics).
- Sends and receives direct messages.
- Manages their own profile.

### Admin (superuser)
- Full access to the Django admin interface.
- Accesses a dedicated **site admin dashboard** at `/admin-site/` for day-to-day management without using the Django admin.
- Can view all users, create/edit/delete subjects, class groups, and assignments.
- Can enrol students into groups and reassign teachers to subjects from the site admin UI.
- Manages user accounts and profiles.

---

## Features

### Authentication & accounts
- Register with username, password, and role (student/teacher).
- Login redirects to the role-specific dashboard automatically.
- `@login_required` protects all authenticated views; `role_required` blocks cross-role access (returns HTTP 403).
- Profile page shows role-specific stats (groups joined, tasks submitted for students; subjects taught, total students, tasks created for teachers).
- Edit profile: display name, bio, phone.
- `post_save` signal auto-creates a `Profile` for every new `User`.

### Classroom management
- Teachers create **subjects** (e.g. "Computer Science") and **class groups** (e.g. "CS-A 2025") linked to subjects.
- Admin or teacher enrols students into groups via `GroupMembership`.
- Teachers post **announcements** to specific groups; students see them in the group view.
- Group detail page shows enrolled students with links to their profiles.

### Assignments & submissions
- Tasks have a **title**, **description**, **task type** (text / python), **optional starter code**, and a **live flag**.
- Students see a personal task list with filters: group, teacher, graded/ungraded, submitted/unsubmitted.
- Opening a task auto-creates a `Submission` and `TaskDocument` (the live editor document) on first visit.
- **Autosave**: editor content is posted to the server every few seconds; a save-status indicator confirms persistence.
- **localStorage fallback**: unsaved changes survive accidental page refreshes.
- **Manual save + explicit snapshot**: clicking "Save" creates a `TaskDocumentVersion` for diff/history.
- Students submit with a "Submit" button; this creates a `FinalSubmission` record.
- Teachers grade via a form that saves a numeric score and written comment on the `Submission`.

### Live code editor (WebSocket)
- Built on **CodeMirror 6** with Python syntax highlighting, One Dark theme, and search.
- Each task page connects to a WebSocket room keyed by task ID.
- Teacher opens `/editor/room/<task_id>` and sees the connected student list update in real time.
- Clicking a student on the teacher side broadcasts a `watch_student` message; the teacher's editor syncs to that student's content.
- The watched student receives a `being_watched` message and sees a **"Teacher is watching"** badge.
- Switching to another student removes the badge from the previous student.
- Students have a floating **"? Help"** button; clicking it sends a `help_request` WebSocket message to the teacher, who sees a dismissible notification toast.
- A **connection indicator** (green dot = Connected, red = Offline) shows WebSocket state.
- **Sequence numbers** on content updates prevent stale out-of-order messages from overwriting newer content.

### In-browser Python execution (Pyodide)
- Python-type tasks show a **"Run"** button.
- Pyodide is loaded from CDN the first time the user clicks Run (lazy-loaded).
- The editor content is sent to Pyodide's `runPython()` API; stdout, return values, and tracebacks are captured and shown in an output panel below the editor.
- No server-side code execution required.

### Direct messaging
- Any logged-in user can open a DM thread with any other user at `/dm/<username>/`.
- Previous message history is shown on page load, ordered chronologically.
- New messages are sent and received instantly via a dedicated WebSocket consumer.
- Messages are marked as read when the thread is opened; unread counts shown in the sidebar badge.
- Inbox page shows all conversations with unread indicators.

### Admin site dashboard
- Separate site-admin section at `/admin-site/` for superusers, accessible directly from the site without the Django admin.
- View and search all users with their roles.
- Create/manage subjects, assign teachers to subjects.
- Create/manage class groups and enrol students.

### UX & responsive design
- Dark-mode only, consistent colour palette across all pages.
- Collapsible sidebar with role-aware navigation links and unread-message badge.
- On mobile (< 768 px): sidebar collapses behind a burger button; an overlay close button replaces the burger when the sidebar is open.
- All forms share a unified style (dark inputs, accent-coloured submit buttons).
- Tables use a consistent dark-card style with hover highlights.
- Context processor (`pages/context_processors.py`) injects `ungraded_count`, `pending_tasks_count`, and `unread_dm_count` into every template so the sidebar badges always reflect live counts.

---

## UX design

### Design principles
- **Role-aware navigation**: the sidebar and dashboard content are different for students, teachers, and admins. Pages irrelevant to a role are hidden.
- **Minimal friction**: first visit to a task page auto-creates the submission so students never see a setup step.
- **Live feedback**: autosave indicator, connection dot, and "Teacher is watching" badge give immediate feedback on background state.
- **Dark mode**: single colour scheme (dark background, muted card surfaces, bright accent for interactive elements) used throughout.

### Key pages

| Page | Route | Who sees it |
|---|---|---|
| Home | `/` | Everyone (public) |
| Student dashboard | `/student/dashboard` | Students |
| Teacher dashboard | `/teacher/dashboard` | Teachers |
| Student task list | `/tasks/list` | Students |
| Task (editor) | `/tasks/task/<id>` | Students |
| Live task room | `/editor/room/<id>` | Teachers |
| Teacher task list | `/tasks/teacher/list` | Teachers |
| Student group view | `/group/<id>` | Students |
| Teacher group view | `/teacher/groups` | Teachers |
| Analytics | `/teacher/analytics` | Teachers |
| Profile | `/accounts/profile/` | All authenticated |
| Edit profile | `/accounts/profile/edit/` | All authenticated |
| DM inbox | `/dm/` | All authenticated |
| DM thread | `/dm/<username>/` | All authenticated |
| Admin site | `/admin-site/` | Superusers |

---

## Data model

```
User (Django built-in)
 └── Profile          role: student | teacher

Subject              teacher → Profile
 └── ClassGroup
      ├── GroupMembership  student → Profile
      ├── Announcement     created_by → Profile
      └── Task             created_by → Profile, type: text | python
           ├── Submission  student → Profile, grade, comment
           │    └── FinalSubmission
           └── TaskDocument  student → Profile, content (live editor)
                └── TaskDocumentVersion  author → Profile

DirectMessage        sender → User, recipient → User, read
LiveTaskSession      document → TaskDocument, user → Profile
```

---

## Project structure

```
DjangoProject/          Django settings, ASGI config, root URLs
accounts/               User registration, login, profile
assignments/            Task and submission models + views
classrooms/             Subject, ClassGroup, GroupMembership, Announcement
editor/                 WebSocket consumer, TaskDocument, DirectMessage
pages/                  Dashboards, task CRUD, group views, analytics, context processor
templates/              All HTML templates (base, per-app subdirectories)
static/css/             App-wide stylesheets
static/js/              base.js (CodeMirror + WebSocket), editor.js (entry point)
static_build/           Vite production build output
staticfiles/            collectstatic output (served by WhiteNoise)
vite.config.js          Vite config
package.json            npm scripts (dev, build, heroku-postbuild)
Procfile                Heroku: daphne ASGI server
requirements.txt        Python dependencies
```

---

## Local development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Redis (for WebSocket channel layer — install locally or use Docker)

### Setup

1. Clone and create a virtual environment:
   ```
   git clone https://github.com/nwtes/DjangoProject.git
   cd DjangoProject
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Node dependencies:
   ```
   npm install
   ```

4. Create `env.py` in the project root (never commit this):
   ```python
   import os
   os.environ['SECRET_KEY'] = 'your-local-secret-key'
   os.environ['DEBUG'] = 'True'
   # Leave DATABASE_URL unset to use SQLite locally
   ```

5. Run migrations and collect static:
   ```
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

6. Start Redis (if not already running):
   ```
   redis-server
   ```

7. Start both servers in separate terminals:
   ```
   npm run dev                   # Vite dev server on :5173
   python manage.py runserver    # Django on :8000
   ```

8. Visit `http://localhost:8000`.

---

## Heroku deployment

### Buildpacks (order matters)
```
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
```

### Environment variables (Heroku config vars)
| Key | Value |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | Set automatically by Heroku Postgres add-on |
| `REDIS_URL` | Set automatically by Heroku Redis add-on |
| `DEBUG` | `False` |
| `DJANGO_VITE_DEV_MODE` | `False` |

### Deploy
```
git push heroku main
heroku run python manage.py migrate
```

### How the build works
1. Node buildpack runs `npm run heroku-postbuild` → `vite build` → copies `.vite/manifest.json` to `static_build/manifest.json`.
2. Python buildpack installs dependencies, then runs `python manage.py collectstatic --noinput` (via `release` phase or manually).
3. `Procfile` starts Daphne (ASGI) which handles both HTTP and WebSocket traffic.

---

## Agile project management

### Tool & approach
This project was planned and tracked using **GitHub Projects (v2)** linked to this repository. All user stories were created as GitHub Issues, labelled by epic and MoSCoW priority, assigned to sprint milestones, and moved to **Done** on the Kanban board once implemented.

**Board:** [https://github.com/users/nwtes/projects/1](https://github.com/users/nwtes/projects/1)
**Issues:** [https://github.com/nwtes/DjangoProject/issues](https://github.com/nwtes/DjangoProject/issues)

Columns on the board: **Todo → In Progress → In Review → Done**
All 36 user stories are marked **Done**.

---

### Project goals

| ID | Goal |
|---|---|
| G1 | Provide teachers with tools to manage classes, groups, and assignments |
| G2 | Provide students with a live coding environment for completing tasks |
| G3 | Enable real-time communication between teachers and students |
| G4 | Ensure secure, role-based access throughout the platform |
| G5 | Deploy a production-ready application accessible via the web |

---

### Epics

| Epic | Label | Goals |
|---|---|---|
| E1 — Authentication & Profiles | `epic:auth` | G4 |
| E2 — Classroom Management | `epic:classrooms` | G1 |
| E3 — Assignments & Submissions | `epic:assignments` | G1, G2 |
| E4 — Live Code Editor | `epic:editor` | G2, G3 |
| E5 — Direct Messaging | `epic:dm` | G3 |
| E6 — Deployment & Infrastructure | `epic:devops` | G5 |

---

### User stories

#### E1 — Authentication & Profiles (Sprint 1)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-01](https://github.com/nwtes/DjangoProject/issues/1) | As a new user I can register with a username, password and role so that I get the correct dashboard | Must Have | ✅ Done |
| [US-02](https://github.com/nwtes/DjangoProject/issues/2) | As a returning user I can log in and be redirected to my role-specific dashboard | Must Have | ✅ Done |
| [US-03](https://github.com/nwtes/DjangoProject/issues/3) | As a logged-in user I can view my profile page showing username, display name and bio | Should Have | ✅ Done |
| [US-04](https://github.com/nwtes/DjangoProject/issues/4) | As a logged-in user I can edit my display name and bio | Should Have | ✅ Done |
| [US-05](https://github.com/nwtes/DjangoProject/issues/5) | As an unauthenticated user I am redirected to login when I access protected pages | Must Have | ✅ Done |
| [US-06](https://github.com/nwtes/DjangoProject/issues/6) | As a student I cannot access teacher-only views | Must Have | ✅ Done |

#### E2 — Classroom Management (Sprint 2)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-07](https://github.com/nwtes/DjangoProject/issues/7) | As a teacher I can create a subject to organise groups underneath it | Must Have | ✅ Done |
| [US-08](https://github.com/nwtes/DjangoProject/issues/8) | As a teacher I can create a class group linked to a subject | Must Have | ✅ Done |
| [US-09](https://github.com/nwtes/DjangoProject/issues/9) | As a teacher I can view all my groups on a dedicated page | Must Have | ✅ Done |
| [US-10](https://github.com/nwtes/DjangoProject/issues/10) | As a teacher I can post an announcement to a class group | Should Have | ✅ Done |
| [US-11](https://github.com/nwtes/DjangoProject/issues/11) | As a student I can view announcements and classmates in my group | Should Have | ✅ Done |
| [US-12](https://github.com/nwtes/DjangoProject/issues/12) | As a teacher I can enrol students into a group | Must Have | ✅ Done |

#### E3 — Assignments & Submissions (Sprint 3)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-13](https://github.com/nwtes/DjangoProject/issues/13) | As a teacher I can create a task (text or Python) with title, description and optional starter code | Must Have | ✅ Done |
| [US-14](https://github.com/nwtes/DjangoProject/issues/14) | As a teacher I can edit an existing task | Should Have | ✅ Done |
| [US-15](https://github.com/nwtes/DjangoProject/issues/15) | As a teacher I can delete a task | Should Have | ✅ Done |
| [US-16](https://github.com/nwtes/DjangoProject/issues/16) | As a student I can view my assigned tasks list filtered by group | Must Have | ✅ Done |
| [US-17](https://github.com/nwtes/DjangoProject/issues/17) | As a student I can open a task and have a Submission and TaskDocument auto-created | Must Have | ✅ Done |
| [US-18](https://github.com/nwtes/DjangoProject/issues/18) | As a student my work autosaves every few seconds | Must Have | ✅ Done |
| [US-19](https://github.com/nwtes/DjangoProject/issues/19) | As a student I can submit my final answer | Must Have | ✅ Done |
| [US-20](https://github.com/nwtes/DjangoProject/issues/20) | As a teacher I can grade a submission and leave a comment | Should Have | ✅ Done |
| [US-21](https://github.com/nwtes/DjangoProject/issues/21) | As a student I can view my graded submission with feedback | Should Have | ✅ Done |

#### E4 — Live Code Editor (Sprint 4)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-22](https://github.com/nwtes/DjangoProject/issues/22) | As a student I can write code in a CodeMirror editor with syntax highlighting | Must Have | ✅ Done |
| [US-23](https://github.com/nwtes/DjangoProject/issues/23) | As a student I can run Python code in the browser via Pyodide | Should Have | ✅ Done |
| [US-24](https://github.com/nwtes/DjangoProject/issues/24) | As a teacher I can open a live session and see which students are connected | Must Have | ✅ Done |
| [US-25](https://github.com/nwtes/DjangoProject/issues/25) | As a teacher I can click a student to view their code in real time | Must Have | ✅ Done |
| [US-26](https://github.com/nwtes/DjangoProject/issues/26) | As a student I see a "Teacher is watching" indicator when observed | Should Have | ✅ Done |
| [US-27](https://github.com/nwtes/DjangoProject/issues/27) | As a student I can send a help request notification to the teacher | Could Have | ✅ Done |
| [US-28](https://github.com/nwtes/DjangoProject/issues/28) | As a student my unsaved content is preserved in localStorage on refresh | Could Have | ✅ Done |

#### E5 — Direct Messaging (Sprint 5)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-29](https://github.com/nwtes/DjangoProject/issues/29) | As a user I can open a DM thread with another user | Must Have | ✅ Done |
| [US-30](https://github.com/nwtes/DjangoProject/issues/30) | As a user I can send a message that appears instantly without a page refresh | Must Have | ✅ Done |
| [US-31](https://github.com/nwtes/DjangoProject/issues/31) | As a user I can see the full message history when I open a thread | Must Have | ✅ Done |
| [US-32](https://github.com/nwtes/DjangoProject/issues/32) | As a user messages are marked as read when I open the thread | Should Have | ✅ Done |

#### E6 — Deployment & Infrastructure (Sprint 6)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-33](https://github.com/nwtes/DjangoProject/issues/33) | As a developer I can deploy to Heroku with a single git push | Must Have | ✅ Done |
| [US-34](https://github.com/nwtes/DjangoProject/issues/34) | As a developer static files are collected and served correctly in production | Must Have | ✅ Done |
| [US-35](https://github.com/nwtes/DjangoProject/issues/35) | As a developer environment secrets are not stored in source code | Must Have | ✅ Done |
| [US-36](https://github.com/nwtes/DjangoProject/issues/36) | As a developer WebSocket connections work in production via Heroku | Must Have | ✅ Done |

---

### Sprint plan

| Sprint | Milestone | Stories | Focus |
|---|---|---|---|
| Sprint 1 | [Sprint 1 — Auth and Profiles](https://github.com/nwtes/DjangoProject/milestone/10) | US-01 – US-06 | Registration, login, role redirect, profile |
| Sprint 2 | [Sprint 2 — Classroom Management](https://github.com/nwtes/DjangoProject/milestone/11) | US-07 – US-12 | Subjects, groups, memberships, announcements |
| Sprint 3 | [Sprint 3 — Assignments and Submissions](https://github.com/nwtes/DjangoProject/milestone/12) | US-13 – US-21 | Task CRUD, submission, autosave, grading |
| Sprint 4 | [Sprint 4 — Live Code Editor](https://github.com/nwtes/DjangoProject/milestone/4) | US-22 – US-28 | CodeMirror, Pyodide, WebSocket live editor |
| Sprint 5 | [Sprint 5 — Direct Messaging](https://github.com/nwtes/DjangoProject/milestone/5) | US-29 – US-32 | DM threads, live WebSocket messaging |
| Sprint 6 | [Sprint 6 — Deployment and Infra](https://github.com/nwtes/DjangoProject/milestone/6) | US-33 – US-36 | Heroku deploy, static files, production config |

---

### MoSCoW summary

| Priority | Count | Stories |
|---|---|---|
| Must Have | 22 | US-01,02,05,06,07,08,09,12,13,16,17,18,19,22,24,25,29,30,31,33,34,35,36 |
| Should Have | 11 | US-03,04,10,11,14,15,20,21,23,26,32 |
| Could Have | 3 | US-27,28 |

---

### Definition of Done

A user story is **Done** when:
1. Feature code is committed to `master`.
2. All existing automated tests still pass (`python manage.py test`).
3. A new test covers the feature where practical.
4. The feature works end-to-end on Heroku.
5. Related templates, URLs, and migrations are included in the commit.

---

## Testing documentation

### Overview

The project uses Django's built-in `unittest`-based test framework (`django.test.TestCase`). Tests are organised per application. All 66 tests run against an isolated in-memory SQLite test database that is created and destroyed automatically.

Run the full suite:

```
python manage.py test
```

Run with verbose output (recommended for reviewing individual results):

```
python manage.py test --verbosity=2
```

Run a single app:

```
python manage.py test accounts
python manage.py test assignments
python manage.py test classrooms
python manage.py test editor
python manage.py test pages
```

---

### Test results summary

| App | Test class | Tests | Result |
|---|---|---|---|
| accounts | ProfileSignalTests | 6 | ✅ PASS |
| accounts | RegistrationViewTests | 4 | ✅ PASS |
| accounts | LoginRedirectTests | 2 | ✅ PASS |
| accounts | ProfileViewTests | 4 | ✅ PASS |
| assignments | TaskModelTests | 7 | ✅ PASS |
| assignments | AssignmentViewTests | 11 | ✅ PASS |
| classrooms | ClassroomModelTests | 6 | ✅ PASS |
| classrooms | ClassroomViewTests | 3 | ✅ PASS |
| editor | TaskDocumentModelTests | 5 | ✅ PASS |
| editor | DirectMessageModelTests | 3 | ✅ PASS |
| pages | PagesViewTests | 15 | ✅ PASS |
| **Total** | | **66** | **✅ All pass** |

Last run: `Ran 66 tests in ~170s — OK`

---

### 4.1 Python test procedures

#### `accounts` app — `accounts/tests.py`

**ProfileSignalTests** — verifies that the `post_save` signal automatically creates/updates a `Profile` whenever a `User` is saved.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 1 | `test_profile_created_on_user_creation` | Create a new User; check `profile` attribute exists and is a Profile instance | Profile created automatically | ✅ PASS |
| 2 | `test_profile_default_role_is_student` | New User's profile role defaults to `'student'` | `role == 'student'` | ✅ PASS |
| 3 | `test_profile_str` | `str(profile)` returns the username | `'charlie'` | ✅ PASS |
| 4 | `test_profile_role_can_be_set_to_teacher` | Save profile with `role='teacher'`, reload | `role == 'teacher'` | ✅ PASS |
| 5 | `test_profile_display_name_optional` | `display_name` is `None` on creation; can be set | Saves and reads back correctly | ✅ PASS |
| 6 | `test_profile_bio_optional` | `bio` field can be populated | Value persisted | ✅ PASS |

**RegistrationViewTests** — covers the `/accounts/register/` view.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 7 | `test_register_page_loads` | GET `/accounts/register/` | 200 OK | ✅ PASS |
| 8 | `test_register_creates_student_user` | POST valid form with `role=student` | Redirect + user created with student role | ✅ PASS |
| 9 | `test_register_creates_teacher_user` | POST valid form with `role=teacher` | User created with teacher role | ✅ PASS |
| 10 | `test_register_invalid_missing_username` | POST with blank username | 200 (form errors), no user created | ✅ PASS |

**LoginRedirectTests** — verifies role-based redirect after login.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 11 | `test_teacher_redirected_to_teacher_dashboard` | Teacher logs in | Redirect to `/teacher/dashboard` | ✅ PASS |
| 12 | `test_student_redirected_to_student_dashboard` | Student logs in | Redirect to `/student/dashboard` | ✅ PASS |

**ProfileViewTests** — covers `/accounts/profile/` and `/accounts/profile/edit/`.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 13 | `test_profile_requires_login` | GET profile page unauthenticated | 302 redirect to login | ✅ PASS |
| 14 | `test_profile_loads_when_logged_in` | GET profile page authenticated | 200 OK | ✅ PASS |
| 15 | `test_edit_profile_get` | GET edit profile page | 200 OK | ✅ PASS |
| 16 | `test_edit_profile_post_updates_display_name` | POST valid form | `display_name` updated in DB | ✅ PASS |

---

#### `assignments` app — `assignments/tests.py`

**TaskModelTests** — unit tests for `Task`, `Submission`, `FinalSubmission` models.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 17 | `test_create_task` | Create Task; check `str()` and `is_live=False` default | Task saved, `is_live` is `False` | ✅ PASS |
| 18 | `test_task_default_type_is_text` | Default `task_type` is `'text'` | `task_type == 'text'` | ✅ PASS |
| 19 | `test_task_python_type` | Task created with `task_type='python'` | `task_type == 'python'` | ✅ PASS |
| 20 | `test_task_starter_code_optional` | `starter_code` defaults to `None` | `None` | ✅ PASS |
| 21 | `test_create_submission` | Create Submission; check `submitted=False` default | Saved, linked to task/student | ✅ PASS |
| 22 | `test_submission_unique_per_student_task` | Create two Submissions for same student+task | `IntegrityError` raised | ✅ PASS |
| 23 | `test_final_submission_str` | `str(FinalSubmission)` contains student name | String contains student | ✅ PASS |

**AssignmentViewTests** — integration tests for assignment views.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 24 | `test_student_task_view_requires_login` | GET task page unauthenticated | 302 redirect | ✅ PASS |
| 25 | `test_student_task_view_loads` | GET task page as student | 200 + task title in response | ✅ PASS |
| 26 | `test_student_task_view_creates_document_and_submission` | First visit creates `TaskDocument` and `Submission` | Both objects exist in DB | ✅ PASS |
| 27 | `test_autosave_saves_content` | POST JSON `{content: 'my code'}` to autosave | `{saved: true}` + content stored | ✅ PASS |
| 28 | `test_autosave_rejects_non_post` | GET autosave endpoint | 400 error | ✅ PASS |
| 29 | `test_submit_task_creates_final_submission` | POST to submit endpoint | `FinalSubmission` row created | ✅ PASS |
| 30 | `test_student_tasks_list_view` | GET student tasks list | 200 + task title visible | ✅ PASS |
| 31 | `test_student_tasks_filter_by_group` | GET tasks list with `?group=<id>` | 200 OK | ✅ PASS |
| 32 | `test_teacher_tasks_list_view` | GET teacher tasks list as teacher | 200 + task title visible | ✅ PASS |
| 33 | `test_grading_view_get` | GET grading form as teacher | 200 OK | ✅ PASS |
| 34 | `test_grading_view_post_grades_submission` | POST grade + comment | `grade=85`, `comment='Good work'` saved | ✅ PASS |
| 35 | `test_student_submission_view` | GET student's own submission view | 200 OK | ✅ PASS |

---

#### `classrooms` app — `classrooms/tests.py`

**ClassroomModelTests** — unit tests for `Subject`, `ClassGroup`, `GroupMembership`, `Announcement`.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 36 | `test_subject_str` | `str(Subject)` returns subject name | `'History'` | ✅ PASS |
| 37 | `test_classgroup_str` | `str(ClassGroup)` returns group name | `'BioGroup'` | ✅ PASS |
| 38 | `test_group_membership_unique` | Second membership for same student+group | `IntegrityError` | ✅ PASS |
| 39 | `test_announcement_str` | `str(Announcement)` returns title | `'Exam'` | ✅ PASS |
| 40 | `test_multiple_groups_per_subject` | Create 2 groups under one subject | `classgroup.count() == 2` | ✅ PASS |
| 41 | `test_student_can_join_multiple_groups` | Student joins 2 groups | `GroupMembership.count() == 2` | ✅ PASS |

**ClassroomViewTests** — integration tests for announcement views.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 42 | `test_create_announcement_requires_login` | GET create announcement unauthenticated | 302 redirect | ✅ PASS |
| 43 | `test_create_announcement_get` | GET create announcement as teacher | 200 OK | ✅ PASS |
| 44 | `test_create_announcement_post` | POST valid announcement | Announcement exists in DB | ✅ PASS |

---

#### `editor` app — `editor/tests.py`

**TaskDocumentModelTests** — unit tests for the live-editor document model.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 45 | `test_task_document_created` | Create TaskDocument with content | `content` stored, `str()` contains task title | ✅ PASS |
| 46 | `test_task_document_unique_per_student_task` | Second document for same student+task | `IntegrityError` | ✅ PASS |
| 47 | `test_task_document_default_content_empty` | Default content is empty string | `content == ''` | ✅ PASS |
| 48 | `test_task_document_version_created` | Create a `TaskDocumentVersion` | Saved with correct content and author | ✅ PASS |
| 49 | `test_multiple_versions_per_document` | Create 2 versions for one document | `count() == 2` | ✅ PASS |

**DirectMessageModelTests** — unit tests for the DM model.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 50 | `test_create_message` | Create DM; check body, `read=False`, str | All correct | ✅ PASS |
| 51 | `test_message_ordered_by_sent_at` | Two messages; check ordering | First created appears first | ✅ PASS |
| 52 | `test_mark_read` | Set `read=True` and save | `read` is `True` after reload | ✅ PASS |

---

#### `pages` app — `pages/tests.py`

**PagesViewTests** — integration tests for dashboards, task CRUD, group views, access control.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 53 | `test_home_view_public` | GET `/` unauthenticated | 200 OK | ✅ PASS |
| 54 | `test_student_dashboard_redirects_when_not_logged_in` | GET student dashboard unauthenticated | 302 | ✅ PASS |
| 55 | `test_student_dashboard_loads_when_logged_in` | GET student dashboard as student | 200 OK | ✅ PASS |
| 56 | `test_teacher_dashboard_redirects_when_not_logged_in` | GET teacher dashboard unauthenticated | 302 | ✅ PASS |
| 57 | `test_teacher_dashboard_requires_teacher` | GET teacher dashboard as student | 403; as teacher → 200 | ✅ PASS |
| 58 | `test_student_group_view_shows_announcements_and_students` | GET group page with announcement | 200 + announcement title + student name visible | ✅ PASS |
| 59 | `test_teacher_can_view_task_page` | GET teacher task detail page | 200 OK | ✅ PASS |
| 60 | `test_teacher_can_create_task_get` | GET create task form | 200 OK | ✅ PASS |
| 61 | `test_teacher_can_create_task_post` | POST valid task form | Redirect + task in DB | ✅ PASS |
| 62 | `test_student_cannot_create_task` | GET create task as student | 403 Forbidden | ✅ PASS |
| 63 | `test_teacher_group_view_loads` | GET teacher group view | 200 OK | ✅ PASS |
| 64 | `test_teacher_analytics_view_loads` | GET analytics page as teacher | 200 OK | ✅ PASS |
| 65 | `test_teacher_can_edit_task` | POST edit task form with new title | `title` updated in DB | ✅ PASS |
| 66 | `test_teacher_can_delete_task` | POST delete task | Task no longer exists in DB | ✅ PASS |

---

### 4.2 JavaScript test procedures

JavaScript testing is performed manually due to the project relying on browser-only APIs (WebSocket, CodeMirror, Pyodide).

| # | Component | Test description | Steps | Expected | Result |
|---|---|---|---|---|---|
| JS-1 | CodeMirror editor | Editor initialises on task page | Open `/tasks/task/<id>` as a student | Editor renders with syntax highlighting, cursor is active | ✅ PASS |
| JS-2 | CodeMirror — Python mode | Python syntax highlighting | Create a Python-type task; open task page | Keywords like `def`, `return` are highlighted | ✅ PASS |
| JS-3 | Autosave | Content saved on typing | Type in editor; wait 2 s | "Saved" status indicator appears, content persists on reload | ✅ PASS |
| JS-4 | Manual save button | Save button triggers save | Click "Save" button | "Saving…" → timestamp shown | ✅ PASS |
| JS-5 | WebSocket — student connect | Student connects to live task room | Open live task page as student | Connection indicator turns green ("Connected") | ✅ PASS |
| JS-6 | WebSocket — teacher sees student | Teacher opens editor view | Open `/editor/room/<task_id>` as teacher | Student appears in the student list sidebar | ✅ PASS |
| JS-7 | WebSocket — live sync | Teacher selects student; editor reflects content | Click a student name in list | Editor updates to show that student's code in real time | ✅ PASS |
| JS-8 | Help request button | Student sends help request | Student clicks floating "?" button | Notification banner appears on teacher's page | ✅ PASS |
| JS-9 | Teacher-watching indicator | Student sees "Teacher is watching" badge | Teacher clicks on that student | Badge appears; disappears when teacher switches student | ✅ PASS |
| JS-10 | Connection indicator — offline | Reconnect behaviour | Kill Django server; observe UI | Indicator turns red ("Offline") | ✅ PASS |
| JS-11 | Local storage fallback | Unsaved content survives page reload | Type in editor; reload without saving | Content restored from `localStorage` | ✅ PASS |
| JS-12 | Pyodide run code | Run button executes Python | Write `print("hello")` in Python task; click "Run" | Output panel shows `hello` | ✅ PASS |
| JS-13 | Pyodide error output | Syntax error displayed | Write `def f(:` ; click "Run" | Error message shown in output panel | ✅ PASS |
| JS-14 | DM — send message | Send a direct message | Open DM thread; type message; press Enter | Message appears instantly without page reload | ✅ PASS |
| JS-15 | DM — receive message | Other user sees message live | Second browser sends DM | Message appears in first browser instantly | ✅ PASS |
| JS-16 | Responsive sidebar | Mobile burger menu | Resize to <768 px; click burger | Sidebar opens; burger hides; close button appears | ✅ PASS |

---

### 4.3 Testing documentation notes

- **Test isolation**: every `TestCase` class sets up its own users, profiles, subjects, groups, and tasks in `setUp()`, so tests are fully independent of each other and of production data.
- **Authentication**: access-control tests verify that unauthenticated users receive HTTP 302 and that students cannot access teacher-only views (HTTP 403 via the `role_required` decorator).
- **Model constraints**: unique-together and integrity constraints are validated by asserting that `IntegrityError` is raised on duplicate creation attempts.
- **View side-effects**: tests that POST data (autosave, grading, submission) reload the relevant object from the database to confirm the change was actually persisted.
- **Bugs found and fixed during testing**:
  - `student_task_view` was missing `@login_required` — anonymous requests raised `AttributeError` instead of redirecting. Fixed by adding the decorator.
  - `create_announcement` was missing `@login_required` — same issue. Fixed.
  - `teacher_group_view` used a hardcoded `get_object_or_404(ClassGroup, id=1)` as fallback, causing 404 in any environment where group id 1 does not exist. Fixed to use `.first()` with a `None`-safe guard.
- **Coverage**: all 5 Django apps have automated tests. WebSocket consumer logic and Pyodide integration are covered by the manual JS test procedures above, as they depend on browser and async runtime environments that are impractical to exercise with `django.test`.
