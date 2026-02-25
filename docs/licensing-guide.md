# Licensing Guide

This document explains the dual-license structure of the Little Free Library (LFL) repository.

---

## Overview

LFL uses two distinct licenses depending on the type of content:

| Content Type | License |
|---|---|
| Corpus data (`corpora/`) | Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0) |
| Tooling & scripts (`scripts/`, `.github/`, etc.) | Apache License 2.0 + Commons Clause |

---

## Corpus Data — CC-BY-SA 4.0

All knowledge base content stored under the `corpora/` directory is licensed under [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

### What this means

- **You can**: copy, redistribute, adapt, and build upon the corpus data for any purpose, including commercial use.
- **You must**: give appropriate credit, provide a link to the license, and indicate if changes were made.
- **You must**: distribute any derivative works under the same CC-BY-SA 4.0 license (ShareAlike).

### Compatibility with source material

All source material contributed to the corpora must have an original license that is **compatible with CC-BY-SA 4.0** redistribution. Examples of compatible licenses:

- CC-BY 4.0
- CC-BY-SA 4.0
- CC0 1.0 (public domain)
- Open Government Licence
- MIT (for documentation and reference material, not code)

If you are unsure whether a source license is compatible, open an issue before submitting.

---

## Tooling & Scripts — Apache 2.0 + Commons Clause

The tooling, scripts, CI workflows, and repository infrastructure are licensed under the **Apache License, Version 2.0**, with the **Commons Clause** condition appended.

### Apache 2.0

Grants broad rights to use, copy, modify, merge, publish, distribute, and sublicense the software, subject to attribution requirements. See the full text in [LICENSE](../LICENSE).

### Commons Clause

The Commons Clause restricts the right to **sell** the software — meaning you may not offer the LFL tooling as a paid hosted service or commercial product without permission from the maintainers.

This restriction is intended to prevent commercial entities from monetizing the tooling without contributing back to the community, while still allowing free use for research, personal projects, and open-source development.

### What this means in practice

| Use Case | Allowed? |
|---|---|
| Using scripts locally or in CI | ✅ Yes |
| Modifying and sharing scripts under the same license | ✅ Yes |
| Using the tooling in an open-source RAG project | ✅ Yes |
| Selling the scripts as a commercial product | ❌ No |
| Offering a paid hosted service powered primarily by LFL tooling | ❌ No |

---

## Source Material Provenance

Every corpus contribution must document the provenance of its source material in `sources.json`. This ensures that license compatibility can be verified and attribution can be maintained. See [contributing-guide.md](contributing-guide.md) for details.

---

## AI-Generated Content Policy

AI-generated text **may not** be used as primary source material in the corpora. AI tools may only be used as:

- A **transcription layer** for converting images or diagrams into text descriptions.
- A **formatting aid** for restructuring human-authored content into chunk format.

Any AI-assisted processing must be clearly documented in the `notes` field of the relevant `sources.json` entry.
