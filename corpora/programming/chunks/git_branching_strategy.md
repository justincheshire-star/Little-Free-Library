---
title: "Git Branching Strategy"
domain: "programming"
subdomain: "version-control"
source: "Git Documentation"
source_license: "CC-BY-SA"
source_id: "git-docs-2.43"
source_path: "branching/strategy"
retrieved_at: "2026-02-26"
verified: "2026-02-26"
importance: 0.85
tags: ["git", "version-control", "branching", "workflow"]
version: "1.0.0"
content_hash: "sha256:placeholder"
---

# Git Branching Strategy

A well-defined branching strategy is essential for team collaboration and maintaining code quality. Different strategies suit different team sizes and development workflows.

## Common Branching Models

### Git Flow

Git Flow is a branching model that uses two main branches:

- **main/master**: Production-ready code
- **develop**: Integration branch for features

Supporting branches:
- **feature/***: New features (branch from develop)
- **release/***: Release preparation (branch from develop)
- **hotfix/***: Emergency fixes (branch from main)

### GitHub Flow

A simpler alternative to Git Flow:

1. Anything in the main branch is deployable
2. Create descriptive branch names for new work
3. Commit to local branches and push regularly
4. Open a pull request when ready for feedback
5. Merge only after pull request review
6. Deploy immediately after merge to main

### Trunk-Based Development

Developers collaborate on code in a single branch (trunk), resisting any pressure to create long-lived feature branches:

- Short-lived feature branches (< 1 day)
- Frequent integration to trunk
- Feature flags for incomplete features
- Continuous integration and automated testing

## Best Practices

**Branch Naming Conventions:**
```
feature/user-authentication
bugfix/login-timeout
hotfix/security-patch-cve-2024-1234
release/v2.3.0
```

**Commit Messages:**
- Use imperative mood: "Add feature" not "Added feature"
- Be descriptive but concise
- Reference issue numbers when applicable

**Pull Requests:**
- Keep PRs small and focused
- Provide context in description
- Respond promptly to review comments
- Ensure CI passes before requesting review
