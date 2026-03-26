import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_owner_with_tasks(tasks: list[Task], available_minutes: int = 480) -> Owner:
    """Build a minimal Owner+Pet+Scheduler setup from a flat list of tasks."""
    owner = Owner("Alex", available_minutes, "08:00")
    pet = Pet("Mochi", "dog", 3)
    for t in tasks:
        pet.add_task(t)
    owner.add_pet(pet)
    return owner


# ===========================================================================
# Sorting Correctness
# ===========================================================================

class TestSortingCorrectness:
    """Tasks must come back in chronological order: morning → afternoon → evening → None."""

    def test_sort_by_time_chronological_order(self):
        """sort_by_time returns morning before afternoon before evening."""
        tasks = [
            Task("Evening stroll",  20, "high",   "walk",      preferred_time="evening"),
            Task("Lunch snack",     10, "medium", "feeding",   preferred_time="afternoon"),
            Task("Morning meds",    5,  "high",   "meds",      preferred_time="morning"),
        ]
        owner = _make_owner_with_tasks(tasks)
        scheduler = Scheduler(owner)

        sorted_pairs = scheduler.sort_by_time()
        times = [t.preferred_time for _, t in sorted_pairs]
        assert times == ["morning", "afternoon", "evening"]

    def test_sort_by_time_none_preferred_time_goes_last(self):
        """Tasks with no preferred_time slot should appear after all slotted tasks."""
        tasks = [
            Task("Whenever task", 10, "low",  "enrichment", preferred_time=None),
            Task("Morning walk",  30, "high", "walk",       preferred_time="morning"),
        ]
        owner = _make_owner_with_tasks(tasks)
        scheduler = Scheduler(owner)

        sorted_pairs = scheduler.sort_by_time()
        times = [t.preferred_time for _, t in sorted_pairs]
        assert times == ["morning", None]

    def test_get_sorted_tasks_priority_tiebreak_within_slot(self):
        """Within the same time slot, high priority must precede low priority."""
        tasks = [
            Task("Low walk",  30, "low",  "walk",    preferred_time="morning"),
            Task("High meds", 5,  "high", "meds",    preferred_time="morning"),
        ]
        owner = _make_owner_with_tasks(tasks)
        scheduler = Scheduler(owner)

        sorted_pairs = scheduler._get_sorted_tasks()
        priorities = [t.priority for _, t in sorted_pairs]
        assert priorities == ["high", "low"]

    def test_get_sorted_tasks_time_beats_priority(self):
        """A low-priority morning task must still precede a high-priority afternoon task."""
        tasks = [
            Task("Afternoon high", 15, "high", "feeding", preferred_time="afternoon"),
            Task("Morning low",    20, "low",  "walk",    preferred_time="morning"),
        ]
        owner = _make_owner_with_tasks(tasks)
        scheduler = Scheduler(owner)

        sorted_pairs = scheduler._get_sorted_tasks()
        times = [t.preferred_time for _, t in sorted_pairs]
        assert times == ["morning", "afternoon"]

    def test_sort_by_time_empty_task_list(self):
        """sort_by_time on an owner with no tasks must return an empty list."""
        owner = Owner("Alex", 120, "08:00")
        owner.add_pet(Pet("Mochi", "dog", 3))
        scheduler = Scheduler(owner)

        assert scheduler.sort_by_time() == []


# ===========================================================================
# Recurrence Logic
# ===========================================================================

class TestRecurrenceLogic:
    """Completing a recurring task must create the next occurrence with the correct due_date."""

    def test_daily_task_creates_next_day_occurrence(self):
        """Completing a daily task appends a new task due the following day."""
        today = date.today()
        pet = Pet("Luna", "cat", 2)
        task = Task("Morning feeding", 10, "high", "feeding",
                    preferred_time="morning", frequency="daily", due_date=today)
        pet.add_task(task)

        next_task = pet.complete_task("Morning feeding")

        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False

    def test_weekly_task_creates_next_week_occurrence(self):
        """Completing a weekly task appends a new task due seven days later."""
        today = date.today()
        pet = Pet("Luna", "cat", 2)
        task = Task("Bath time", 30, "medium", "grooming",
                    frequency="weekly", due_date=today)
        pet.add_task(task)

        next_task = pet.complete_task("Bath time")

        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_as_needed_task_does_not_recur(self):
        """Completing an as-needed task must NOT create a new task instance."""
        pet = Pet("Luna", "cat", 2)
        task = Task("Vet visit", 60, "high", "meds", frequency="as-needed")
        pet.add_task(task)

        result = pet.complete_task("Vet visit")

        assert result is None
        assert len(pet.tasks) == 1  # only the original, now completed

    def test_recurring_task_inherits_properties(self):
        """The newly created recurring task should inherit all properties of the original."""
        pet = Pet("Luna", "cat", 2)
        task = Task("Evening meds", 5, "high", "meds",
                    preferred_time="evening", frequency="daily")
        pet.add_task(task)

        next_task = pet.complete_task("Evening meds")

        assert next_task.title == "Evening meds"
        assert next_task.duration_minutes == 5
        assert next_task.priority == "high"
        assert next_task.category == "meds"
        assert next_task.preferred_time == "evening"
        assert next_task.frequency == "daily"

    def test_completed_original_task_is_marked_done(self):
        """After completing a daily task the original instance must be marked completed."""
        pet = Pet("Luna", "cat", 2)
        task = Task("Morning feeding", 10, "high", "feeding", frequency="daily")
        pet.add_task(task)

        pet.complete_task("Morning feeding")

        assert pet.tasks[0].completed is True

    def test_daily_task_chain_advances_date_each_time(self):
        """Completing the recurring copy should advance due_date by another day."""
        today = date.today()
        pet = Pet("Luna", "cat", 2)
        pet.add_task(Task("Morning feeding", 10, "high", "feeding",
                          frequency="daily", due_date=today))

        first_next  = pet.complete_task("Morning feeding")   # tomorrow
        second_next = pet.complete_task("Morning feeding")   # day after tomorrow

        assert first_next.due_date  == today + timedelta(days=1)
        assert second_next.due_date == today + timedelta(days=2)


# ===========================================================================
# Conflict Detection
# ===========================================================================

class TestConflictDetection:
    """detect_conflicts must flag overlapping time blocks and ignore non-overlapping ones."""

    def _build_schedule_entry(self, pet: str, task: str, start: str, end: str) -> dict:
        """Return a minimal schedule dict as produced by build_schedule."""
        return {
            "pet": pet, "task": task,
            "start": start, "end": end,
            "category": "walk", "priority": "medium",
            "preferred_time": "morning", "frequency": "daily",
            "pin_time": None, "duration_minutes": 30,
            "reason": "",
        }

    def test_two_pinned_tasks_at_same_time_flagged(self):
        """Two tasks pinned to the same start time must produce a conflict warning."""
        owner = Owner("Alex", 480, "08:00")
        pet = Pet("Mochi", "dog", 3)
        pet.add_task(Task("Vet visit",   60, "high", "meds",  pin_time="09:00", frequency="as-needed"))
        pet.add_task(Task("Groomer",     60, "low",  "grooming", pin_time="09:00", frequency="as-needed"))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        schedule  = scheduler.build_schedule()
        conflicts = scheduler.detect_conflicts(schedule)

        assert len(conflicts) >= 1
        assert any("Vet visit" in c and "Groomer" in c for c in conflicts)

    def test_overlapping_intervals_flagged(self):
        """Tasks whose time windows overlap must be flagged."""
        owner = Owner("Alex", 480, "08:00")
        scheduler = Scheduler(owner)

        schedule = [
            self._build_schedule_entry("Mochi", "Walk",    "08:00", "08:30"),
            self._build_schedule_entry("Mochi", "Feeding", "08:15", "08:45"),
        ]
        conflicts = scheduler.detect_conflicts(schedule)

        assert len(conflicts) == 1

    def test_adjacent_tasks_not_flagged(self):
        """Tasks that share only a boundary (A.end == B.start) must NOT be a conflict."""
        owner = Owner("Alex", 480, "08:00")
        scheduler = Scheduler(owner)

        schedule = [
            self._build_schedule_entry("Mochi", "Walk",    "08:00", "08:30"),
            self._build_schedule_entry("Mochi", "Feeding", "08:30", "08:40"),
        ]
        conflicts = scheduler.detect_conflicts(schedule)

        assert conflicts == []

    def test_no_conflict_for_sequential_tasks(self):
        """Well-separated tasks must produce no conflicts."""
        owner = Owner("Alex", 480, "08:00")
        scheduler = Scheduler(owner)

        schedule = [
            self._build_schedule_entry("Mochi", "Walk",    "08:00", "08:30"),
            self._build_schedule_entry("Mochi", "Feeding", "12:00", "12:15"),
        ]
        conflicts = scheduler.detect_conflicts(schedule)

        assert conflicts == []

    def test_skipped_tasks_excluded_from_conflict_check(self):
        """Skipped tasks (start=None) must be ignored by detect_conflicts."""
        owner = Owner("Alex", 480, "08:00")
        scheduler = Scheduler(owner)

        schedule = [
            self._build_schedule_entry("Mochi", "Walk", "08:00", "08:30"),
            {**self._build_schedule_entry("Mochi", "Skipped", "08:00", "08:30"),
             "start": None, "end": None},
        ]
        conflicts = scheduler.detect_conflicts(schedule)

        assert conflicts == []

    def test_cross_pet_overlap_flagged(self):
        """Overlapping tasks belonging to different pets must still be flagged."""
        owner = Owner("Alex", 480, "08:00")
        scheduler = Scheduler(owner)

        schedule = [
            self._build_schedule_entry("Mochi", "Walk",    "09:00", "09:30"),
            self._build_schedule_entry("Luna",  "Feeding", "09:00", "09:15"),
        ]
        conflicts = scheduler.detect_conflicts(schedule)

        assert len(conflicts) == 1
