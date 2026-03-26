import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session state init ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# --- Owner setup ---
st.subheader("Owner Info")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=90)
with col3:
    start_time = st.text_input("Start time (HH:MM)", value="08:00")

if st.button("Set Owner"):
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferred_start_time=start_time,
    )
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)
    st.success(f"Owner set: {owner_name}")

if st.session_state.owner is None:
    st.info("Set an owner above to get started.")
    st.stop()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

st.divider()

# --- Add a Pet ---
st.subheader("Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

special_needs_input = st.text_input("Special needs (comma-separated, optional)", value="")

if st.button("Add Pet"):
    special_needs = [s.strip() for s in special_needs_input.split(",") if s.strip()]
    pet = Pet(name=pet_name, species=species, age=int(pet_age), special_needs=special_needs)
    owner.add_pet(pet)
    st.success(f"Added pet: {pet_name} ({species})")

if owner.pets:
    st.write("**Your pets:**", ", ".join(p.name for p in owner.pets))
else:
    st.info("No pets added yet.")
    st.stop()

st.divider()

# --- Add a Task ---
st.subheader("Add a Task")
pet_names = [p.name for p in owner.pets]
selected_pet_name = st.selectbox("Assign to pet", pet_names)
selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment"])
with col5:
    preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening"])

if st.button("Add Task"):
    owner.create_task(
        pet=selected_pet,
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        category=category,
        preferred_time=preferred_time,
    )
    st.success(f"Task '{task_title}' added to {selected_pet_name}.")

# Show all current tasks per pet
for pet in owner.pets:
    if pet.tasks:
        st.write(f"**{pet.name}'s tasks:**")
        st.table([t.to_dict() for t in pet.tasks])

st.divider()

# --- Generate Schedule ---
st.subheader("Generate Schedule")
if st.button("Build Today's Schedule"):
    all_pending = owner.get_all_tasks()
    if not all_pending:
        st.warning("No pending tasks to schedule.")
    else:
        st.text(scheduler.get_summary())
        schedule = scheduler.build_schedule()
        scheduled = [s for s in schedule if s["start"] is not None]
        skipped = [s for s in schedule if s["start"] is None]
        if scheduled:
            st.success(f"Scheduled {len(scheduled)} task(s).")
            st.table(scheduled)
        if skipped:
            st.warning(f"Skipped {len(skipped)} task(s) — not enough time.")
            st.table(skipped)
