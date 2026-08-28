# EXAMORA

EXAMORA is a Flask + MySQL online examination application with a browser-based student flow for login, exam start, timed questions, submission, result review, and logout.

## Project structure

- `backend/` - Flask API and exam/auth logic
- `frontend/` - student-facing HTML/JS pages
- `database/` - SQL scripts and database setup artifacts

## Prerequisites

- Python 3.10+
- MySQL Server
- A browser for the student flow

## Environment configuration

Create a local `.env` file from `.env.example` and update the values to match your environment.

## Backend setup

1. Open a terminal in the project root.
2. Create and activate a virtual environment if desired.
3. Install backend dependencies (if a requirements file is present in the project).
4. Start the Flask app:

   python backend/app.py

5. Serve the frontend using a local HTTP server from the project root or from the frontend folder, depending on your local setup.

## Notes

- The validated exam flow and authentication hardening are already implemented.
- Do not commit local `.env` files or any secret values.
- Keep credentials out of source control.
