# PROJECT REPORT
## LIBRARY MANAGEMENT SYSTEM

**Submitted by:** MAREEDU CHARAN  
**Department:** CSE – AI, ML and DS  
**Subject:** Programming with Python (01AI0302)  
**Semester:** 3  
**Project Work:** 10 Marks

---

## 1. Introduction
The Library Management System is a desktop application developed using Python. It helps manage book information, student/member records, book issue and return activities, and library reports. The application uses a graphical user interface created with Tkinter and stores data in an SQLite database.

## 2. Problem Statement
Manual library records can be difficult to maintain, search, and update. Tracking issued books, due dates, and overdue returns manually may lead to errors. This project provides a computerized system to organize books and members and record transactions.

## 3. Objectives
- Store and manage book details.
- Register and maintain library members.
- Issue books and record due dates.
- Accept returned books and calculate overdue fines.
- Display current library statistics.
- Export book, member, and transaction reports.

## 4. Software and Hardware Requirements
| Component | Requirement |
|---|---|
| Programming language | Python 3.8+ |
| GUI | Tkinter |
| Database | SQLite |
| Operating system | Windows / Linux / macOS |
| Third-party packages | Not required |
| Hardware | Standard computer capable of running Python |

## 5. System Modules
1. **Dashboard:** Displays total book copies, available copies, members, issued books, and overdue issues.
2. **Book Catalogue:** Adds, updates, deletes, searches, and displays book records.
3. **Member Management:** Maintains student/member details.
4. **Issue and Return:** Issues available books, records due dates, processes returns, and calculates fines.
5. **Reports:** Displays transaction history and exports CSV reports.

## 6. Database Design
- **Books:** book_id, title, author, category, ISBN, total_copies, available_copies.
- **Members:** member_id, name, class_name, phone, email.
- **Loans:** loan_id, book_id, member_id, issue_date, due_date, return_date, fine.

The loans table links each transaction to one book and one member using foreign keys.

## 7. Algorithm
1. Start the application.
2. Connect to the SQLite database.
3. Create the required tables if they do not exist.
4. Display the main dashboard and navigation menu.
5. When the user selects an operation:
   - Add, update, delete, or search books.
   - Add, update, or delete members.
   - Issue an available book to a registered member.
   - Return an issued book and calculate any late fine.
   - Display or export reports.
6. Update the database after each successful operation.
7. Continue until the user closes the application.
8. Close the database connection and stop.

## 8. Business Rules and Formula
- Standard issue period: 14 days.
- Fine rate: ₹2 per overdue day.
- Fine = Number of late days × ₹2.
- A book can be issued only when an available copy exists.
- The same member cannot have the same book issued twice at the same time.
- Available copies are reduced when a book is issued and increased when it is returned.

## 9. Sample Input and Output
Example book details:
```text
Title: Python Programming
Author: Reema Thareja
Category: Programming
ISBN: 9789351199076
Copies: 3
```

Example member details:
```text
Name: Aarav Patel
Class: EN3
Phone: 9876543210
Email: aarav@example.com
```

Illustrative issue confirmation:
```text
Book issued successfully.
Due date: [issue date + 14 days]
```

Illustrative return confirmation:
```text
Book returned successfully.
Late days: 2
Fine: ₹4.00
```

*The sample values are for demonstration. Actual dates and records depend on user input.*

## 10. Python Concepts Used
- Variables and data types
- Conditional statements and loops
- Functions and classes
- Object-oriented programming
- Tkinter GUI widgets and event handling
- SQLite database connectivity and SQL queries
- Exception handling
- CSV file handling
- Date and time calculations

## 11. Advantages
- Easy-to-use graphical interface.
- Faster book and member record management.
- Accurate availability tracking.
- Automatic due-date and fine calculation.
- Data remains saved after closing the application.
- Reports can be opened in spreadsheet applications.

## 12. Limitations and Future Scope
The current project is designed for a single local computer. Future enhancements may include librarian login, barcode scanning, email/SMS reminders, cloud database support, multiple library branches, and a web-based interface.

## 13. Conclusion
The Library Management System demonstrates the practical use of Python programming, GUI development, database operations, and file export. It provides a simple and organized way to manage library books, members, and transactions.
