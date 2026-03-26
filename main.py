from pawpal_system import Owner, Pet, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90, preferred_start_time="08:00")

mochi = Pet(name="Mochi", species="dog", age=3)
whiskers = Pet(name="Whiskers", species="cat", age=5, special_needs=["kidney diet"])

owner.add_pet(mochi)
owner.add_pet(whiskers)

# --- Add tasks to Mochi (dog) ---
owner.create_task(mochi, title="Morning walk",     duration_minutes=30, priority="high",   category="walk",      preferred_time="morning")
owner.create_task(mochi, title="Breakfast feeding", duration_minutes=10, priority="high",   category="feeding",   preferred_time="morning")
owner.create_task(mochi, title="Evening play",      duration_minutes=20, priority="medium", category="enrichment", preferred_time="evening")

# --- Add tasks to Whiskers (cat) ---
owner.create_task(whiskers, title="Medication",       duration_minutes=5,  priority="high",   category="meds",      preferred_time="morning")
owner.create_task(whiskers, title="Afternoon feeding", duration_minutes=10, priority="medium", category="feeding",   preferred_time="afternoon")
owner.create_task(whiskers, title="Grooming brush",   duration_minutes=15, priority="low",    category="grooming",  preferred_time="evening")

# --- Build and print schedule ---
scheduler = Scheduler(owner)

print("=" * 50)
print("         TODAY'S SCHEDULE")
print("=" * 50)
print(scheduler.get_summary())
print("=" * 50)
