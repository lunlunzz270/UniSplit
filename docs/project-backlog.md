# UniSplit Product Backlog

This product backlog defines the prioritized user stories for the UniSplit MVP.  
Stories are grouped by Epic and include acceptance criteria for verification.

---

## Epic 1 — User Account Management

| ID | User Story | Acceptance Criteria | Priority | Story Points | Sprint |
|----|------------|--------------------|---------|-------------|-------|
| US1 | As a student, I want to create an account so that I can use the expense tracking system. | User can register with email and password. Account is stored in database. User can log in successfully. | High | 3 | Sprint 1 |
| US2 | As a user, I want to log in securely so that my account information is protected. | Authentication validates credentials. Invalid login shows error. Session created after login. | High | 2 | Sprint 1 |

---

## Epic 2 — Group Management

| ID | User Story | Acceptance Criteria | Priority | Story Points | Sprint |
|----|------------|--------------------|---------|-------------|-------|
| US3 | As a user, I want to create a group for a trip or shared household so that expenses can be tracked among members. | User creates group. Group ID stored. Creator becomes group owner. | High | 3 | Sprint 1 |
| US4 | As a user, I want to join a group via invite link or code so that I can participate in shared expenses. | User enters invite code. System validates membership. User added to group. | High | 2 | Sprint 1 |

---

## Epic 3 — Expense Recording and Splitting

| ID | User Story | Acceptance Criteria | Priority | Story Points | Sprint |
|----|------------|--------------------|---------|-------------|-------|
| US5 | As a user, I want to add a shared expense so that costs can be recorded for the group. | User enters amount, description, payer, and participants. System validates input. Expense record stored. | High | 5 | Sprint 1 |
| US6 | As a user, I want the system to automatically split expenses equally so that balances are calculated correctly. | System calculates equal share. Balances updated in group ledger. | High | 3 | Sprint 1 |

---

## Epic 4 — Ledger and Balance Tracking

| ID | User Story | Acceptance Criteria | Priority | Story Points | Sprint |
|----|------------|--------------------|---------|-------------|-------|
| US7 | As a user, I want to view the group ledger so that I can see all expense history. | Ledger displays list of expenses with payer, amount, and date. | High | 3 | Sprint 2 |
| US8 | As a user, I want to see current balances so that I know who owes money and how much. | System calculates net balances for each user. Dashboard displays results. | High | 3 | Sprint 2 |

---

## Epic 5 — Payment and Reminder System

| ID | User Story | Acceptance Criteria | Priority | Story Points | Sprint |
|----|------------|--------------------|---------|-------------|-------|
| US9 | As a user, I want to mark a payment as completed so that balances update correctly. | Payment recorded. Ledger updated. Balances recalculated. | Medium | 2 | Sprint 2 |
| US10 | As a user, I want the system to send reminders to members who owe money so that payments are settled faster. | System generates reminder notification. Message sent to selected users. | Medium | 3 | Sprint 3 |

---

## Epic 6 — Administration and System Integrity

| ID | User Story | Acceptance Criteria | Priority | Story Points | Sprint |
|----|------------|--------------------|---------|-------------|-------|
| US11 | As an administrator, I want to view system transaction logs so that system integrity can be monitored. | Admin dashboard displays transaction history and audit logs. | Medium | 3 | Sprint 3 |
| US12 | As an administrator, I want to manage user accounts so that problematic accounts can be suspended if necessary. | Admin can suspend or restore accounts. All actions recorded in audit log. | Low | 2 | Sprint 3 |

---

## Backlog Management Notes

- High priority items represent the **Minimum Viable Product (MVP)** functionality.
- Stories are estimated using **story points** based on relative complexity.
- Backlog items may be refined during sprint planning sessions.