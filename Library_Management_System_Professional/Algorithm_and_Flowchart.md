# Algorithm and Flowchart

## Algorithm
1. Start.
2. Connect to SQLite and create Books, Members, and Loans tables if absent.
3. Display the dashboard and navigation options.
4. Accept the user's selected module.
5. For Books: add, edit, delete, or search book records.
6. For Members: register, edit, or delete member records.
7. For Issue: validate member and available book, create loan, reduce available copies.
8. For Return: find active loan, calculate overdue fine, record return, increase available copies.
9. For Reports: display summaries and export CSV data.
10. Refresh the interface after each operation.
11. On close, close the database connection.
12. Stop.

## Flowchart
```mermaid
flowchart TD
    A([Start]) --> B[Connect to SQLite database]
    B --> C[Create tables if required]
    C --> D[Display dashboard and menu]
    D --> E{Select module}
    E -->|Books| F[Add / Edit / Delete / Search books]
    E -->|Members| G[Register / Edit / Delete members]
    E -->|Issue| H[Check member and book availability]
    H --> I{Available?}
    I -->|Yes| J[Create loan and reduce available copies]
    I -->|No| K[Show unavailable message]
    E -->|Return| L[Find active loan and calculate fine]
    L --> M[Save return and increase available copies]
    E -->|Reports| N[Display and export reports]
    F --> D
    G --> D
    J --> D
    K --> D
    M --> D
    N --> D
    D --> O{Close application?}
    O -->|No| D
    O -->|Yes| P[Close database]
    P --> Q([Stop])
```
