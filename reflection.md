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

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
