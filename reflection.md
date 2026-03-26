# PawPal+ Project Reflection

## 1. System Design

Core Actions: add a pet, schedule a walk, see today's tasks

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The system uses four classes: `Task`, `Pet`, `Owner`, and `Scheduler`.

- `Task` holds the details of a single care activity — title, duration, priority, category, and preferred time of day.
- `Pet` represents the animal being cared for. It stores basic info (name, species, age, special needs) and is responsible for completing tasks.
- `Owner` represents the person managing care. It stores their name, available time, and preferred start time. It owns one `Pet` and is responsible for creating tasks.
- `Scheduler` takes an `Owner` (and accesses the pet through them) and manages the task list. It is responsible for building the daily schedule and summarizing the plan.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, three small changes were made after reviewing the skeleton:

- Added `completed: bool = False` to `Task`. The original design had no way to track whether a task was done, which made `Pet.complete_task()` meaningless.
- Implemented `Pet.complete_task()` to set `task.completed = True`. It was the only method with an obvious one-line body and needed to be wired up for the completed state to work.
- Added `category` and `preferred_time` to `Owner.create_task()`. The original signature was missing these fields, so it couldn't fully construct a valid `Task` object.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints: available time (tasks are skipped once `remaining_minutes` runs out), priority (high → medium → low), and preferred time of day (morning / afternoon / evening slot boundaries). Time budget came first because a plan that overruns the owner's day is useless. Priority came second because missing a medication is worse than missing a grooming session. Preferred time was third — a soft preference that improves realism without being a hard rule.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler sorts by time slot before priority, so a low-priority morning task is placed before a high-priority evening task. This trades strict priority ordering for a more natural daily flow. For a pet owner, doing things at the right time of day (feeding in the morning, walks before dinner) matters more than a rigid global ranking — a high-priority evening task doesn't need to happen at 8 AM just because it ranks highest.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

Copilot's `#codebase` chat was most effective for cross-file reasoning — asking "how does Scheduler access tasks?" surfaced the Owner → Pet → Task chain instantly without manually tracing imports. Inline completions were useful for filling out `to_dict()` and the sort lambda once the pattern was established. Using separate chat sessions per phase (design, logic, UI) kept context focused so Copilot didn't confuse UML intent with implementation details.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

Copilot suggested storing a flat `List[Task]` directly on `Scheduler`, matching the initial UML, but I rejected it because tasks logically belong to a `Pet` — the scheduler should only read, not own. I verified by checking that every method (`filter_tasks`, `detect_conflicts`) only needed read access through `owner.pets`, confirming no write path required Scheduler to hold state.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested sorting correctness (morning before afternoon before evening, with priority tiebreaking), recurrence logic (daily +1 day, weekly +7 days, as-needed no successor), and conflict detection (overlapping intervals flagged, adjacent ones not). These were the three algorithms most likely to have off-by-one or ordering bugs that would silently produce a wrong schedule.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Confidence is high for the tested paths, but edge cases remain around pin-time tasks that overlap the owner's start time and tasks where `preferred_time` is `None` mixed with slotted tasks. Next I'd test a schedule where pinned and sequential tasks collide at the boundary to confirm `detect_conflicts` catches it and `build_schedule` still returns a valid result.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Satisfied with the entire project but mainly the moment for Copilot Agent Mode as well as polishing by reflection.md and readme.md files.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Improve my starting UML so that it included more tasks so not as much changes down the line.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The importance of always testing and creating tests in between big feature additions. 