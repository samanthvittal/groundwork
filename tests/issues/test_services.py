"""Tests for issue services."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Permission, Role, User
from groundwork.auth.utils import hash_password
from groundwork.issues.models import (
    Issue,
    IssueType,
    Label,
    Priority,
    Status,
    StatusCategory,
)
from groundwork.issues.services import (
    IssueService,
    IssueTypeService,
    LabelService,
    StatusService,
)
from groundwork.projects.models import Project, ProjectRole
from groundwork.projects.services import ProjectService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """Create a test role."""
    permission = Permission(
        codename="issues:read",
        description="Can read issues",
    )
    db_session.add(permission)

    role = Role(
        name="test_role",
        description="Test role",
        is_system=True,
        permissions=[permission],
    )
    db_session.add(role)
    await db_session.flush()
    return role


@pytest.fixture
async def test_user(db_session: AsyncSession, test_role: Role) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
        first_name="Test",
        last_name="User",
        role_id=test_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def second_user(db_session: AsyncSession, test_role: Role) -> User:
    """Create a second test user."""
    user = User(
        email="second@example.com",
        hashed_password=hash_password("password123"),
        first_name="Second",
        last_name="User",
        role_id=test_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    service = ProjectService(db_session)
    project = await service.create_project(
        key="TEST",
        name="Test Project",
        owner_id=test_user.id,
        description="A test project",
    )
    return project


@pytest.fixture
async def test_issue_type(db_session: AsyncSession) -> IssueType:
    """Create a test issue type."""
    issue_type = IssueType(
        project_id=None,  # System default
        name="Task",
        description="A task",
        icon="task",
        color="#3b82f6",
        is_subtask=True,
        position=0,
    )
    db_session.add(issue_type)
    await db_session.flush()
    return issue_type


@pytest.fixture
async def test_status(db_session: AsyncSession) -> Status:
    """Create a test status."""
    status = Status(
        project_id=None,  # System default
        name="To Do",
        description="Work not started",
        category=StatusCategory.TODO,
        color="#6b7280",
        position=0,
    )
    db_session.add(status)
    await db_session.flush()
    return status


@pytest.fixture
async def done_status(db_session: AsyncSession) -> Status:
    """Create a done status."""
    status = Status(
        project_id=None,
        name="Done",
        description="Work completed",
        category=StatusCategory.DONE,
        color="#22c55e",
        position=1,
    )
    db_session.add(status)
    await db_session.flush()
    return status


@pytest.fixture
async def test_issue(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> Issue:
    """Create a test issue."""
    service = IssueService(db_session)
    issue = await service.create_issue(
        project_id=test_project.id,
        title="Test Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        priority=Priority.MEDIUM,
        description="Test issue description",
    )
    return issue


@pytest.fixture
async def test_label(db_session: AsyncSession, test_project: Project) -> Label:
    """Create a test label."""
    service = LabelService(db_session)
    label = await service.create_label(
        project_id=test_project.id,
        name="Bug",
        color="#ef4444",
        description="A bug label",
    )
    return label


# =============================================================================
# Issue Service Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_issue_success(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.create_issue should create issue with generated key."""
    service = IssueService(db_session)
    issue = await service.create_issue(
        project_id=test_project.id,
        title="New Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        priority=Priority.HIGH,
        description="Issue description",
    )

    assert issue is not None
    assert issue.key == "TEST-1"
    assert issue.issue_number == 1
    assert issue.title == "New Issue"
    assert issue.priority == Priority.HIGH
    assert issue.reporter_id == test_user.id


@pytest.mark.asyncio
async def test_create_issue_auto_increment_key(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """Issue keys should auto-increment within a project."""
    service = IssueService(db_session)

    issue1 = await service.create_issue(
        project_id=test_project.id,
        title="Issue 1",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )
    issue2 = await service.create_issue(
        project_id=test_project.id,
        title="Issue 2",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )

    assert issue1.key == "TEST-1"
    assert issue2.key == "TEST-2"
    assert issue1.issue_number == 1
    assert issue2.issue_number == 2


@pytest.mark.asyncio
async def test_get_issue_by_id(db_session: AsyncSession, test_issue: Issue) -> None:
    """IssueService.get_issue should return issue by ID."""
    service = IssueService(db_session)
    issue = await service.get_issue(test_issue.id)

    assert issue is not None
    assert issue.id == test_issue.id
    assert issue.title == "Test Issue"


@pytest.mark.asyncio
async def test_get_issue_by_key(db_session: AsyncSession, test_issue: Issue) -> None:
    """IssueService.get_issue_by_key should return issue by key."""
    service = IssueService(db_session)
    issue = await service.get_issue_by_key("TEST-1")

    assert issue is not None
    assert issue.key == "TEST-1"


@pytest.mark.asyncio
async def test_get_issue_by_key_case_insensitive(
    db_session: AsyncSession, test_issue: Issue
) -> None:
    """IssueService.get_issue_by_key should be case insensitive."""
    service = IssueService(db_session)
    issue = await service.get_issue_by_key("test-1")

    assert issue is not None
    assert issue.key == "TEST-1"


@pytest.mark.asyncio
async def test_update_issue(db_session: AsyncSession, test_issue: Issue) -> None:
    """IssueService.update_issue should update issue fields."""
    service = IssueService(db_session)
    issue = await service.update_issue(
        issue_id=test_issue.id,
        title="Updated Title",
        description="Updated description",
        priority=Priority.CRITICAL,
    )

    assert issue is not None
    assert issue.title == "Updated Title"
    assert issue.description == "Updated description"
    assert issue.priority == Priority.CRITICAL


@pytest.mark.asyncio
async def test_update_issue_unassign(
    db_session: AsyncSession, test_issue: Issue, second_user: User
) -> None:
    """IssueService.update_issue should allow unassigning."""
    service = IssueService(db_session)

    # First assign
    await service.update_issue(test_issue.id, assignee_id=second_user.id)
    issue = await service.get_issue(test_issue.id)
    assert issue.assignee_id == second_user.id

    # Then unassign
    issue = await service.update_issue(test_issue.id, assignee_id=None)
    assert issue.assignee_id is None


@pytest.mark.asyncio
async def test_delete_issue_soft(db_session: AsyncSession, test_issue: Issue) -> None:
    """IssueService.delete_issue should soft delete."""
    service = IssueService(db_session)
    result = await service.delete_issue(test_issue.id)

    assert result is True

    issue = await service.get_issue(test_issue.id)
    assert issue.deleted_at is not None


@pytest.mark.asyncio
async def test_restore_issue(db_session: AsyncSession, test_issue: Issue) -> None:
    """IssueService.restore_issue should restore deleted issue."""
    service = IssueService(db_session)

    # Delete first
    await service.delete_issue(test_issue.id)

    # Then restore
    issue = await service.restore_issue(test_issue.id)

    assert issue is not None
    assert issue.deleted_at is None


@pytest.mark.asyncio
async def test_list_issues(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.list_issues should return issues in project."""
    service = IssueService(db_session)

    # Create multiple issues
    for i in range(3):
        await service.create_issue(
            project_id=test_project.id,
            title=f"Issue {i}",
            type_id=test_issue_type.id,
            reporter_id=test_user.id,
            status_id=test_status.id,
        )

    issues = await service.list_issues(test_project.id)

    assert len(issues) == 3


@pytest.mark.asyncio
async def test_list_issues_filter_by_status(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
    done_status: Status,
) -> None:
    """IssueService.list_issues should filter by status."""
    service = IssueService(db_session)

    # Create issue with todo status
    await service.create_issue(
        project_id=test_project.id,
        title="Todo Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )

    # Create issue with done status
    await service.create_issue(
        project_id=test_project.id,
        title="Done Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=done_status.id,
    )

    todo_issues = await service.list_issues(test_project.id, status_id=test_status.id)
    done_issues = await service.list_issues(test_project.id, status_id=done_status.id)

    assert len(todo_issues) == 1
    assert len(done_issues) == 1
    assert todo_issues[0].title == "Todo Issue"
    assert done_issues[0].title == "Done Issue"


@pytest.mark.asyncio
async def test_list_issues_filter_by_priority(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.list_issues should filter by priority."""
    service = IssueService(db_session)

    await service.create_issue(
        project_id=test_project.id,
        title="High Priority",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        priority=Priority.HIGH,
    )

    await service.create_issue(
        project_id=test_project.id,
        title="Low Priority",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        priority=Priority.LOW,
    )

    high_issues = await service.list_issues(test_project.id, priority=Priority.HIGH)

    assert len(high_issues) == 1
    assert high_issues[0].title == "High Priority"


@pytest.mark.asyncio
async def test_list_issues_search(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.list_issues should search in title and description."""
    service = IssueService(db_session)

    await service.create_issue(
        project_id=test_project.id,
        title="Login bug",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )

    await service.create_issue(
        project_id=test_project.id,
        title="Feature request",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        description="Something about login",
    )

    await service.create_issue(
        project_id=test_project.id,
        title="Other issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )

    issues = await service.list_issues(test_project.id, search="login")

    assert len(issues) == 2


@pytest.mark.asyncio
async def test_change_status(
    db_session: AsyncSession, test_issue: Issue, done_status: Status
) -> None:
    """IssueService.change_status should update issue status."""
    service = IssueService(db_session)
    issue = await service.change_status(test_issue.id, done_status.id)

    assert issue is not None
    assert issue.status_id == done_status.id


# =============================================================================
# Subtask Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_subtask(
    db_session: AsyncSession,
    test_issue: Issue,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """Subtasks should link to parent issue."""
    service = IssueService(db_session)

    subtask = await service.create_issue(
        project_id=test_issue.project_id,
        title="Subtask",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        parent_id=test_issue.id,
    )

    assert subtask.parent_id == test_issue.id

    # Reload parent to check subtasks
    parent = await service.get_issue(test_issue.id)
    assert len(parent.subtasks) == 1


@pytest.mark.asyncio
async def test_set_parent(
    db_session: AsyncSession,
    test_project: Project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.set_parent should link issues."""
    service = IssueService(db_session)

    parent = await service.create_issue(
        project_id=test_project.id,
        title="Parent Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )

    child = await service.create_issue(
        project_id=test_project.id,
        title="Child Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
    )

    # Link as subtask
    updated = await service.set_parent(child.id, parent.id)

    assert updated.parent_id == parent.id


@pytest.mark.asyncio
async def test_set_parent_remove(
    db_session: AsyncSession,
    test_issue: Issue,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.set_parent with None should unlink."""
    service = IssueService(db_session)

    # Create subtask
    subtask = await service.create_issue(
        project_id=test_issue.project_id,
        title="Subtask",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        parent_id=test_issue.id,
    )

    # Remove parent
    updated = await service.set_parent(subtask.id, None)

    assert updated.parent_id is None


@pytest.mark.asyncio
async def test_list_subtasks(
    db_session: AsyncSession,
    test_issue: Issue,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """IssueService.list_subtasks should return subtasks."""
    service = IssueService(db_session)

    # Create subtasks
    for i in range(2):
        await service.create_issue(
            project_id=test_issue.project_id,
            title=f"Subtask {i}",
            type_id=test_issue_type.id,
            reporter_id=test_user.id,
            status_id=test_status.id,
            parent_id=test_issue.id,
        )

    subtasks = await service.list_subtasks(test_issue.id)

    assert len(subtasks) == 2


# =============================================================================
# Label Tests
# =============================================================================


@pytest.mark.asyncio
async def test_add_label_to_issue(
    db_session: AsyncSession, test_issue: Issue, test_label: Label
) -> None:
    """IssueService.add_label should add label to issue."""
    service = IssueService(db_session)
    issue = await service.add_label(test_issue.id, test_label.id)

    assert issue is not None
    assert len(issue.labels) == 1
    assert issue.labels[0].id == test_label.id


@pytest.mark.asyncio
async def test_add_label_idempotent(
    db_session: AsyncSession, test_issue: Issue, test_label: Label
) -> None:
    """Adding same label twice should be idempotent."""
    service = IssueService(db_session)

    await service.add_label(test_issue.id, test_label.id)
    issue = await service.add_label(test_issue.id, test_label.id)

    assert len(issue.labels) == 1


@pytest.mark.asyncio
async def test_remove_label(
    db_session: AsyncSession, test_issue: Issue, test_label: Label
) -> None:
    """IssueService.remove_label should remove label from issue."""
    service = IssueService(db_session)

    # Add first
    await service.add_label(test_issue.id, test_label.id)

    # Then remove
    issue = await service.remove_label(test_issue.id, test_label.id)

    assert len(issue.labels) == 0


# =============================================================================
# Permission Tests
# =============================================================================


@pytest.mark.asyncio
async def test_user_can_view_project_member(
    db_session: AsyncSession, test_issue: Issue, test_user: User
) -> None:
    """Project member should be able to view issues."""
    service = IssueService(db_session)
    can_view = await service.user_can_view(test_issue.id, test_user.id)

    assert can_view is True


@pytest.mark.asyncio
async def test_user_cannot_view_non_member(
    db_session: AsyncSession, test_issue: Issue, second_user: User
) -> None:
    """Non-member should not be able to view private project issues."""
    service = IssueService(db_session)
    can_view = await service.user_can_view(test_issue.id, second_user.id)

    assert can_view is False


@pytest.mark.asyncio
async def test_user_can_edit_assignee(
    db_session: AsyncSession,
    test_issue: Issue,
    second_user: User,
    test_project: Project,
) -> None:
    """Assignee should be able to edit issue."""
    project_service = ProjectService(db_session)
    issue_service = IssueService(db_session)

    # Add user as member and assign to issue
    await project_service.add_member(
        test_project.id, second_user.id, ProjectRole.VIEWER
    )
    await issue_service.update_issue(test_issue.id, assignee_id=second_user.id)

    can_edit = await issue_service.user_can_edit(test_issue.id, second_user.id)

    assert can_edit is True


@pytest.mark.asyncio
async def test_user_can_edit_member(
    db_session: AsyncSession,
    test_issue: Issue,
    second_user: User,
    test_project: Project,
) -> None:
    """Project MEMBER should be able to edit issues."""
    project_service = ProjectService(db_session)
    issue_service = IssueService(db_session)

    await project_service.add_member(
        test_project.id, second_user.id, ProjectRole.MEMBER
    )

    can_edit = await issue_service.user_can_edit(test_issue.id, second_user.id)

    assert can_edit is True


@pytest.mark.asyncio
async def test_user_cannot_edit_viewer(
    db_session: AsyncSession,
    test_issue: Issue,
    second_user: User,
    test_project: Project,
) -> None:
    """Project VIEWER (non-assignee) should not be able to edit issues."""
    project_service = ProjectService(db_session)
    issue_service = IssueService(db_session)

    await project_service.add_member(
        test_project.id, second_user.id, ProjectRole.VIEWER
    )

    can_edit = await issue_service.user_can_edit(test_issue.id, second_user.id)

    assert can_edit is False


@pytest.mark.asyncio
async def test_user_can_delete_admin(
    db_session: AsyncSession,
    test_issue: Issue,
    second_user: User,
    test_project: Project,
) -> None:
    """Project ADMIN should be able to delete issues."""
    project_service = ProjectService(db_session)
    issue_service = IssueService(db_session)

    await project_service.add_member(test_project.id, second_user.id, ProjectRole.ADMIN)

    can_delete = await issue_service.user_can_delete(test_issue.id, second_user.id)

    assert can_delete is True


@pytest.mark.asyncio
async def test_user_cannot_delete_member(
    db_session: AsyncSession,
    test_issue: Issue,
    second_user: User,
    test_project: Project,
) -> None:
    """Project MEMBER should not be able to delete issues."""
    project_service = ProjectService(db_session)
    issue_service = IssueService(db_session)

    await project_service.add_member(
        test_project.id, second_user.id, ProjectRole.MEMBER
    )

    can_delete = await issue_service.user_can_delete(test_issue.id, second_user.id)

    assert can_delete is False


# =============================================================================
# Label Service Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_label(db_session: AsyncSession, test_project: Project) -> None:
    """LabelService.create_label should create a label."""
    service = LabelService(db_session)
    label = await service.create_label(
        project_id=test_project.id,
        name="Feature",
        color="#8b5cf6",
        description="Feature label",
    )

    assert label is not None
    assert label.name == "Feature"
    assert label.color == "#8b5cf6"


@pytest.mark.asyncio
async def test_create_label_duplicate_name(
    db_session: AsyncSession, test_project: Project, test_label: Label
) -> None:
    """LabelService.create_label should return None for duplicate name."""
    service = LabelService(db_session)
    label = await service.create_label(
        project_id=test_project.id,
        name="Bug",  # Same as test_label
        color="#000000",
    )

    assert label is None


@pytest.mark.asyncio
async def test_update_label(db_session: AsyncSession, test_label: Label) -> None:
    """LabelService.update_label should update label fields."""
    service = LabelService(db_session)
    label = await service.update_label(
        label_id=test_label.id,
        name="Updated Bug",
        color="#dc2626",
    )

    assert label is not None
    assert label.name == "Updated Bug"
    assert label.color == "#dc2626"


@pytest.mark.asyncio
async def test_delete_label(db_session: AsyncSession, test_label: Label) -> None:
    """LabelService.delete_label should delete label."""
    service = LabelService(db_session)
    result = await service.delete_label(test_label.id)

    assert result is True

    label = await service.get_label(test_label.id)
    assert label is None


@pytest.mark.asyncio
async def test_list_labels(
    db_session: AsyncSession, test_project: Project, test_label: Label
) -> None:
    """LabelService.list_labels should return project labels."""
    service = LabelService(db_session)

    # Create another label
    await service.create_label(test_project.id, "Feature", "#8b5cf6")

    labels = await service.list_labels(test_project.id)

    assert len(labels) == 2


# =============================================================================
# Issue Type and Status Service Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_issue_types(
    db_session: AsyncSession, test_project: Project, test_issue_type: IssueType
) -> None:
    """IssueTypeService.list_issue_types should return types."""
    service = IssueTypeService(db_session)
    types = await service.list_issue_types(test_project.id)

    assert len(types) >= 1
    assert any(t.name == "Task" for t in types)


@pytest.mark.asyncio
async def test_list_statuses(
    db_session: AsyncSession, test_project: Project, test_status: Status
) -> None:
    """StatusService.list_statuses should return statuses."""
    service = StatusService(db_session)
    statuses = await service.list_statuses(test_project.id)

    assert len(statuses) >= 1
    assert any(s.name == "To Do" for s in statuses)
