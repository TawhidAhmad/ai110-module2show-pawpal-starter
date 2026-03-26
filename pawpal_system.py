from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str          # "low", "medium", "high"
    category: str          # "walk", "feeding", "meds", "grooming", "enrichment"
    preferred_time: str | None = None  # "morning", "afternoon", "evening"

    def is_urgent(self) -> bool:
        pass

    def to_dict(self) -> dict:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)

    def complete_task(self, task: Task) -> None:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferred_start_time: str, pet: Pet):
        self.name = name
        self.available_minutes = available_minutes
        self.preferred_start_time = preferred_start_time  # e.g. "08:00"
        self.pet = pet

    def create_task(self, title: str, duration_minutes: int, priority: str) -> Task:
        pass

    def has_enough_time(self, tasks: list[Task]) -> bool:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, title: str) -> None:
        pass

    def build_schedule(self) -> list[dict]:
        pass

    def get_summary(self) -> str:
        pass
