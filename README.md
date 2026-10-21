JobTrack — Job Application Tracker

A web-based job application tracker built with Python, SQLite, and vanilla JavaScript. Organize applications, monitor hiring progress, and manage your job search in one place.

Live Demo: "Open JobTrack" (https://jobtrack-0e9w.onrender.com)

📌 Overview

JobTrack helps students and job seekers manage their job applications through a dashboard with application status tracking, search, filtering, and statistics.

✨ Features

- Authentication: Registration and login with PBKDF2-hashed passwords, per-user salts, and expiring session tokens.
- Application Management: Create, read, update, and delete job applications.
- REST API: Endpoints for registration, login, logout, user details, applications, and statistics.
- Kanban Board: Drag-and-drop application status updates with error rollback.
- Search & Filtering: Find applications and filter them by status.
- Dashboard Statistics: Pipeline counts, response rate, and application activity over the last seven days.
- Database: SQLite with foreign keys, indexes, parameterized queries, and user-scoped data access.

🛠️ Tech Stack

Technology| Purpose
Python| Backend and HTTP server
SQLite| Database
HTML| Page structure
CSS| Styling
Vanilla JavaScript| Frontend interactions and API requests

🚀 Run Locally

Prerequisites

- Python 3
- Git

1. Clone the repository

git clone YOUR_GITHUB_REPOSITORY_URL

Replace "YOUR_GITHUB_REPOSITORY_URL" with your repository's actual HTTPS clone URL.

2. Enter the project directory

cd JOBTRACK

3. Start the server

python3 server.py

On Windows, you may need:

python server.py

4. Open the application

Visit "http://localhost:8000" (http://localhost:8000) in your browser, unless you configured a different port.

Optional environment variables

- "PORT" — Port used by the server.
- "DB_PATH" — Path to the SQLite database file.

No third-party Python packages are required for the standard-library backend.

📸 Screenshots

Add screenshots of the actual running application here.

Login / Registration

Show the authentication page.

Dashboard

Show application statistics and the job application board.

Application Management

Show the form for adding or editing a job application.

⚠️ Known Limitations

- No built-in rate limiting.
- The built-in HTTP server is intended for demos and small-scale use, not production deployment.
- HTTPS must be provided by the hosting platform or a properly configured reverse proxy.
- Automated test coverage has not been added yet.
- SQLite data persistence depends on the hosting environment and database path.

Security note: Do not use sensitive real-world data until the deployment's security and database persistence have been properly reviewed.

🔮 Future Improvements

- Automated tests for authentication and application management.
- Rate limiting and stronger production security.
- Reliable persistent database storage and backups.
- Improved accessibility and mobile usability.

👨‍💻 Author

Prashant Navrang
B.Tech — Computer Science and Engineering

📄 License

No license has been specified yet. Add a "LICENSE" file if you decide to publish this project under an open-source license.
