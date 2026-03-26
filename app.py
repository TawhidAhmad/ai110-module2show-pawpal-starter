import streamlit as st
import pandas as pd
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

col4, col5, col6 = st.columns(3)
with col4:
    category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment"])
with col5:
    preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening"])
with col6:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

pin_time_input = st.text_input("Pin to exact time (HH:MM, optional — e.g. vet appt)", value="")

if st.button("Add Task"):
    pin_time = pin_time_input.strip() if pin_time_input.strip() else None
    owner.create_task(
        pet=selected_pet,
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        category=category,
        preferred_time=preferred_time,
        frequency=frequency,
        pin_time=pin_time,
    )
    st.success(f"Task '{task_title}' added to {selected_pet_name}.")

st.divider()

# --- View Tasks (sorted by time slot) ---
all_pending = owner.get_all_tasks()
if all_pending:
    st.subheader("All Pending Tasks — Sorted by Time Slot")

    # Use scheduler.sort_by_time() for the display order
    sorted_pairs = scheduler.sort_by_time()
    rows = []
    for pet, task in sorted_pairs:
        rows.append({
            "Pet": pet.name,
            "Task": task.title,
            "Priority": task.priority,
            "Category": task.category,
            "Time Slot": task.preferred_time or "—",
            "Duration (min)": task.duration_minutes,
            "Frequency": task.frequency,
            "Pinned At": task.pin_time or "—",
        })
    df = pd.DataFrame(rows)

    # Color-code priority column
    def highlight_priority(val):
        colors = {"high": "background-color: #ffd6d6", "medium": "background-color: #fff4cc", "low": "background-color: #d6f0d6"}
        return colors.get(val, "")

    styled = df.style.map(highlight_priority, subset=["Priority"])
    st.dataframe(styled, use_container_width=True)

    # --- Filter Tasks ---
    with st.expander("Filter Tasks"):
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
        with filter_col2:
            filter_status = st.selectbox("Filter by status", ["All", "pending", "completed"], key="filter_status")

        f_pet = None if filter_pet == "All" else filter_pet
        f_status = None if filter_status == "All" else filter_status
        filtered = scheduler.filter_tasks(pet_name=f_pet, status=f_status)

        if filtered:
            filter_rows = [{"Pet": p.name, "Task": t.title, "Priority": t.priority,
                            "Status": "Done" if t.completed else "Pending",
                            "Duration (min)": t.duration_minutes} for p, t in filtered]
            st.table(filter_rows)
        else:
            st.info("No tasks match the selected filters.")

    # --- Recurring Summary ---
    with st.expander("Recurring Task Breakdown"):
        st.text(scheduler.get_recurring_summary())

st.divider()

# --- Generate Schedule ---
st.subheader("Generate Schedule")
if st.button("Build Today's Schedule"):
    all_pending = owner.get_all_tasks()
    if not all_pending:
        st.warning("No pending tasks to schedule.")
    else:
        schedule = scheduler.build_schedule()
        scheduled = [s for s in schedule if s["start"] is not None]
        skipped = [s for s in schedule if s["start"] is None]
        conflicts = scheduler.detect_conflicts(schedule)

        # Summary metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Scheduled", len(scheduled))
        m2.metric("Skipped", len(skipped))
        m3.metric("Conflicts", len(conflicts))

        # Conflict warnings — shown prominently before the table
        if conflicts:
            for conflict_msg in conflicts:
                st.warning(conflict_msg)
        else:
            st.success("No scheduling conflicts detected.")

        # Scheduled tasks table
        if scheduled:
            st.success(f"{len(scheduled)} task(s) successfully scheduled.")
            sched_df = pd.DataFrame([{
                "Time": f"{s['start']} – {s['end']}",
                "Pet": s["pet"],
                "Task": s["task"],
                "Priority": s["priority"],
                "Category": s["category"],
                "Time Slot": s["preferred_time"] or "—",
                "Pinned": s["pin_time"] or "—",
                "Duration (min)": s["duration_minutes"],
            } for s in scheduled])
            st.dataframe(sched_df, use_container_width=True)

        # Skipped tasks table
        if skipped:
            st.warning(f"{len(skipped)} task(s) skipped — not enough time remaining.")
            skip_df = pd.DataFrame([{
                "Pet": s["pet"],
                "Task": s["task"],
                "Priority": s["priority"],
                "Duration (min)": s["duration_minutes"],
                "Reason": s["reason"],
            } for s in skipped])
            st.table(skip_df)
