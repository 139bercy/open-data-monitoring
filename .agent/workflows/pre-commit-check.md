---
description: Run standard checks before committing code
---

Use this workflow to ensure the codebase is clean and all tests Pass before a commit or push.

1. Format the code:
   ```bash
   black src tests
   isort .
   ```
2. Run all tests:
   ```bash
   pytest tests/
   ```
3. Check for any linting errors or obvious regressions in logs.
