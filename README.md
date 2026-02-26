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

---

## Project overview

**Learny** is a web-based classroom management and live coding platform built as a personal course project. It connects teachers and students in a shared, role-driven environment where:

- Teachers create subjects, class groups, and assignments â€” including tasks that students complete entirely in the browser.
- Students join groups, write and run code in an embedded editor, submit work, and view their graded feedback.
- During a **live task session**, a teacher can observe any connected student's editor in real time over a WebSocket connection, while students can send a help-request notification without interrupting the class.
- Any two users can send **direct messages** to each other with instant delivery via WebSocket â€” no page refresh needed.

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

### Design goals

The visual design of Learn prioritises **clarity**, **role-awareness**, and **minimal friction** for both teachers and students. A dark-mode colour palette was chosen to reduce eye strain during coding sessions, and to give the code editor (CodeMirror) a natural context.

### Design principles
- **Role-aware navigation**: the sidebar and dashboard content are different for students, teachers, and admins. Pages irrelevant to a role are hidden.
- **Minimal friction**: first visit to a task page auto-creates the submission so students never see a setup step.
- **Live feedback**: autosave indicator, connection dot, and "Teacher is watching" badge give immediate feedback on background state.
- **Dark mode**: single colour scheme (dark background, muted card surfaces, bright accent for interactive elements) used throughout.

### Colour palette

| Token | Value | Used for |
|---|---|---|
| `--bg-900` | `#06070a` | Page background |
| `--bg-800` | `#0f1724` | Sidebar, modals |
| `--panel` | `#0f1728` | Card backgrounds |
| `--accent` | `#7c5cff` | Primary actions, links |
| `--accent-2` | `#39d1a2` | Success states, submitted badges |
| `--muted` | `#98a0b3` | Secondary text, labels |
| `--border` | `rgba(255,255,255,0.06)` | Dividers, card edges |

### Typography

- **Body**: Inter, system-ui â€” chosen for readability at small sizes in table rows and form labels.
- **Code**: Fira Code (monospace) â€” used inside the CodeMirror editor for clear character distinction.

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

### Wireframes

The following ASCII wireframes represent the initial layout planning for key pages. The final implementation follows these layouts closely.

#### Base layout (all pages)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   SIDEBAR    â”‚           MAIN CONTENT           â”‚
â”‚              â”‚                                  â”‚
â”‚  [Avatar]    â”‚  Page header + actions           â”‚
â”‚  Username    â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚                                  â”‚
â”‚  Home        â”‚  Content cards / tables          â”‚
â”‚  Dashboard   â”‚                                  â”‚
â”‚  My groups   â”‚                                  â”‚
â”‚  My tasks    â”‚                                  â”‚
â”‚  Messages    â”‚                                  â”‚
â”‚  Logout      â”‚                                  â”‚
â”‚              â”‚                                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Teacher dashboard

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Teacher Dashboard       [Create task] [Analytics] â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Groups                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”‚
â”‚  â”‚ CS-A     â”‚ â”‚ CS-B     â”‚ â”‚ Math-A   â”‚        â”‚
â”‚  â”‚ 24 stud  â”‚ â”‚ 18 stud  â”‚ â”‚ 30 stud  â”‚        â”‚
â”‚  â”‚ [View]   â”‚ â”‚ [View]   â”‚ â”‚ [View]   â”‚        â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Ungraded Submissions                           â”‚
â”‚  Student  â”‚ Group â”‚ Task       â”‚ [Grade â†’]      â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”‚
â”‚                        [View All Submissions]   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Task editor (student)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Task: Fibonacci Sequence      [Save] [Submit]  â”‚
â”‚  â–¾ Task description (collapsible)               â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”‚
â”‚  â”‚  CodeMirror editor    â”‚  Task info      â”‚    â”‚
â”‚  â”‚                       â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”‚    â”‚
â”‚  â”‚  def fibonacci(n):    â”‚  Group: CS-A    â”‚    â”‚
â”‚  â”‚      ...              â”‚  Teacher: John  â”‚    â”‚
â”‚  â”‚                       â”‚  Type: Python   â”‚    â”‚
â”‚  â”‚                       â”‚  [Run â–¶]        â”‚    â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚
â”‚  â— Connected  Saved 12:34                       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Mobile layout (<900px)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ â˜°  Learn                â”‚  â† burger button
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Page header            â”‚
â”‚  Content cards          â”‚
â”‚  (full width)           â”‚
â”‚                         â”‚
â”‚  Tables scroll          â”‚
â”‚  horizontally           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

[Sidebar slides in from left on burger click]
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  âœ•           â”‚  â† close button
â”‚  [Avatar]    â”‚
â”‚  Username    â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚
â”‚  Home        â”‚
â”‚  Dashboard   â”‚
â”‚  ...         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Design decisions and rationale

| Decision | Rationale |
|---|---|
| Single dark colour scheme, no light mode | Students use the app during long coding sessions â€” dark mode reduces fatigue and makes the code editor feel natural |
| Role-aware sidebar (different links per role) | Reduces cognitive load â€” users only see actions relevant to them; avoids confusion from seeing disabled links |
| Collapsible task description | Keeps the editor as large as possible on smaller screens; description is available on demand |
| Auto-create Submission on task open | Removes a setup step for students â€” first visit is all it takes to start working |
| Floating "? Help" button on live tasks | Positioned bottom-right, out of the way of the editor, but immediately accessible during a live session |
| Tables with horizontal scroll wrapper on mobile | Preserves information density on desktop; allows tables to be used on mobile without breaking the layout |
| Green dot connection indicator | Gives immediate, ambient feedback on WebSocket state without a modal or alert |

### Responsiveness approach

- **Breakpoints**: `900px` (tablet/mobile) and `600px` (small mobile).
- At `<900px`: sidebar collapses behind a fixed burger button; main content takes full width with top padding.
- At `<900px`: all tables are wrapped in `.inbox-container { overflow-x: auto }` â€” tables scroll horizontally rather than breaking layout.
- At `<900px`: multi-column grids (`subject-grid`, `cards-grid`) collapse to single column.
- At `<900px`: flex rows in forms and headers switch to `flex-direction: column`.
- Tested manually on Chrome DevTools at 375px (iPhone SE), 768px (iPad), and 1280px (desktop).

---

## Data model

```
User (Django built-in)
 â””â”€â”€ Profile          role: student | teacher

Subject              teacher â†’ Profile
 â””â”€â”€ ClassGroup
      â”œâ”€â”€ GroupMembership  student â†’ Profile
      â”œâ”€â”€ Announcement     created_by â†’ Profile
      â””â”€â”€ Task             created_by â†’ Profile, type: text | python
           â”œâ”€â”€ Submission  student â†’ Profile, grade, comment
           â”‚    â””â”€â”€ FinalSubmission
           â””â”€â”€ TaskDocument  student â†’ Profile, content (live editor)
                â””â”€â”€ TaskDocumentVersion  author â†’ Profile

DirectMessage        sender â†’ User, recipient â†’ User, read
LiveTaskSession      document â†’ TaskDocument, user â†’ Profile
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
- Redis (for WebSocket channel layer â€” install locally or use Docker)

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

### Prerequisites

- A [Heroku account](https://heroku.com) with billing enabled (required for Redis add-on).
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed and logged in.
- [Git](https://git-scm.com/) installed.
- [Node.js 20+](https://nodejs.org/) and [Python 3.11+](https://python.org/) installed locally.

### Step-by-step deployment

#### 1. Clone the repository

```bash
git clone https://github.com/nwtes/DjangoProject.git
cd DjangoProject
```

#### 2. Create a Heroku app

```bash
heroku create your-app-name
```

#### 3. Set buildpacks (Node must come before Python)

```bash
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
```

Verify the order:

```bash
heroku buildpacks
# Expected:
# 1. heroku/nodejs
# 2. heroku/python
```

#### 4. Provision add-ons

```bash
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini
```

Both add-ons automatically set `DATABASE_URL` and `REDIS_URL` as config vars.

#### 5. Set environment variables

```bash
heroku config:set SECRET_KEY="your-long-random-secret-key"
heroku config:set DEBUG="False"
heroku config:set DJANGO_VITE_DEV_MODE="False"
```

Generate a secure secret key locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

#### 6. Verify config vars

```bash
heroku config
# Should show: SECRET_KEY, DEBUG, DATABASE_URL, REDIS_URL, DJANGO_VITE_DEV_MODE
```

#### 7. Files that must be present in the repository

| File | Purpose |
|---|---|
| `Procfile` | `web: daphne DjangoProject.asgi:application --port $PORT --bind 0.0.0.0` |
| `runtime.txt` | `python-3.11.x` â€” tells Heroku which Python version to use |
| `requirements.txt` | All Python dependencies |
| `package.json` | Must include `heroku-postbuild` script that runs `npm run build` |
| `static_build/` | Vite build output â€” must be committed or built in CI |
| `staticfiles/manifest.json` | Must match the Vite manifest |

#### 8. Deploy

```bash
git push heroku main
```

During the build Heroku will:
1. Run `npm ci` and `npm run heroku-postbuild` (Vite build).
2. Run `pip install -r requirements.txt`.
3. Run `python manage.py collectstatic --noinput`.

#### 9. Run database migrations

```bash
heroku run python manage.py migrate
```

#### 10. Create a superuser (optional)

```bash
heroku run python manage.py createsuperuser
```

#### 11. Verify the deployment

```bash
heroku open
heroku logs --tail
```

### Environment variables reference

| Variable | Required | Description | Example |
|---|---|---|---|
| `SECRET_KEY` | Yes | Django secret key â€” must be long and random | `abc123...` |
| `DEBUG` | Yes | Must be `False` in production | `False` |
| `DATABASE_URL` | Auto | Set by Heroku Postgres add-on | `postgres://...` |
| `REDIS_URL` | Auto | Set by Heroku Redis add-on | `redis://...` |
| `DJANGO_VITE_DEV_MODE` | Yes | Must be `False` in production | `False` |

### How `env.py` works (local only)

The project uses `env.py` (never committed) to set environment variables locally:

```python
import os
os.environ['SECRET_KEY'] = 'local-dev-secret'
os.environ['DEBUG'] = 'True'
# Leave DATABASE_URL unset to use SQLite
```

In `settings.py`:

```python
try:
    import env
except ImportError:
    pass

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

### How the build works

1. Node buildpack runs `npm run heroku-postbuild` â†’ `vite build` â†’ copies `.vite/manifest.json` to `static_build/manifest.json`.
2. Python buildpack installs dependencies, then runs `python manage.py collectstatic --noinput`.
3. `Procfile` starts Daphne (ASGI) which handles both HTTP and WebSocket traffic.

---

## Agile project management

### Tool & approach
This project was planned and tracked using **GitHub Projects (v2)** linked to this repository. All user stories were created as GitHub Issues, labelled by epic and MoSCoW priority, assigned to sprint milestones, and moved to **Done** on the Kanban board once implemented.

**Board:** [https://github.com/users/nwtes/projects/1](https://github.com/users/nwtes/projects/1)
**Issues:** [https://github.com/nwtes/DjangoProject/issues](https://github.com/nwtes/DjangoProject/issues)

Columns on the board: **Todo â†’ In Progress â†’ In Review â†’ Done**
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
| E1 â€” Authentication & Profiles | `epic:auth` | G4 |
| E2 â€” Classroom Management | `epic:classrooms` | G1 |
| E3 â€” Assignments & Submissions | `epic:assignments` | G1, G2 |
| E4 â€” Live Code Editor | `epic:editor` | G2, G3 |
| E5 â€” Direct Messaging | `epic:dm` | G3 |
| E6 â€” Deployment & Infrastructure | `epic:devops` | G5 |

---

### User stories

#### E1 â€” Authentication & Profiles (Sprint 1)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-01](https://github.com/nwtes/DjangoProject/issues/1) | As a new user I can register with a username, password and role so that I get the correct dashboard | Must Have | âœ… Done |
| [US-02](https://github.com/nwtes/DjangoProject/issues/2) | As a returning user I can log in and be redirected to my role-specific dashboard | Must Have | âœ… Done |
| [US-03](https://github.com/nwtes/DjangoProject/issues/3) | As a logged-in user I can view my profile page showing username, display name and bio | Should Have | âœ… Done |
| [US-04](https://github.com/nwtes/DjangoProject/issues/4) | As a logged-in user I can edit my display name and bio | Should Have | âœ… Done |
| [US-05](https://github.com/nwtes/DjangoProject/issues/5) | As an unauthenticated user I am redirected to login when I access protected pages | Must Have | âœ… Done |
| [US-06](https://github.com/nwtes/DjangoProject/issues/6) | As a student I cannot access teacher-only views | Must Have | âœ… Done |

#### E2 â€” Classroom Management (Sprint 2)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-07](https://github.com/nwtes/DjangoProject/issues/7) | As a teacher I can create a subject to organise groups underneath it | Must Have | âœ… Done |
| [US-08](https://github.com/nwtes/DjangoProject/issues/8) | As a teacher I can create a class group linked to a subject | Must Have | âœ… Done |
| [US-09](https://github.com/nwtes/DjangoProject/issues/9) | As a teacher I can view all my groups on a dedicated page | Must Have | âœ… Done |
| [US-10](https://github.com/nwtes/DjangoProject/issues/10) | As a teacher I can post an announcement to a class group | Should Have | âœ… Done |
| [US-11](https://github.com/nwtes/DjangoProject/issues/11) | As a student I can view announcements and classmates in my group | Should Have | âœ… Done |
| [US-12](https://github.com/nwtes/DjangoProject/issues/12) | As a teacher I can enrol students into a group | Must Have | âœ… Done |

#### E3 â€” Assignments & Submissions (Sprint 3)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-13](https://github.com/nwtes/DjangoProject/issues/13) | As a teacher I can create a task (text or Python) with title, description and optional starter code | Must Have | âœ… Done |
| [US-14](https://github.com/nwtes/DjangoProject/issues/14) | As a teacher I can edit an existing task | Should Have | âœ… Done |
| [US-15](https://github.com/nwtes/DjangoProject/issues/15) | As a teacher I can delete a task | Should Have | âœ… Done |
| [US-16](https://github.com/nwtes/DjangoProject/issues/16) | As a student I can view my assigned tasks list filtered by group | Must Have | âœ… Done |
| [US-17](https://github.com/nwtes/DjangoProject/issues/17) | As a student I can open a task and have a Submission and TaskDocument auto-created | Must Have | âœ… Done |
| [US-18](https://github.com/nwtes/DjangoProject/issues/18) | As a student my work autosaves every few seconds | Must Have | âœ… Done |
| [US-19](https://github.com/nwtes/DjangoProject/issues/19) | As a student I can submit my final answer | Must Have | âœ… Done |
| [US-20](https://github.com/nwtes/DjangoProject/issues/20) | As a teacher I can grade a submission and leave a comment | Should Have | âœ… Done |
| [US-21](https://github.com/nwtes/DjangoProject/issues/21) | As a student I can view my graded submission with feedback | Should Have | âœ… Done |

#### E4 â€” Live Code Editor (Sprint 4)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-22](https://github.com/nwtes/DjangoProject/issues/22) | As a student I can write code in a CodeMirror editor with syntax highlighting | Must Have | âœ… Done |
| [US-23](https://github.com/nwtes/DjangoProject/issues/23) | As a student I can run Python code in the browser via Pyodide | Should Have | âœ… Done |
| [US-24](https://github.com/nwtes/DjangoProject/issues/24) | As a teacher I can open a live session and see which students are connected | Must Have | âœ… Done |
| [US-25](https://github.com/nwtes/DjangoProject/issues/25) | As a teacher I can click a student to view their code in real time | Must Have | âœ… Done |
| [US-26](https://github.com/nwtes/DjangoProject/issues/26) | As a student I see a "Teacher is watching" indicator when observed | Should Have | âœ… Done |
| [US-27](https://github.com/nwtes/DjangoProject/issues/27) | As a student I can send a help request notification to the teacher | Could Have | âœ… Done |
| [US-28](https://github.com/nwtes/DjangoProject/issues/28) | As a student my unsaved content is preserved in localStorage on refresh | Could Have | âœ… Done |

#### E5 â€” Direct Messaging (Sprint 5)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-29](https://github.com/nwtes/DjangoProject/issues/29) | As a user I can open a DM thread with another user | Must Have | âœ… Done |
| [US-30](https://github.com/nwtes/DjangoProject/issues/30) | As a user I can send a message that appears instantly without a page refresh | Must Have | âœ… Done |
| [US-31](https://github.com/nwtes/DjangoProject/issues/31) | As a user I can see the full message history when I open a thread | Must Have | âœ… Done |
| [US-32](https://github.com/nwtes/DjangoProject/issues/32) | As a user messages are marked as read when I open the thread | Should Have | âœ… Done |

#### E6 â€” Deployment & Infrastructure (Sprint 6)

| ID | Story | Priority | Status |
|---|---|---|---|
| [US-33](https://github.com/nwtes/DjangoProject/issues/33) | As a developer I can deploy to Heroku with a single git push | Must Have | âœ… Done |
| [US-34](https://github.com/nwtes/DjangoProject/issues/34) | As a developer static files are collected and served correctly in production | Must Have | âœ… Done |
| [US-35](https://github.com/nwtes/DjangoProject/issues/35) | As a developer environment secrets are not stored in source code | Must Have | âœ… Done |
| [US-36](https://github.com/nwtes/DjangoProject/issues/36) | As a developer WebSocket connections work in production via Heroku | Must Have | âœ… Done |

---

### Sprint plan

| Sprint | Milestone | Stories | Focus |
|---|---|---|---|
| Sprint 1 | [Sprint 1 â€” Auth and Profiles](https://github.com/nwtes/DjangoProject/milestone/10) | US-01 â€“ US-06 | Registration, login, role redirect, profile |
| Sprint 2 | [Sprint 2 â€” Classroom Management](https://github.com/nwtes/DjangoProject/milestone/11) | US-07 â€“ US-12 | Subjects, groups, memberships, announcements |
| Sprint 3 | [Sprint 3 â€” Assignments and Submissions](https://github.com/nwtes/DjangoProject/milestone/12) | US-13 â€“ US-21 | Task CRUD, submission, autosave, grading |
| Sprint 4 | [Sprint 4 â€” Live Code Editor](https://github.com/nwtes/DjangoProject/milestone/4) | US-22 â€“ US-28 | CodeMirror, Pyodide, WebSocket live editor |
| Sprint 5 | [Sprint 5 â€” Direct Messaging](https://github.com/nwtes/DjangoProject/milestone/5) | US-29 â€“ US-32 | DM threads, live WebSocket messaging |
| Sprint 6 | [Sprint 6 â€” Deployment and Infra](https://github.com/nwtes/DjangoProject/milestone/6) | US-33 â€“ US-36 | Heroku deploy, static files, production config |

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
| accounts | ProfileSignalTests | 6 | âœ… PASS |
| accounts | RegistrationViewTests | 4 | âœ… PASS |
| accounts | LoginRedirectTests | 2 | âœ… PASS |
| accounts | ProfileViewTests | 4 | âœ… PASS |
| assignments | TaskModelTests | 7 | âœ… PASS |
| assignments | AssignmentViewTests | 11 | âœ… PASS |
| classrooms | ClassroomModelTests | 6 | âœ… PASS |
| classrooms | ClassroomViewTests | 3 | âœ… PASS |
| editor | TaskDocumentModelTests | 5 | âœ… PASS |
| editor | DirectMessageModelTests | 3 | âœ… PASS |
| pages | PagesViewTests | 15 | âœ… PASS |
| **Total** | | **66** | **âœ… All pass** |

Last run: `Ran 66 tests in ~170s â€” OK`

---

### 4.1 Python test procedures

#### `accounts` app â€” `accounts/tests.py`

**ProfileSignalTests** â€” verifies that the `post_save` signal automatically creates/updates a `Profile` whenever a `User` is saved.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 1 | `test_profile_created_on_user_creation` | Create a new User; check `profile` attribute exists and is a Profile instance | Profile created automatically | âœ… PASS |
| 2 | `test_profile_default_role_is_student` | New User's profile role defaults to `'student'` | `role == 'student'` | âœ… PASS |
| 3 | `test_profile_str` | `str(profile)` returns the username | `'charlie'` | âœ… PASS |
| 4 | `test_profile_role_can_be_set_to_teacher` | Save profile with `role='teacher'`, reload | `role == 'teacher'` | âœ… PASS |
| 5 | `test_profile_display_name_optional` | `display_name` is `None` on creation; can be set | Saves and reads back correctly | âœ… PASS |
| 6 | `test_profile_bio_optional` | `bio` field can be populated | Value persisted | âœ… PASS |

**RegistrationViewTests** â€” covers the `/accounts/register/` view.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 7 | `test_register_page_loads` | GET `/accounts/register/` | 200 OK | âœ… PASS |
| 8 | `test_register_creates_student_user` | POST valid form with `role=student` | Redirect + user created with student role | âœ… PASS |
| 9 | `test_register_creates_teacher_user` | POST valid form with `role=teacher` | User created with teacher role | âœ… PASS |
| 10 | `test_register_invalid_missing_username` | POST with blank username | 200 (form errors), no user created | âœ… PASS |

**LoginRedirectTests** â€” verifies role-based redirect after login.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 11 | `test_teacher_redirected_to_teacher_dashboard` | Teacher logs in | Redirect to `/teacher/dashboard` | âœ… PASS |
| 12 | `test_student_redirected_to_student_dashboard` | Student logs in | Redirect to `/student/dashboard` | âœ… PASS |

**ProfileViewTests** â€” covers `/accounts/profile/` and `/accounts/profile/edit/`.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 13 | `test_profile_requires_login` | GET profile page unauthenticated | 302 redirect to login | âœ… PASS |
| 14 | `test_profile_loads_when_logged_in` | GET profile page authenticated | 200 OK | âœ… PASS |
| 15 | `test_edit_profile_get` | GET edit profile page | 200 OK | âœ… PASS |
| 16 | `test_edit_profile_post_updates_display_name` | POST valid form | `display_name` updated in DB | âœ… PASS |

---

#### `assignments` app â€” `assignments/tests.py`

**TaskModelTests** â€” unit tests for `Task`, `Submission`, `FinalSubmission` models.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 17 | `test_create_task` | Create Task; check `str()` and `is_live=False` default | Task saved, `is_live` is `False` | âœ… PASS |
| 18 | `test_task_default_type_is_text` | Default `task_type` is `'text'` | `task_type == 'text'` | âœ… PASS |
| 19 | `test_task_python_type` | Task created with `task_type='python'` | `task_type == 'python'` | âœ… PASS |
| 20 | `test_task_starter_code_optional` | `starter_code` defaults to `None` | `None` | âœ… PASS |
| 21 | `test_create_submission` | Create Submission; check `submitted=False` default | Saved, linked to task/student | âœ… PASS |
| 22 | `test_submission_unique_per_student_task` | Create two Submissions for same student+task | `IntegrityError` raised | âœ… PASS |
| 23 | `test_final_submission_str` | `str(FinalSubmission)` contains student name | String contains student | âœ… PASS |

**AssignmentViewTests** â€” integration tests for assignment views.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 24 | `test_student_task_view_requires_login` | GET task page unauthenticated | 302 redirect | âœ… PASS |
| 25 | `test_student_task_view_loads` | GET task page as student | 200 + task title in response | âœ… PASS |
| 26 | `test_student_task_view_creates_document_and_submission` | First visit creates `TaskDocument` and `Submission` | Both objects exist in DB | âœ… PASS |
| 27 | `test_autosave_saves_content` | POST JSON `{content: 'my code'}` to autosave | `{saved: true}` + content stored | âœ… PASS |
| 28 | `test_autosave_rejects_non_post` | GET autosave endpoint | 400 error | âœ… PASS |
| 29 | `test_submit_task_creates_final_submission` | POST to submit endpoint | `FinalSubmission` row created | âœ… PASS |
| 30 | `test_student_tasks_list_view` | GET student tasks list | 200 + task title visible | âœ… PASS |
| 31 | `test_student_tasks_filter_by_group` | GET tasks list with `?group=<id>` | 200 OK | âœ… PASS |
| 32 | `test_teacher_tasks_list_view` | GET teacher tasks list as teacher | 200 + task title visible | âœ… PASS |
| 33 | `test_grading_view_get` | GET grading form as teacher | 200 OK | âœ… PASS |
| 34 | `test_grading_view_post_grades_submission` | POST grade + comment | `grade=85`, `comment='Good work'` saved | âœ… PASS |
| 35 | `test_student_submission_view` | GET student's own submission view | 200 OK | âœ… PASS |

---

#### `classrooms` app â€” `classrooms/tests.py`

**ClassroomModelTests** â€” unit tests for `Subject`, `ClassGroup`, `GroupMembership`, `Announcement`.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 36 | `test_subject_str` | `str(Subject)` returns subject name | `'History'` | âœ… PASS |
| 37 | `test_classgroup_str` | `str(ClassGroup)` returns group name | `'BioGroup'` | âœ… PASS |
| 38 | `test_group_membership_unique` | Second membership for same student+group | `IntegrityError` | âœ… PASS |
| 39 | `test_announcement_str` | `str(Announcement)` returns title | `'Exam'` | âœ… PASS |
| 40 | `test_multiple_groups_per_subject` | Create 2 groups under one subject | `classgroup.count() == 2` | âœ… PASS |
| 41 | `test_student_can_join_multiple_groups` | Student joins 2 groups | `GroupMembership.count() == 2` | âœ… PASS |

**ClassroomViewTests** â€” integration tests for announcement views.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 42 | `test_create_announcement_requires_login` | GET create announcement unauthenticated | 302 redirect | âœ… PASS |
| 43 | `test_create_announcement_get` | GET create announcement as teacher | 200 OK | âœ… PASS |
| 44 | `test_create_announcement_post` | POST valid announcement | Announcement exists in DB | âœ… PASS |

---

#### `editor` app â€” `editor/tests.py`

**TaskDocumentModelTests** â€” unit tests for the live-editor document model.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 45 | `test_task_document_created` | Create TaskDocument with content | `content` stored, `str()` contains task title | âœ… PASS |
| 46 | `test_task_document_unique_per_student_task` | Second document for same student+task | `IntegrityError` | âœ… PASS |
| 47 | `test_task_document_default_content_empty` | Default content is empty string | `content == ''` | âœ… PASS |
| 48 | `test_task_document_version_created` | Create a `TaskDocumentVersion` | Saved with correct content and author | âœ… PASS |
| 49 | `test_multiple_versions_per_document` | Create 2 versions for one document | `count() == 2` | âœ… PASS |

**DirectMessageModelTests** â€” unit tests for the DM model.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 50 | `test_create_message` | Create DM; check body, `read=False`, str | All correct | âœ… PASS |
| 51 | `test_message_ordered_by_sent_at` | Two messages; check ordering | First created appears first | âœ… PASS |
| 52 | `test_mark_read` | Set `read=True` and save | `read` is `True` after reload | âœ… PASS |

---

#### `pages` app â€” `pages/tests.py`

**PagesViewTests** â€” integration tests for dashboards, task CRUD, group views, access control.

| # | Test name | Description | Expected | Actual |
|---|---|---|---|---|
| 53 | `test_home_view_public` | GET `/` unauthenticated | 200 OK | âœ… PASS |
| 54 | `test_student_dashboard_redirects_when_not_logged_in` | GET student dashboard unauthenticated | 302 | âœ… PASS |
| 55 | `test_student_dashboard_loads_when_logged_in` | GET student dashboard as student | 200 OK | âœ… PASS |
| 56 | `test_teacher_dashboard_redirects_when_not_logged_in` | GET teacher dashboard unauthenticated | 302 | âœ… PASS |
| 57 | `test_teacher_dashboard_requires_teacher` | GET teacher dashboard as student | 403; as teacher â†’ 200 | âœ… PASS |
| 58 | `test_student_group_view_shows_announcements_and_students` | GET group page with announcement | 200 + announcement title + student name visible | âœ… PASS |
| 59 | `test_teacher_can_view_task_page` | GET teacher task detail page | 200 OK | âœ… PASS |
| 60 | `test_teacher_can_create_task_get` | GET create task form | 200 OK | âœ… PASS |
| 61 | `test_teacher_can_create_task_post` | POST valid task form | Redirect + task in DB | âœ… PASS |
| 62 | `test_student_cannot_create_task` | GET create task as student | 403 Forbidden | âœ… PASS |
| 63 | `test_teacher_group_view_loads` | GET teacher group view | 200 OK | âœ… PASS |
| 64 | `test_teacher_analytics_view_loads` | GET analytics page as teacher | 200 OK | âœ… PASS |
| 65 | `test_teacher_can_edit_task` | POST edit task form with new title | `title` updated in DB | âœ… PASS |
| 66 | `test_teacher_can_delete_task` | POST delete task | Task no longer exists in DB | âœ… PASS |

---

### 4.2 JavaScript test procedures

JavaScript testing is performed manually due to the project relying on browser-only APIs (WebSocket, CodeMirror, Pyodide).

| # | Component | Test description | Steps | Expected | Result |
|---|---|---|---|---|---|
| JS-1 | CodeMirror editor | Editor initialises on task page | Open `/tasks/task/<id>` as a student | Editor renders with syntax highlighting, cursor is active | âœ… PASS |
| JS-2 | CodeMirror â€” Python mode | Python syntax highlighting | Create a Python-type task; open task page | Keywords like `def`, `return` are highlighted | âœ… PASS |
| JS-3 | Autosave | Content saved on typing | Type in editor; wait 2 s | "Saved" status indicator appears, content persists on reload | âœ… PASS |
| JS-4 | Manual save button | Save button triggers save | Click "Save" button | "Savingâ€¦" â†’ timestamp shown | âœ… PASS |
| JS-5 | WebSocket â€” student connect | Student connects to live task room | Open live task page as student | Connection indicator turns green ("Connected") | âœ… PASS |
| JS-6 | WebSocket â€” teacher sees student | Teacher opens editor view | Open `/editor/room/<task_id>` as teacher | Student appears in the student list sidebar | âœ… PASS |
| JS-7 | WebSocket â€” live sync | Teacher selects student; editor reflects content | Click a student name in list | Editor updates to show that student's code in real time | âœ… PASS |
| JS-8 | Help request button | Student sends help request | Student clicks floating "?" button | Notification banner appears on teacher's page | âœ… PASS |
| JS-9 | Teacher-watching indicator | Student sees "Teacher is watching" badge | Teacher clicks on that student | Badge appears; disappears when teacher switches student | âœ… PASS |
| JS-10 | Connection indicator â€” offline | Reconnect behaviour | Kill Django server; observe UI | Indicator turns red ("Offline") | âœ… PASS |
| JS-11 | Local storage fallback | Unsaved content survives page reload | Type in editor; reload without saving | Content restored from `localStorage` | âœ… PASS |
| JS-12 | Pyodide run code | Run button executes Python | Write `print("hello")` in Python task; click "Run" | Output panel shows `hello` | âœ… PASS |
| JS-13 | Pyodide error output | Syntax error displayed | Write `def f(:` ; click "Run" | Error message shown in output panel | âœ… PASS |
| JS-14 | DM â€” send message | Send a direct message | Open DM thread; type message; press Enter | Message appears instantly without page reload | âœ… PASS |
| JS-15 | DM â€” receive message | Other user sees message live | Second browser sends DM | Message appears in first browser instantly | âœ… PASS |
| JS-16 | Responsive sidebar | Mobile burger menu | Resize to <768 px; click burger | Sidebar opens; burger hides; close button appears | âœ… PASS |

---

### 4.3 Testing documentation notes

- **Test isolation**: every `TestCase` class sets up its own users, profiles, subjects, groups, and tasks in `setUp()`, so tests are fully independent of each other and of production data.
- **Authentication**: access-control tests verify that unauthenticated users receive HTTP 302 and that students cannot access teacher-only views (HTTP 403 via the `role_required` decorator).
- **Model constraints**: unique-together and integrity constraints are validated by asserting that `IntegrityError` is raised on duplicate creation attempts.
- **View side-effects**: tests that POST data (autosave, grading, submission) reload the relevant object from the database to confirm the change was actually persisted.
- **Bugs found and fixed during testing**:
  - `student_task_view` was missing `@login_required` â€” anonymous requests raised `AttributeError` instead of redirecting. Fixed by adding the decorator.
  - `create_announcement` was missing `@login_required` â€” same issue. Fixed.
  - `teacher_group_view` used a hardcoded `get_object_or_404(ClassGroup, id=1)` as fallback, causing 404 in any environment where group id 1 does not exist. Fixed to use `.first()` with a `None`-safe guard.
- **Coverage**: all 5 Django apps have automated tests. WebSocket consumer logic and Pyodide integration are covered by the manual JS test procedures above, as they depend on browser and async runtime environments that are impractical to exercise with `django.test`.

---

## AI reflection (LO8)

This project was developed with **GitHub Copilot** as the primary AI assistant. The following sections document how AI tools affected the development process.

### 8.1 AI-assisted code generation

GitHub Copilot was used extensively to generate boilerplate and accelerate implementation of well-defined patterns:

- **Django views**: Copilot generated the initial structure of all CRUD views (create/edit/delete task, grading view, student submission view). The generated code was reviewed, decorator protection (`@login_required`, `@role_required`) was verified or added, and docstrings were added to every function.
- **WebSocket consumer**: The initial `EditorConsumer` class was largely Copilot-generated based on Django Channels documentation patterns. Group broadcast logic and the `help_request` message handler were generated and then debugged manually.
- **CodeMirror setup**: Copilot generated the initial `initEditor` function in `base.js` from a description of requirements (CodeMirror 6, Python mode, One Dark theme, autosave). The generated code required fixes for the `drawSelection` import error and the `@codemirror/state` duplicate-instance error.
- **Django model definitions**: Model fields, `__str__` methods, `Meta.unique_together` constraints, and `post_save` signal for auto-creating `Profile` were all Copilot-generated.
- **Test cases**: Copilot generated the initial test skeletons for all 5 apps. Test class structure, `setUp` methods, and individual test methods were generated from descriptions of what each test should verify.

### 8.2 AI-assisted debugging

Copilot and iterative prompting were used to resolve several bugs:

- **`FieldError: Cannot resolve keyword 'duration_minutes'`**: After `Task` fields `duration_minutes` and `started_at` were removed in migration `0008`, Copilot identified all remaining references in `views.py` and generated the corrected code removing those fields.
- **CORS / Vite dev mode**: Cross-origin errors in local development were traced to the `DJANGO_VITE_DEV_MODE` setting and the Vite dev server not running. Copilot helped identify the root cause and the correct sequence of commands.
- **`NoReverseMatch` for `groups` URL**: A URL pattern mismatch between `path("group", ...)` and template `{% url 'groups' group_id %}` was identified with Copilot's help, which generated the corrected URL patterns.
- **Missing `@login_required` on views**: A systematic audit prompted via Copilot identified 8 views missing authentication decorators across 4 apps, which were all added in a single pass.
- **Duplicate `toggle_live` function**: Copilot identified that the function was defined twice in `assignments/views.py` and generated the de-duplicated version.

### 8.3 AI-assisted optimisation and UX improvements

Copilot contributed to performance and UX improvements in the following areas:

- **Context processor**: Copilot suggested centralising `ungraded_count`, `pending_tasks_count`, and `unread_dm_count` into a single context processor (`pages/context_processors.py`) rather than passing them in every view individually. This eliminated repeated query logic across 10+ views.
- **QuerySet annotations**: Copilot suggested using `annotate()` with `Count` and `Exists` subqueries for the student task list and teacher dashboard, replacing Python-level loops that would have caused N+1 query problems.
- **localStorage fallback**: Copilot suggested storing editor content in `localStorage` on every keystroke and restoring it on reconnect/refresh as a low-cost reliability improvement.
- **Sequence numbers on WebSocket messages**: Copilot suggested adding a `seq` field to outgoing editor updates to allow the receiver to discard stale out-of-order messages â€” a lightweight conflict avoidance technique.
- **`select_related` on querysets**: Copilot identified several views loading related objects with N+1 queries (e.g. `Submission.task.group`) and added `select_related` calls to reduce database round-trips.

### 8.4 AI-generated unit tests

GitHub Copilot generated the initial versions of all test cases across all 5 apps. The process was:

1. Describe the model or view to test in a comment or prompt.
2. Copilot generated a test class with `setUp` and individual test methods.
3. Tests were run; failures identified cases where the generated assertions were incorrect (e.g. expected HTTP 200 but received 302 for a protected view â€” corrected to 302).
4. Coverage gaps (e.g. no test for `@role_required` returning 403, no test for `IntegrityError` on duplicate submissions) were identified manually and filled with Copilot-generated additions.

Key adjustments made to Copilot-generated tests:
- Added `profile.role = 'teacher'` / `'student'` + `.save()` after user creation â€” Copilot initially omitted the role assignment, causing tests to fail with `PermissionDenied`.
- Corrected `assertRedirects` target URLs to match actual URL patterns.
- Added the `student_submission_view` ownership guard test after manually identifying that a student could access another student's submission.

### Summary

AI tools significantly accelerated initial code generation and reduced the time spent on boilerplate. The most valuable contributions were in debugging (systematic audits of decorator coverage and field references), query optimisation (N+1 detection and annotation suggestions), and test generation. All AI-generated code was reviewed, tested, and adjusted before being committed.

The following ASCII wireframes represent the initial layout planning for key pages. The final implementation follows these layouts closely.

#### Base layout (all pages)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   SIDEBAR    â”‚           MAIN CONTENT           â”‚
â”‚              â”‚                                  â”‚
â”‚  [Avatar]    â”‚  Page header + actions           â”‚
â”‚  Username    â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚                                  â”‚
â”‚  Home        â”‚  Content cards / tables          â”‚
â”‚  Dashboard   â”‚                                  â”‚
â”‚  My groups   â”‚                                  â”‚
â”‚  My tasks    â”‚                                  â”‚
â”‚  Messages    â”‚                                  â”‚
â”‚  Logout      â”‚                                  â”‚
â”‚              â”‚                                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Teacher dashboard

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Teacher Dashboard          [Create task] [Analytics] â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Groups                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”‚
â”‚  â”‚ CS-A     â”‚ â”‚ CS-B     â”‚ â”‚ Math-A   â”‚        â”‚
â”‚  â”‚ 24 stud  â”‚ â”‚ 18 stud  â”‚ â”‚ 30 stud  â”‚        â”‚
â”‚  â”‚ [View]   â”‚ â”‚ [View]   â”‚ â”‚ [View]   â”‚        â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Ungraded Submissions                           â”‚
â”‚  Student  â”‚ Group â”‚ Task       â”‚ [Grade â†’]      â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”‚
â”‚                        [View All Submissions]   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Task editor (student)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Task: Fibonacci Sequence      [Save] [Submit]  â”‚
â”‚  â–¾ Task description (collapsible)               â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”‚
â”‚  â”‚  CodeMirror editor    â”‚  Task info      â”‚    â”‚
â”‚  â”‚                       â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â”‚    â”‚
â”‚  â”‚  def fibonacci(n):    â”‚  Group: CS-A    â”‚    â”‚
â”‚  â”‚      ...              â”‚  Teacher: John  â”‚    â”‚
â”‚  â”‚                       â”‚  Type: Python   â”‚    â”‚
â”‚  â”‚                       â”‚  [Run â–¶]        â”‚    â”‚
â”‚  â”‚                       â”‚                 â”‚    â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚
â”‚  â— Connected  Saved 12:34                       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

#### Mobile layout (<900px)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ â˜°  Learn                â”‚  â† burger button
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Page header            â”‚
â”‚  Content cards          â”‚
â”‚  (full width)           â”‚
â”‚                         â”‚
â”‚  Tables scroll          â”‚
â”‚  horizontally           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

[Sidebar slides in from left on burger click]
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  âœ•           â”‚  â† close button
â”‚  [Avatar]    â”‚
â”‚  Username    â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€   â”‚
â”‚  Home        â”‚
â”‚  Dashboard   â”‚
â”‚  ...         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Design decisions and rationale

| Decision | Rationale |
|---|---|
| Single dark colour scheme, no light mode | Students use the app during long coding sessions â€” dark mode reduces fatigue and makes the code editor feel natural |
| Role-aware sidebar (different links per role) | Reduces cognitive load â€” users only see actions relevant to them; avoids confusion from seeing disabled links |
| Collapsible task description | Keeps the editor as large as possible on smaller screens; description is available on demand |
| Auto-create Submission on task open | Removes a setup step for students â€” first visit is all it takes to start working |
| Floating "? Help" button on live tasks | Positioned bottom-right, out of the way of the editor, but immediately accessible during a live session |
| Tables with horizontal scroll wrapper on mobile | Preserves information density on desktop; allows tables to be used on mobile without breaking the layout |
| Green dot connection indicator | Gives immediate, ambient feedback on WebSocket state without a modal or alert |

### Responsiveness approach

- **Breakpoints**: `900px` (tablet/mobile) and `600px` (small mobile).
- At `<900px`: sidebar collapses behind a fixed burger button; main content takes full width with top padding.
- At `<900px`: all tables are wrapped in `.inbox-container { overflow-x: auto }` â€” tables scroll horizontally rather than breaking layout.
- At `<900px`: multi-column grids (`subject-grid`, `cards-grid`) collapse to single column.
- At `<900px`: flex rows in forms and headers switch to `flex-direction: column`.
- Tested manually on Chrome DevTools at 375px (iPhone SE), 768px (iPad), and 1280px (desktop).

