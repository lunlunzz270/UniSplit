# UniSplit: Use Cases and User Roles

---

## Part 1: Use Case

### 1. Use Case Name
Record and Split a Shared Expense

### 2. Primary Actor
Registered User (Student)

### 3. Stakeholders and Interests
- **User (Expense Payer)**: Wants fair cost distribution; Wants balances calculated correctly; Wants record of who owes what.
- **Other Group Members**: Want accurate balance tracking; Want transparency of expenses.
- **System Administrator**: Wants consistent ledger integrity; Wants audit log for dispute resolution.

### 4. Preconditions
- User is authenticated.
- User belongs to an existing group.
- Group contains at least two members.
- Group ledger exists.

### 5. Trigger
User submits a new shared expense entry.

### 6. Main Success Scenario (Basic Flow)

1. User selects a group.
2. User selects "Add Expense".
3. User enters expense amount.
4. User selects payer.
5. User selects participants included in split.
6. User submits expense.
7. System validates amount > 0.
8. System validates participants belong to group.
9. System calculates equal share per participant.
10. System creates expense record.
11. System debits each participant's balance.
12. System credits payer's balance.
13. System records transaction in group ledger.
14. System displays updated balances to user.

*(Every step is observable and testable)*

### 7. Alternate Flows (Extensions)

#### 7A. Invalid Amount
- 7a. System detects amount <= 0.
- 7b. System rejects expense.
- 7c. System displays error message.
- 7d. No ledger changes occur.

#### 7B. Invalid Participant
- 8a. System detects participant not in group.
- 8b. System rejects submission.
- 8c. System displays error message.
- 8d. No ledger changes occur.

#### 7C. System Failure During Update
- 11a. System fails before ledger commit.
- 11b. System rolls back transaction.
- 11c. No partial balances are updated.
- 11d. System logs failure.

*(This satisfies: "Undefined behavior is still behavior.")*

### 8. Postconditions

**Success Guarantee**
- Expense record created
- Ledger updated
- Balances reflect split
- Transaction logged

**Failure Guarantee**
- No account balances modified
- No partial ledger entries
- System state unchanged

### 9. Non-Functional Requirements
- Transaction must complete within 2 seconds.
- Ledger update must be atomic.
- System must maintain consistency of group balances.
- Every expense must generate an audit log entry.
- System must prevent duplicate submissions (idempotent behavior).

---

# Part 2: User Roles and Permissions

## 1. Regular User (Student)

A regular user is a student who participates in shared expenses for trips or household bills.

### A regular user can:
- Create an account and sign in/out.
- Create a group (Trip / Household).
- Join a group via invite link or code.
- Add/remove members (if they are the group owner).
- Enter an expense with: amount, description, date, category, payer, and included participants.
- Choose a split method (equal split for MVP).
- View group ledger (full expense history).
- View current balances (who owes whom and how much).
- Mark a payment as "paid" (manual confirmation for MVP).
- Request a reminder to be sent to specific members.
- Receive reminders and notifications (e.g., "you owe $X").
- Export or download a summary report (CSV/PDF for MVP optional).
- Leave a group (if balance is settled).

### Restrictions (Regular User cannot):
- Access groups they are not a member of.
- Modify another user's account information.
- Delete ledger records once confirmed (only allowed if system supports "void with audit log").
- Change system-wide reminder templates or rules.

---

## 2. Administrator (System Administrator)

An administrator is responsible for maintaining platform integrity, security, and operational stability across the entire system.

### An administrator can:
- View all registered users and their account status across the entire platform.
- Disable, suspend, or restore user accounts.
- Reset user passwords and manage credential recovery workflows.
- View platform-wide system transactions and system-level audit logs.
- Monitor and analyze platform-wide usage metrics (e.g., total active users, total groups, global expense volume, reminder frequency, reminder efficiency rate).
- Configure reminder policies (e.g., maximum reminder frequency, default reminder template).
- Lock or remove groups that violate platform policies (with audit logging).
- Manage external API integrations (e.g., API key rotation and configuration).
- Monitor system health status and error logs.
- Perform data backup and restore operations.

### Restrictions (Administrator cannot):
- Modify individual group balances without generating an audit record.
- Access private user credentials (passwords stored as hashed values only).
- Confirm or fabricate user payments without documented support workflow.
- Bypass transaction logging mechanisms.