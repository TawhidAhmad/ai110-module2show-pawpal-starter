from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str                  # "low", "medium", "high"
    category: str                  # "walk", "feeding", "meds", "grooming", "enrichment"
    preferred_time: str | None = None  # "morning", "afternoon", "evening"
    frequency: str = "daily"       # "daily", "weekly", "as-needed"
    completed: bool = False
    # due_date tracks when this occurrence is due.
    # timedelta(days=1) advances it for daily tasks; timedelta(weeks=1) for weekly.
    due_date: date = field(default_factory=date.today)
    # pin_time forces the task to start at an exact clock time ("HH:MM"), e.g. a
    # vet appointment at "09:30".  Pinned tasks can overlap each other or with
    # sequential tasks — detect_conflicts() will catch and report them.
    pin_time: str | None = None

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_urgent(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "preferred_time": self.preferred_time,
            "frequency": self.frequency,
            "completed": self.completed,
            "due_date": self.due_date.isoformat(),
            "pin_time": self.pin_time,
        }


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task from this pet's task list by title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def complete_task(self, title: str) -> Task | None:
        """
        Mark the first pending task matching title as completed.

        For recurring tasks the method uses timedelta to calculate the next
        due_date and automatically appends a fresh, incomplete copy:
          - "daily"  → due_date + timedelta(days=1)
          - "weekly" → due_date + timedelta(weeks=1)
          - "as-needed" → no new instance (one-off)

        Returns the newly created Task, or None if no recurrence applies.
        """
        for task in self.tasks:
            if task.title == title and not task.completed:
                task.completed = True

                if task.frequency == "daily":
                    next_due = task.due_date + timedelta(days=1)
                elif task.frequency == "weekly":
                    next_due = task.due_date + timedelta(weeks=1)
                else:
                    return None  # "as-needed" — no auto-recurrence

                next_task = Task(
                    title=task.title,
                    duration_minutes=task.duration_minutes,
                    priority=task.priority,
                    category=task.category,
                    preferred_time=task.preferred_time,
                    frequency=task.frequency,
                    due_date=next_due,
                )
                self.tasks.append(next_task)
                return next_task

        return None

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]


class Owner:
    def __init__(self, name: str, available_minutes: int, preferred_start_time: str):
        self.name = name
        self.available_minutes = available_minutes
        self.preferred_start_time = preferred_start_time  # e.g. "08:00"
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all pending tasks across all pets as (pet, task) pairs."""
        result = []
        for pet in self.pets:
            for task in pet.get_pending_tasks():
                result.append((pet, task))
        return result

    def create_task(self, pet: Pet, title: str, duration_minutes: int,
                    priority: str, category: str,
                    preferred_time: str | None = None,
                    frequency: str = "daily",
                    pin_time: str | None = None) -> Task:
        """Create a new task, add it to the given pet, and return it."""
        task = Task(
            title=title,
            duration_minutes=duration_minutes,
            priority=priority,
            category=category,
            preferred_time=preferred_time,
            frequency=frequency,
            pin_time=pin_time,
        )
        pet.add_task(task)
        return task

    def has_enough_time(self, tasks: list[Task]) -> bool:
        """Return True if the total task duration fits within the owner's available time."""
        total = sum(t.duration_minutes for t in tasks)
        return total <= self.available_minutes


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, None: 3}

# Each slot's start and end time (24-hour)
TIME_SLOTS: dict[str, tuple[str, str]] = {
    "morning":   ("08:00", "12:00"),
    "afternoon": ("12:00", "17:00"),
    "evening":   ("17:00", "21:00"),
}


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def sort_by_time(self) -> list[tuple[Pet, Task]]:
        """
        Return all pending tasks sorted chronologically by their preferred time slot.

        The lambda maps each task's preferred_time label to its slot-start string
        ("08:00", "12:00", "17:00").  Because these strings are zero-padded they
        sort lexicographically in the same order as chronologically — no datetime
        parsing required.  Tasks with no preferred_time fall to the end ("99:99").

        Example key values produced by the lambda:
            morning   → "08:00"
            afternoon → "12:00"
            evening   → "17:00"
            None      → "99:99"
        """
        all_tasks = self.owner.get_all_tasks()
        return sorted(
            all_tasks,
            key=lambda pt: TIME_SLOTS.get(pt[1].preferred_time, ("99:99", "99:99"))[0]
        )

    def _get_sorted_tasks(self) -> list[tuple[Pet, Task]]:
        """
        Retrieve all pending tasks and sort them by time slot, then by priority.

        The sort key is a two-element tuple so Python applies a tiebreaker
        automatically: tasks in the same time slot are ordered high → low priority.

            Key element 0 — time slot  (TIME_ORDER dict):
                morning=0, afternoon=1, evening=2, None=3
            Key element 1 — priority   (PRIORITY_ORDER dict):
                high=0, medium=1, low=2

        Lower numbers sort first, so a high-priority morning task always
        precedes a low-priority morning task, and all morning tasks precede
        all afternoon tasks.

        Returns a list of (Pet, Task) pairs in the computed order.
        """
        all_tasks = self.owner.get_all_tasks()
        return sorted(
            all_tasks,
            key=lambda pt: (TIME_ORDER[pt[1].preferred_time], PRIORITY_ORDER[pt[1].priority])
        )

    # ------------------------------------------------------------------
    # Feature 1: Filter tasks by pet name and/or completion status
    # ------------------------------------------------------------------
    def filter_tasks(
        self,
        pet_name: str | None = None,
        status: str | None = None,   # "pending" | "completed" | None
    ) -> list[tuple[Pet, Task]]:
        """
        Return tasks filtered by pet name and/or completion status.

        Both parameters are optional and can be combined:
            filter_tasks()                          → every task for every pet
            filter_tasks(pet_name="Mochi")          → all of Mochi's tasks
            filter_tasks(status="pending")          → incomplete tasks, all pets
            filter_tasks(pet_name="Mochi",
                         status="completed")        → Mochi's finished tasks only

        Args:
            pet_name: Case-insensitive pet name to match. Pass None to include
                      all pets.
            status:   "pending" keeps only incomplete tasks; "completed" keeps
                      only finished tasks; None keeps both.

        Returns:
            A list of (Pet, Task) pairs that satisfy all supplied filters,
            in the order pets were added to the owner.
        """
        result = []
        for pet in self.owner.pets:
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if status == "pending" and task.completed:
                    continue
                if status == "completed" and not task.completed:
                    continue
                result.append((pet, task))
        return result

    # ------------------------------------------------------------------
    # Feature 2: Recurring task awareness
    # ------------------------------------------------------------------
    def get_recurring_summary(self) -> str:
        """
        Return a human-readable summary of all pending tasks grouped by frequency.

        Tasks are bucketed into three groups using Task.frequency:
            "daily"     — tasks that recur every day (e.g. feeding, medication)
            "weekly"    — tasks that recur every seven days (e.g. bath time)
            "as-needed" — one-off or irregular tasks; also the fallback for any
                          unrecognised frequency value

        Only pending tasks (completed=False) are included because
        get_all_tasks() delegates to get_pending_tasks() internally.

        Returns a multi-line string ready to print, with each group introduced
        by a bracketed header and each task indented beneath it.
        """
        groups: dict[str, list[tuple[Pet, Task]]] = {
            "daily": [],
            "weekly": [],
            "as-needed": [],
        }
        for pet, task in self.owner.get_all_tasks():
            bucket = task.frequency if task.frequency in groups else "as-needed"
            groups[bucket].append((pet, task))

        lines = ["Recurring task breakdown:"]
        for freq, pairs in groups.items():
            if not pairs:
                continue
            lines.append(f"\n  [{freq.upper()}]")
            for pet, task in pairs:
                lines.append(f"    - [{pet.name}] {task.title} ({task.duration_minutes} min, {task.priority} priority)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Feature 3: Build time-slot-aware schedule
    # ------------------------------------------------------------------
    def build_schedule(self) -> list[dict]:
        """
        Fit pending tasks into the owner's available time and return a schedule.

        Placement rules (applied in order):
            1. pin_time set  → task starts at that exact "HH:MM" clock time.
               current_time is NOT advanced afterward, so sequential tasks are
               unaffected. Two pinned tasks can therefore land at the same time;
               detect_conflicts() will report the overlap as a warning.
            2. pin_time None → task starts at current_time, but if the preferred
               slot (morning / afternoon / evening) hasn't opened yet, current_time
               is first jumped forward to the slot's boundary. This idle gap does
               not consume remaining_minutes.

        Budget tracking:
            remaining_minutes starts at owner.available_minutes and decreases by
            task.duration_minutes for every scheduled task. Tasks that no longer
            fit are recorded with start=None and end=None ("skipped").

        Returns:
            A list of dicts, one per task, each containing:
                pet, task, category, priority, preferred_time, frequency,
                pin_time, start ("HH:MM" or None), end ("HH:MM" or None),
                duration_minutes, reason.
        """
        sorted_tasks = self._get_sorted_tasks()
        schedule = []
        remaining_minutes = self.owner.available_minutes
        current_time = datetime.strptime(self.owner.preferred_start_time, "%H:%M")

        for pet, task in sorted_tasks:
            # Determine where this task starts.
            # pin_time overrides everything — task is anchored to an exact clock time.
            # Otherwise jump to the slot boundary if the window hasn't opened yet.
            if task.pin_time:
                task_start = datetime.strptime(task.pin_time, "%H:%M")
            else:
                if task.preferred_time and task.preferred_time in TIME_SLOTS:
                    slot_start = datetime.strptime(TIME_SLOTS[task.preferred_time][0], "%H:%M")
                    if current_time < slot_start:
                        current_time = slot_start
                task_start = current_time

            if task.duration_minutes <= remaining_minutes:
                end_time = task_start + timedelta(minutes=task.duration_minutes)
                schedule.append({
                    "pet": pet.name,
                    "task": task.title,
                    "category": task.category,
                    "priority": task.priority,
                    "preferred_time": task.preferred_time,
                    "frequency": task.frequency,
                    "pin_time": task.pin_time,
                    "start": task_start.strftime("%H:%M"),
                    "end": end_time.strftime("%H:%M"),
                    "duration_minutes": task.duration_minutes,
                    "reason": f"Priority: {task.priority}. Scheduled for {pet.name}.",
                })
                # Advance current_time only for non-pinned tasks so sequential
                # tasks don't accidentally land inside a pinned window.
                if not task.pin_time:
                    current_time = end_time
                remaining_minutes -= task.duration_minutes
            else:
                schedule.append({
                    "pet": pet.name,
                    "task": task.title,
                    "category": task.category,
                    "priority": task.priority,
                    "preferred_time": task.preferred_time,
                    "frequency": task.frequency,
                    "pin_time": task.pin_time,
                    "start": None,
                    "end": None,
                    "duration_minutes": task.duration_minutes,
                    "reason": f"Skipped — not enough time remaining ({remaining_minutes} min left).",
                })

        return schedule

    # ------------------------------------------------------------------
    # Feature 4: Conflict detection  (pairwise interval overlap)
    # ------------------------------------------------------------------
    def detect_conflicts(self, schedule: list[dict]) -> list[str]:
        """
        Return warning strings for every pair of tasks whose time blocks overlap.

        Strategy — lightweight pairwise interval test:
            Two tasks A and B overlap when:
                A.start < B.end  AND  B.start < A.end
            This catches same-pet AND cross-pet conflicts without crashing.
            Skipped tasks (start=None) are ignored entirely.

        Returns an empty list when there are no conflicts.
        """
        warnings: list[str] = []
        scheduled = [e for e in schedule if e["start"] is not None]

        for i in range(len(scheduled)):
            for j in range(i + 1, len(scheduled)):
                a = scheduled[i]
                b = scheduled[j]

                a_start = datetime.strptime(a["start"], "%H:%M")
                a_end   = datetime.strptime(a["end"],   "%H:%M")
                b_start = datetime.strptime(b["start"], "%H:%M")
                b_end   = datetime.strptime(b["end"],   "%H:%M")

                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"WARNING: '[{a['pet']}] {a['task']}' ({a['start']}–{a['end']}) "
                        f"overlaps with '[{b['pet']}] {b['task']}' ({b['start']}–{b['end']})"
                    )

        return warnings

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------
    def get_summary(self) -> str:
        """Return a human-readable string of the day's scheduled and skipped tasks."""
        schedule = self.build_schedule()
        scheduled = [s for s in schedule if s["start"] is not None]
        skipped = [s for s in schedule if s["start"] is None]
        conflicts = self.detect_conflicts(schedule)

        lines = [f"Daily plan for {self.owner.name}:\n"]
        current_slot = None
        for entry in scheduled:
            slot = entry.get("preferred_time") or "unspecified"
            if slot != current_slot:
                lines.append(f"\n  -- {slot.upper()} --")
                current_slot = slot
            freq_tag = f" [{entry['frequency']}]" if entry["frequency"] != "daily" else ""
            lines.append(
                f"  {entry['start']} – {entry['end']}  [{entry['pet']}] "
                f"{entry['task']} ({entry['priority']} priority){freq_tag}"
            )

        if skipped:
            lines.append("\nSkipped (not enough time):")
            for entry in skipped:
                lines.append(f"  - [{entry['pet']}] {entry['task']}")

        if conflicts:
            lines.append("\nConflicts detected:")
            for c in conflicts:
                lines.append(f"  ! {c}")

        return "\n".join(lines)
