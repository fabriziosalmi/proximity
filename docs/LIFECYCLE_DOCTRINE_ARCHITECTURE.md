# Lifecycle & Consistency Doctrine - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROXIMITY LIFECYCLE MANAGEMENT ENGINE                     │
│                         (Unified & Intelligent)                              │
└─────────────────────────────────────────────────────────────────────────────┘

                                                                                
┌─────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION TYPES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📦 NATIVE/DEPLOYED APPS          │  🔖 ADOPTED APPS                        │
│  • Created by Proximity            │  • Imported from Proxmox               │
│  • Fully managed                   │  • Soft-managed                        │
│  • config.adopted = False          │  • config.adopted = True               │
│  • Hard delete on removal          │  • Soft delete on removal              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                     DOCTRINE #1: ADOPTION-AWARE DELETION                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DELETE REQUEST                                                              │
│       │                                                                      │
│       ├──────► Check: is_adopted?                                           │
│       │              │                                                       │
│       │              ├─── TRUE ──► 🧹 SOFT DELETE                           │
│       │              │                  • Release ports                      │
│       │              │                  • Delete DB record                   │
│       │              │                  • ✅ Container preserved             │
│       │              │                                                       │
│       │              └─── FALSE ─► 🗑️  HARD DELETE                          │
│       │                                 • Stop container                     │
│       │                                 • Delete container                   │
│       │                                 • Release ports                      │
│       │                                 • Delete DB record                   │
│       │                                                                      │
│       └──────► Log strategy & execute                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                DOCTRINE #2: INTELLIGENT RECONCILIATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RECONCILIATION CYCLE                                                        │
│       │                                                                      │
│       ├──────► 1. Fetch all VMIDs from Proxmox                              │
│       │                                                                      │
│       ├──────► 2. Fetch all apps from DB                                    │
│       │                                                                      │
│       ├──────► 3. Identify orphans (DB but not Proxmox)                     │
│       │                                                                      │
│       └──────► 4. Classify orphans:                                         │
│                     │                                                        │
│                     ├─── status in [removing, error]                        │
│                     │          ↓                                             │
│                     │    ✅ EXPECTED ORPHAN                                  │
│                     │    • Log: INFO                                         │
│                     │    • Clean silently                                    │
│                     │                                                        │
│                     └─── status in [running, stopped, ...]                  │
│                              ↓                                               │
│                        🚨 ANOMALOUS ORPHAN                                   │
│                        • Log: CRITICAL                                       │
│                        • Alert: Sentry                                       │
│                        • Clean safely                                        │
│                                                                              │
│       All cleanups are SOFT (DB/ports only, never touch Proxmox)            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                 DOCTRINE #3: CONSERVATIVE JANITOR                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  JANITOR CYCLE (Every 1 hour)                                               │
│       │                                                                      │
│       ├──────► 1. Find apps in transitional states                          │
│       │           [deploying, cloning, removing, updating]                  │
│       │                                                                      │
│       ├──────► 2. Check if stuck > timeout threshold                        │
│       │                                                                      │
│       └──────► 3. Mark as ERROR (ONLY!)                                     │
│                     • Update status to 'error'                               │
│                     • Log timeout message                                    │
│                     • ❌ NEVER delete containers                             │
│                     • ✅ Let reconciler handle cleanup                       │
│                                                                              │
│  🩺 DOCTOR MODE: Diagnose, don't execute                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                   DOCTRINE #4: INFORMED ADOPTION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ADOPTION PROCESS                                                            │
│       │                                                                      │
│       ├──────► 1. Connect to Proxmox                                        │
│       │                                                                      │
│       ├──────► 2. Get basic container info                                  │
│       │           • Name, status, resources                                 │
│       │                                                                      │
│       ├──────► 3. 📸 CAPTURE CONFIG SNAPSHOT                                │
│       │           • Full 'pct config' output                                │
│       │           • Network configuration                                   │
│       │           • Resource allocation                                     │
│       │                                                                      │
│       ├──────► 4. Detect/specify ports                                      │
│       │                                                                      │
│       ├──────► 5. Allocate public port                                      │
│       │                                                                      │
│       ├──────► 6. Create Application with RICH metadata:                    │
│       │           • adopted: true                                            │
│       │           • proxmox_config_snapshot: {...}                          │
│       │           • resources_at_adoption: {...}                            │
│       │           • status_at_adoption: 'running'                           │
│       │                                                                      │
│       └──────► 7. Set status to ACTUAL Proxmox state                        │
│                                                                              │
│  📋 Result: Complete "clinical record" for troubleshooting                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                      SEPARATION OF CONCERNS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🩺 JANITOR SERVICE                                                          │
│     Responsibility: INTERNAL state health                                   │
│     • Monitors transitional states                                          │
│     • Marks stuck apps as error                                             │
│     • Never touches external resources                                      │
│                                                                              │
│  🔄 RECONCILIATION SERVICE                                                   │
│     Responsibility: EXTERNAL state consistency                              │
│     • Syncs DB with Proxmox                                                 │
│     • Cleans up orphaned records                                            │
│     • Detects anomalies                                                     │
│                                                                              │
│  🗑️  DELETE TASK                                                             │
│     Responsibility: LIFECYCLE termination                                   │
│     • Respects adoption status                                              │
│     • Executes appropriate strategy                                         │
│     • Ensures complete cleanup                                              │
│                                                                              │
│  🔖 ADOPT TASK                                                               │
│     Responsibility: ONBOARDING existing resources                           │
│     • Captures complete metadata                                            │
│     • Creates management record                                             │
│     • Preserves original configuration                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE FLOW DIAGRAM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌──────────┐                                        │
│                          │ adopting │  (Adoption in progress)               │
│                          └────┬─────┘                                        │
│                               │                                              │
│                               ├──► running  (If container was running)      │
│                               └──► stopped  (If container was stopped)      │
│                                                                              │
│  ┌──────────┐                                                               │
│  │deploying │  (Native app being created)                                   │
│  └────┬─────┘                                                               │
│       │                                                                      │
│       ├──► running  (Success)                                               │
│       ├──► error    (Failure or timeout - Janitor marks)                    │
│       └──► [removed] (Manual Proxmox deletion - Reconciler detects)         │
│                                                                              │
│  ┌─────────┐                                                                │
│  │ running │  (Stable state)                                                │
│  └────┬────┘                                                                │
│       │                                                                      │
│       ├──► stopped  (User action)                                           │
│       ├──► removing (Delete requested)                                      │
│       └──► [orphan]  (Manual Proxmox deletion → ALERT!)                     │
│                                                                              │
│  ┌──────────┐                                                               │
│  │ removing │  (Deletion in progress)                                       │
│  └────┬─────┘                                                               │
│       │                                                                      │
│       ├──► [deleted]  (Success - record removed)                            │
│       ├──► error      (Failure - Janitor marks if stuck)                    │
│       └──► [orphan]   (Expected if container deleted)                       │
│                                                                              │
│  ┌───────┐                                                                  │
│  │ error │  (Terminal failure state)                                        │
│  └───┬───┘                                                                  │
│      │                                                                       │
│      └──► [orphan]  (If container manually removed - Expected)              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOGGING PATTERNS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Deletion:                                                                   │
│    🔖 SOFT DELETE → "Removing Proximity management (container preserved)"   │
│    🗑️  HARD DELETE → "Destroying container and cleaning up resources"       │
│                                                                              │
│  Reconciliation:                                                             │
│    ✅ "EXPECTED ORPHAN: Container removal expected"                          │
│    🚨 "ANOMALOUS ORPHAN DETECTED: Container was MANUALLY DELETED"            │
│                                                                              │
│  Janitor:                                                                    │
│    🩺 "DIAGNOSING: ... Stuck for Xh Ym"                                     │
│    ✓ "DIAGNOSED AS ERROR: ... (was: deploying)"                             │
│    → "Container (if any) will be handled by ReconciliationService"          │
│                                                                              │
│  Adoption:                                                                   │
│    📸 "Capturing complete container configuration snapshot..."               │
│    ✓ "Config snapshot: X keys captured"                                     │
│    ✅ "INFORMED ADOPTION COMPLETED SUCCESSFULLY"                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                            KEY BENEFITS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🔐 SAFETY          No accidental container destruction                     │
│  🎯 INTELLIGENCE    Context-aware decision making                           │
│  🔍 VISIBILITY      Clear audit trail for all operations                    │
│  ⚡ RESILIENCE      Graceful handling of edge cases                         │
│  🧩 MODULARITY      Clear separation of concerns                            │
│  📊 OBSERVABILITY   Rich metrics and monitoring                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
