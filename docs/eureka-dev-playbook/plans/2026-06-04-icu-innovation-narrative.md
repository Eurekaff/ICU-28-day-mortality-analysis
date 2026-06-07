# ICU Innovation Narrative Implementation Plan

> **For agentic workers:** Use eureka-dev-playbook:subagent-driven-development for independent high-risk or broad tasks, or eureka-dev-playbook:executing-plans for inline execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the project-facing research narrative so the ICU 28-day mortality study foregrounds literature-grounded innovation in calibration, missingness, ablation, and explanation stability.

**Architecture:** This is a documentation-only change. The new redesign document remains the detailed source of truth; README and experiment plan become concise entry points; the presentation script gets a defendable innovation answer for teacher feedback.

**Tech Stack:** Markdown documentation, existing project outputs in `outputs/tables/` and `outputs/docs/`.

---

### Task 1: README Research Positioning

**Files:**
- Modify: `README.md`

- [x] **Step 1: Add innovation-oriented project framing**

Replace the opening description with a concise statement that the existing experiment is the baseline and the revised research focus is clinical usability rather than raw model comparison.

- [x] **Step 2: Add literature-grounded innovation section**

Add a section covering:
- MIMIC-IV/data source is not itself the innovation.
- Traditional scores such as APACHE II, SAPS II, and SOFA provide interpretable baselines.
- MIMIC benchmark work motivates standard time windows and reproducibility.
- TRIPOD/TRIPOD+AI motivates transparent reporting.
- The study's differentiator is calibration, missingness, ablation, and explanation stability.

- [x] **Step 3: Update results caveat**

Keep current LightGBM results, but add the caveat that AUROC-best is not automatically probability-best because HistGradientBoosting/XGBoost currently have lower Brier scores.

### Task 2: Experiment Plan Rewrite

**Files:**
- Modify: `outputs/docs/EXPERIMENT_PLAN_icu_28d_mortality.md`

- [x] **Step 1: Reframe study objective**

Rewrite the objective around an updated experiment plan:
- Baseline model comparison.
- Calibration and threshold evaluation.
- Missingness feature engineering.
- Feature-group/time-window ablation where data supports it.
- SHAP stability rather than one-off SHAP interpretation.

- [x] **Step 2: Add literature comparison table**

Add a compact table comparing traditional scores, MIMIC benchmark studies, disease-specific MIMIC/eICU mortality models, and TRIPOD+AI.

- [x] **Step 3: Separate completed baseline from proposed extensions**

Make it clear that the current LightGBM result is the baseline already completed, while missingness, calibration, ablation, and stability experiments are the next experimental modules.

### Task 3: Presentation Script Innovation Answer

**Files:**
- Modify: `outputs/docs/基于MIMIC-IV的ICU患者28天死亡风险预测研究_终版讲稿.md`

- [x] **Step 1: Update research significance and limitations wording**

Change the script from "we built a model and used SHAP" to "we use the completed model as baseline and redesign around clinical reliability and reproducibility."

- [x] **Step 2: Add teacher-question answer**

Add a Q&A entry answering why the work is innovative despite many similar MIMIC-IV ICU mortality studies.

### Task 4: Verification

**Files:**
- Check: modified Markdown files

- [x] **Step 1: Search for overclaims and placeholders**

Run:

```bash
rg -n "首创|首次|TBD|TODO|待定|已经完成.*缺失|已经完成.*消融|已经完成.*稳定性" README.md outputs/docs/EXPERIMENT_PLAN_icu_28d_mortality.md outputs/docs/基于MIMIC-IV的ICU患者28天死亡风险预测研究_终版讲稿.md
```

Expected: no unsupported overclaim or placeholder remains.

- [x] **Step 2: Confirm changed files**

Run:

```bash
git status --short README.md outputs/docs/EXPERIMENT_PLAN_icu_28d_mortality.md outputs/docs/基于MIMIC-IV的ICU患者28天死亡风险预测研究_终版讲稿.md outputs/docs/实验方案重构_创新点与文献对照.md docs/eureka-dev-playbook/plans/2026-06-04-icu-innovation-narrative.md
```

Expected: only intended documentation files are listed for this task.
