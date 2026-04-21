# History Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add CSV export to the transaction history page using the existing authenticated expense export endpoint.

**Architecture:** Reuse the existing `/api/expenses/export` backend contract and the shared `window.UniSplitApp.downloadResponseAsFile()` helper. Keep the change isolated to `frontend/src/history.html` so the history page can export its current filters without introducing new backend behavior.

**Tech Stack:** HTML, vanilla JavaScript, existing UniSplit frontend helper functions, authenticated fetch via session token.

---

### Task 1: Add the export control to the history filter bar

**Files:**
- Modify: `frontend/src/history.html`

**Step 1: Update the UI**

Add an `Export CSV` button beside the existing `Apply Filters` button in the filter grid.

**Step 2: Verify the layout stays consistent**

Confirm the new button uses the existing button styles and fits the current filter bar without changing page structure.

### Task 2: Wire export behavior to the existing endpoint

**Files:**
- Modify: `frontend/src/history.html`

**Step 1: Add the click handler**

Build the export URL from the current `search`, `category`, and `group_name` filters and call `/api/expenses/export` through `window.UniSplitApp.apiFetch()`.

**Step 2: Download the CSV**

Reuse `window.UniSplitApp.downloadResponseAsFile()` so the browser saves the CSV with a sensible filename.

**Step 3: Handle errors**

Show a history status message when export fails and restore the button label afterward.

### Task 3: Quick verification

**Files:**
- None

**Step 1: Sanity check the page**

Open `history.html` and confirm the button appears and uses the current filters.

**Step 2: Test export**

Use the page with and without filters and confirm the CSV downloads successfully.
