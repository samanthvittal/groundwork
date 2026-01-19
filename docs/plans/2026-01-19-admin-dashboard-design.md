# Admin Dashboard - Design Document

**Date:** 2026-01-19
**Status:** Planning
**Author:** Stakeholder discussion

---

## User Requirements

The Admin Dashboard should show:

### 1. Analytics Based on All Projects
- Overview analytics across all projects
- Placeholder values acceptable until Analytics phase (P2.2)

### 2. Projects Card View
- Card layout showing each project with:
  - User count
  - Total # of Stories
  - # of Stories completed
  - # of Issues
  - # of Issues fixed
- Clicking a card → Project-specific analytics page

### 3. Admin Tasks
Since Admin is not part of any projects and has no project-based tasks:
- Today's tasks
- Next 3 days tasks
- Next 7 days tasks
- Next 30 days tasks
- Tasks can be created/modified by Admin themselves

### 4. Calendar View
- Default monthly view
- Shows which tasks are due on which day

---

## Overview.md Analysis

According to the project roadmap:

| Feature | Planned Phase | Notes |
|---------|---------------|-------|
| Dashboard Builder | **P2.2.5** | Widget-based dashboards, real-time updates |
| Reports & Analytics | **P2.2** | Report framework, built-in reports, custom reports |
| Calendar Integration | **P2.5.4** | Calendar sync, due date calendars |
| Views & Navigation | **P0.6** | List views, Kanban boards, search |
| Projects | **P0.3** | Project CRUD, members, settings |
| Issues | **P0.4** | Issue CRUD, types, statuses |

---

## Recommendation

### What Can Be Done Now (P0.2/P0.3)

**Simple Admin Landing Page:**
- Welcome message with user info
- Quick action buttons (Create User, Manage Roles, View Projects)
- Navigation cards to main sections
- Static placeholder for future analytics widgets

**Rationale:** This provides a useful landing page without building the full analytics infrastructure that P2 requires.

### What Should Be Deferred

| Feature | Defer To | Reason |
|---------|----------|--------|
| Project Analytics | P2.2 | Requires P0.3 Projects, P0.4 Issues, P1.3 Time Tracking |
| Project Card Stats | P0.6+ | Requires P0.3 Projects, P0.4 Issues to exist first |
| Calendar View | P2.5.4 | Requires Calendar infrastructure |
| Admin Tasks System | P1+ | Admin tasks concept needs design - not in current spec |

### Suggested Phased Approach

**Phase 0.2 (Now):**
```
┌─────────────────────────────────────────────────────────┐
│  Welcome, [Admin Name]                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Users   │  │  Roles   │  │ Settings │              │
│  │    12    │  │    4     │  │    →     │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                         │
│  Quick Actions                                          │
│  [+ Create User]  [+ Create Role]                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Analytics Coming Soon                           │   │
│  │  Full project analytics available in v0.3.0     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Phase 0.3 (After Projects exist):**
- Add Projects count card
- Add "Recent Projects" list

**Phase 0.4 (After Issues exist):**
- Add Issues count card
- Add "Recent Activity" feed

**Phase 2.2 (Full Analytics):**
- Full dashboard with widgets
- Charts and graphs
- Project card view with real stats
- Custom dashboard builder

---

## Admin Tasks Feature - Design Discussion

The concept of "Admin Tasks" (tasks not tied to projects) is interesting but not currently in the spec. Options:

### Option A: Personal Tasks Module
- Add a `PersonalTask` model separate from project issues
- Admin can create, schedule, track personal tasks
- Not tied to any project

### Option B: System Admin Project
- Create a hidden "System Administration" project
- Admin tasks are issues in this project
- Reuses existing issue infrastructure

### Option C: Defer
- Not implement admin tasks now
- Focus on core project/issue features
- Revisit in P2 when Calendar is implemented

**Recommendation:** Option C (Defer) - The core product is project management. Personal task management is a separate feature that could complicate the MVP.

---

## Decision Required

1. **For P0.2:** Create simple landing page with navigation cards?
2. **Admin Tasks:** Defer to P2 or implement as Option A/B?
3. **Calendar:** Confirm deferral to P2.5.4?

---

## Next Steps

If approved:
1. Create simple Dashboard template for P0.2
2. Add dashboard route that redirects based on role
3. Update post-login redirect to go to Dashboard
4. Document P2.2 Dashboard as future enhancement
