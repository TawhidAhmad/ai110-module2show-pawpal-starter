from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str                  # "low", "medium", "high"
    category: str                  # "walk", "feeding", "meds", "grooming", "enrichment"
    preferred_time: str | None = None  # "morning", "afternoon", "evening"
    frequency: str = "daily"       # "daily", "weekly", "as-needed"
    completed: bool = False

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

    def complete_task(self, title: str) -> None:
        """Mark the first task matching the given title as completed."""
        for task in self.tasks:
            if task.title == title:
                task.completed = True
                return

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
                    frequency: str = "daily") -> Task:
        """Create a new task, add it to the given pet, and return it."""
        task = Task(
            title=title,
            duration_minutes=duration_minutes,
            priority=priority,
            category=category,
            preferred_time=preferred_time,
            frequency=frequency,
        )
        pet.add_task(task)
        return task

    def has_enough_time(self, tasks: list[Task]) -> bool:
        """Return True if the total task duration fits within the owner's available time."""
        total = sum(t.duration_minutes for t in tasks)
        return total <= self.available_minutes


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, None: 3}


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def _get_sorted_tasks(self) -> list[tuple[Pet, Task]]:
        """Retrieve all pending tasks from owner's pets, sorted by priority then preferred time."""
        all_tasks = self.owner.get_all_tasks()
        return sorted(
            all_tasks,
            key=lambda pt: (PRIORITY_ORDER[pt[1].priority], TIME_ORDER[pt[1].preferred_time])
        )

    def build_schedule(self) -> list[dict]:
        """Fit tasks into available time, highest priority first, and return the ordered schedule."""
        sorted_tasks = self._get_sorted_tasks()
        schedule = []
        remaining_minutes = self.owner.available_minutes
        current_time = datetime.strptime(self.owner.preferred_start_time, "%H:%M")

        for pet, task in sorted_tasks:
            if task.duration_minutes <= remaining_minutes:
                end_time = current_time + timedelta(minutes=task.duration_minutes)
                schedule.append({
                    "pet": pet.name,
                    "task": task.title,
                    "category": task.category,
                    "priority": task.priority,
                    "start": current_time.strftime("%H:%M"),
                    "end": end_time.strftime("%H:%M"),
                    "duration_minutes": task.duration_minutes,
                    "reason": f"Priority: {task.priority}. Scheduled for {pet.name}.",
                })
                current_time = end_time
                remaining_minutes -= task.duration_minutes
            else:
                schedule.append({
                    "pet": pet.name,
                    "task": task.title,
                    "category": task.category,
                    "priority": task.priority,
                    "start": None,
                    "end": None,
                    "duration_minutes": task.duration_minutes,
                    "reason": f"Skipped — not enough time remaining ({remaining_minutes} min left).",
                })

        return schedule

    def get_summary(self) -> str:
        """Return a human-readable string of the day's scheduled and skipped tasks."""
        schedule = self.build_schedule()
        scheduled = [s for s in schedule if s["start"] is not None]
        skipped = [s for s in schedule if s["start"] is None]

        lines = [f"Daily plan for {self.owner.name}:\n"]
        for entry in scheduled:
            lines.append(f"  {entry['start']} – {entry['end']}  [{entry['pet']}] {entry['task']} ({entry['priority']} priority)")
        if skipped:
            lines.append("\nSkipped (not enough time):")
            for entry in skipped:
                lines.append(f"  - [{entry['pet']}] {entry['task']}")
        return "\n".join(lines)
