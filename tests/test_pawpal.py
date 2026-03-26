import pytest
from pawpal_system import Task, Pet


# --- Fixtures ---

@pytest.fixture
def sample_task():
    return Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        category="walk",
        preferred_time="morning",
    )

@pytest.fixture
def sample_pet():
    return Pet(name="Mochi", species="dog", age=3)


# --- Task Completion Tests ---

def test_task_starts_incomplete(sample_task):
    assert sample_task.completed is False

def test_mark_complete_changes_status(sample_task):
    sample_task.mark_complete()
    assert sample_task.completed is True

def test_mark_complete_is_idempotent(sample_task):
    sample_task.mark_complete()
    sample_task.mark_complete()
    assert sample_task.completed is True


# --- Task Addition Tests ---

def test_pet_starts_with_no_tasks(sample_pet):
    assert len(sample_pet.tasks) == 0

def test_adding_task_increases_count(sample_pet, sample_task):
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == 1

def test_adding_multiple_tasks_increases_count(sample_pet):
    sample_pet.add_task(Task("Feeding",  10, "high",   "feeding"))
    sample_pet.add_task(Task("Grooming", 15, "low",    "grooming"))
    sample_pet.add_task(Task("Play",     20, "medium", "enrichment"))
    assert len(sample_pet.tasks) == 3
