## Corpus Contribution Checklist

Thank you for contributing to Little Free Library! Please complete all sections below before requesting review.

---

### Description

<!-- Briefly describe what corpus data this PR adds or modifies. -->

---

### Source Licensing

- [ ] I have verified the original source license for all content in this PR.
- [ ] The original source license is compatible with CC-BY-SA 4.0 redistribution.
- [ ] I have documented the source license in `sources.json` for every source used.
- [ ] No content in this PR is from a source with a restrictive or unknown license.

### Provenance Metadata

- [ ] Every new source has an entry in the relevant `sources.json` file.
- [ ] Each `sources.json` entry includes: `id`, `url`, `title`, `original_license`, `retrieval_date`.
- [ ] The `source` field in each chunk's frontmatter matches an ID in `sources.json` (or is a full URL).

### AI-Generated Content

- [ ] No AI-generated text has been used as primary source material.
- [ ] If AI was used for transcription or description of images/diagrams, this is documented in the `notes` field of the relevant `sources.json` entry.

### Chunk Quality

- [ ] All chunk files have valid YAML frontmatter with all required fields.
- [ ] I have run `python scripts/validate_corpus.py corpora/<domain>/chunks/` and all chunks pass.
- [ ] Chunks are logically self-contained and correctly sized (approximately 100–1000 tokens each).
- [ ] Content is factually accurate and verifiable against the cited source.
- [ ] No duplicate content with existing chunks.

### Corpus Manifest

- [ ] `CORPUS.md` has been created or updated to reflect any new subdomains or sources.

---

### Validation Output

<!-- Paste the output of the validation script here: -->

```
python scripts/validate_corpus.py corpora/<domain>/chunks/

<paste output here>
```

---

### Additional Notes

<!-- Any other context, caveats, or information the reviewer should know. -->
