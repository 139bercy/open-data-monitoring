---
description: Run standard checks before committing code
---

Use this workflow to ensure the codebase is clean and all tests Pass before a commit or push. The project configuration in `.pre-commit-config.yaml` automates these checks and is configured in **fail-fast** mode (stops at the first failure).

### 1. Automatic Pre-commit Hooks
The following tools are integrated into the `git commit` process:
- **Python**: Black, Ruff (fix & format)
- **Frontend**: Prettier (specifically for `front/`)
- **Tests**: Pytest (backend) and Vitest (frontend)

### 2. Automation & Re-commit Rules
If a commit fails, refer to the following rules:

- **Linter Failures (Linter-Only)**:
  If the failure is due to formatting/linting tools (Black, Ruff, Prettier) modifying files, you must manually re-stage and re-commit:
  ```bash
  git add .
  git commit -m "your message"
  ```
- **Test Failures**:
  If a test falls (**pytest** or **vitest**), you MUST fix the code first. Automatic re-staging is prohibited in case of logic errors.

### 3. Manual Check (Optional)
To run all checks manually on the entire codebase without committing:
```bash
pre-commit run --all-files
```

### 4. Direct Tool Usage
If you need to target specific areas:
- **Backend Format**: `ruff format .` or `black src tests`
- **Frontend Format**: `cd front && npx prettier --write .`
- **Backend Tests**: `pytest`
- **Frontend Tests**: `cd front && npm test`
