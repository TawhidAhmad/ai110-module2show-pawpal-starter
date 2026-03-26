from pawpal_system import Owner, Pet, Scheduler

# ── Setup ─────────────────────────────────────────────────────────────────────
owner = Owner(name="Jordan", available_minutes=180, preferred_start_time="08:00")

mochi    = Pet(name="Mochi",    species="dog", age=3)
whiskers = Pet(name="Whiskers", species="cat", age=5, special_needs=["kidney diet"])

owner.add_pet(mochi)
owner.add_pet(whiskers)

# ── Normal sequential tasks ────────────────────────────────────────────────────
owner.create_task(mochi,    title="Morning walk",      duration_minutes=30, priority="high",
                  category="walk",      preferred_time="morning",   frequency="daily")
owner.create_task(mochi,    title="Breakfast feeding", duration_minutes=10, priority="high",
                  category="feeding",   preferred_time="morning",   frequency="daily")
owner.create_task(whiskers, title="Medication",        duration_minutes=5,  priority="high",
                  category="meds",      preferred_time="morning",   frequency="daily")
owner.create_task(mochi,    title="Evening play",      duration_minutes=20, priority="medium",
                  category="enrichment",preferred_time="evening",   frequency="daily")
owner.create_task(whiskers, title="Afternoon feeding", duration_minutes=10, priority="medium",
                  category="feeding",   preferred_time="afternoon", frequency="daily")

# ── CONFLICT SCENARIO ──────────────────────────────────────────────────────────
# Both tasks are pinned to 09:00.
# Mochi's vet checkup runs 09:00–10:00 (60 min).
# Whiskers' vet exam   runs 09:30–10:00 (30 min).
# They overlap between 09:30 and 10:00 — detect_conflicts() must catch this.
owner.create_task(mochi,    title="Vet checkup",       duration_minutes=60, priority="high",
                  category="vet",       preferred_time="morning",   frequency="as-needed",
                  pin_time="09:00")   # <-- pinned: forces start at exactly 09:00

owner.create_task(whiskers, title="Vet exam",           duration_minutes=30, priority="high",
                  category="vet",       preferred_time="morning",   frequency="as-needed",
                  pin_time="09:30")   # <-- pinned at 09:30 — inside Mochi's 09:00–10:00 block

# ── Scheduler ─────────────────────────────────────────────────────────────────
scheduler = Scheduler(owner)
schedule  = scheduler.build_schedule()

# ════════════════════════════════════════════════════════════════════════════════
# 1) Full schedule — shows every task with its actual start/end
# ════════════════════════════════════════════════════════════════════════════════
print("=" * 62)
print("  FULL SCHEDULE")
print("=" * 62)
scheduled = [e for e in schedule if e["start"] is not None]
skipped   = [e for e in schedule if e["start"] is None]

for entry in scheduled:
    pin_tag = "  [PINNED]" if entry.get("pin_time") else ""
    print(f"  {entry['start']} – {entry['end']}  [{entry['pet']:<8}] "
          f"{entry['task']}{pin_tag}")

if skipped:
    print("\n  Skipped (time budget exhausted):")
    for entry in skipped:
        print(f"    - [{entry['pet']}] {entry['task']}")

# ════════════════════════════════════════════════════════════════════════════════
# 2) Conflict detection — pairwise interval overlap check
#    Algorithm: for every pair (A, B), flag if A.start < B.end AND B.start < A.end
#    Returns warning strings only — no exceptions raised.
# ════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
print("  CONFLICT DETECTION  (pairwise A.start < B.end AND B.start < A.end)")
print("=" * 62)

conflicts = scheduler.detect_conflicts(schedule)
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No scheduling conflicts detected.")

# ════════════════════════════════════════════════════════════════════════════════
# 3) Verify no-conflict baseline — run detect_conflicts on the non-pinned tasks only
# ════════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
print("  BASELINE CHECK  (non-pinned tasks only — expect zero conflicts)")
print("=" * 62)

baseline = [e for e in schedule if not e.get("pin_time") and e["start"] is not None]
baseline_conflicts = scheduler.detect_conflicts(baseline)
if baseline_conflicts:
    for warning in baseline_conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts among sequential tasks — scheduler is clean.")

print("=" * 62)
