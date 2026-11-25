# Library Management System

**Student:** MAREEDU CHARAN  
**Subject:** Programming with Python (01AI0302)  
**Department:** CSE – AI, ML and DS  
**Semester:** 3

## Project overview
A desktop-based Library Management System built with Python Tkinter and SQLite. It helps a librarian manage books and student members, issue and return books, calculate overdue fines, and export reports.

## Requirements
- Python 3.8 or later
- Tkinter (included with most standard Python installations)
- SQLite (included with Python)
- No pip packages required

## Run the project
1. Extract the ZIP file.
2. Open the extracted `Library_Management_System_Professional` folder.
3. Open Command Prompt in this folder.
4. Run `python main.py` (or `py main.py` on Windows).
5. The desktop application opens. Use the left menu to navigate.

## First-time demonstration
1. Open **Books** and add a few books. ISBN must be unique if entered.
2. Open **Members** and register student members.
3. Open **Issue / Return**, select a book and a member, and click **Issue Book**.
4. Select an active issue and click **Return Selected** to return it.
5. Open **Reports** to view history and export CSV files.

## Main features
- Book catalogue: add, update, delete, search
- Member management: add, update, delete
- Issue and return workflow
- Availability tracking and duplicate active-issue prevention
- 14-day loan period and ₹2/day overdue fine
- Dashboard statistics and CSV report export
- SQLite persistence in `library.db`

## Database
The application automatically creates `library.db` in the same folder. It contains:
- `books`: book details and copy counts
- `members`: student/member details
- `loans`: issue, due, return dates and fine

Keep `library.db` with `main.py` to preserve records. Back it up regularly.

## Troubleshooting
- If `tkinter` is missing on Linux, install the OS package for Python Tk support (often `python3-tk`).
- If the window does not appear, run the command from a desktop session rather than a headless terminal.
- Do not delete `library.db` unless you intend to reset all project data.
