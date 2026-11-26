# E2E Test Infra: Wishlists Production Features

## Test Philosophy
- Opaque-box, requirement-driven, outside-in testing methodology.
- Test runner: `python manage.py test accounts lists functional_tests`.
- Requirements verification: password reset flow end-to-end, groups discovery and subscription, wishlist privacy defaults, remember me session expiry control.

## Feature Inventory & Test Coverage
| # | Feature | Source | Tier 1 (Coverage) | Tier 2 (Boundary) | Tier 3 (Cross-Feature) |
|---|---------|--------|:-----------------:|:-----------------:|:----------------------:|
| 1 | Git Worktrees Setup | R1 | 5 | 5 | ✓ |
| 2 | Password Reset URL & Views | R2 | 5 | 5 | ✓ |
| 3 | Password Reset Styling | R2 | 5 | 5 | ✓ |
| 4 | Password Reset Exposure | R2 | 5 | 5 | ✓ |
| 5 | Remember Me Default Checked | R4 | 5 | 5 | ✓ |
| 6 | Remember Me Session Persistence | R4 | 5 | 5 | ✓ |
| 7 | Wishlist Private Default | R3 | 5 | 5 | ✓ |
| 8 | Group Discovery & Subscription | R3 | 5 | 5 | ✓ |
| 9 | Wishlist Group Exposure & Access Control | R3 | 5 | 5 | ✓ |

## Test Architecture
- Test Runner: `cd <worktree>/wishlists && python manage.py test accounts lists functional_tests`
- Formats:
  - Django `TestCase` testing HTTP views, status codes, template rendering, and session state.
  - Django `TestCase` testing model fields, defaults, queries, and permissions.
  - Functional / integration tests simulating browser clients.
- Pre-commit Hook Runner: `pre-commit run --all-files`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | User requests password reset via UI link, receives email, resets password with valid token, logs in with new password | F2, F3, F4 | High |
| 2 | User logs in with default "Remember me" checked, session expiry is set to 2 weeks; logs out, logs in with "Remember me" unchecked, session expires on browser close | F5, F6 | Medium |
| 3 | User creates a new wishlist (defaults to private), verifies unauthenticated/other users cannot view it (403), creates a group, subscribes another user, exposes the wishlist to the group, and verifies the group member can now view the wishlist | F7, F8, F9 | High |
| 4 | User browses public groups, finds group, subscribes, views group details showing member list and shared wishlists | F8, F9 | Medium |
| 5 | Invalid password reset token or expired token gracefully rejected with error message | F2, F3 | Medium |

## Coverage Thresholds
- Tier 1: >= 5 tests per feature (happy path coverage)
- Tier 2: >= 5 tests per feature (boundary and error conditions)
- Tier 3: Pairwise cross-feature interaction tests (Auth + Session, Privacy + Groups, Forms + UI)
- Tier 4: >= 5 realistic end-to-end application scenarios
