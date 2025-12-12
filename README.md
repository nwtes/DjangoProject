# DjangoProject

## Project overview
DjangoProject is a classroom and assignments platform with an integrated web code editor. It supports user accounts and profiles, classroom management, assignment creation, starter code, submissions, and grading. Frontend built with Vite and CodeMirror; Django serves backend and static assets.

## Key files and directories
- `manage.py` — Django CLI entry point  
- `package.json` — frontend scripts and Heroku postbuild hook  
- `vite.config.js` — Vite build configuration  
- `Procfile` — Heroku process specification  
- `static_build/` — Vite build output  
- `staticfiles/manifest.json` — manifest consumed by Django templates  
- Apps: `accounts`, `assignments`, `classrooms`, `editor`, `pages`

## Production-ready features
- Account registration, login, password reset, profile management  
- Classroom creation and join-by-code  
- Assignment authoring with due dates and starter code  
- In-browser code editor with syntax highlighting  
- Submission history, grading workflow, inline feedback  
- Admin interface for site management  
- CI/Deploy hooks for Heroku: frontend build and `collectstatic`

## User stories
1. As a student, I want to register an account so I can join classrooms and submit assignments.  
2. As a student, I want to set a display name and avatar so others recognize me.  
3. As a teacher, I want to create a classroom with a join code so I can invite students.  
4. As a student, I want to join a classroom using a code to access assignments.  
5. As a teacher, I want to create assignments with due dates and starter code.  
6. As a student, I want to edit starter code in the in-browser editor and save drafts.  
7. As a student, I want to submit my assignment with attached files or code.  
8. As a teacher, I want to view and filter submissions (late, ungraded).  
9. As a teacher, I want to leave inline comments on submissions for contextual feedback.  
10. As a student, I want to view graded submissions with comments and scores.  
11. As an admin, I want to manage users and classrooms via the Django admin.  
12. As a developer, I want Vite-built static assets referenced by Django manifest.  
13. As a DevOps engineer, I want Heroku to run `npm run build` and `python manage.py collectstatic` during deploy.  
14. As a teacher, I want bulk grade publishing for efficient workflows.  
15. As a student, I want a dashboard showing upcoming due dates and recent feedback.  
16. As a teacher, I want configurable auto-run tests for assignment types.  
17. As a user, I want strong authentication and input sanitization for security.  
18. As a developer, I want reproducible local dev commands (`npm run dev`, `python manage.py runserver`).

## Installation (local)
1. Create a virtual environment and activate it:
    
    python -m venv .venv  
    .venv\Scripts\activate

2. Install backend dependencies:
    
    pip install -r requirements.txt

3. Install frontend dependencies and build:
    
    npm install  
    npm run build

4. Prepare database and static files:
    
    python manage.py migrate  
    python manage.py collectstatic --noinput

5. Run development server:
    
    python manage.py runserver

## Heroku deployment notes
- Ensure migration files under `accounts/migrations/` are committed.  
- Configure Heroku buildpacks: add Node buildpack before Python.  
- `package.json` should include `build` and `heroku-postbuild` scripts (project has a postbuild that copies the manifest).  
- `Procfile` should include the web command, e.g., `web: gunicorn DjangoProject.wsgi`.  
- If you do not commit built assets, ensure Heroku runs the frontend build and copies `static_build/.vite/manifest.json` to `static_build/manifest.json` as part of build.

## Fast production fixes (hotfix)
If static assets are missing due to `.gitignore` excluding build outputs:
- Hotfix: force-add built assets and push:
    
    git add -f static_build/ staticfiles/ static/assets/ static_build/manifest.json staticfiles/manifest.json  
    git commit -m "hotfix: add built static assets for Heroku"  
    git push origin main  
    git push heroku main

- Recommended: enable Heroku frontend build instead of committing artifacts:
    
    heroku buildpacks:clear --app <app-name>  
    heroku buildpacks:add --index 1 heroku/nodejs --app <app-name>  
    heroku buildpacks:add --index 2 heroku/python --app <app-name>

## Database migrations and profile sync
- Run migrations on Heroku:
    
    heroku run python manage.py migrate --app <app-name>

- Ensure every existing `User` has a `Profile`:
    
    heroku run python manage.py shell --app <app-name>  
    from django.contrib.auth import get_user_model  
    from accounts.models import Profile  
    User = get_user_model()  
    for u in User.objects.all():  
        Profile.objects.get_or_create(user=u)

## Troubleshooting
- MIME error (HTML returned instead of JS): check rendered script URLs; they should start with `/static/assets/`. If they show `/static/static/assets/...` remove double-prefixing in templates and ensure `manifest.json` paths match `STATIC_URL`.  
- If migrations show missing column (e.g., `accounts_profile.display_name`), ensure migration that adds the column exists (`accounts/migrations/0003_...`) and run `migrate` on production.  
- Inspect Heroku runtime logs:
    
    heroku logs --tail --app <app-name>

## Testing and CI
- Run Django tests:
    
    python manage.py test

- CI pipeline should run:
  - `npm ci`  
  - `npm run build`  
  - `python -m pip install -r requirements.txt`  
  - `python manage.py test`  
  - Linting for Python and JS

## Operational
- Add a release step to run migrations automatically if desired (use with caution).  
- Store secrets in environment variables (Heroku config vars).  
- Monitor logs and backups for the production database.

## Contributing
- Fork, create a feature branch, run tests and builds locally, open a pull request.

## License
- Add a `LICENSE` file to declare project terms.
