# Project: Wishlists Production Features & Worktrees

## Architecture
Django-based web application with Bootstrap 4 UI, SQLite database (in-memory during testing), session-based authentication, and git worktrees for isolated feature development.
- **Root Repository**: `/workspaces/wishlists`
- **Worktree Base**: `/workspaces/wishlists/.worktrees/`
  - `.worktrees/password-reset` (branch `feature/styled-password-reset`)
  - `.worktrees/groups-privacy` (branch `feature/groups-and-wishlist-privacy`)
  - `.worktrees/remember-me` (branch `feature/remember-me-session`)
- **Key Modules**:
  - `wishlists/accounts`: Authentication, login/logout, registration, password reset, session control.
  - `wishlists/lists`: Wishlists, items, custom Groups, privacy controls, access enforcement.
  - `wishlists/functional_tests`: End-to-end integration and Selenium tests.
  - `wishlists/wishlists`: Core settings, root URL routing.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Git Worktree Setup | Create `.worktrees/password-reset`, `.worktrees/groups-privacy`, `.worktrees/remember-me` with baseline code | M1: Worktree Setup | R1 |
| 2 | Password Reset URL Routing | Wire `password_reset_done` to `PasswordResetDoneView.as_view()` in `accounts/urls.py` | M2: Password Reset | R2 |
| 3 | Styled Password Reset Templates | Custom Bootstrap 4 templates extending `lists.base.html` for password reset form, done, confirm, and complete | M2: Password Reset | R2 |
| 4 | UI Exposure of Password Reset | Uncomment and wire password reset links in navbar dropdown and standalone login page | M2: Password Reset | R2 |
| 5 | Password Reset TDD Test Suite | Comprehensive unit/functional tests for the complete password reset cycle | M2: Password Reset | R2, R5 |
| 6 | Remember Me Checkbox Default | Default `remember_me` checkbox to checked/ticked in `LoginForm` and all login templates | M3: Remember Me | R4 |
| 7 | Session Expiration Control | Persistent session (`SESSION_COOKIE_AGE`) when checked; browser close expiry (`set_expiry(0)`) when unchecked | M3: Remember Me | R4 |
| 8 | Remember Me TDD Test Suite | Unit and functional tests verifying session cookie age and expiry behavior | M3: Remember Me | R4, R5 |
| 9 | Wishlist Private Default | Add `is_private = models.BooleanField(default=True)` to `Wishlist` so all new wishlists default to private | M4: Groups & Privacy | R3 |
| 10 | Custom Group Model | Create `Group` model with `name`, `description`, `creator` (FK User), `members` (M2M User) | M4: Groups & Privacy | R3 |
| 11 | Group-Wishlist Association | Add `groups = models.ManyToManyField(Group, blank=True)` to `Wishlist` allowing wishlist exposure to groups | M4: Groups & Privacy | R3 |
| 12 | Group Discovery & Subscription | Views/templates to browse, search, and subscribe/unsubscribe to groups | M4: Groups & Privacy | R3 |
| 13 | Wishlist Exposure Management | UI and views allowing users to select which of their wishlists are exposed to specific groups | M4: Groups & Privacy | R3 |
| 14 | Privacy & Group Access Control | Enforce access rules: owner, public, or exposed group member; HTTP 403 PermissionDenied otherwise | M4: Groups & Privacy | R3 |
| 15 | Groups Navigation Link | Add "Groups" navigation link in `lists.base.html` for authenticated users | M4: Groups & Privacy | R3 |
| 16 | Groups & Privacy TDD Suite | Comprehensive unit, view, and functional tests covering privacy defaults, groups, and access rules | M4: Groups & Privacy | R3, R5 |
| 17 | Cross-Worktree Verification & Audit | Verify all Django tests pass, pre-commit runs clean, all worktree changes remain uncommitted | M5: Final Verification | R6 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Worktree Setup | Create 3 worktrees under `.worktrees/` with baseline fixes | none | DONE |
| 2 | Password Reset | Styled password reset page, routing, templates, UI links, tests in `.worktrees/password-reset` | M1 | DONE |
| 3 | Remember Me | Remember me default checked, session expiry logic, tests in `.worktrees/remember-me` | M1 | DONE |
| 4 | Groups & Privacy | Wishlists default to private, Group model, M2M, discovery, exposure, access control, tests in `.worktrees/groups-privacy` | M1 | IN_PROGRESS |
| 5 | Final Verification & Audit | Full Django test suite across all worktrees, clean pre-commit, zero git commits/pushes, forensic audit | M2, M3, M4 | PLANNED |

## Interface Contracts
### Accounts ↔ Session & Password Reset
- `LoginForm`: Form with fields `email`, `password`, `remember_me` (BooleanField, initial=True, required=False).
- `account_login(request)`: If `remember_me` is True -> `request.session.set_expiry(settings.SESSION_COOKIE_AGE)`; if False -> `request.session.set_expiry(0)`.
- Password reset URLs:
  - `password_reset`: `PasswordResetView.as_view(template_name="registration/password_reset_form.html")`
  - `password_reset_done`: `PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html")`
  - `password_reset_confirm`: `PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html")`
  - `password_reset_complete`: `PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html")`

### Lists ↔ Groups & Privacy
- `Wishlist`:
  - `is_private = models.BooleanField(default=True)`
  - `groups = models.ManyToManyField(Group, related_name="wishlists", blank=True)`
- `Group`:
  - `uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, db_index=True)`
  - `name = models.CharField(max_length=128, unique=True)`
  - `description = models.TextField(blank=True)`
  - `creator = models.ForeignKey(User, related_name="created_groups", on_delete=models.CASCADE)`
  - `members = models.ManyToManyField(User, related_name="subscribed_groups", blank=True)`
- Access Control:
  - `can_view_wishlist(user, wishlist)`:
    - If `user.is_authenticated and user == wishlist.owner` -> True
    - If `not wishlist.is_private` -> True
    - If `user.is_authenticated and wishlist.groups.filter(members=user).exists()` -> True
    - Otherwise -> False (raises `PermissionDenied` in views)

## Code Layout
- Root Workspace: `/workspaces/wishlists/`
- Worktrees:
  - `.worktrees/password-reset/wishlists/`
  - `.worktrees/groups-privacy/wishlists/`
  - `.worktrees/remember-me/wishlists/`
- Agent Metadata (orchestrator only):
  - `.agents/teamwork/`
