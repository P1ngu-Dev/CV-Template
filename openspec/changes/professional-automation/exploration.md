## Exploration: professional-automation

### Current State

The workspace is a **well-structured but fully manual** CV-as-code environment built on RenderCV v2.8. It has a clean architecture: `main/cv.yaml` is the source of truth, `applications/` is intended for per-job variants, `templates/` has scaffolding, and 21 skills in `.agents/skills/` provide the AI-assisted content generation. However, **zero automation exists** — the `scripts/` folder is empty, `applications/` has never been used, and the recommended workflow (`job-description-analyzer` → `resume-tailor` → `rendercv` → `resume-ats-optimizer` → `cover-letter-generator`) is entirely ad-hoc.

The user wants to evolve this into a **professional presence automation environment** that produces tailored CVs, cover letters, outreach messages, and eventually feeds into external automation (Hermes/n8n). The first deliverable is a **manual end-to-end job-application flow** that will later be codified.

### Affected Areas

- `scripts/` — currently `.gitkeep`; will hold automation scripts and orchestration.
- `applications/` — currently `.gitkeep`; will hold the first real job application folder.
- `main/cv.yaml` — source of truth; will be read and adapted by future scripts.
- `templates/` — static scaffolding; may need programmatic templates or Jinja2/YAML overrides.
- `docs/cv_workspace_architecture.md` — architecture doc; needs updates for automation phases.
- `.agents/skills/` — 21 CV skills; orchestration may need a meta-skill or script to call them in sequence.
- `contexts/` — dated context files; automation may need to read the latest context automatically.

### Approaches

1. **Phase-Gated Manual → Scripted → Automated**
   - **Description:** Start with a single manual job application performed step-by-step (store JD, run analysis, tailor CV, render, ATS check, write cover letter, log). Each phase produces artifacts and notes. Once the flow is proven, wrap each step into a shell/Python script. Finally, compose scripts into a CLI or pipeline.
   - **Pros:**
     - Each phase is immediately useful (the first manual flow is a real job application).
     - Risk is low; we only automate what we have validated.
     - Artifacts from the manual run become test fixtures for the scripted version.
   - **Cons:**
     - Slower overall than designing the full pipeline up front.
     - Requires discipline to document the manual run so it can be codified.
   - **Effort:** Low for Phase 1, Medium for Phase 2, High for Phase 3.

2. **Big-Design-Up-Front Pipeline (YAML/JSON Config Driven)**
   - **Description:** Design a `pipeline.yaml` that defines the full job-application workflow: input JD URL/text, extract analysis, map to skills, generate variants, render outputs, and produce a final application package. Implement the engine in Python or Bash that reads the pipeline and orchestrates skill calls.
   - **Pros:**
     - Clean architecture from the start.
     - Easy to extend to LinkedIn/Indeed/GitHub later.
   - **Cons:**
     - High upfront cost before any real job application is produced.
     - High risk of building the wrong abstraction if the manual flow is not yet understood.
     - May over-engineer a simple problem (RenderCV + YAML + skills are already the heavy lifting).
   - **Effort:** High.

3. **Hermes/n8n-First Integration**
   - **Description:** Build the workflow directly in an external automation tool (n8n, Hermes, etc.) and treat the workspace as a file-backed state store.
   - **Pros:**
     - Visual workflow design.
     - Built-in triggers (webhooks, RSS for job boards, email).
   - **Cons:**
     - Adds a hard dependency on an external tool before the core logic is validated.
     - Complex to version-control and test.
     - Overkill for a student with a single target: second professional practice.
   - **Effort:** High.

### Recommendation

**Approach 1 — Phase-Gated Manual → Scripted → Automated.**

The most pragmatic path is to **perform one complete manual job application first**, then extract scripts from the proven steps. This mirrors the user's explicit request: "a first manual job-description flow to be performed later, then used as the base for automation." The workspace is already designed for this (templates, docs, skills catalog). We only need to execute the flow and capture the pain points.

### Risks

- **Scope creep:** The user listed many targets (LinkedIn, GitHub, Indeed, Hermes, n8n). If we try to design for all of them now, the first slice becomes unbounded. **Mitigation:** Scope the first slice to a single job application (CV + cover letter + log). Everything else is Phase 2+.
- **Skill orchestration mismatch:** The 21 skills are designed for human-in-the-loop interaction (e.g., `resume-tailor` expects a back-and-forth). Automating them may require wrapper logic or meta-prompts. **Mitigation:** Document the manual interaction first, then decide if a lightweight Python wrapper (e.g., `click` CLI) can replay the steps.
- **RenderCV dependency:** RenderCV is a Python CLI tool. Automation must run inside the `.venv` or use `uv`. **Mitigation:** The first script should be `render_main.sh` and `render_application.sh` that activate the correct environment.
- **YAML fragility:** The CV is YAML; programmatic edits (e.g., overriding sections for a job) are error-prone. **Mitigation:** Use RenderCV's CLI override feature (`--cv.sections...`) where possible, or maintain per-job `cv.yaml` copies rather than trying to patch the master file in place.
- **No test harness:** The project has no tests. Automation scripts will regress silently. **Mitigation:** Add a simple `make check` or `scripts/validate.sh` that runs `rendercv render --dont-generate-pdf` on all `cv.yaml` files in `applications/`.

### Ready for Proposal

**Yes.** The exploration confirms that the repository has a solid foundation and a clear roadmap. The orchestrator should tell the user that the recommended path is a **3-phase transformation**:

1. **Phase 1 — Manual Proof:** Perform a complete job application manually (find a real job, run analysis, tailor CV, render, write cover letter, log). This validates the workflow and produces real artifacts.
2. **Phase 2 — Scripting:** Extract shell/Python scripts for the repetitive steps (folder creation, rendering, validation, ATS check). The manual run becomes the test case.
3. **Phase 3 — Automation:** Compose scripts into a single CLI or integrate with an external workflow tool (Hermes/n8n) for triggers like RSS feeds or email.

The first slice should be bounded to **Phase 1 only** for the next SDD phase (proposal/spec). The proposal should ask the user to confirm a real job description they want to target, or if they want a synthetic one for the proof of concept.
