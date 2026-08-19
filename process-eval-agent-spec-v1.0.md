# Process Evaluation Agent — Working Specification

> **Status:** **v1.0 — Plan Mode baseline.** All critical items resolved. Remaining `[PROVIDE]` markers are confirmations of stated recommendations, not gaps: Claude Code can plan against this document as written, defaulting to the recommendation wherever one is given.
>
> **Source data baseline:** `EPIC.xlsx` (revised, 18/08/2026 — sheets: EPIC, EPIC Transition, Capabilities, Features, Transitions, ART) and `EPIC_Releases.xlsx` (sheets: About, EPIC Releases, Capability Releases, ALL UNRELEASED). All figures in this document are computed from these two files.
> **Purpose of this doc:** Give Claude Code everything it needs in Plan Mode to propose an architecture without guessing at business logic.
>
> **Change log — v1.0:** Document baselined for Plan Mode. All body-text figures refreshed to the revised `EPIC.xlsx` (598 in-scope Features, 371 Capabilities, 74 EPICs), replacing figures from the superseded extract. Change-log entries below retain the numbers current at the time they were written.
>
> **Change log — v0.21:** **Section 15 Non-negotiables written — the last critical gap closed.** Headline constraints: **all scoring is deterministic code, never LLM-derived** (agents summarise and explain, they never derive a score); **every score reproducible** from stored data, with rule-set versioning so past weeks never silently recompute; **low-confidence rows flagged** where a score is derived from a minority of children; 30-second dashboard load; current by **Monday 09:00**. Proof-of-Concept boundaries recorded in 15.4, with **configuration-over-hardcoding** made a hard requirement so the rule set is portable to other customers.
>
> **Change log — v0.20:** Section 7.3 finalised — **"At risk" caps the RAG at Amber**, and a missed date is projected on a **30-day horizon**. Rule Set 3 gains an explicit **compliance target (6.1.4)**: every post-Backlog Capability must carry a Delivery Increment and both Target Dates, measured and trended weekly. Current in-scope compliance is **130 of 215 post-Backlog Capabilities (60.5%)** — DI is close to clean at 92.6%, target dates are the weak point.
>
> **Change log — v0.19:** **Roll-up logic complete (Sections 7.2 and 7.3) — the last critical gap closed.** Weights and bands apply unchanged at every level, with each child weighted by **simple count share** (10 children → 10% each). Critically, new **Section 7.3** adds the **delivery-impact override**: a count-weighted score dilutes a small number of late items into invisibility (2 late Features in 100 scores 98% = Green), so every row now reports **two values — a health score and a delivery status — with the RAG being the worse of the two.** Late is late regardless of percentage complete.
>
> **Change log — v0.18:** **Keys are confirmed mutable** — a Capability reassociated with a Backlog EPIC is re-keyed to `FCB`, and a Feature reassociated with a Backlog Capability is likewise re-keyed to `FCB`. New **Section 13.2** covers this in full: why naive upsert-by-key produces *both* a phantom record and a reset duplicate, the requested re-key mapping, and a title-based fallback (Capability titles are 100% unique in the current extract, which makes the fallback viable). This is now the highest-priority implementation risk in the document.
>
> **Change log — v0.17:** Two confirmations. **(1) `FCB` is a real prefix** for Capabilities and Features belonging to EPICs still in Backlog — added to the scope rules in 3.2, with a warning about key migration. **(2) A Capability must belong to exactly one Release**; two or more is a Data Quality defect (new Rule Set 1 Part C). This **removes the many-to-many roll-up problem** — the Capability → Release relationship is now 1:1 by rule, so the roll-up in Section 7.2 is a tree again.
>
> **Change log — v0.16:** **Revised `EPIC.xlsx` received and folded in.** Titles are present and 100% populated at all three levels, but are named after the issue type (`Portfolio Epic`, `Capability`, `Feature`) rather than "Summary", and the **`Capability` sheet has been renamed `Capabilities`** — both recorded in 3.2.1 and 13. **Feature `Created` date is present on all 2,714 rows**, which closes 6.2.8 and enabled a correction to Section 6.2: **phase is now determined from current status, not transition history**, with Created as the clock fallback. Measurable in-flight Features rise from 124 to **163**, and every open in-scope Feature now has a usable clock anchor. New **6.2.9 Ageing Backlog** covers the 224 pre-analysis Features that Created date makes visible for the first time.
>
> **Change log — v0.15:** **Delta deletion semantics resolved (Section 13).** There is **no deletion capability** — every item is Done, Cancelled, or in progress, and nothing is ever removed from the source. **Cancelled is the only "removal" signal.** Re-parenting is a change event and arrives in the weekly delta, which makes **scope membership dynamic** — new Section 13.1 covers scope re-evaluation, items entering and leaving scope, and snapshot immutability.
>
> **Change log — v0.14:** **Section 8.5 now carries a four-stage blocked persistence ladder** — Flagged (week 1), Warning (week 2), Priority (week 3), Escalate (week 4) — replacing the single "High Priority at week 2" step. A long-running block is now visibly distinct from a new one at every stage.
>
> **Change log — v0.13:** New **Section 7.1.1** — because single attribution (7.1) pushes any defect that is *also* a delivery impact out of the Data Quality score, the DQ RAG will read better than the cleanup checklist implies. **Every view must therefore show the DQ defect count alongside the DQ RAG**, and suppressed defects must be marked with the category they were attributed to. Reflected in the checklist output (6.1.9).
>
> **Change log — v0.12:** Six decisions confirmed. **(1)** **11 weeks** of trend history; weekly file contains only items changed in the last 7 days. **(2)** New **Section 7.1 — single-attribution principle**: nothing is penalised twice, with precedence **Delivery Impact → KPIs → Data Quality**. **(3)** **Blocked overrides everything** — it freezes the stagnation clock and the DI Late/High Risk ladder, KPI clocks keep running, and a still-blocked item on the following week's report escalates to High Priority (new Section 8.5). Blocked cascades Feature → Capability → **Release**. **(4)** **"In Delivery" defined** for both Capability and Feature (6.1.1). **(5)** The Scoping phase is to be **instrumented and reviewed** rather than assumed real (6.2.7). **(6)** **KPI RAG bands set** — fail = Red, within 20% of target = Amber, better = Green (6.3.6).
>
> **Change log — v0.11:** Four source-data decisions confirmed. **(1)** A Release's **name is its identifier** — there is no independent Release ID, which makes the duplicate-name tie-break rule mandatory rather than optional. **(2)** A **summary/title field is being added** for EPIC, Capability and Feature; the column name is not yet known and must be mapped at ingestion. **(3)** Scope refined in 3.2 — **EPIC and Capability keys are always FCM or RN**; Feature keys vary by delivering team, and the **ART worksheet is the team attribution**, not the key prefix. **(4)** **No personal data anywhere** — no owners, assignees or names; all reporting rolls up to EPIC level, and Section 11.3 has been rewritten accordingly.
>
> **Change log — v0.10:** Section 4.5 completed — the **one-month grace period** is confirmed. A Feature flagged Late that is still undelivered one calendar month later escalates to **High Risk**, which *is* a reportable risk (unlike the non-impacting Late label) and is called out as its own line item.
>
> **Change log — v0.9:** **The DI-alignment contradiction is resolved.** Section 4.3 stands as written (a Feature's valid DI is the Capability's own quarter or exactly one quarter *earlier*); the conflicting DI misalignment check in Rule Set 4 is **retired**. Section 4.5 is rewritten: a Feature in the earlier quarter that overruns is flagged **Late as a label with no RAG or score impact**, because the parent Capability's own DI end date still provides slack.
>
> **Change log — v0.8:** **Scope is now formally defined (new Section 3.2).** Only the fully-connected Fixed Connectivity chain is in scope — Features → Capabilities → EPICs where the EPIC key is FCM or RN. Standalone Capabilities and Features are **out of scope, not data quality defects.** This reduces the working population from 2,713 Features to **591**, and the transition history from 150,003 rows to **1,879**, so **every baseline volume table in this document has been recomputed** against the in-scope population. Section 6.2's exclusion of pre-In-Analysis Features is confirmed.
>
> **Change log — v0.7:** **Section 6.2 Flow Throughput now has a numeric formula** — a two-phase stagnation ladder (Scoping and Delivery) driven by days since last forward transition, with a 60-day Scoping phase budget, Blocked handled as a prominent callout, and a defined Feature-score → Capability roll-up. This closes the last unspecified health check: **all three RAG rubrics (6.1, 6.2, 6.3) are now specified.**
>
> **Change log — v0.6:** **The Release entity now has a data source** (`EPIC_Releases.xlsx`) and is defined in new Section 3.1 — Releases are JIRA **Fix versions**, a multi-valued field on both EPICs and Capabilities, which changes the Release model from a single ID to a many-to-many link. Rule Set 1 (6.1.2) has been rewritten against the real field. A new **Rule Set 5 — Orphaned & Unlinked Release Anomalies (6.1.6)** covers releases with no linked work items, releases linked to nothing, and duplicate release names; subsections 6.1.7–6.1.9 renumbered.
>
> **Change log — v0.5:** **Section 6.3 KPIs is now specified** — three Feature-level flow KPIs (Full Cycle Time, Delivery Predictability, Delivery Cycle Time) with calendar-day SLAs, the open-item `NOW()` boundary convention, and an SLA Breach Report. A fourth data quality rule set (**6.1.5 — Date Boundary & Schedule Alignment Errors**) has been added, and subsections 6.1.6–6.1.8 renumbered accordingly.
>
> **Change log — v0.4:** **Section 6.1 Data Quality is now fully specified** — the weekly triage and remediation rule set, severity model, status-name normalisation, and the required "Immediate Data Cleanup Checklist" output format. This work is assigned to a dedicated **Data Quality & Remediation Agent** (new Section 11.4). Section 13 now defines the **full-then-delta** upload model.
>
> **Change log — v0.3:** The **Feature workflow is now confirmed** from the supplied JIRA diagrams and transcribed in full at Section 12.3. All three work-item workflows required for Phase 1 (EPIC, Capability, Feature) are now provided. Section 6.2 gains a confirmed forward/backward transition classification derived from it.
>
> **Change log — v0.2:** The **Story level has been removed throughout**. The source extract contains no Story records, so **Feature is now the lowest grain in the model**. Flow Throughput, Data Quality, KPIs and Blocked-status logic that previously referenced Stories now operate on Features and their own status-transition history (see Sections 3, 5, 6.2, 7, 8 and 12.3).

---

## 1. Purpose

Build an agentic dashboard system that evaluates process health from weekly-uploaded data, surfaced differently for three audiences, each with a RAG (Red/Amber/Green) status.

---

## 2. Viewers & Views

| Viewer | Scope | Granularity shown |
|---|---|---|
| **SLT** | All EPICs | One RAG row per EPIC (overall process health) |
| **Delivery Manager** | A chosen EPIC | One RAG row per Release within that EPIC |
| **Release Manager** | A chosen Release | One RAG row per Capability within that Release |

**Access model:** No role-based restriction — any viewer can open any dashboard. SLT in particular may want to drill down from EPIC → Release → Capability → Feature, so navigation must support that path even though the "home" view differs by audience.

**Selection controls required:**
- EPIC selector (used to enter Delivery Manager view)
- Release selector (used to enter Release Manager view)
- Drill-down links so SLT can jump from EPIC all the way down to Feature level without re-selecting from scratch

---

## 3. Data Hierarchy

```
EPIC
 └── Release
      └── Capability
           └── Feature
```

- One EPIC has many Releases.
- One Release has many Capabilities → each Capability has many Features.
- **Feature is the lowest grain in the model.** There is no Story level (see below).

**Story level removed (confirmed):** the source extract contains **no Story records** — Features are the leaf items, and the only status-change history available is at Feature level. Stories have therefore been removed from the data model, the RAG logic, and all views. Every metric that was previously described as Story-driven is now computed from a Feature's own status-transition history, with volume/ratio logic applied across the set of Features within a Capability (see Sections 6.2 and 7).

### 3.1 The Release entity (confirmed — source: `EPIC_Releases.xlsx`)

**A Release is a JIRA Fix Version.** It is not a work item with its own key — it is a named version referenced by a multi-valued `Fix versions` field carried on both EPICs and Capabilities.

Three consequences that change the data model:

1. **Releases are identified by name — confirmed, there is no independent Release ID.** The release name *is* the primary key, and all joins from `Fix versions` are name-based. This makes the duplicate-name problem structural rather than cosmetic: **5 names appear twice in the release list, in some cases with conflicting dates**, and there is no fallback identifier to disambiguate them. The tie-break rule in 6.1.6 is therefore **mandatory to implement**, not optional. Recommended: normalise names on ingestion (trim whitespace, collapse internal spaces, case-insensitive match) before joining, since name-based keys are fragile to formatting drift.
2. **A Capability belongs to exactly one Release (confirmed); an EPIC may span several.** The `Fix versions` field is technically multi-valued, but **by rule a Capability must carry exactly one Release — two or more is a Data Quality defect** (Rule Set 1 Part C, 6.1.2). EPICs legitimately carry several: 18 have one, and the rest range up to 7, because an EPIC spans multiple Releases by design.

   This matters for the roll-up: because Capability → Release is 1:1 by rule, **the Capability → Release → EPIC chain is a tree**, and Section 7.2's aggregation does not need to handle a Capability contributing to two Releases. The only exception is a Capability in breach of Part C, which must be flagged as a defect and `[PROVIDE]` handled deterministically for scoring in the meantime — recommendation: attribute it to its **earliest-dated** Release and flag the defect, so the roll-up stays deterministic rather than double-counting.
3. **Capabilities link to Releases directly, not via their EPIC.** The two are independent assignments and can disagree: **11 of 119** Capabilities with a release assigned reference a release that is *not* on their parent EPIC. `[PROVIDE]` Is that a defect to flag (a new rule), or legitimate?

**Source structure:**

| Sheet | Rows | Content |
|---|---|---|
| `EPIC Releases` | 43 | EPIC key, Summary, `Fix versions` (semicolon-delimited). Query scope: open Portfolio Epics only |
| `Capability Releases` | 246 | Capability key, Summary, `Fix versions` |
| `ALL UNRELEASED` | 89 | Release name, Status, Progress, Start date, Release date, Description |

**Coverage limitation — important.** The `ALL UNRELEASED` sheet contains only releases with status UNRELEASED. **Released (completed) releases are absent**, so 6 of the 30 releases linked to Capabilities have no date record available at all. Any Capability whose release has already shipped cannot be date-checked. `[PROVIDE]` Add a RELEASED sheet, or is a shipped release out of scope by definition?

**Scope mismatch.** `Capability Releases` covers 246 Capabilities while the main extract holds 406, and 32 of its keys are absent from the main extract. 192 Capabilities therefore cannot be evaluated for release assignment. `[PROVIDE]` Align the two exports to the same query scope.

**Phase scope:**
- **Phase 1 (this build):** hierarchy above only — EPIC, Release, Capability, Feature.
- **Phase 2 (future):** Releases also contain **Defects, Tests, and Test Plans**, which sit alongside (not strictly beneath) the Capability/Feature chain. Stories may also be introduced at that point if Story-level data becomes available. These are explicitly **out of scope for Phase 1** and should not be included in the data model, RAG logic, or dashboard views yet — but the architecture should not preclude adding them later (i.e. the hierarchy should be modelled generically enough that a level can be added beneath Feature without restructuring).

**Resolved:** the Release Manager view shows **one RAG row per Capability** within the chosen Release. Data Quality, Flow Throughput, and KPIs are driven at the **Feature level**, then roll up to produce each Capability's RAG (feeding into the weighted roll-up logic in Section 7).

---

### 3.2 Scope & Join Model (confirmed)

**Scope statement:** the system covers **Fixed Connectivity only** — the fully-connected chain of EPIC → Capability → Feature where the EPIC key carries an **`FCM`** or **`RN`** prefix.

**Standalone Capabilities and Features are out of scope.** A Capability whose parent EPIC is not present, or a Feature whose parent Capability is not present, is **excluded from the dataset** — it is *not* a Data Quality defect and must not appear in the cleanup checklist, the RAG calculations, or any view. This is a deliberate scoping decision, not an error to be remediated.

#### 3.2.1 Join map

Scope is resolved by walking these joins in order. Note the child key column differs by sheet:

| From | Join key | To | Notes |
|---|---|---|---|
| `Capabilities` sheet, `EPICKey` (col A) | → | `EPIC` sheet, `EPICKEY` (col A) | Capability is in scope only if its parent EPIC resolves |
| `Features` sheet, `CapKey` (col A) | → | `Capabilities` sheet, `CapKEY` (col B) | Feature is in scope only if its parent Capability is in scope |
| `EPIC Transition` sheet, `IssueKEY` (col A) | → | `EPIC` sheet, `EPICKEY` (col A) | EPIC status history |
| `Transitions` sheet, `IssueKEY` (col A) | → | `Features` sheet, `FeatureKEY` (col B) | Feature status history — the input to Flow Throughput (6.2) and the derived KPI dates (6.3.3) |
| `ART` sheet, `IssueKey` (col A) | → | `Features` sheet, `FeatureKEY` (col B) | Agile Release Train — the **authoritative delivering-team attribution** for a Feature (see the key-prefix note below) |

**Key-prefix expectations by level (confirmed):**

| Level | Key prefix | Rule |
|---|---|---|
| **EPIC** | Always `FCM` or `RN` | A non-FCM/RN EPIC is not Fixed Connectivity and is out of scope |
| **Capability** | `FCM`, `RN` or **`FCB`** | `FCB` denotes a Capability belonging to an EPIC still in **Backlog**. All three are in scope |
| **Feature** | **Many prefixes** (RN, FCM, CSI, DXL, PPEP, CTE, `FCB` and others) | Features are delivered by various teams across the business, so the key prefix carries **no scope meaning**. Scope is inherited from the parent Capability. `FCB` here likewise indicates a Backlog-EPIC origin |

**`FCB` — Backlog-stage items (confirmed).** `FCB` is a valid prefix for Capabilities and Features whose parent EPIC is still in Backlog. It is **in scope**: these are Fixed Connectivity items at an early portfolio stage, not foreign work.

- **No FCB keys appear in the current extract** (0 rows at any level), so this cannot be validated against real data yet. The filter must accept the prefix regardless, or Backlog-stage work will be silently dropped the first week it appears.
- **Because scope is inherited from the parent chain (not the child's own prefix), an FCB Capability under a resolvable FCM/RN EPIC is already in scope** without any filter change. The prefix matters for the *expectation* recorded above and for the anomaly check below, not for the join itself.

> ⚠ **Keys are mutable — see Section 13.2.** Reassociation with a Backlog parent **re-keys the item to `FCB`**. Keys are therefore *not* stable identifiers, which breaks naive upsert-by-key. Section 13.2 sets out the required handling. This remains the highest-priority implementation risk in the document.

**Team attribution comes from the ART worksheet, not the key prefix.** The variety of Feature key prefixes reflects which team is delivering the work; the `ART` sheet (Agile Release Train, joined on `FeatureKEY`) is the authoritative source for that attribution. Never infer a delivering team from a key prefix.

**ART coverage in the current extract:** 400 of the 598 in-scope Features have an ART value; **198 have none**. Of those that do, 103 read `(Contributing Team - Not Set)` and 39 read `Not applicable` — so genuine team attribution exists for **258 of 598** in-scope Features (43%). `[PROVIDE]` Is missing or unset ART a Data Quality defect (candidate addition to Rule Set 3), or expected for early-stage work?

**Anomaly to note:** two Capabilities in the current extract break the FCM/RN/FCB rule — `PPEP-13349` and `PPEP-31932`. One has a parent EPIC that resolves (`RN-78169`), one does not (`RN-31543` is absent from the EPIC sheet). `[PROVIDE]` Given Capability keys should always be FCM or RN, is a non-conforming Capability key an **exclusion** (out of scope, silently dropped) or a **Data Quality defect** (in scope, flagged for correction)? These pull in opposite directions and the answer sets the pattern for future cases.

**Filter order matters:** apply the scope filter **first**, at ingestion, before any rule set, RAG calculation, or KPI runs. Every threshold, denominator and percentage in this document refers to the in-scope population.

**Scope is dynamic, not fixed.** Items can be re-parented, and re-parenting arrives in the weekly delta (Section 13.1), so an item can move into or out of scope between uploads. The filter must therefore be **re-applied to the whole accumulated baseline on every upload** rather than evaluated once and stored against the record. An item that leaves scope is retained but no longer scored or displayed — never deleted, because it contributed to earlier weeks' snapshots.

#### 3.2.1a Sheet and column names (confirmed — revised extract)

**The sheet formerly named `Capability` is now `Capabilities`.** Ingestion must target the new name; a hardcoded reference to the old one will fail silently on an empty read.

**Title columns are named after the issue type, not "Summary":**

| Level | Sheet | Title column | Populated |
|---|---|---|---|
| EPIC | `EPIC` | **`Portfolio Epic`** | 74 / 74 (100%) |
| Capability | `Capabilities` | **`Capability`** | 410 / 410 (100%) |
| Feature | `Features` | **`Feature`** | 2,714 / 2,714 (100%) |

Note the column name equals the sheet-level entity name, so `Capabilities.Capability` and `Features.Feature` are title fields, not key fields. The loader must map these explicitly — inferring a title column by header name will not work, and a silent fallback to displaying keys must fail loudly instead (see Section 13).

**`Features.Created`** is present as the usual four-part Year/Quarter/Month/Day set, populated on **2,714 / 2,714 rows (100%)**, spanning 30/04/2018 to 17/08/2026.

#### 3.2.2 In-scope population in the current extract

*(Figures below are from the revised extract of 18/08/2026.)*

| Level | In scope | Excluded | Note |
|---|---|---|---|
| EPICs | **74** | 0 | all carry an FCM or RN prefix |
| Capabilities | **371** | 39 | excluded ones point at an EPIC not present in the EPIC sheet |
| Features | **598** | 2,116 | excluded ones point at a Capability not in scope — **78% of the raw Feature rows** |
| Feature transitions | **1,903** | 148,100 | **98.7% of the transition history is out of scope** |
| EPIC transitions | 116 | 319 | |
| ART rows | ~396 | ~31,558 | |

The scale of the reduction is the headline here: the transition history — which drives Flow Throughput and two of the three KPI start dates — shrinks from 150k rows to under 2k. Of the 598 in-scope Features, **only 362 have any transition history at all**.

#### 3.2.3 Consequences for the views — `[PROVIDE]`

- **41 of the 74 in-scope EPICs have no Capabilities beneath them**, and **219 of the 371 Capabilities have no Features.** They are in scope by the FCM/RN rule but have nothing to roll up. How should they render — an explicit "No data" state, a Grey/Unassessed RAG distinct from Green, or omitted from the view entirely? Scoring them Green would be actively misleading; scoring them Red would flood the SLT view. **Recommendation: a fourth Unassessed state, reported separately from the RAG counts.**
- **Should exclusion counts be reported?** The agent processes 2,714 Feature rows and uses 598. Surfacing "2,116 rows excluded as out of scope" in the Agent Transparency Panel (11.1) guards against a future export change silently dropping in-scope work. **Recommendation: yes** — report the count, not the detail.

---

## 4. Delivery Increment (DI)

**Definition (confirmed):** A Delivery Increment is a fixed quarterly window. Example: **FY26/27 Q1 = 01/04/2026 to 30/06/2026**.

**General pattern (confirmed):** This is not a one-off — the same quarterly structure applies to **all Delivery Increments, past and future**, not just FY26/27 Q1. Each subsequent/prior quarter follows the equivalent pattern (i.e. the data model needs a general DI concept with a start date and end date, not a hardcoded single quarter).

**Applies to (confirmed):** Delivery Increment is assigned at **both Feature and Capability level** — each Feature and each Capability has its own DI association.

**Why it matters:** DI is the time reference used to assess whether items are progressing and aligned — it underpins:
- Feature-level Flow Throughput risk scoring (Section 6.2), which measures Feature status-change activity relative to elapsed DI time.
- Blocked-item risk escalation timing — early/mid/late-in-DI penalties, and the pre-DI Warning-only exception (Section 8.3–8.4).

**Confirmed fiscal quarter calendar (FY26/27):**
| Quarter | Start | End |
|---|---|---|
| Q1 | 01/04/2026 | 30/06/2026 |
| Q2 | 01/07/2026 | 30/09/2026 |
| Q3 | 01/10/2026 | 31/12/2026 |
| Q4 | 01/01/2027 | 31/03/2027 |

This Apr–Jun / Jul–Sep / Oct–Dec / Jan–Mar pattern applies identically to every fiscal year, past and future (e.g. FY25/26 Q4 = 01/01/2026–31/03/2026, FY27/28 Q1 = 01/04/2027–30/06/2027, and so on).

### 4.1 Release Dates (confirmed)
Every Release assigned to an EPIC must always have a **Start Date** and a **Release Date** (end date) available. These are required fields, not optional — the alignment checks below depend on them.

**Current reality:** they are frequently absent. Of the 89 releases in the source list, **48 have no Start date and 48 no Release date (45 have neither)**. Of the 30 releases actually linked to Capabilities, only **14 have both dates**. This makes Section 4.2 and the Rule Set 4 boundary checks (6.1.5) partially blind, and is why missing release dates is a High Priority defect in Rule Set 1 Part B.

### 4.2 Release–Capability DI Alignment (confirmed)
A Capability's Delivery Increment **end date** must fall on or before its parent Release's **Release Date**.
- Example: Capability DI = FY26/27 Q1, ending 30/06/2026 → the Release Date must be **on or after 30/06/2026**.
- **Risk rule:** if the Release Date is *earlier* than the Capability's DI end date, this is a risk that the release will fail (the Capability's work isn't scheduled to finish before the release ships).
- **Multi-release Capabilities — resolved.** A Capability must carry exactly one Release (Section 3.1, Rule Set 1 Part C), so there is a single governing Release Date and no ambiguity. Where a Capability is in breach and carries several, use the **earliest** Release Date for this check and raise the Part C defect.

### 4.3 Capability–Feature DI Alignment (confirmed)
There is **no explicit flag** distinguishing single-quarter from multi-quarter Capabilities in the data — alignment is inferred purely by comparing each Feature's DI to its parent Capability's DI:

- **(A) Single-quarter Capability:** all of its Features should share the **same DI** as the Capability.
- **(B) Multi-quarter Capability:** it is acceptable for Features to fall in the Capability's own DI quarter **or** the one quarter immediately **before** it (see worked example in 4.5).
- **(C) DQ issue:** a Feature's DI must **never be after** its parent Capability's DI — regardless of (A) or (B). Applies only while the Feature is still **Open** (see 4.4).
- **(D) DQ issue:** a Feature's DI must **never be two or more quarters before** its parent Capability's DI. Applies only while the Feature is still **Open** (see 4.4).

In short, a Feature's valid DI range is: **the Capability's own quarter, or exactly one quarter earlier.** Anything outside that range (later than the Capability's quarter, or two+ quarters earlier) is a Data Quality issue.

> ✅ **Resolved (v0.9):** this is the authoritative definition of Feature/Capability DI alignment. A Capability's `Delivery Increment` denotes its **end/target quarter**, which is why Features may sit in that quarter or the one before it, and why a later quarter is a defect. The conflicting DI misalignment check formerly in Rule Set 4 (6.1.5) has been retired. Capabilities do **not** carry a quarter range.

### 4.4 Done/Cancelled Features Excluded (confirmed)
Once a Feature's status is **Done** or **Cancelled**, it is excluded from the Capability–Feature DI alignment checks in 4.3 (rules C and D) — no longer evaluated for DI-misalignment risk.

### 4.5 Multi-Quarter Capabilities — Late label and High Risk escalation (confirmed)

Worked example: Capability DI = FY26/27 Q1 (ending 30/06/2026) → Features may legitimately be tagged FY26/27 Q1 (the Capability's own quarter) **or** FY25/26 Q4 (the one quarter immediately before, per rule 4.3-B).

**Late label for Features in the earlier of the two valid quarters:**
- A Feature tagged with the earlier quarter (FY25/26 Q4, ending 31/03/2026) that is still **In Progress** on the first day of the Capability's own quarter (**01/04/2026**) is flagged **Late**.
- **The Late label carries no RAG or score impact.** It does not affect the parent Capability's status, its RAG, or its delivery date. The Capability's own DI end date (30/06/2026) still provides slack — the Feature has overrun its own tag, but not the Capability's window, so there is no delivery risk to report yet.
- Treatment is therefore the same shape as the pre-DI Warning in Section 8.4: **surfaced as a label, kept out of the score.**

**One month's grace, then it becomes a risk (confirmed):**
- If the Feature is **still undelivered one calendar month after the Late trigger** — i.e. by **01/05/2026** in this example — it escalates to **High Risk**.
- One month is the *only* grace allowed. At that point the overrun stops being a tagging artefact and becomes a genuine delivery concern: the Feature has consumed a third of the Capability's quarter without landing.
- Unlike Late, **High Risk is a reportable risk and must be recorded as such.** It is called out as its own line item at every viewer level, following the same pattern as blocked items in Section 8.2 — SLT per EPIC, Delivery Manager per Release, Release Manager per Capability.

**State summary for a Feature tagged the earlier quarter:**

| From | State | Score impact | Reporting |
|---|---|---|---|
| While its own quarter is still open (to 31/03/2026) | Healthy | None | Normal |
| First day of the Capability's quarter (01/04/2026), still undelivered | **Late** | **None** — Capability's DI end date still provides slack | Label on the Feature |
| One calendar month later (01/05/2026), still undelivered | **High Risk** | **Yes** — see below | Mandatory callout line item at every viewer level |
| Feature reaches Done or Cancelled | Cleared | n/a | Label removed (per 4.4) |

**Generalised timing rule** (this example is FY26/27 Q1; the pattern applies to every quarter): *Late* triggers on the first day of the parent Capability's DI quarter. *High Risk* triggers exactly **one calendar month** after that date — calendar-month arithmetic, not 30 days, so a Q3 Capability (starting 01/10) escalates on 01/11.

`[PROVIDE]` **Penalty size.** High Risk needs a number to affect the score. Proposal: a per-item penalty on the parent Capability's overall score, mirroring the blocked-item model in Section 8.3 — **−5% per High Risk Feature**, sitting between the −2% early-DI and −10% late-DI blocked penalties. Confirm the value, and whether it should itself escalate the longer the overrun continues.

`[PROVIDE]` **Beyond the Capability's own DI end date.** The grace logic covers the first month of the Capability's quarter. If the Feature is *still* undelivered at the Capability's DI end date (30/06/2026), the Capability itself is now overrunning, which is a different and larger problem. Working assumption: that is handled by the Capability's own DI and Release-alignment logic (Sections 4.2 and 6.1.5) rather than by a third escalation step here. Confirm.

**Why this matters for implementation:** the Late label must be rendered as a distinct visual flag on the Feature and must **not** be summed into any Capability, Release or EPIC aggregate. High Risk is the opposite — it both scores and reports. The two states must therefore be modelled as genuinely different things, not as two severities of one flag.

**Interaction with other measures.** A Late or High Risk Feature is very often also stagnating, but the two are independent: these states are *DI-tagging* observations (the Feature's quarter tag has expired), while Flow Throughput (6.2) measures *movement*. A Feature that is transitioning normally scores healthy on Flow and simply carries the label. One that is also static will additionally be caught by the stagnation ladder — legitimate, because that reflects lack of movement rather than the expired tag. `[PROVIDE]` Note this does mean a static, overrunning Feature can be penalised twice (stagnation score + High Risk penalty). Acceptable, or should one suppress the other?

---

## 5. Health Checks (three parts, computed at every level)

1. **Data Quality**
2. **Flow Throughput**
3. **KPIs**

Each of the three produces its own RAG. These three combine into a single overall RAG per row (see Section 7).

**Lowest-grain scope note (confirmed):** **Feature is the lowest grain at which the three health checks are computed.** There is no Story level in the model (see Section 3). A Feature's own status-transition history is the raw input to Flow Throughput (see Section 6.2); Capability, Release and EPIC RAGs are produced entirely by roll-up (Section 7), not by separate measurement at those levels.

---

## 6. RAG Rubric — *partially provided*

For each health check, define what drives Red / Amber / Green. Be as specific as possible — exact thresholds, not just descriptions — since this becomes the core logic of the agent.

**Status:** **All three rubrics are now specified.** 6.1 Data Quality — five rule sets. 6.2 Flow Throughput — two-phase stagnation ladder. 6.3 KPIs — three SLA-based flow KPIs. What remains in this section are confirmations of proposed constants, not missing logic.

### 6.1 Data Quality (confirmed)

Data Quality is assessed by running a fixed set of **triage and remediation rules** over every weekly upload (full dump or delta — see Section 13). The rules are grouped into three priority tiers. Each violation is a discrete, addressable defect with a named required fix, so the output is a work list, not just a score.

This is owned by the **Data Quality & Remediation Agent** (Section 11.4).

#### 6.1.1 Status-name normalisation (must be applied before any rule is evaluated)

The rules below were written using shorthand status names that do not all match the confirmed JIRA workflows in Section 12. The engine must normalise via this mapping table. **Proposed mappings marked ⚠ need confirmation** — they change which items get flagged.

| Rule shorthand | Level | Actual JIRA status (per Section 12) |
|---|---|---|
| Backlog | Capability | Backlog |
| Reviewing / Review | Capability | In Review ⚠ |
| In Analysis | Capability | In Analysis |
| In Dev | Capability | In Development |
| In Testing | Capability | In Testing |
| In Delivery | Capability | **As a condition/grouping:** In Development, In Testing, or Ready for Delivery. **As a required-fix target status (Rule D):** Ready for Delivery — the only one of the three that is a single valid end state for that rule |
| Done | Capability | Done |
| Funnel | Feature | Funnel |
| In Analysis | Feature | In Analysis |
| **In Delivery** | Feature | **Every status ordinally after Committed** — In Development, Dev Complete, In Testing, Test Complete, Deploying, Deployment Complete, Releasing. **Committed itself is *not* in delivery** |
| In Dev | Feature | In Development, Dev Complete ⚠ |
| Testing | Feature | In Testing, Test Complete ⚠ |
| Deploying | Feature | Deploying, Deployment Complete, Releasing ⚠ |
| Done | Feature | Done |
| Cancelled | Feature | Cancelled |
| Reviewing | Feature | ⚠ **no such Feature status exists** — see 6.1.7 |

**"In Delivery" — confirmed definitions (resolves the earlier ⚠):**

| Level | In Delivery means |
|---|---|
| **Capability** | In Development, In Testing, or Ready for Delivery |
| **Feature** | Every status **after** Committed — In Development, Dev Complete, In Testing, Test Complete, Deploying, Deployment Complete, Releasing. Committed is excluded |

This also settles one of the 6.1.7 questions: **Committed does not count as "In Dev"** for Rule Set 2 Rule A, because it sits before the delivery boundary. Done and Cancelled remain separate terminal categories, not part of "In Delivery".

Note the term does double duty — as a **condition** it is a set of statuses; as a **required fix** it must resolve to one target status. For Rule D the target is **Ready for Delivery**. `[PROVIDE]` Confirm that reading of Rule D.

#### 6.1.2 Rule Set 1 — Missing Releases & Incorrect Release Records (High Priority)

**Field note:** the release assignment is the JIRA **`Fix versions`** field (semicolon-delimited, multi-valued) — not a single `Assigned_Release_ID`. "Unassigned" means the field is empty. See Section 3.1.

**Part A — Capabilities without a Release.** Flag any Capability whose `Fix versions` field is null, empty, or unassigned. Severity is set by the Capability's Delivery Increment relative to the current quarter:

| Capability DI | Severity |
|---|---|
| Current quarter or any past quarter | **High impact** |
| Exactly one quarter in the future | **Medium impact** |
| Two or more quarters in the future | **Warning** |

**Part C — Capability assigned to more than one Release (confirmed).** A Capability must belong to **exactly one Release**. Flag any Capability whose `Fix versions` field contains two or more values. Severity: treat as **High** — an ambiguous release assignment invalidates the Section 4.2 DI/Release date alignment check and makes the roll-up non-deterministic.

**Observed baseline:** 1 breach today — `RN-85441`, carrying both *VeloCloud SDWAN 7.0 Rel 7.3 KTLO* and *VeloCloud SDWAN 8.0 Rel 8.2 KTLO [Q2 FY27]*. Distribution: 118 Capabilities with exactly one Release, 1 with two, 127 with none (Part A).

*Note this rule applies to Capabilities only. EPICs may legitimately carry multiple Releases and must not be flagged.*

**Part B — Release record integrity.**
- Flag any Release whose **name** does **not** begin with the EPIC Number as a prefix (e.g. `FCM-30593 R5 Global Internet Transformation` passes; `NaaS Portal` fails). Note the source has both a Release *name* and a separate free-text *Description* column; the observed convention places the EPIC key at the start of the **name**, so the check applies there. `[PROVIDE]` Confirm — your wording said "Description".
- Flag any Release missing a **Start Date** or a **Release End Date** (both mandatory per Section 4.1).

**Observed baseline:** only **15 of 89** release names begin with a valid EPIC key, so 74 would flag on the prefix rule as written. All 15 that do carry a key resolve to a real EPIC. Given a 17% pass rate, `[PROVIDE]` confirm this is a genuine standard being enforced rather than a convention used by one team — otherwise this single rule will dominate the checklist.

#### 6.1.3 Rule Set 2 — Capability Status Rollup Inconsistencies (Medium Priority)

Evaluate child Feature statuses against the parent Capability status. Each rule states its condition and the required corrective status.

| Rule | Condition | Required fix |
|---|---|---|
| **A** — Premature Capability status | Capability is in an early status (Backlog, In Review, In Analysis) **AND** at least 1 child Feature is In Dev, Testing, or Done | Set Capability → **In Development** |
| **B** — Analysis transition | Capability is in an early status (Backlog or In Review) **AND** at least 1 child Feature is In Analysis **AND** all other children are Funnel or Reviewing | Set Capability → **In Analysis** |
| **C** — Testing stage | **ALL** child Features are In Testing, Deploying, or Done, with at least 1 In Testing | Set Capability → **In Testing** |
| **D** — Delivery stage | **ALL** child Features are Deploying or Done, with at least 1 Deploying | Set Capability → **In Delivery** (i.e. Ready for Delivery — see 6.1.1) |
| **E** — Completion | **ALL** child Features are strictly Done or Cancelled | Set Capability → **Done** |

**Blocked children (confirmed):** a Blocked child Feature has a direct impact on the Release occurring (Section 8.1), so it is treated as a delivery impact in its own right and **does not satisfy the "ALL child Features are…" conditions** in Rules C, D or E. A Capability with any Blocked child cannot be advanced by those rules; it is reported as Blocked instead.

**Precedence (proposed — needs confirmation):** rules overlap. A Capability in Backlog whose Features are all Done satisfies both A and E, but only E is the right answer. Evaluate **most-advanced-state-first and stop at the first match: E → D → C → A → B.** Report one rule per Capability.

#### 6.1.4 Rule Set 3 — Missing Critical Dates & Baseline Fields (Low Priority)

- Flag any **Capability not in Backlog** that has no Delivery Increment.
- Flag any **Feature not in Funnel** that has no Delivery Increment.
- Flag any Capability missing a **Target Start Date** or **Target End Date**.

**Compliance target (confirmed):** **every Capability past Backlog must carry a Delivery Increment and both Target Dates.** This is an active data quality push, not an aspiration — the fields are prerequisites for Section 4.2 DI/Release alignment, the Rule Set 4 boundary checks, and the Section 7.3 delivery status, all of which are blind without them.

The agent must therefore **measure and trend compliance weekly**, not just list defects: report the percentage of post-Backlog Capabilities holding all three fields, alongside the raw defect list, so progress toward 100% is visible week on week. A shrinking defect count is the intended trend line.

**Current in-scope position (371 Capabilities, of which 215 are past Backlog):**

| Field | Missing | Compliance |
|---|---|---|
| Delivery Increment | 16 | **92.6%** |
| Target Start Date | 51 | 76.3% |
| Target End Date | 70 | 67.4% |
| Missing either Target Date | 77 | 64.2% |
| **All three fields present** | 85 short | **60.5% (130 of 215)** |

Delivery Increment is close to clean; **Target Dates are the weak point**. Concentration by status is worth noting for the remediation effort:
- All 16 missing DIs sit in just two statuses — **In Review (14)** and Blocked (2).
- Missing target dates are more widely spread: In Review 36, In Development 20, In Testing 10, In Analysis 10, Ready for Delivery 1. **30 Capabilities already in Development or Testing have no target dates**, which is the more concerning subset — work in flight with no committed date cannot be assessed for delivery risk at all.

`[PROVIDE]` Should the compliance percentage itself be surfaced as a headline metric in the SLT view (e.g. "Capability baseline compliance: 60.5%, up 3pts"), or kept inside the cleanup checklist? Recommendation: **headline** — it is the single clearest measure of whether the data foundation is improving, and it is the precondition for most other measures being trustworthy.
- **Confirmed contributing factor (carried forward):** an Open Feature whose DI is after its parent Capability's DI, or two or more quarters before it, counts as a Data Quality issue (see Section 4.3, rules C and D).

#### 6.1.5 Rule Set 4 — Date Boundary & Schedule Alignment Errors (High Priority)

Schedule containment checks: a child's dates must sit inside its parent's dates.

| Check | Condition to flag |
|---|---|
| **Capability vs. Release boundary violation** | Capability `Target_Start_Date` < Release `Start_Date` **OR** Capability `Target_End_Date` > Release `Release_Date` |
| **Feature vs. Capability boundary violation** | Feature `Target_Start_Date` < Capability earliest start **OR** Feature `Target_End_Date` > Capability `Target_End_Date` |
| ~~Delivery Increment (quarter) misalignment~~ | **RETIRED (v0.9)** — superseded by Section 4.3 rules C and D, which are the authoritative DI alignment checks |

**Relationship to existing rules — read this before implementing:**

- The **Capability vs. Release** check is a stricter, date-level version of Section 4.2, which only compared the Capability's *DI end date* to the Release Date. Rule Set 4 compares actual target dates at both ends. Both should be implemented; 4.2 still applies where a Capability has a DI but no target dates.
- The **DI misalignment** check is **retired**. It contradicted Section 4.3, which is confirmed as authoritative: a Feature's valid DI is the Capability's own quarter or exactly one quarter *earlier*, and a later quarter is a defect (rule C). Rule Set 4's phrasing implied the opposite direction and a Capability quarter *range*; neither applies. **Implement DI alignment once, from Section 4.3 only** — do not build a second, separate quarter check here. Capabilities carry a single Delivery Increment value denoting their end/target quarter, not a span.
- The **Feature vs. Capability** check needs a definition of "Capability earliest start". Proposed: the Capability's own `Target_Start_Date`. `[PROVIDE]` Or does it mean the earliest start across the Capability's sibling Features (a derived value)?

**Baseline volumes in the current extract:**

*(In-scope population per Section 3.2: 371 Capabilities, 598 Features.)*

| Check | Result |
|---|---|
| Capability vs. Release boundary | **Partially runnable** — only 14 of the 30 releases linked to Capabilities carry both a Start and Release date, so most pairings cannot be evaluated |
| Feature vs. Capability boundary | Only **106 of 598** in-scope Feature/Capability pairs have target dates populated on both sides; of those, **40 violate** (38%) |
| DI misalignment | *Retired — see Section 4.3. For reference, that rule flags **126 of 291** evaluable open pairs: 97 Features two-or-more quarters early (rule D), 26 one quarter late and 3 two-or-more quarters late (rule C).* |

Note the coverage problem: Feature target dates are sparsely populated, as are Capability target dates (211 of 371 in-scope Capabilities are missing one or both), so this rule set currently sees a small fraction of the estate. Rule Set 3 (missing dates) is effectively the precondition for Rule Set 4 producing meaningful results. A related self-consistency defect also exists and is not covered by any rule you've specified: **6 in-scope Features have a Target End Date earlier than their Target Start Date.** `[PROVIDE]` Add as a rule?

#### 6.1.6 Rule Set 5 — Orphaned & Unlinked Release Anomalies (High Priority)

Release-side hygiene: the mirror image of Rule Set 1, which looks at work items missing a release. These rules look at releases missing work.

| Anomaly | Condition to flag | Current count |
|---|---|---|
| **A — Release with no work items** | Release whose JIRA `Progress` field reads *No work items* | **9 of 89** |
| **B — Release linked to nothing** | Release present in the release list but referenced by no EPIC and no Capability `Fix versions` value | **34 of 84** distinct names |
| **C — Release referenced but not listed** | Release name appearing in a `Fix versions` value that has no record in the release list (so no dates, no status) | **25** |
| **D — Duplicate release name** | Two or more release records sharing the same name | **5 names, 10 records** |
| **E — Undated release** | Release missing Start date and/or Release date (overlaps Rule Set 1 Part B; report once, under Part B) | 48 / 48 |

**Notes on each:**

- **A and B overlap but are not the same.** 8 of the 9 "No work items" releases are also unreferenced, but B is the broader check and catches releases whose only linkage was removed. Report an item under its most specific anomaly and do not double-count in the score.
- **C is the more serious of the two orphan directions.** A Capability pointing at a release with no record means the Capability's release dates cannot be resolved at all — it silently defeats Section 4.2 and the Rule Set 4 boundary check. Partly explained by the coverage limitation in Section 3.1 (released versions absent from the source), so `[PROVIDE]` resolving that may retire much of this count.
- **D is a data-model problem, not just untidiness.** Because `Fix versions` references releases **by name** (Section 3.1), a duplicated name makes the join ambiguous — and the duplicates carry *conflicting dates*. Example: `NaaS 1.1.9 Technical Release` exists twice, once with a start date and once without, both with the same release date. `[PROVIDE]` Tie-break rule needed: prefer the record with the most complete dates, the most recent, or flag and exclude?
- **Empty-release severity.** `[PROVIDE]` A release with no work items and no dates is arguably housekeeping rather than delivery risk. Should Rule Set 5 findings carry the same High severity weighting as Rule Set 1, or a lower one? Proposal: **Warning** severity for A and B, **High** for C, since C actively breaks downstream checks.

#### 6.1.7 Open questions on the rule set — `[PROVIDE]`

These are genuine gaps, not restatements — each changes the flagged population:

1. **Feature statuses not referenced by any rule.** The Feature workflow (12.3) has 15 states, but Rules A–E only name Funnel, In Analysis, In Dev, Testing, Deploying, Done, Cancelled. Unaddressed: **PI Backlog, PI Planning, Committed, Dev Complete, Test Complete, Deployment Complete, Releasing, Blocked**. Specifically:
   - Does **Committed** count as "In Dev" for Rule A (work committed but not started)?
   - Do **Dev Complete / Test Complete / Deployment Complete** roll into In Dev / Testing / Deploying respectively?
   - Does **Releasing** satisfy "Deploying" for Rule D?
2. **Blocked children and the "ALL child Features are…" conditions (C, D, E).** Does a single Blocked child prevent C/D/E from firing, or should Blocked children be excluded from the denominator? Blocked is a global state a Feature can enter from anywhere, so this will occur in practice.
3. **Rule B references a Feature status "Reviewing" that does not exist.** Should this read In Analysis, PI Backlog, or be dropped?
4. **Rule B's early-status set excludes In Analysis** while Rule A includes it — deliberate, or should both be (Backlog, In Review, In Analysis)?
5. **Capabilities with zero child Features.** 219 of the 371 in-scope Capabilities have no Features at all. Note these are *in scope* (their parent EPIC resolves) — they simply have nothing beneath them, which is different from the out-of-scope exclusions in Section 3.2. Are they a Rule Set 2 violation in their own right (a Capability in In Development with no Features is arguably a defect), or simply exempt from status rollup and rendered Unassessed per 3.2.3?
6. **Part A severity when the Capability has no DI at all.** Such a Capability is already flagged by Rule Set 3, but what severity does its missing-Release flag get? Proposed default: **High impact**, on the basis that unknown timing is not a reason to defer.
7. **DQ score → RAG thresholds.** The rules produce a severity-weighted defect count, but Data Quality is 30% of the weighted score in Section 7, which needs a 0–100% figure. Proposal: score = 100% − (weighted defects ÷ items in scope), with High = 3 points, Medium = 2, Warning/Low = 1, then apply the standard 85% / 60% bands from Section 7. **Confirm or replace.**

#### 6.1.8 Baseline volumes in the current extract

Counts against the **in-scope population only** (Section 3.2: 74 EPICs, 371 Capabilities, 598 Features), using the ⚠ mappings above. Expect these to move once 6.1.7 is answered:

| Check | Count |
|---|---|
| Rule Set 1 Part A — Capabilities with no release assigned | **127 of 246** covered by the release export (52%); the export's scope does not align with the 371 in-scope Capabilities, leaving a gap that must be closed at source |
| Rule Set 1 Part A — EPICs with no release assigned | 12 of 43 (28%) |
| Rule Set 1 Part B — release name missing EPIC key prefix | 74 of 89 (83%) |
| Rule Set 1 Part C — Capability assigned to more than one Release | 1 (`RN-85441`) |
| Rule Set 1 Part B — release missing Start and/or Release date | 48 of 89 (54%) |
| Rule Set 5 — release anomalies | 9 with no work items, 34 linked to nothing, 25 referenced but unlisted, 5 duplicate names |
| Rule Set 2, Rule A | 19 Capabilities |
| Rule Set 2, Rule B | 6 Capabilities |
| Rule Set 2, Rule C | 4 Capabilities |
| Rule Set 2, Rule D | 1 Capability |
| Rule Set 2, Rule E | 14 Capabilities |
| Rule Set 2 total | 44 of the **152** in-scope Capabilities that have child Features (29%) |
| Rule Set 3 — Capabilities missing DI (excl. Backlog) | **16** (135 missing in total, 119 exempt as Backlog) |
| Rule Set 3 — Features missing DI (excl. Funnel) | **8** (87 missing in total, 79 exempt as Funnel) |
| Rule Set 3 — Capabilities missing Target Start and/or End | **211 of 371** (57%) |
| Rule Set 4 — Feature vs. Capability boundary violations | 40 of 106 evaluable pairs |

Worth noting how much the scope filter changes the picture: Rule Set 3's Feature DI defects drop from 228 to **8**, because almost all of the missing-DI Features were out-of-scope rows. The Capability-level defects barely move, since Capabilities were already mostly in scope.

#### 6.1.9 Required output — "Immediate Data Cleanup Checklist"

The agent produces this artefact on every upload, in this structure:

**Header — reconciliation summary** *(per 7.1.1)*

Every checklist opens with: total defects found; number scored under Data Quality; number attributed to a higher-priority category (Delivery Impact or KPIs) and therefore excluded from the DQ score. Each defect row carries its scoring attribution, so a defect suppressed from the score is still listed and still actionable.

**Section 1 — Missing Releases and Incorrectly Completed (Highest Priority)**
- List of all Capabilities missing a Release assignment, with severity (High / Medium / Warning) per 6.1.2 Part A.
- List of all Releases with the EPIC Number missing from the Title prefix.
- List of all Releases missing a Start Date and/or Release End Date.

**Section 2 — Capability Status Correction Table (Medium Priority)**

| Capability ID | Current Status | Child Feature Status Summary | Rule Triggered | Required Capability Status |
|---|---|---|---|---|

**Section 3 — Missing Critical Dates & Baseline Fields (Low Priority)**

| Capability ID | Missing Field | Required Fix Action |
|---|---|---|

**Section 4 — Date Boundary & Schedule Alignment Errors (High Priority)** *(Rule Set 4, per 6.1.5)*

| Item ID | Level | Parent ID | Violation Type | Child Dates | Parent Dates | Required Fix Action |
|---|---|---|---|---|---|---|

**Section 5 — Orphaned & Unlinked Release Anomalies (High Priority)** *(Rule Set 5, per 6.1.6)*

| Release Name | Anomaly | Start Date | Release Date | Linked EPICs | Linked Capabilities | Required Fix Action |
|---|---|---|---|---|---|---|

*(The Flow SLA breaches are a KPI output, not a data quality defect — they are reported separately in the SLA Breach Report, 6.3.4.)*

`[PROVIDE / DECIDE IN PLANNING]` Delivery of the checklist: rendered in-dashboard, exported (CSV/XLSX/PDF), or both? And is it a per-upload snapshot only, or should defect *age* be tracked so the same unresolved defect can be shown as recurring week over week? (Recommend the latter — a defect open for six weeks is a different conversation from a new one.)

### 6.2 Flow Throughput (confirmed)

**EPIC-level stage definitions (confirmed):**
| Stage | EPIC Status |
|---|---|
| Time to Scope | Reviewing, In Analysis, or Ready |
| Time to Deliver | In Progress |

#### 6.2.1 Core measure: stagnation (confirmed)

Flow Throughput is measured by **stagnation — the number of calendar days since a Feature's last forward status transition.** A Feature that keeps moving is healthy regardless of how far through the workflow it has got; a Feature that stops moving is the risk. The clock is absolute (elapsed days), not relative to DI position.

The stagnation thresholds differ by phase, because the two phases have different time budgets:

| Phase | Feature's current status | Rationale |
|---|---|---|
| **Pre-analysis** | Funnel | Not yet in flight — no stagnation clock (see 6.2.9) |
| **Scoping** | In Analysis, PI Backlog, PI Planning | Full Cycle Time SLA 150d − Delivery Predictability SLA 90d = **60 days budget** to get from In Analysis to Committed |
| **Delivery** | Committed and every status beyond it | Covered by the 90-day Delivery Predictability / Delivery Cycle Time SLAs |
| **Blocked** | Blocked | Frozen — see 6.2.5 |

**Phase is determined by the Feature's *current status*, not by its transition history (confirmed correction).** An earlier draft inferred phase from whether a Feature had ever transitioned into In Analysis or Committed. That was wrong: transition history is missing for a large share of in-scope Features, which misclassified **43 Features whose current status was already In Development, Dev Complete, In Testing or Releasing** as pre-analysis, wrongly excluding live delivery work from Flow Throughput. Current status is always present; transition history is not. Status sets the phase; transitions supply the timestamp.

**Clock anchor with fallback (confirmed):** the stagnation clock measures days since the Feature's **last forward transition**. Where a Feature has no transition history, use its **`Created` date** as the anchor. With the revised extract this leaves **no open in-scope Feature without a usable anchor** (137 anchored on a transition, 259 on Created).

#### 6.2.2 Stagnation ladder (confirmed)

**Scoping phase — In Analysis to Committed (60-day budget):**

| Days since last forward transition | State |
|---|---|
| < 10 | 🟢 Healthy |
| ≥ 10 | 🟠 **Stagnation Warning** |
| ≥ 20 | 🔴 **Priority Risk** |

**Delivery phase — Committed onward:**

| Days since last forward transition | State |
|---|---|
| < 10 | 🟢 Healthy |
| ≥ 10 | 🟠 **Warning 1** |
| ≥ 20 | 🟠 **Warning 2** |
| ≥ 30 | 🔴 **HIGH ALERT** |

**Pre-analysis (Feature not yet in In Analysis) — confirmed exclusion.** No flow clock runs. A Feature in Funnel is not yet in flight, so it is **excluded from the Flow Throughput denominator** rather than scored as healthy — otherwise a backlog of untouched Features would inflate the score. The clock starts only when the Feature reaches **In Analysis**, which is also where the Full Cycle Time KPI starts (6.3.2). See the coverage note in 6.2.7, which makes this exclusion consequential.

#### 6.2.3 Scoping phase budget breach (confirmed, derived)

Independent of stagnation: a Feature that takes **more than 60 days from In Analysis to Committed** has consumed its scoping budget and is on track to breach Full Cycle Time (6.3.2). Flag as a **Phase Budget Breach** and treat as Priority Risk regardless of recent movement — a Feature can transition every 9 days and still blow the 60-day budget.

#### 6.2.4 What resets the clock (confirmed)

Only a **forward** transition resets the stagnation clock, per the ordinal classification below. A backward transition is activity but not progress, so it does **not** reset the clock — otherwise a Feature could churn between two statuses indefinitely and always read as healthy.

**Transition direction classification (confirmed — derived from Section 12.3):**
Flow Throughput needs to distinguish genuine forward progress from churn. Using the Feature workflow's ordinal sequence:

`1. Funnel → 2. In Analysis → 3. PI Backlog → 4. PI Planning → 5. Committed → 6. In Development → 7. Dev Complete → 8. In Testing → 9. Test Complete → 10. Deploying → 11. Deployment Complete → 12. Releasing → 13. Done`

- **Forward transition:** any transition to a *higher* ordinal (including the shortcut jumps Dev Complete → Done and Test Complete → Done).
- **Backward transition:** any transition to a *lower* ordinal (e.g. In Development → Committed, Done → Releasing). Counts as activity but **not** as progress — a Feature bouncing backwards is not throughput.
- **Neutral / non-progress:** any transition into or out of **Blocked**, and any transition into **Cancelled**. Blocked is handled separately by the Section 8 penalties rather than by Flow Throughput.

`[PROVIDE]` One judgement call remains: when a Feature resumes from **Blocked** back into an active status (e.g. Blocked → Committed), does that count as a forward transition and reset the stagnation clock, or as neutral? It is the most common single edge out of Blocked in the data.

#### 6.2.5 Blocked Features (confirmed)

**A Feature entering Blocked must be captured prominently in Flow Throughput reporting** — listed explicitly as its own line item, not merely absorbed into a score. This is in addition to the Section 8.2 mandatory callout and the Section 8.3 score penalties.

**Blocked overrides the stagnation clock (confirmed).** Blocked is the **highest-priority issue in the model** — it impacts delivery and must be actioned immediately to get the work back on track. Per the single-attribution principle (7.1), a Blocked item is not additionally penalised for failing to move, because being unable to move is the whole point.

**What freezes and what keeps running while Blocked (confirmed):**

| Measure | While Blocked |
|---|---|
| Stagnation clock (6.2.2) | **Frozen** — resumes from where it stopped when the block clears |
| DI Late / High Risk ladder (4.5) | **Frozen** — the overrun escalation does not advance |
| Section 4.5 and 6.2 scoring | **Frozen** — no further penalty accrues from these |
| **KPI clocks (6.3)** | **Keep running** — Full Cycle Time, Delivery Predictability and Delivery Cycle Time continue to accrue elapsed days, because the customer-facing delivery date does not pause just because the work is blocked |
| Section 8.3 blocked penalty | Applies, set by DI position at the moment of blocking (see 8.3) |

The asymmetry is deliberate: internal process clocks stop because the team cannot act, but the delivery SLAs do not, because elapsed time still matters to the business.

**Blocked Feature reporting requirements:**
- Feature ID, parent Capability, date entered Blocked, days blocked to date, status it was blocked from, and **whether it was blocked on the previous week's report** (see 8.5).
- Surfaced at every viewer level per Section 8.2, as the top-priority item.
- Stagnation state shown as **Blocked**, distinct from both Healthy and the warning bands.

#### 6.2.6 Feature score → Capability roll-up (proposed)

The ladder gives each Feature a state; the roll-up needs a number. Proposed conversion:

| State | Feature score |
|---|---|
| Healthy | 100 |
| Warning / Warning 1 | 70 |
| Warning 2 | 50 |
| Priority Risk / HIGH ALERT | 20 |
| Phase Budget Breach (6.2.3) | 20 |
| Blocked | Excluded from the Flow score; handled by Section 8 penalties and the callout |

**Capability Flow Throughput score = mean of its in-flight Features' scores** (Pre-analysis, Done, Cancelled and Blocked Features excluded from the denominator). Then apply the standard bands from Section 7: ≥85% Green, ≥60% Amber, <60% Red.

This preserves the volume/ratio behaviour confirmed earlier: a ten-Feature Capability with nine healthy and one stagnant scores 92% (Green); a single-Feature Capability whose only Feature is at HIGH ALERT scores 20% (Red).

`[PROVIDE]` Confirm the 100/70/50/20 mapping and the simple mean. Alternative worth considering: weight each Feature by its stage (a Feature stalled at Releasing is closer to shipping than one stalled at In Analysis, and arguably more urgent).

#### 6.2.7 Baseline volumes in the current extract

Applied to the **396 open in-scope Features** in the revised extract at 18/08/2026, using status-based phase and the Created-date fallback:

| Phase | Features | Healthy | Warning bands | Top risk band |
|---|---|---|---|---|
| **Delivery** (Committed onward) | 103 | 20 | 27 | **56 HIGH ALERT** |
| **Scoping** (In Analysis / PI Backlog / PI Planning) | 60 | 3 | 12 | **45 Priority Risk** |
| **Blocked** (frozen) | 9 | — not scored on stagnation — | | |
| **Pre-analysis** (Funnel) | 224 | — excluded from Flow, see 6.2.9 — | | |

In-flight (scored) population: **163 Features** — up from 124 under the previous transition-based method, because 43 Features already in delivery statuses were being wrongly classified as pre-analysis. Median days since anchor: **39 days.**

Three observations the thresholds should be sanity-checked against:

1. **The thresholds put ~62% of in-flight Features in the top risk band today** (101 of 163). If that reflects reality, fine — the tool is telling you something true. But at that hit rate the Flow Throughput RAG will read Red almost everywhere and lose its ability to discriminate between Capabilities. `[PROVIDE]` Worth a look at a handful of the 56 HIGH ALERT Features to confirm they really are stalled, before locking 10/20/30 in. Note the Created-date fallback contributes here: a Feature created 400 days ago with no transitions anchors at 400 days and lands in the top band immediately.
2. **163 of 598 in-scope Features are measurable on stagnation** — 224 are pre-analysis, 9 blocked, and the rest Done or Cancelled. Flow Throughput is 40% of the overall score but computed from roughly 27% of the in-scope estate. That is defensible (it measures work in flight) but should be understood before the SLT sees it.
3. **The 60-day Scoping budget almost never binds on in-scope data** — across 169 in-scope Features with both timestamps, the median In Analysis → Committed gap is **0 days** and only 9 exceed 60 days. The two transitions typically happen on the same day, most likely as part of a bulk PI-planning update.

**Decision (confirmed): build the Scoping ladder, but instrument it.** Rather than assume the phase is real or drop it, the system monitors whether it is a genuine workflow stage or merely a transitional status that work passes through instantly. Required instrumentation, reported weekly alongside the RAGs:
- Count of Features whose In Analysis → Committed gap is **0 days** (i.e. passed straight through), as a proportion of those reaching Committed.
- Median and distribution of the In Analysis → Committed gap.
- Count of times the Scoping ladder (10/20-day) actually fired, and the count of 60-day Phase Budget Breaches.

If the pass-through proportion stays high over several weeks, the Scoping ladder can be retired and the Delivery ladder left to do the work. Surface these figures in the Agent Transparency Panel (11.1) so the decision can be taken on evidence. `[PROVIDE / DECIDE IN PLANNING]` How many weeks of evidence before the review — suggest reviewing after the 11-week history is full (Section 9).

#### 6.2.8 Created date — resolved

**Closed.** `Features.Created` is now supplied and populated on 100% of rows. Every open in-scope Feature therefore has a clock anchor: its last forward transition where one exists, otherwise its Created date (6.2.1). No Feature is invisible to Flow Throughput for want of a timestamp.

#### 6.2.9 Ageing Backlog — pre-analysis Features (new, needs a threshold)

The Created date makes a previously invisible population measurable: **224 open in-scope Features sit in Funnel**, excluded from the stagnation ladder by design (6.2.1), but now with a known age.

| Age since Created | Features |
|---|---|
| < 30 days | 69 |
| 30–60 days | 52 |
| 60–90 days | 5 |
| 90–180 days | 40 |
| 180–365 days | 35 |
| 1–2 years | 18 |
| **Over 2 years** | **53** |

Median age 49 days, mean 480 — a heavily skewed distribution. **68 Features have sat in Funnel for over a year**, and 53 for over two.

These are not a Flow Throughput problem (they are not in flight, so nothing is stalling), but a backlog carrying 53 items older than two years is a portfolio hygiene signal that belongs somewhere in the model.

`[PROVIDE]` Three decisions:
1. **Is ageing backlog reported at all?** Recommendation: yes, as its own callout — an **Ageing Backlog** line item alongside blocked items, not folded into a RAG.
2. **What age threshold?** The distribution suggests a natural break around 180 days (98 Features beyond it) or 365 days (68 Features). Recommendation: **365 days**, giving a defensible "over a year untouched" list of manageable size.
3. **Does it score?** Recommendation: **no** — reporting only, consistent with the Late label (4.5) and the single-attribution principle (7.1). Pre-analysis work is not a delivery impact until someone commits to it.

### 6.3 KPIs (confirmed)

Three flow KPIs, all measured **at Feature level** and rolled up per Section 7. All are elapsed **calendar days** (not working days).

#### 6.3.1 Open-item boundary convention (confirmed)

Where `Date_Done` is null or missing (i.e. the Feature is still open), use **`NOW()` — the current audit date** — as the end boundary. Every KPI therefore reports an elapsed-so-far figure for open items and a final figure for completed ones.

Implication for reporting: an open Feature's KPI value **increases every week until it closes**, so a Feature can cross an SLA threshold without anything changing in JIRA. This is intended, but it means the SLA Breach Report (6.3.4) will grow week on week unless breaches are actioned.

#### 6.3.2 KPI definitions and SLAs (confirmed)

| KPI | Calculation | SLA | Output |
|---|---|---|---|
| **Full Cycle Time** | (`Date_Done` OR `NOW()`) − `In Analysis Date` | ≤ 150 calendar days | Days elapsed |
| **Delivery Predictability** | (`Date_Done` OR `NOW()`) − `Date_Committed` | ≤ 90 calendar days | **PASS / FAIL** |
| **Delivery Cycle Time** | (`Date_Done` OR `NOW()`) − `Date_In_Development` | ≤ 90 calendar days | Days elapsed |

#### 6.3.3 Where the date fields come from

Only two of the four required dates exist as columns on the Feature record. The other two must be derived from the transition history (Section 12.3):

| Field | Source |
|---|---|
| `Date_Done` | `DATE_Done` column on the Feature record |
| `Date_Committed` | `DATE_Committed` column on the Feature record |
| `In Analysis Date` | **Derived** — first transition `→ In Analysis` in the transition history |
| `Date_In_Development` | **Derived** — first transition `→ In Development` in the transition history |

Two consequences to settle:

- **First entry or last entry?** Features can re-enter a status (the workflow has backward transitions at every step — see 12.3). Proposed default: **first** entry into the status, so the clock measures total elapsed time rather than the most recent attempt. `[PROVIDE]` Confirm.
- **`DATE_Committed` and the transition history disagree on roughly 4% of Features** where both are present (78 of 1,851 across the raw extract). Which is authoritative? Proposed: use the column, and raise the mismatch as a new Data Quality defect. `[PROVIDE]` Confirm.

#### 6.3.4 SLA Breach Report — required output (confirmed)

Each breach type is reported as its own list, and each entry **must note the Feature's current status** (as specified):

| Breach | Threshold |
|---|---|
| Full Cycle Time Breach | > 150 days from In Analysis to completion/present |
| Delivery Cycle Time Breach | > 90 days from In Development to completion/present |
| Delivery Predictability Breach | > 90 days from Committed to completion/present |

Suggested columns: `Feature ID | Parent Capability | Current Status | Start Date Used | End Date Used (or NOW) | Elapsed Days | SLA | Days Over`.

#### 6.3.5 Baseline volumes in the current extract

Computed against the **in-scope population** (598 Features) with `NOW()` = 18/08/2026, using the 6.3.6 bands:

| KPI | Computable | Median | 🔴 Red | 🟠 Amber | Red still open |
|---|---|---|---|---|---|
| Full Cycle Time (≤150d) | 220 of 598 (37%) | 47 days | 33 | 6 | 23 |
| Delivery Predictability (≤90d) | 213 of 598 (36%) | 39 days | 37 | 18 | 10 |
| Delivery Cycle Time (≤90d) | 188 of 598 (31%) | 33 days | 34 | 15 | 9 |

**This materially changes the open question in 6.3.6 (1).** On the raw extract, 91% of breaches sat on already-Done Features, which threatened to flatten the KPI RAG. In scope, the balance flips — **23 of 33** Full Cycle Time breaches are on *open* Features. The KPI RAG will therefore be live and responsive whichever scope option you choose, which makes that decision much lower-risk. Coverage is the bigger constraint now: only about a third of in-scope Features have the transition history needed to compute each KPI at all.

#### 6.3.6 KPI RAG bands (confirmed)

Each Feature is banded per KPI against its SLA. Amber is the **20% approach zone** below the target:

| KPI | SLA | 🟢 Green | 🟠 Amber (within 20% of target) | 🔴 Red |
|---|---|---|---|---|
| Full Cycle Time | 150 days | < 120 days | 120–150 days | > 150 days |
| Delivery Predictability | 90 days | < 72 days | 72–90 days | > 90 days |
| Delivery Cycle Time | 90 days | < 72 days | 72–90 days | > 90 days |

- **Red = the KPI has failed** (elapsed days exceed the SLA).
- **Amber = within 20% of the target** — i.e. between 80% and 100% of the SLA consumed. An early warning that the SLA is about to be missed, which for an open Feature it will be unless it lands.
- **Green = anything better than the Amber zone.**

Because the open-item convention uses `NOW()` (6.3.1), an open Feature migrates Green → Amber → Red on its own as time passes, with roughly 30 days' warning on Full Cycle Time and 18 on the two 90-day KPIs.

`[PROVIDE]` One conversion still needed: these bands are **per Feature per KPI**, but Section 7 needs a 0–100% figure for the 30% KPI weighting. Proposal, consistent with the Flow mapping in 6.2.6: Green = 100, Amber = 70, Red = 20; take the mean across a Capability's in-scope Features for each KPI, then the mean of the three KPIs. Confirm or replace.

#### 6.3.7 Open questions — `[PROVIDE]`

1. **Scope: which Features count toward the KPI RAG?** This is the most consequential open item in this section. Breaches are overwhelmingly **historical**: of 499 Full Cycle Time breaches, 456 are on Features already Done. If the KPI RAG includes all-time completed work, it will be dominated by years-old delivery and will barely move week to week — and the trend view (Section 9) becomes meaningless. Options: (a) open Features only, (b) open plus Features completed within the current DI, (c) all Features ever. Proposal: **(b)**.
2. **Green/Amber/Red thresholds.** The SLAs give a binary pass/fail per Feature; the RAG needs bands. Proposal: score each KPI as % of in-scope Features within SLA, then apply the standard 85% / 60% bands from Section 7, and average the three KPIs equally within the 30% KPI weighting. **Confirm or replace.**
3. **Does the clock stop?** Two cases the definitions don't address:
   - **Blocked time.** Should days spent in Blocked be excluded from elapsed time? A Feature blocked for 60 days on an external dependency currently breaches the same as one that simply ran slow — and Section 8 already penalises Blocked separately, so counting it here may double-penalise.
   - **Backward transitions.** 25 Features currently sitting in **Funnel** are Full Cycle Time breaches — they entered In Analysis, went backwards, and the clock kept running. Correct behaviour, or should the clock reset?
4. **Cancelled Features.** Excluded from KPIs entirely, or measured to completion of cancellation? Proposal: exclude.
5. **Missing start dates.** Around 63% of in-scope Features have no In Analysis date, so Full Cycle Time is not computable for them. Are these excluded from the KPI denominator, or is a missing KPI-critical date itself a Data Quality defect (Rule Set 3 currently covers Delivery Increment and target dates, not these)? Proposal: **both** — exclude from the KPI, flag in DQ.

> Note: rubric may differ by level — flag if so. Confirmed: Data Quality, Flow Throughput, and KPIs are measured at **Feature level**, then roll up to Capability, Release, and EPIC (see Section 7).

---

## 7. Roll-up Logic (confirmed)

**Confirmed approach:** Weighted aggregate (not worst-of-three).

**Confirmed roll-up chain:** Data Quality / Flow Throughput / KPIs are measured at Feature level → roll up to **Capability** RAG (shown in Release Manager view) → roll up to **Release** RAG (shown in Delivery Manager view) → roll up to **EPIC** RAG (shown in SLT view). Feature is the base of the chain; there is no Story tier beneath it.

**Confirmed weighting across the three health checks:**
| Health Check | Weight |
|---|---|
| Data Quality | 30% |
| Flow Throughput | 40% |
| KPIs | 30% |

**Confirmed score → RAG conversion:**
| Score | RAG |
|---|---|
| ≥ 85% | 🟢 Green |
| ≥ 60% and < 85% | 🟠 Amber |
| < 60% | 🔴 Red |

### 7.1 Single-attribution principle (confirmed)

**Nothing is penalised twice.** Where one underlying problem would otherwise register against more than one health check, it is counted **once**, against the highest-priority category:

| Priority | Category | Weighting |
|---|---|---|
| **1** | **Impact on Delivery** — Blocked items, the Section 4.5 High Risk overrun, and Flow Throughput stagnation | 40% (Flow Throughput) plus the Section 8.3 penalties |
| **2** | **KPIs** — the three SLA measures in 6.3 | 30% |
| **3** | **Data Quality** — the five rule sets in 6.1 | 30% |

Note the weighting already reflects this order (40 > 30 = 30), so the precedence and the weights are consistent rather than competing.

**Worked consequences already applied in this document:**
- A **Blocked** Feature is a delivery impact, so its stagnation clock freezes (6.2.5) — it is not additionally penalised for not moving.
- A Feature that is both **static and overrunning** (4.5) is penalised once, under the higher of the two.
- A Feature failing a **KPI** because a required date is missing is a Data Quality defect *or* a KPI failure, not both.

`[PROVIDE / DECIDE IN PLANNING]` The exact de-duplication mechanics — how the engine detects that two findings share one root cause, and whether the lower-priority finding is suppressed entirely or reported without scoring. Agreed to settle during Plan Mode; the principle and the ordering above are fixed.

#### 7.1.1 Reporting consequence — score and defect count must both be shown (confirmed)

Single attribution has a side effect worth designing around rather than discovering in a review meeting.

**Data Quality sits third in the precedence order.** Any defect that is *also* a delivery impact is attributed to Delivery and therefore **drops out of the Data Quality score**. Because Data Quality is 30% of the overall RAG, the DQ score will read **better than the cleanup checklist implies** — potentially an amber-or-green DQ sitting next to a long list of defects. That is arithmetically correct and consistent with 7.1, but it looks wrong, and the first person to notice will assume the tool is broken.

**Requirements to prevent that:**

1. **Every view that shows a Data Quality RAG must show the Data Quality defect count next to it** — SLT per EPIC, Delivery Manager per Release, Release Manager per Capability. The score answers "how healthy is the data"; the count answers "how much work is there to do". They are different questions and both are needed.
2. **Suppressed defects remain visible in the cleanup checklist**, marked with the category they were attributed to (e.g. *"scored under Delivery Impact"*). Nothing is hidden — only the *scoring* is de-duplicated, never the reporting.
3. **The checklist header carries a reconciliation line**: total defects found, how many scored under Data Quality, and how many were attributed to a higher-priority category. This makes the gap between score and count self-explaining, so nobody has to ask.

**Why this matters beyond presentation:** without it, the remedial email drafting (11.3) would summarise an EPIC as data-quality-healthy while its checklist runs to dozens of rows, and the Conversational Q&A (11.2) would give contradictory answers depending on whether the question was phrased about scores or defects.

`[PROVIDE]` Should the same treatment apply in reverse — i.e. does the Delivery Impact reporting need to flag which of its items were *promoted* from Data Quality or KPI findings? (Recommendation: yes, same reconciliation logic, low extra cost once the attribution is tracked.)

### 7.2 Roll-up weighting (confirmed)

**The 30/40/30 health-check weighting and the 85% / 60% RAG bands apply unchanged at every level** — Feature, Capability, Release and EPIC. There is no separate rubric higher up the tree.

**Each child is weighted by simple count share.** A parent's score is the mean of its children's scores: *n* children means each contributes **1/n**, so 10 children are worth 10% each, 4 children 25% each. No weighting by size, effort or priority — those fields do not exist in the data, and count share is the only weighting the source supports.

The roll-up is a strict tree, since a Capability belongs to exactly one Release by rule (3.1, Rule Set 1 Part C):

```
Feature score  →  mean per Capability  →  mean per Release  →  mean per EPIC
```

**Worked example.** 10 Capabilities, each with 10 Features (100 Features total). Two Features in one Capability are in trouble:
- That Capability: 8 healthy + 2 failing → **20% of the Capability is impacted**
- The Release: one of ten Capabilities partially impacted → roughly **2% of total work**
- Weighted health score: **≈ 98% → 🟢 Green**

### 7.3 Delivery-impact override — "late is still late" (confirmed)

**The arithmetic above is necessary but not sufficient, and on its own it is misleading.** In the worked example the Release scores 98% and reads Green — yet if those two Features do not land, **the Release is late**. Percentage completion says nothing about whether a date will be met. Count-weighted aggregation is designed to dilute outliers, which is exactly the wrong behaviour when the outlier is the thing that makes the Release miss.

**Every row therefore reports two values, and the RAG is the worse of them:**

| Output | What it measures | How it is derived |
|---|---|---|
| **Health score** | *How much* of the work is healthy | Count-weighted roll-up per 7.2, banded at 85% / 60% |
| **Delivery status** | *Whether the date will be met* | Date logic — is any child jeopardising the parent's committed date? Not proportional, not diluted |
| **Reported RAG** | **The worse of the two** | A row can never show Green while its delivery status is at risk or late |

**Delivery status derivation:**

| Status | Condition |
|---|---|
| 🟢 **On track** | No child jeopardises the parent's committed date |
| 🟠 **At risk** | At least one child is projected to miss the parent's committed date — a Feature at HIGH ALERT / Priority Risk, a High Risk overrun (4.5), or a Blocked item (Section 8) whose parent date falls within the block window |
| 🔴 **Late** | The parent's committed date has passed, or will pass, with at least one child not Done. For a **Release** the committed date is its **Release Date**; for a **Capability** it is its **DI end date** |

**This is the mechanism that makes Section 7.1's precedence real.** Delivery Impact ranks first not merely in attribution but in presentation: it can override a healthy score, whereas a healthy score can never suppress a delivery problem. It is also what stops the mandatory callouts (8.2) contradicting the RAG beside them — a Release with a blocked item listed above it will no longer read Green.

**Applied to the worked example:** health score 98% (Green), delivery status Late (two Features will not land before the Release Date) → **reported RAG: Red.** The 98% is still shown, because it correctly tells the reader that almost all the work is done and the problem is narrow — which is a different remedial conversation from a Release that is 60% complete.

**Confirmed parameters:**

1. **"At risk" caps the RAG at 🟠 Amber.** Red is reserved for a date that has actually been missed, or that cannot now be met. This keeps the two states meaningfully different: Amber means *act now and the date is still recoverable*; Red means *the date is gone*.
2. **The projection horizon is 30 days.** A parent is At risk when its committed date falls **within the next 30 days** and at least one child is not on course to complete by it. Beyond 30 days, no delivery-status flag is raised — the health score alone carries the signal. This keeps the At risk list short and actionable rather than a standing list of everything due this quarter.

`[PROVIDE]` One detail left: **what if the parent has no committed date?** 48 of 89 Releases have no Release Date, and 77 of 215 post-Backlog Capabilities are missing a Target Date. Delivery status cannot be computed for these. Recommendation: report **Unassessed** on delivery status (per 3.2.3) and rely on the health score alone, with the missing date flagged by Rule Set 1 Part B / Rule Set 3 — **never default a missing date to "On track"**, which would silently hide the riskiest rows in the estate. This should become rare as the 6.1.4 compliance target is met.

---

## 8. Blocked Status & Risk Escalation

**Applies to:** Capabilities and Features (not EPICs or Releases directly — they inherit blocked status via cascade below). Features are the lowest level at which a Blocked status is recorded, as there is no Story tier.

### 8.1 Cascade Rule (confirmed)
Blocked status cascades upward:
- Feature Blocked → parent Capability is treated as Blocked.
- Capability Blocked → **the parent Release is impacted.** A blocked item has a direct impact on the Release occurring, so the cascade continues to Release level and is reflected in the Release's own status, not merely as a callout.

`[PROVIDE]` Does the cascade continue one further step to **EPIC** status, or does it stop at Release and appear at EPIC level only as the mandatory callout (8.2)? Working assumption: stops at Release, since an EPIC typically spans several Releases and one blocked item should not turn an entire EPIC's status.

### 8.2 Mandatory Callout (confirmed)
Blocked items are risk in themselves and must be **specifically called out as their own line item** at every viewer level — not just folded into an aggregate RAG:
- SLT view: blocked items called out per EPIC.
- Delivery Manager view: blocked items called out per Release.
- Release Manager view: blocked items called out per Capability.

### 8.3 Risk Scoring Impact (confirmed)
Being blocked increases risk (reduces score), with the penalty scaling by how far into the Delivery Increment the item is blocked:

| Timing within Delivery Increment | Penalty per blocked item |
|---|---|
| Early | −2% |
| Mid | −5% |
| Late | −10% |

`[PROVIDE]` Exact boundaries for "early / mid / late" within a DI (e.g. by elapsed % of the quarter, or fixed calendar splits like month 1 / month 2 / month 3) — needed to implement this precisely.

### 8.4 Pre-Delivery-Increment Exception (confirmed)
If an item is blocked **before** its Delivery Increment has started (e.g. blocked on 13/03/2026 for a DI starting 01/04/2026), this has **no RAG/score impact** — it is surfaced only as a **Warning** label, distinct from the RAG status.

### 8.5 Week-over-Week Persistence Escalation (confirmed)

**Expectation: a blocked item is resolved within the week.** A Feature or Capability that is Blocked should **not appear on the following week's report**. Blocked items are the immediate action list, and clearing them is the point of surfacing them.

**Failing to clear a block is itself the issue** — it signals the block is not being worked, not merely that the work is stuck. Persistence therefore escalates through four stages, one per consecutive weekly upload:

| Consecutive weeks blocked | Stage | Meaning |
|---|---|---|
| **Week 1** (first appearance) | **FLAGGED** | Newly blocked. Surfaced for immediate action; expected to clear before the next upload |
| **Week 2** | **WARNING** | Not cleared within seven days. The block is not being actioned at the pace expected |
| **Week 3** | **PRIORITY** | Sustained block. Requires deliberate intervention, not just visibility |
| **Week 4 and beyond** | **ESCALATE** | The block has consumed a month. Treated as an escalation item in its own right |

**Week 4 is the ceiling** — an item blocked for ten weeks remains at ESCALATE, but its consecutive-weeks count keeps incrementing and must be displayed, so a ten-week block is never visually identical to a four-week one.

Implementation requirements:
- **Week-over-week comparison** of the blocked set. The retained weekly history (Section 9) is a hard dependency, not a trend nicety. The 11-week retention comfortably covers a four-stage ladder.
- Each blocked item carries a **consecutive weeks blocked** counter and its current stage, both surfaced in the callout at every viewer level.
- Items are **ordered by stage, descending** — ESCALATE first, then PRIORITY, WARNING, FLAGGED — above all other risk items, per the Section 7.1 precedence that puts delivery impact first.
- A **week** means one weekly upload cycle, not seven calendar days, so a missed or late upload must not silently advance or reset the ladder.

**Naming note:** `[PROVIDE]` the first stage was described as a "late flag", but **"Late" is already an established and unrelated state** in this document — the Section 4.5 DI overrun label. Two different meanings for one word across two sections will cause confusion in both the UI and the code. Written here as **FLAGGED**; confirm, or supply an alternative that doesn't collide with 4.5.

`[PROVIDE]` **Score behaviour across the ladder.** Two workable models:
- **(a) Reporting-only** — the Section 8.3 penalty is set once by DI position at the moment of blocking and stays flat; the ladder purely drives visibility and ordering.
- **(b) Escalating penalty** — the penalty grows with the stage, e.g. FLAGGED −2%, WARNING −5%, PRIORITY −10%, ESCALATE −15%, superseding the flat 8.3 figure for persistent blocks.

*(b) is arguably more truthful — a four-week block genuinely is a bigger delivery risk than a one-week one, and escalating within a single category does not breach the Section 7.1 no-double-penalty rule, which governs attribution across categories. But it does mean an EPIC's score can decline week on week with no change in the underlying data, which needs to be understood before it is seen. Recommendation: (b).*

`[PROVIDE]` **Two further behaviours:**
- **Re-blocking.** If an item clears and is later blocked again, does the counter reset to week 1 or resume? Recommendation: **reset**, but retain a "previously blocked" marker so repeat offenders are visible.
- **What ESCALATE triggers.** Since the model holds no personal data (11.3), escalation cannot route to an individual. Recommendation: an ESCALATE item appears as a named line in the **SLT view** regardless of which EPIC it sits under, and automatically populates that EPIC's remedial email draft (11.3).

---

## 9. Trend vs Snapshot

Both required, at every viewer level:
- **Snapshot:** current week's RAG per row (EPIC / Release / Item as applicable).
- **Trend:** movement over time (e.g. was Amber last week, now Red). Needs to show direction of travel, not just current state.

**Retention: 11 weeks (confirmed).** Eleven weekly snapshots are retained, giving eleven trend data points — a rolling quarter plus a fortnight.

**Critical distinction — two different retentions.** The 11-week limit applies to **weekly snapshot history**, not to the current-state baseline. Because uploads are deltas (Section 13), an item that has not changed for six months appears in no recent delta; its record must persist in the baseline indefinitely. Ageing the baseline out at 11 weeks would silently delete long-lived work. **Retain: the full current-state baseline for all in-scope items, plus 11 weeks of weekly RAG/score snapshots.**

**Week-over-week comparison is a hard requirement, not just a visual.** Section 8.5's blocked-persistence escalation depends on comparing this week's blocked set to last week's, so at minimum the previous week's state must always be queryable.

Open questions to resolve in Plan Mode:
- Trend shown per health check individually, or only on the overall RAG?
- Visual treatment for trend (sparkline, arrow indicator, RAG-over-time strip)?
- What is shown for a row with fewer than 11 weeks of history (new EPICs, or the first 11 weeks after go-live)?

---

## 10. Navigation

- Three entry views (SLT / Delivery Manager / Release Manager) but shared underlying data model.
- Drill-down: SLT → click EPIC → Delivery Manager view for that EPIC → click Release → Release Manager view for that Release.
- Selectors for EPIC and Release must be available independent of drill-down (i.e. jump straight to a Delivery Manager or Release Manager view without going through SLT first).

---

## 11. Agentic AI Features

### 11.1 Agent Transparency Panel
An area of the dashboard showing which agentic agents are active and what each is doing in processing the weekly data (e.g. a "Data Quality Agent", "Throughput Agent", "KPI Agent" — naming TBD once agent architecture is decided in Plan Mode). Should give the user visibility into how the RAG statuses were derived, not just the end result.

- `[PROVIDE / DECIDE IN PLANNING]` What level of detail is shown per agent (status only, e.g. "last run 09:00 Mon", vs. reasoning/log output)?
- `[PROVIDE / DECIDE IN PLANNING]` Is this panel global (one list of agents) or shown per-view (agents relevant to EPIC/Release/Item level)?

### 11.2 Conversational Q&A (Chat Function)
A chat interface allowing the user to ask free-text questions about the data — EPICs, trends, KPIs, etc. — and get answers grounded in the uploaded dataset.

- Should be available across all three viewer levels (SLT / Delivery Manager / Release Manager), scoped to whatever EPIC/Release is currently in view.
- `[PROVIDE / DECIDE IN PLANNING]` Should answers cite the underlying data/evidence (e.g. which rows/records support the answer)?
- `[PROVIDE / DECIDE IN PLANNING]` Should chat be able to answer cross-EPIC/trend questions from the SLT view (e.g. "which EPICs went Red this week")?

### 11.3 Automated Remedial Email Drafting
Ability to prepare a draft email **per EPIC** summarising that EPIC's status and any critical remedial actions needed to get the process back on track.

**No personal data (confirmed).** The system holds **no owners, assignees, names or email addresses**, and none will be added to the source data. All attribution and reporting rolls up to **EPIC level only**. Consequences:
- The draft email is generated **per EPIC**, not per person, and carries **no recipient** — the user supplies the addressee themselves when they send it.
- No view, rule, KPI or agent output may reference an individual. Where "owner" appeared in earlier drafts, read "the EPIC".
- Team-level attribution is available via the ART worksheet (Section 3.2) and is the *only* sub-EPIC attribution in the model. `[PROVIDE]` Should remedial drafts reference the ART where one is set, or stay strictly at EPIC level?

- Trigger: `[PROVIDE / DECIDE IN PLANNING]` — on demand per EPIC, or auto-suggested when an EPIC is Red/Amber?
- Content should include: current RAG status (overall + per health check), what's driving it, and recommended remedial actions.
- `[PROVIDE / DECIDE IN PLANNING]` Does the tool send the email directly, or only draft it for the user to review/send?
- `[PROVIDE / DECIDE IN PLANNING]` Source of "critical remedial actions" — agent-generated recommendations, a predefined playbook per RAG driver, or both?

### 11.4 Data Quality & Remediation Agent (confirmed)

Runs on every weekly upload, before RAG computation. Responsibilities:

1. **Validate the upload** — schema check, and for delta uploads reconcile against the retained baseline (Section 13).
2. **Execute the triage rule sets** in Section 6.1 (Rule Sets 1–5, including the date boundary checks in 6.1.5 and the release anomalies in 6.1.6), applying the normalisation table in 6.1.1.
3. **Produce the Immediate Data Cleanup Checklist** in the format defined in 6.1.9.
4. **Emit the Data Quality score** feeding the 30% weighting in Section 7.
5. **Surface itself in the Agent Transparency Panel** (11.1) — last run time, records processed, defects found by tier.

Design notes:
- The agent **proposes fixes, it does not apply them.** Every Rule Set 2 output is a *recommended* status change for a human to action in JIRA; nothing is written back to the source system. This keeps the tool read-only over JIRA and avoids the agent and JIRA fighting over state.
- Rule outputs must be **traceable to the records that triggered them** — the Capability/Feature IDs and field values behind each flag — so a user can dispute a flag. This ties to the evidence requirement in 11.2.
- `[PROVIDE / DECIDE IN PLANNING]` Should this agent's findings also feed the remedial email drafting in 11.3 (i.e. does an EPIC's draft email include its DQ defects alongside its RAG status)?

---

## 12. JIRA Workflows

Status-transition workflows for each work-item type, used to define status logic, Blocked-state detection, and stage groupings referenced throughout this spec (Sections 6.2, 8).

### 12.1 EPIC Workflow (confirmed — from attached diagram)

**States:** Portfolio Funnel, Reviewing, In Analysis, Ready, In Progress, **Done** (terminal), On Hold, **Cancelled** (terminal).

**Forward flow:** Start → Portfolio Funnel → Reviewing → In Analysis → Ready → In Progress → Done

**Backward transitions:**
- Reviewing → Portfolio Funnel
- In Analysis → Reviewing
- In Progress → Ready
- Done → In Progress (reopen)

*(Note: no backward transition shown between In Analysis and Ready — that step is forward-only.)*

**On Hold:**
- Reachable from **any** status via a global `Any → On Hold` transition.
- From On Hold, can transition into any active working status: Portfolio Funnel, Reviewing, In Analysis, Ready, or In Progress.

**Cancelled:**
- Reachable from **any** status via a global `Any → Cancelled` transition.
- Terminal state.

**Confirms Section 6.2 stage definitions:**
| Stage | EPIC Status |
|---|---|
| Time to Scope | Reviewing, In Analysis, Ready |
| Time to Deliver | In Progress |

`[PROVIDE]` Please double-check the backward-transition and On Hold-resume reading above against the live JIRA workflow config — some directions were read off a photographed diagram and are worth a quick sanity check.

### 12.2 Capability Workflow (confirmed — from attached diagram)

**States:** Backlog, In Review, In Analysis, Portfolio Backlog, In Development, In Testing, Ready for Delivery, Blocked, **Done** (terminal), **Cancelled** (terminal).

**Forward flow:** Start → Backlog → In Review → In Analysis → Portfolio Backlog → In Development → In Testing → Ready for Delivery

**Shortcut transition:** In Analysis → In Development directly, bypassing Portfolio Backlog.

**No backward transitions shown** — unlike the EPIC workflow, this flow is forward-only/linear; no loop-back arrows between adjacent states.

**Blocked, Done, Cancelled:** each reachable via a global `Any → ...` transition from any status (not part of the linear flow itself). Done and Cancelled are terminal.

`[PROVIDE]` Please confirm: is Ready for Delivery expected to transition into Done, and is that simply not drawn explicitly because it's already covered by the global `Any → Done` transition?

### 12.3 Feature Workflow (confirmed — from attached diagrams, cross-checked against transition data)

*(Story workflow no longer required — the Story level has been removed from the model, see Section 3.)*

**States (15):** Funnel, In Analysis, PI Backlog, PI Planning, Committed, In Development, Dev Complete, In Testing, Test Complete, Deploying, Deployment Complete, Releasing, Done, Blocked, Cancelled.

**Forward flow:**
Start → Funnel → In Analysis → PI Backlog → PI Planning → Committed → In Development → Dev Complete → In Testing → Test Complete → Deploying → Deployment Complete → Releasing → Done

**Backward transitions — every adjacent pair is bidirectional.** Unlike the Capability workflow (12.2, forward-only), each state can step back to its immediate predecessor:
| Backward transition | Backward transition |
|---|---|
| In Analysis → Funnel | Test Complete → In Testing |
| PI Backlog → In Analysis | Deploying → Test Complete |
| PI Planning → PI Backlog | Deployment Complete → Deploying |
| Committed → PI Planning | Releasing → Deployment Complete |
| In Development → Committed | Done → Releasing (reopen) |
| Dev Complete → In Development | |
| In Testing → Dev Complete | |

**Shortcut transitions to Done:** two states can jump straight to Done, bypassing the deployment chain:
- Dev Complete → Done
- Test Complete → Done

**Blocked:**
- Reachable from **any** status via a global `Any → Blocked` transition.
- From Blocked, can resume into **any** active working status (Funnel, In Analysis, PI Backlog, PI Planning, Committed, In Development, Dev Complete, In Testing, Test Complete, Deploying, Deployment Complete, Releasing) — same pattern as On Hold in the EPIC workflow (12.1).
- Not terminal.

**Cancelled:**
- Reachable from **any** status via a global `Any → Cancelled` transition.
- Terminal in intent (no outbound transitions drawn).

**Done:**
- Also reachable from **any** status via a global `Any → Done` transition, in addition to the flow and shortcut routes above.
- Reversible via Done → Releasing (reopen), so **not strictly terminal** for state-machine purposes, even though Section 4.4 treats Done as an exclusion for DI-alignment checks.

**Implementation notes (verified against the extract's Feature transition history):**
- Every transition above is present in the real data, including all twelve backward edges, both `→ Done` shortcuts, and Blocked resuming into ten different active statuses. The diagram and the data agree — no reconciliation needed.
- Because `Any → Blocked` and `Any → Done` are truly global, the data contains transitions **out of the nominally terminal states** (Done → Blocked, Cancelled → Blocked). The parser must tolerate these rather than assuming Done/Cancelled are absorbing states.
- **Legacy/retired statuses appear in historical transitions** and must not crash the parser or be treated as unknown-status data quality issues: Backlog, Deferred, Dev Preparation, Draft, In Review, Ready for Delivery, Release train backlog. None of these is the current status of any live Feature — they only occur in older history.
- Blocked-entry timestamps for the Section 8.3 / 8.4 penalty timing come from `Any → Blocked` transition rows. Note that in the current extract only some Features whose *present* status is Blocked have a corresponding `→ Blocked` transition row, so the model needs a defined fallback for a Blocked item with no dateable block event (see Section 14, Section 8).

`[PROVIDE]` Nothing outstanding on the workflow itself — flag only if the live JIRA config has since added states beyond the 15 above.

---

## 13. Weekly Data Input

**Upload model (confirmed):** the **first upload is a full data dump**; **every subsequent weekly upload is a delta** containing only records that **changed in the preceding 7 days**. An item that has not changed is **excluded from the file entirely** — absence means unchanged, never deleted.

This makes the system stateful — the retained baseline, not the uploaded file, is the source of truth for any given week. Implications the architecture must handle:

- **Persistent baseline.** The full dump establishes the baseline; each delta is applied on top of it to produce that week's state. Every weekly state must be retained, both because Section 9 requires trend history and because a bad delta needs to be reversible.
- **Upsert by key (confirmed).** Records are matched on their key (EPICKEY / CapKEY / FeatureKEY). A key present in the delta updates the baseline record; a key absent from the delta means **unchanged**, not deleted.
- **Transition rows are append-only.** The initial dump supplies full history; each delta is expected to carry only transitions from the preceding 7 days, which accumulate onto the baseline. Flow Throughput (6.2) and the derived KPI dates (6.3.3) therefore read from the accumulated baseline history, never from a single week's file. `[PROVIDE]` Confirm deltas carry only *new* transition rows rather than the full history for each changed item — if the latter, the loader must de-duplicate rather than append.
- **Baseline never ages out.** See Section 9: the 11-week retention applies to weekly snapshots only. The current-state baseline persists for as long as an item is in scope, because a delta-based feed will not re-send an unchanged item.
- **Delta integrity checks** (new Rule Set candidate for the 11.4 agent): a delta referencing a parent key absent from the baseline, or introducing a Capability/Feature with no parent, should be flagged rather than silently dropped.

**Confirmed additions to the next export (single consolidated file):**

| Addition | Purpose | Status |
|---|---|---|
| **Title** for EPIC, Capability and Feature | Views would otherwise render bare JIRA keys (`RN-42135`), unusable for an SLT audience. Required for all dashboards, the cleanup checklist, the SLA breach report and the remedial email drafts | ✅ **Delivered** — 100% populated at all three levels |
| **Feature Created date** | Provides a clock anchor for Features with no transition history (6.2.8) and enables the Ageing Backlog measure (6.2.9) | ✅ **Delivered** — 100% populated |

**Confirmed column and sheet names (see 3.2.1a):** titles are `EPIC.Portfolio Epic`, `Capabilities.Capability`, `Features.Feature` — **not** "Summary" — and the `Capability` sheet is now **`Capabilities`**. Both must be mapped explicitly in the loader; both would fail silently against the previous names. The loader must **fail loudly if a title column is absent** rather than falling back to displaying keys.

*(Note: `EPIC_Releases.xlsx` also carries a `Summary` column for the EPICs and Capabilities it covers. The main extract is now the authoritative title source; the release export's Summary should be ignored to avoid two divergent title fields.)*

**Explicitly out of scope: personal data.** No owner, assignee, or name fields are to be included in any export. All reporting rolls up to EPIC level (see 11.3), with ART as the only team-level attribution.

### 13.1 No deletion — terminal states and re-parenting (confirmed)

**There is no deletion capability.** No item is ever removed from the source system. Every EPIC, Capability and Feature is in exactly one of three conditions:

| Condition | Meaning |
|---|---|
| **Done** | Completed. Terminal for reporting purposes (though the workflows in Section 12 permit reopening) |
| **Cancelled** | Abandoned. **This is the only "removal" signal in the model** — a Cancelled item is the equivalent of a deletion and should be treated as such by the RAG logic, per the existing exclusions in 4.4 |
| **In progress** | Any other status, including movement *backwards* to Backlog or Funnel — a regression is still an in-progress item, not a removal |

**Consequences for the loader:**
- **Never infer deletion from absence.** An item missing from a delta is unchanged, full stop. There is no case in which absence means "gone".
- **Cancelled is a status change like any other**, arriving as a normal delta row. It does not require special handling on ingestion — only in the scoring rules, which already exclude Cancelled items (4.4).
- **Regression to Backlog or Funnel is a legitimate change** and will appear in the delta. The item stays in the dataset and stays scored; it does not become dormant. Note this interacts with Flow Throughput — a backward transition is activity but not progress and does not reset the stagnation clock (6.2.4).

**Re-parenting is a change event (confirmed).** If an item's parent changes — e.g. a Feature's parent key becomes a different Capability — that item **is included in the weekly delta**. This makes the hierarchy mutable between uploads, with two implications:

1. **Scope must be re-evaluated on every upload, not once at go-live.** Because scope is defined by the parent chain (Section 3.2), a re-parent can move an item **into** scope (new parent is an in-scope Capability) or **out of** scope (new parent is not). The scope filter is a per-upload operation applied to the accumulated baseline, never a one-time classification stored against the record.
2. **An item leaving scope is the one case that resembles a deletion** — and it must not be handled as one. Retain the record, mark it out of scope, stop scoring it, and stop showing it in the views. Hard-deleting it would corrupt the retained history, since it contributed to earlier weeks' scores.

`[PROVIDE]` **Snapshot immutability.** When a Feature moves from Capability A to Capability B, are the previous weeks' snapshots restated to reflect the new parent, or left as they were recorded? Recommendation: **leave them** — snapshots are immutable records of what was true that week, and re-parenting applies from the current week forward. Restating history would make trend lines move retrospectively, which defeats the purpose of a trend.

`[PROVIDE]` **A key-prefix question this raises.** The example given used a parent key of the form **`FCB-nnnn`**. Section 3.2 records EPIC and Capability keys as **always FCM or RN**, confirmed earlier, and no FCB keys appear anywhere in the current extracts. Is `FCB` a third valid Fixed Connectivity prefix that must be added to the scope filter, or was it shorthand for FCM? This matters directly: if FCB is real and the filter omits it, that work is silently dropped from every view. Note the two Capabilities already breaking the prefix rule (`PPEP-13349`, `PPEP-31932`) make this more than hypothetical.

### 13.2 Key mutability and re-keying (confirmed — highest implementation risk)

**Item keys change.** Reassociating an item with a Backlog parent re-keys it:

| Event | What is re-keyed | What is not |
|---|---|---|
| **Capability reassociated with a Backlog EPIC** | The **Capability** gets a new **`FCB`** key | Its child **Features keep** their existing FCM / RN / other keys — but their `CapKey` parent pointer must change to the new FCB Capability key |
| **Feature reassociated with a Backlog Capability** | The **Feature** gets a new **`FCB`** key | Its parent Capability is unaffected |

**Why this cannot be handled by upsert-by-key alone.** Two failures occur simultaneously, and the second is the dangerous one:

1. **A reset duplicate.** The item arrives under its new key with no prior record, so the loader creates a fresh row. Its stagnation clock resets (6.2.1), its derived KPI start dates are lost (6.3.3), its blocked persistence count resets (8.5), and its trend line starts from zero.
2. **A scored phantom.** Under the no-deletion model (13.1), the *old* key simply stops appearing in deltas — and **absence means unchanged**. The old record therefore persists in the baseline indefinitely, still in scope, still scored, and never updated again. Its stagnation clock runs unchecked to HIGH ALERT and its KPI clocks accrue against `NOW()` forever.

The net effect is that **one item becomes two, both counted**, and the phantom's health decays permanently. Left unhandled, the estate silently inflates with phantoms week on week and every RAG drifts pessimistic — a failure mode that looks like deteriorating delivery rather than a data defect.

#### 13.2.1 Required handling

**Preferred: an explicit re-key mapping in the weekly file.** `[PROVIDE]` Please request a small additional sheet — `Re-keys`, with columns `Old Key`, `New Key`, `Date changed`, `Level` — covering any key changed in the preceding 7 days. This is the only fully reliable solution: it lets the loader merge the new key onto the existing record, preserving clocks, KPI dates, blocked counts and trend history, with no guessing.

**Fallback if no mapping can be supplied: title-based matching.** Now that titles are 100% populated (3.2.1a), a re-key is detectable by fingerprint. Viability in the current extract:

| Level | Title uniqueness |
|---|---|
| Capability | **410 of 410 titles distinct** — a title is a reliable identifier |
| Feature | 2,659 distinct titles across 2,714 rows (55 duplicates); **title + Created date gives 2,701 distinct groups** — near-unique |

Proposed fallback algorithm, per upload:
1. Identify candidate re-keys: a new `FCB-` key appearing for the first time whose **title** (and, for Features, **Created date**) matches an existing baseline record.
2. **Corroborate with a second signal** before merging — for a Capability, its child Feature set should be largely unchanged; for a Feature, its `Created` date must match exactly.
3. **Quarantine rather than auto-merge on a weak match.** Report probable re-keys in the cleanup checklist for confirmation, and hold scoring for the pair until resolved. A wrong merge is harder to unpick than a flagged duplicate.

**Detect the phantom directly as well**, independent of matching: an in-scope record that has received **no delta update for N consecutive weeks while its parent or children have changed** is a re-key candidate. A Capability that abruptly has zero Features while a new FCB Capability appears with that same Feature set is the clearest single signature. `[PROVIDE]` Confirm a value for N — recommendation: **4 weeks**, aligning with the 8.5 escalation ceiling.

#### 13.2.2 Open questions — `[PROVIDE]`

1. **Is re-keying reversible?** When an EPIC leaves Backlog, does its `FCB` Capability revert to an `FCM` / `RN` key? If so, an item can be re-keyed repeatedly, and matching must handle FCB → FCM as well as FCM → FCB.
2. **Do Features revert their original prefix?** A Feature re-keyed from `DXL-` to `FCB-` — does it return to `DXL-` when its Capability leaves Backlog, or keep `FCB-`?
3. **Are historical transitions carried across the re-key?** After the change, does the `Transitions` sheet report that item's history under the new key, the old key, or split across both? This determines whether the transition history has to be re-keyed too — and it directly drives Flow Throughput and the derived KPI dates.
4. **Snapshot treatment.** Consistent with 13.1, prior weeks' snapshots stay as recorded under the old key. Confirm — the alternative (restating history under the new key) would make trend lines move retrospectively.

`[PROVIDE]` Still needed on the input:
- **Source system** — confirmed as a JIRA export? Which report/JQL produces it?
- **File format** — the initial dump is `.xlsx` with one sheet per level plus transition history. Will deltas use the identical sheet/column structure? *(Strongly recommended — divergent schemas between full and delta uploads are a common failure mode.)*
- ~~Deletions and cancellations~~ — **resolved, see 13.1.**
- **Transition history in deltas.** Does each delta carry only new transition rows since the last upload, or the full history for any changed item? This matters for Flow Throughput (6.2), which needs the complete transition timeline per Feature.
- **Upload mechanism** — manual upload, watched folder, or API.
- **Re-baselining.** Is there a periodic full refresh (e.g. quarterly) to correct baseline drift, or is the initial dump the only full load ever?
- **The Release entity — now sourced** from a second workbook, `EPIC_Releases.xlsx` (sheets: `EPIC Releases`, `Capability Releases`, `ALL UNRELEASED`). See Section 3.1 for the model and its three limitations: releases identified by name with duplicates, released versions absent, and a Capability scope mismatch against the main extract. Remaining questions: will the weekly upload be **two files or one consolidated workbook**, and do the release sheets follow the same full-then-delta convention?
- Definition of "Item" — *superseded: the hierarchy in Section 3 (EPIC → Release → Capability → Feature) defines the work-item types in scope, with Feature as the leaf.*

---

## 14. Open Questions / Assumptions Log

*Consolidated from every `[PROVIDE]` / open item across this document, grouped by source section. Tick off as each is resolved — when you answer one, the corresponding section above will be updated to match.*

**Section 4 — Delivery Increment**
- [x] 4.3 / 6.1.5: **DI-alignment contradiction resolved** — Section 4.3 is authoritative (Capability's own quarter or exactly one earlier); Rule Set 4's DI misalignment check is retired.
- [x] 4.5: **Late label confirmed as non-impacting** — flagged on the Feature, excluded from RAG and score, because the parent Capability's DI end date still provides slack.
- [x] 4.5: **High Risk escalation confirmed** — one calendar month's grace after the Late trigger, then it becomes a reportable risk with score impact and a mandatory callout.
- [ ] 4.5: **Penalty size for High Risk** — proposal −5% per High Risk Feature on the parent Capability's score (mirroring 8.3), and whether it escalates further over time.
- [ ] 4.5: If the Feature is still undelivered at the **Capability's own DI end date**, is that handled by the Capability's own DI/Release logic (4.2, 6.1.5) rather than a third escalation step?
- [x] 7.1.1: **DQ score vs defect count** — *confirmed: every view shows the DQ defect count alongside the DQ RAG; suppressed defects stay in the checklist marked with their scoring attribution; checklist header carries a reconciliation line.*
- [ ] 7.1.1: Should Delivery Impact reporting also flag which items were *promoted* from DQ/KPI findings? (Recommendation: yes.)
- [x] 4.5 / 7.1: **Nothing is penalised twice** — *confirmed, with precedence Delivery Impact → KPIs → Data Quality (new Section 7.1). De-duplication mechanics to be settled in Plan Mode.*
- [ ] 4.5: Confirm the trigger date is **01/04/2026** — the first day of FY26/27 Q1 per the confirmed calendar in Section 4. Your examples have twice written 01/04/2025, which is in FY25/26 Q1, two years before the Capability's quarter.

**Section 15 — Non-negotiables**
- [x] **Section 15 written** — *determinism, reproducibility with rule-set versioning, low-confidence flagging, evidence traceability, read-only, no personal data, missing-data-never-Green, reporting never suppressed; 30-second load, Monday 09:00 arrival; configuration-over-hardcoding for portability; PoC boundaries recorded.*
- [ ] 15.1(3): Confirm the low-confidence threshold — recommendation: **below 50% of children contributing**.
- [ ] 15.2: Confirm the processing deadline — recommendation: **dashboard current by 09:30 Monday**.

**Section 3 — Scope & Join Model**
- [x] Scope — *confirmed: Fixed Connectivity only; fully-connected FCM/RN EPIC → Capability → Feature chain. Standalone Capabilities and Features are excluded, not flagged as defects.*
- [x] Join map — *confirmed and documented in 3.2.1.*
- [ ] 3.2.3: How do the **43 in-scope EPICs with no Capabilities** and **217 Capabilities with no Features** render — "No data", a fourth Unassessed state, or omitted? (Recommendation: Unassessed, reported separately from RAG counts.)
- [ ] 3.2.3: Report out-of-scope exclusion counts in the Agent Transparency Panel? (Recommendation: yes, count only.)
- [x] Missing titles / owners — *resolved: titles being added (13); owners deliberately excluded (11.3).*

**Section 6 — RAG Rubric**
- [x] 6.1 Data Quality: rule set **provided** — triage Rule Sets 1–3, severity model, and required checklist output now specified in 6.1.
- [x] 6.1.1: **"In Delivery" defined** — *Capability: In Development / In Testing / Ready for Delivery. Feature: every status after Committed. Committed itself is excluded, which also confirms it does not count as "In Dev" for Rule A.*
- [x] 6.1.3: **Blocked children confirmed** — *a Blocked child blocks Rules C/D/E from firing; the Capability is reported as Blocked instead.*
- [ ] 6.1.1: Confirm the remaining ⚠ mappings — Reviewing → In Review, and which Feature statuses roll into the narrower In Dev / Testing / Deploying bands used by Rules A–D.
- [ ] 6.1.3: Confirm Rule D's required fix resolves to **Ready for Delivery** (since "In Delivery" is a three-status set as a condition but must be one status as a fix).
- [ ] 6.1.3: Confirm rule precedence E → D → C → A → B where rules overlap.
- [ ] 6.1.7: Seven open questions on rule scope — unreferenced Feature statuses (Committed, Dev Complete, Test Complete, Releasing, etc.), Blocked children in "ALL child" conditions, the non-existent Feature status "Reviewing" in Rule B, Rule B's narrower early-status set, Capabilities with zero child Features, Part A severity when DI is absent, and the DQ score → RAG conversion.
- [ ] 6.1.9: Checklist delivery format, and whether defect age is tracked across weeks.
- [x] 6.2 Flow Throughput: **formula provided** — two-phase stagnation ladder (Scoping 10/20 days; Delivery 10/20/30 days), 60-day Scoping phase budget, Blocked callout, and Feature → Capability roll-up.
- [x] 6.2.5 / 8.1 / 8.5: **Blocked semantics confirmed** — Blocked overrides and freezes the stagnation clock and the 4.5 ladder; KPI clocks keep running; cascade continues to Release; a still-blocked item next week escalates to High Priority.
- [ ] 8.1: Does the blocked cascade continue from Release to **EPIC** status, or stop at Release? (Working assumption: stops at Release.)
- [x] 8.5: **Four-stage persistence ladder confirmed** — *FLAGGED (wk 1) → WARNING (wk 2) → PRIORITY (wk 3) → ESCALATE (wk 4+), ceiling at week 4 with the consecutive-weeks count still displayed.*
- [ ] 8.5: Confirm the first stage is named **FLAGGED** rather than "Late flag" — "Late" already means the 4.5 DI overrun label.
- [ ] 8.5: Score behaviour — flat 8.3 penalty (reporting-only ladder) or escalating penalty per stage (recommendation: escalating, −2/−5/−10/−15%).
- [ ] 8.5: On re-blocking, does the counter reset or resume? (Recommendation: reset, with a "previously blocked" marker.)
- [ ] 8.5: What does ESCALATE trigger? (Recommendation: surfaced in the SLT view and auto-populated into that EPIC's remedial email draft.)
- [ ] 6.2.6: Confirm the state → score mapping (100 / 70 / 50 / 20) and the simple mean roll-up to Capability; or adopt stage-weighting instead.
- [ ] 6.2.7: Sanity-check the 10/20/30-day thresholds — they place ~59% of in-flight Features (73 of 124) in the top risk band today, which would leave Flow Throughput Red almost everywhere.
- [x] 6.2.7: **Scoping phase — build and instrument.** *Confirmed: implement the ladder, monitor pass-through rate and gap distribution weekly, review whether to retire it once the 11-week history is full.*
- [x] 6.2.8: **Feature Created date added** — *resolved in the revised extract.*
- [ ] 6.2 Flow Throughput: does a **Blocked → active status** resume count as a forward transition or as neutral? (Transition direction classification is otherwise confirmed — see 6.2.)
- [x] 6.3 KPIs: **provided** — Full Cycle Time (≤150d), Delivery Predictability (≤90d, PASS/FAIL), Delivery Cycle Time (≤90d), with the `NOW()` convention for open items and the SLA Breach Report format.
- [ ] 6.3.7 (1): **Which Features count toward the KPI RAG** — open only, open plus completed-this-DI, or all-time? (Lower risk than first thought: in scope, 23 of 33 Full Cycle Time breaches are on *open* Features, so the RAG stays responsive either way.)
- [x] 6.3.6: **KPI RAG bands confirmed** — fail = Red; within 20% of target (120–150d / 72–90d) = Amber; better = Green.
- [ ] 6.3.6: Confirm the per-Feature band → score conversion (proposal Green 100 / Amber 70 / Red 20, then mean across Features and across the three KPIs).
- [ ] 6.3.7 (3): Does the elapsed clock exclude Blocked time, and does it reset on backward transitions?
- [ ] 6.3.7 (4): Are Cancelled Features excluded from KPIs?
- [ ] 6.3.7 (5): Treatment of in-scope Features with no In Analysis / In Development date — only 220 and 188 of 598 are computable (37% and 31%), so roughly two-thirds have no KPI at all.
- [ ] 6.3.3: First or last entry into a status when deriving In Analysis / In Development dates; and which source wins where `DATE_Committed` disagrees with the transition history (78 Features).
- [ ] 6.1.5: Definition of "Capability earliest start" — the Capability's own Target Start, or the earliest across sibling Features?
- [ ] 6.1.5: Add a rule for Features whose Target End precedes their Target Start (10 in the current extract)?

**Section 7 — Roll-up Logic**
- [x] **Roll-up weighting confirmed** — *same 30/40/30 weights and 85%/60% bands at every level; each child weighted by simple count share (n children → 1/n each).*
- [x] 7.3: **Delivery-impact override confirmed** — *every row reports a health score and a delivery status; the RAG is the worse of the two. Late is late regardless of percentage complete.*
- [x] 7.3: **"At risk" caps the RAG at Amber** — *confirmed; Red reserved for a date missed or unrecoverable.*
- [x] 7.3: **30-day projection horizon** — *confirmed.*
- [x] 6.1.4: **Post-Backlog compliance target confirmed** — *every Capability past Backlog must hold a Delivery Increment and both Target Dates; compliance measured and trended weekly. Currently 130 of 215 (60.5%).*
- [ ] 6.1.4: Surface Capability baseline compliance as a **headline SLT metric**, or keep it inside the checklist? (Recommendation: headline.)
- [ ] 7.3: Confirm a parent with **no committed date** reports delivery status **Unassessed** rather than On track.

**Section 8 — Blocked Status & Risk Escalation**
- [ ] 8.1: Does a Blocked Capability cascade to also flag its parent Release/EPIC's own status, or is it surfaced only as a callout at those levels (per 8.2) without forcing the parent's status?
- [ ] 8.3: Exact boundaries for "early / mid / late" within a Delivery Increment (e.g. by % of quarter elapsed, or fixed month 1/2/3 splits) — needed to apply the −2%/−5%/−10% blocked-item penalties precisely.

**Section 9 — Trend vs Snapshot**
- [x] **Trend retention confirmed — 11 weeks** *of weekly snapshots, plus a permanently retained current-state baseline (the two are different things — see Section 9).*
- [ ] What is shown for a row with fewer than 11 weeks of history?
- [ ] Trend shown per health check individually, or only on the overall RAG?
- [ ] Visual treatment for trend (sparkline, arrow indicator, RAG-over-time strip)?

**Section 11 — Agentic AI Features**
- [ ] 11.1: What level of detail is shown per agent — status only (e.g. "last run 09:00 Mon"), or reasoning/log output?
- [ ] 11.1: Is the Agent Transparency Panel global (one list) or shown per-view (agents relevant to the current EPIC/Release/Capability level)?
- [ ] 11.2: Should chat answers cite the underlying data/evidence (e.g. which rows/records support the answer)?
- [ ] 11.2: Should chat answer cross-EPIC/trend questions from the SLT view (e.g. "which EPICs went Red this week")?
- [ ] 11.3: Email trigger — on-demand per EPIC only, or auto-suggested when an EPIC is Red/Amber?
- [ ] 11.3: Does the tool send the email directly, or only draft it for the user to review/send?
- [ ] 11.3: Source of "critical remedial actions" — agent-generated recommendations, a predefined playbook per RAG driver, or both?

**Section 11 — Agentic AI Features (cont.)**
- [ ] 11.4: Should the Data Quality & Remediation Agent's findings feed the remedial emails in 11.3?

**Section 12 — JIRA Workflows**
- [x] 12.1 EPIC workflow — *provided, diagram transcribed*
- [ ] 12.1: Sanity-check the transcribed EPIC workflow (backward transitions, On Hold-resume paths) against the live JIRA config
- [x] 12.2 Capability workflow — *provided, diagram transcribed*
- [ ] 12.2: Confirm whether Ready for Delivery transitions into Done, or if that's purely covered by the global `Any → Done` transition
- [x] 12.3 Story workflow — *no longer required, Story level removed from the model (Section 3)*
- [x] 12.3 Feature workflow — *provided, diagrams transcribed and cross-checked against the transition data; forward/backward classification now defined in Section 6.2*
- [ ] All three Phase 1 workflows (EPIC, Capability, Feature) are now provided. Remaining workflow question: fallback treatment for a Feature whose current status is **Blocked** but which has no dateable `→ Blocked` transition row in the extract — assume Warning-only, assume mid-DI penalty, or exclude?

**Section 13 — Weekly Data Input**
- [x] Upload model — *confirmed: initial full dump, subsequent uploads are deltas*
- [x] Definition of "Item" — *superseded by Section 3's hierarchy (EPIC → Release → Capability → Feature, Feature as leaf)*
- [x] Sample file — *provided (EPIC.xlsx: EPIC, EPIC Transition, Capability, Features, Transitions, ART)*
- [x] **Release records** — *provided via `EPIC_Releases.xlsx`; modelled in Section 3.1. Rule Set 1 and the Delivery Manager view are now unblocked.*
- [x] 3.1: **Release ID** — *confirmed: the release **name** is the identifier; no independent ID exists. The 6.1.6 duplicate-name tie-break rule is therefore mandatory.*
- [x] 3.2: **Key-prefix rules** — *confirmed: EPIC and Capability keys are always FCM/RN; Feature keys vary by delivering team and carry no scope meaning; ART is the authoritative team attribution.*
- [x] 11.3 / 13: **No personal data** — *confirmed: no owners, assignees or names in any export; all reporting rolls up to EPIC level.*
- [x] 13: **Summary/title fields and Feature Created date** — *confirmed as being added to a single consolidated export.*
- [x] 13 / 3.2.1a: **Titles and Feature Created date delivered** — *100% populated. Columns are `Portfolio Epic`, `Capability`, `Feature`; the `Capability` sheet is renamed `Capabilities`.*
- [x] 6.2.8: **Created date resolved** — *every open in-scope Feature now has a clock anchor (last forward transition, else Created).*
- [x] 6.2.1: **Phase detection corrected** — *phase now derives from current status, not transition history; this recovered 43 Features already in delivery statuses that were wrongly excluded.*
- [ ] 6.2.9: **Ageing Backlog** — is it reported, at what age threshold (recommend 365 days: 68 Features), and does it score (recommend no)?
- [ ] 3.2: Is a **non-FCM/RN Capability key** an exclusion or a Data Quality defect? Two exist today (`PPEP-13349`, `PPEP-31932`).
- [ ] 3.2: Is **missing or unset ART** a Data Quality defect? Genuine team attribution exists for only 258 of 598 in-scope Features (43%).
- [ ] 11.3: Should remedial email drafts reference the ART where one is set, or stay strictly at EPIC level?
- [ ] 3.1: Add a **RELEASED** sheet — completed releases are absent, so 6 of 30 Capability-linked releases have no dates at all.
- [ ] 3.1: **Align export scope** — the release export covers 246 Capabilities against 406 in the main extract, leaving 192 unassessable.
- [ ] 3.1: Is it a defect when a Capability's release is **not** one of its parent EPIC's releases (11 of 119 cases)?
- [x] 4.2 / 3.1 / 7.2: **One Release per Capability confirmed** — *two or more is a DQ defect (Rule Set 1 Part C). This makes the roll-up a strict tree and removes the multi-release aggregation problem.*
- [ ] 3.1: For a Capability currently in breach of Part C, confirm the interim scoring rule — recommendation: attribute to its earliest-dated Release and flag the defect.
- [ ] 6.1.2 Part B: Confirm the EPIC-key prefix check applies to the release **name** (your wording said Description), and that an 83% failure rate reflects a real standard rather than one team's convention.
- [ ] 6.1.6: Tie-break rule for duplicate release names with conflicting dates.
- [ ] 6.1.6: Severity for Rule Set 5 anomalies — same High weighting as Rule Set 1, or lower (proposal: Warning for A/B, High for C)?
- [ ] 13: Will the weekly upload be two files or one consolidated workbook, and do the release sheets follow the full-then-delta convention?
- [ ] Source system / JQL or report that produces the export
- [ ] Will deltas use the identical sheet and column structure as the full dump?
- [ ] How a delta expresses a deletion versus a cancellation
- [x] Delta content — *confirmed: only items changed in the preceding 7 days; unchanged items excluded entirely; absence means unchanged.*
- [x] 13.1: **Deletion semantics resolved** — *no deletion capability exists; items are Done, Cancelled or in progress; Cancelled is the only removal signal; regression to Backlog/Funnel is a normal change.*
- [x] 13.1: **Re-parenting confirmed** as a delta-borne change event, making scope membership dynamic and re-evaluated every upload.
- [x] 3.2: **`FCB` confirmed as a real prefix** — *for Capabilities and Features belonging to EPICs still in Backlog; in scope. No FCB rows exist in the current extract, so the filter must accept it pre-emptively.*
- [x] 3.2 / 13.2: **Keys confirmed mutable** — *Capability reassociated with a Backlog EPIC is re-keyed to FCB (Features keep their keys but re-point); a Feature reassociated with a Backlog Capability is re-keyed to FCB. Handling specified in 13.2.*
- [ ] 13.2.1: **Request a `Re-keys` sheet** in the weekly file (`Old Key`, `New Key`, `Date changed`, `Level`) — the only fully reliable handling. Fallback is title-based matching with quarantine.
- [ ] 13.2.1: Confirm N weeks of no-update before a record is treated as a phantom re-key candidate (recommendation: 4).
- [ ] 13.2.2: Is re-keying **reversible** (FCB → FCM/RN when the EPIC leaves Backlog), and do Features revert their original prefix?
- [ ] 13.2.2: After a re-key, is the item's **transition history** reported under the new key, the old key, or split?
- [ ] 13.1: **Snapshot immutability** — when an item is re-parented, are prior weeks' snapshots restated or left as recorded? (Recommendation: left as recorded.)
- [ ] Confirm deltas carry only **new** transition rows (append) rather than full history per changed item (which would require de-duplication)
- [ ] Upload mechanism (manual upload, folder watch, API)
- [ ] Is there a periodic full re-baseline, or is the initial dump the only full load?
- [ ] Column definitions / data dictionary

---

## 15. Non-negotiables / Constraints

These are the constraints Claude Code must respect. Where a constraint is also stated elsewhere in this document, it is restated here deliberately — a rule buried in a subsection gets designed around; a rule in this section does not.

### 15.1 Absolute constraints

**1. All scoring is deterministic code. Agents never derive a score.**
Every RAG score, rule evaluation, KPI calculation, threshold comparison and roll-up is computed by deterministic code from the stored data. **No LLM sits anywhere in the scoring path.** The agents' role is to *summarise, explain, answer questions and draft emails* — never to decide a status.

Rationale: this output goes to an SLT and drives remedial action. If a model is in the scoring path, the same input can yield a different RAG on Tuesday than on Monday, last week's number becomes unreproducible, and the trend line — the whole point of Section 9 — becomes meaningless. This also bounds the Conversational Q&A (11.2): it may *report and explain* computed scores, and must never compute a new one in its answer.

**2. Every score must be reproducible.**
Any past week's RAG must be exactly reproducible from stored data, because people will rely on the trend and act on it. Requirements:
- Store the **computed scores** per weekly snapshot, not merely the inputs.
- Snapshots are **immutable** — never restated retrospectively (13.1, 13.2.2).
- **Version the rule set.** If a threshold or rule changes, historical weeks retain the scores produced under the rules in force at the time. A rule change must never silently recompute the past and move a trend line that a delivery manager has already acted on. Each snapshot records the rule-set version that produced it.

**3. Low-confidence evaluations must be visibly flagged.**
Coverage is uneven and will remain so: Flow Throughput is computable on 163 of 598 in-scope Features, and the KPIs on 31–37%. A Capability scored from 2 of its 10 Features must not look identical to one scored from all 10.
- Every scored row displays **how many of its children contributed** (e.g. "scored from 3 of 11").
- A row is marked **low confidence** where the contributing proportion falls below a threshold. `[PROVIDE]` Threshold — recommendation: **below 50% of children contributing**.
- Low confidence is a **display flag, not a score adjustment** — it does not alter the RAG, consistent with the single-attribution principle (7.1).

**4. Every RAG must be traceable to its evidence.**
A user must be able to get from any score to the specific records and field values that produced it (7.1.1, 11.4). No score is presented without a path to its underlying rows.

**5. Read-only over JIRA.**
The system never writes back to the source. Rule Set 2 outputs are *recommended* status changes for a human to action (11.4).

**6. No personal data — ever.**
No owners, assignees, names or email addresses in any export, view, rule, agent output or email draft. All attribution rolls up to EPIC; ART is the only team-level attribution (3.2, 11.3).

**7. Missing data is never rendered Green.**
An absent date, DI or transition history reports **Unassessed**, never "On track" or healthy (3.2.3, 7.3). Silence is not good news.

**8. Reporting is never suppressed — only scoring is de-duplicated.**
Under 7.1, a finding may be excluded from a *score* because it is attributed to a higher-priority category. It is never removed from the *reports* (7.1.1).

### 15.2 Performance and operating window

| Constraint | Requirement |
|---|---|
| **Dashboard responsiveness** | Real-time interaction. **Maximum 30 seconds to load** any view, including drill-down |
| **Weekly data arrival** | The delta file lands **first thing Monday, by 09:00** |
| **Processing** | Ingestion, all five rule sets, scoring and snapshot generation must complete on arrival, so the dashboard is current for Monday-morning use. `[PROVIDE]` Confirm the deadline — recommendation: **current by 09:30**, giving a 30-minute processing window |
| **Data volumes (current)** | 598 in-scope Features, 371 Capabilities, 74 EPICs, ~150k raw transition rows, 11 weekly snapshots |

### 15.3 Portability — configuration over hardcoding

**The requirements in this document are the durable asset.** The intent is that this proof of concept is re-pointable at other customers, so **nothing customer-specific may be hardcoded**. The following must all be configuration:

- Key prefixes and the scope filter (`FCM`, `RN`, `FCB` — Section 3.2)
- The fiscal calendar and DI quarter boundaries (Section 4)
- All thresholds: stagnation bands (10/20/30), KPI SLAs (150/90/90), the 20% Amber approach zone, RAG bands (85%/60%), health-check weights (30/40/30), blocked penalties, the 30-day delivery horizon, retention (11 weeks)
- JIRA workflow status names and their ordinal sequence (Section 12), and the status-normalisation map (6.1.1)
- Sheet and column names (3.2.1a) — these have already changed once between extracts

A hardcoded threshold is a defect, not a shortcut. Every constant in this document should be traceable to a single configuration source.

### 15.4 Proof-of-Concept scope boundaries

This build is a **Claude Code proof of concept**. The following are deliberately out of scope, recorded here so the decisions are visible rather than assumed:

| Area | PoC position | Would need revisiting for production |
|---|---|---|
| **Authentication / RBAC** | None. No role-based restriction, consistent with the access model in Section 2 | Real auth, and a decision on whether the "any viewer, any dashboard" model survives |
| **Hosting / data residency / classification** | Not constrained for the PoC | Where it runs, whether Vodafone Business delivery data may leave the corporate boundary, and its data classification |
| **Device support** | Desktop assumed | Whether the SLT view needs to work on mobile |
| **Scale headroom** | Current volumes (15.2) | Growth beyond the current order of magnitude, and whether other customers' estates are larger |
| **Availability / DR / backup** | Not addressed | Uptime expectations and snapshot backup — note the 11-week history becomes irreplaceable once deltas begin, since it cannot be reconstructed from a delta feed |

⚠ **One PoC caveat worth flagging now:** the retained weekly snapshots **cannot be rebuilt** from a delta-based feed. If the PoC's storage is lost, the trend history is gone permanently and takes 11 weeks to rebuild. Even at PoC stage, the snapshot store deserves a backup.
