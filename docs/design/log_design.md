# UniSplit Security Logging Design

This document outlines the security logging and monitoring strategy for the UniSplit project, following the [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) and OWASP Top 10 C9 guidelines.

## 1. Where to Record Event Data

| Item | Implementation Status | Reasoning / Strategy |
| :--- | :--- | :--- |
| Application Logs (Local File) | **Implementing** | We will use Python's `logging` module to write to a rotating file (`unisplit_security.log`). |
| System Logs (Syslog) | **Not Implementing** | For this project stage, local application logs are sufficient. External syslog is more complex for local dev. |
| Database Security Audit | **Implementing** | Critical state changes are already partially tracked in `activity_log` table, but we will supplement this with application logs. |
| Centralized Log Management | **Not Implementing** | Out of scope for current MVP architecture. |

## 2. Which Events to Log

| Event Category | Implementation Status | Specific Events |
| :--- | :--- | :--- |
| Authentication | **Implementing** | Success/failure of Login, Registration, and Logouts. |
| Authorization | **Implementing** | Access denied events (e.g., unauthorized access to sensitive API endpoints). |
| Data Access | **Implementing** | Significant changes: creation or deletion of expenses and groups. |
| Input Validation | **Implementing** | Failures in input validation (e.g., malformed email, negative amounts). |
| System Errors | **Implementing** | Unexpected 500 errors and database integrity failures. |

## 3. Event Attributes (Log Format)

Each log entry will follow a structured format to ensure they are searchable and actionable.

**Format:**
`[Timestamp] [Level] [User_ID] [IP_Address] [Event_ID] [Outcome] [Message]`

| Attribute | Description |
| :--- | :--- |
| Timestamp | UTC time of the event. |
| Level | INFO (for success), WARN (for failures), ERROR (for critical issues). |
| User ID | The ID of the user performing the action (or "Anonymous"). |
| IP Address | The client's IP address making the request. |
| Event ID | A unique string identifier for the type of event (e.g., `AUTH_LOGIN_FAIL`). |
| Outcome | Success, Failure, or Pending. |
| Message | A human-readable description (Avoid logging PII like passwords). |

## 4. Implementation Details

- **Log Rotation**: We will limit log file size to 10MB with 5 backups to prevent disk exhaustion.
- **No PII Strategy**: We strictly forbid logging sensitive data such as passwords, JWT secrets, or full credit card numbers.
