# Refactoring/Design Plan: Project Initialization and Cleanup (V2)

## 1. Executive Summary & Goals
This plan outlines the necessary steps to clean up and configure a new AI agent project generated from the ADK starter pack. The focus is on preparing the repository for local-first development, resolving immediate CI/CD failures, and consolidating documentation, while preserving the option for future cloud deployment.

-   **Goal 1: Consolidate Documentation:** Create a single, authoritative `README.md` by merging relevant information from the starter pack's documentation and removing redundant files.
-   **Goal 2: Stabilize CI/CD:** Disable the failing `Deploy to Staging` GitHub Actions workflow, ensuring that essential checks like linting and unit testing can still run successfully.
-   **Goal 3: Simplify Project Structure:** Identify and remove files and configurations from the starter pack that are not required for the current local development and future self-hosted deployment scope, while preserving useful local development tools like the `Makefile`.

## 2. Current Situation Analysis
The project is in its initial state, created from a starter pack template. This has resulted in three key issues hindering development:
1.  **Documentation Conflict:** Information is split between the project's `README.md` and the starter pack's `docs/STARTER_PACK_README.md`, potentially leading to confusion and inconsistency.
2.  **CI/CD Failures:** The "Deploy to Staging / deploy_and_test_staging" GitHub Actions workflow is failing on every push because the necessary Google Cloud Platform (GCP) infrastructure and credentials are not configured.
3.  **File Clutter:** The repository contains numerous files and directories specific to the starter pack's example use case and its default GCP deployment strategy, which are irrelevant to the project's immediate needs. The `Makefile` is useful but may contain cloud-specific targets that need removal.

## 3. Proposed Solution / Refactoring Strategy
### 3.1. High-Level Design / Architectural Overview
The strategy is to methodically strip the project down to a clean, stable baseline. We will address the most disruptive issues first (documentation and CI/CD) before performing a general cleanup. This ensures the project is immediately usable and has a clear source of truth. The process will be non-destructive for future-facing features like cloud deployment, opting to disable rather than permanently delete critical workflow configurations.

### 3.2. Key Components / Modules
This plan primarily affects project configuration, documentation, and CI/CD workflows. No application code or architectural components will be modified. The key areas of focus are:
-   **Root Directory:** `README.md`, `Makefile`.
-   **Documentation:** `docs/` directory.
-   **CI/CD:** `.github/workflows/` directory.
-   **Infrastructure as Code (IaC):** Any directories related to Terraform, CloudFormation, etc. (Assumed).
-   **Scripts:** `scripts/` directory (if present).

### 3.3. Detailed Action Plan / Phases

---

#### **Phase 1: Documentation Consolidation**
-   **Objective(s):** Establish a single, comprehensive `README.md` as the project's primary documentation.
-   **Priority:** High

-   **Task 1.1: Analyze and Synthesize READMEs**
    -   **Rationale/Goal:** Identify essential setup, installation, usage, and architectural information from `docs/STARTER_PACK_README.md` that is missing from the root `README.md`.
    -   **Estimated Effort (Optional):** S
    -   **Deliverable/Criteria for Completion:** A clear list or understanding of the sections to be merged.

-   **Task 1.2: Update Project `README.md`**
    -   **Rationale/Goal:** Integrate the valuable information identified in Task 1.1 into the main `README.md`. Re-structure the document for clarity, ensuring it accurately reflects the AI agent project's purpose, not the generic starter pack.
    -   **Estimated Effort (Optional):** M
    -   **Deliverable/Criteria for Completion:** The root `README.md` is updated and contains all necessary information for a new developer to understand and run the project locally.

-   **Task 1.3: Clean Up Obsolete Documentation**
    -   **Rationale/Goal:** Remove the now-redundant starter pack documentation to eliminate confusion.
    -   **Estimated Effort (Optional):** S
    -   **Deliverable/Criteria for Completion:** The `docs/STARTER_PACK_README.md` file is deleted.

---

#### **Phase 2: CI/CD Stabilization**
-   **Objective(s):** Stop CI/CD pipeline failures by disabling workflows not relevant to the current development stage.
-   **Priority:** High

-   **Task 2.1: Identify and Disable Deployment Workflows**
    -   **Rationale/Goal:** Prevent failing GitHub Actions runs by disabling the "Deploy to Staging" workflow. Renaming the file is a clean, non-destructive way to achieve this, preserving it for future use.
    -   **Estimated Effort (Optional):** S
    -   **Deliverable/Criteria for Completion:** The workflow file, likely named `deploy_and_test_staging.yml` (or similar), located in `.github/workflows/`, is renamed to `deploy_and_test_staging.yml.disabled`.

-   **Task 2.2: Review and Retain Core CI Workflows**
    -   **Rationale/Goal:** Ensure that essential quality checks that can run without cloud infrastructure (e.g., linting, unit tests, code formatting) remain active.
    -   **Estimated Effort (Optional):** S
    -   **Deliverable/Criteria for Completion:** A successful run of the CI pipeline is triggered on a commit, showing that only the desired, non-deployment jobs have executed.

---

#### **Phase 3: Project File Cleanup**
-   **Objective(s):** Remove unnecessary files and configurations to simplify the project structure.
-   **Priority:** Medium

-   **Task 3.1: Create a Backup Branch**
    -   **Rationale/Goal:** Safeguard against accidental deletion of a necessary file. All cleanup work should be done on a separate branch.
    -   **Estimated Effort (Optional):** S
    -   **Deliverable/Criteria for Completion:** A new branch (e.g., `feature/project-cleanup`) is created from the main branch.

-   **Task 3.2: Identify Unnecessary Files and Configurations**
    -   **Rationale/Goal:** Systematically identify items that are purely for the starter pack's example or for a GCP-centric deployment that is not currently needed.
    -   **Estimated Effort (Optional):** M
    -   **Deliverable/Criteria for Completion:** A list of files, directories, and configurations recommended for removal or modification is created. This list will likely include:
        -   **To Delete:** `terraform/` or similar IaC directories.
        -   **To Delete:** `cloudbuild.yaml` (specific to Google Cloud Build).
        -   **To Delete:** `.gcloudignore`.
        -   **To Delete:** Example application code in `src/` or `app/` that is not related to the AI agent project.
        -   **To Review & Prune:** The `scripts/` directory. Review each script; delete those specific to GCP deployment, but keep any that assist with local development (e.g., setting up environment variables, running local services).
        -   **To Review & Prune:** The `Makefile`. Identify all targets related to `gcloud`, `terraform`, or cloud deployment.

-   **Task 3.3: Execute Cleanup**
    -   **Rationale/Goal:** Execute the cleanup by removing the identified files and editing configurations that reference them.
    -   **Estimated Effort (Optional):** M
    -   **Deliverable/Criteria for Completion:** The files and directories from the list in Task 3.2 are deleted. The `Makefile` is edited to remove only the cloud-specific targets, preserving local development commands like `make test` and `make lint`.

-   **Task 3.4: Verify Project Integrity**
    -   **Rationale/Goal:** Ensure the project remains functional (e.g., dependencies install, tests run, make commands work) after the cleanup.
    -   **Estimated Effort (Optional):** M
    -   **Deliverable/Criteria for Completion:** The project's local setup, test commands, and essential `make` targets run successfully on the cleanup branch. The branch is ready for review and merging.

## 4. Key Considerations & Risk Mitigation
### 4.1. Technical Risks & Challenges
-   **Risk:** Accidental deletion of a critical configuration file or `Makefile` target that is essential for local development.
    -   **Mitigation:** Perform all deletions on a dedicated branch (Task 3.1). Thoroughly test the project's local setup and core functionality, including all remaining `make` targets, before merging the changes (Task 3.4).
-   **Risk:** A script in the `scripts/` directory has a dual purpose for both local dev and cloud deployment, and is mistakenly deleted.
    -   **Mitigation:** During Task 3.2, carefully review the content of each script. If in doubt, retain the script and document its suspected purpose for later clarification.

### 4.2. Dependencies
-   The phases are largely independent but are ordered logically. Completing Phase 1 (Docs) and Phase 2 (CI/CD) first provides immediate value and stability.
-   Task 3.3 is directly dependent on the analysis performed in Task 3.2.

### 4.3. Non-Functional Requirements (NFRs) Addressed
-   **Maintainability:** The plan directly improves maintainability by removing dead code/configuration and creating a single source of truth for documentation. A cleaner codebase is easier for new developers to understand and contribute to.
-   **Usability (Developer Experience):** A stable CI/CD pipeline and clear, concise documentation significantly improve the day-to-day developer experience.

## 5. Success Metrics / Validation Criteria
-   The project has a single, consolidated `README.md` file.
-   All pull requests and commits to the main branch result in successful (green) GitHub Actions runs.
-   The project's file tree is free of starter-pack-specific example code, IaC, and GCP configuration files.
-   A new developer can successfully clone, install dependencies, run tests, and use local `make` commands by following the updated `README.md`.

## 6. Assumptions Made
-   The failing GitHub Actions workflow is defined in a single file, likely named `deploy_and_test_staging.yml`, within the `.github/workflows/` directory.
-   The project contains common files for GCP deployment, such as a `terraform/` directory, `cloudbuild.yaml`, and `.gcloudignore`.
-   The starter pack includes example source code that is not relevant to the user's AI agent project and can be safely removed.
-   The user has administrative access to the GitHub repository to review and merge the changes.

## 7. Open Questions / Areas for Further Investigation
-   What criteria should be used to determine if a script in the `scripts/` directory is "valuable for local development" and should be kept? (e.g., Does it run Docker? Does it set environment variables from a `.env` file? Does it run tests?) This should be considered during Task 3.2.