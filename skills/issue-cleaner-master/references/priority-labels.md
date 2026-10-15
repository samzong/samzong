# Priority Labels Reference

## Priority Definitions

| Priority | Label Combination | Target Audience | Expected Effort |
|----------|-------------------|-----------------|-----------------|
| P0 | `help-wanted` + `good-first-issue` | First-time contributors | Small |
| P1 | `good-first-issue` | Beginners | Small |
| P2 | `help-wanted` | Experienced community contributors | Medium |
| P3 | `kind/bug` / `bug` | Contributors familiar with the project | Medium |
| P4 | `kind/documentation` / `kind/cleanup` / `documentation` | Anyone | Small |
| P5 | Other | Core contributors | Large |

## Exclusion Labels

The following labels are **strong exclusion signals**:

| Label | Reason |
|-------|--------|
| `question` | Inquiry type, not a code contribution |
| `support` | Support request, not a code contribution |
| `duplicate` | Duplicate issue |
| `wontfix` | Will not be fixed |
| `invalid` | Invalid issue |

Note: Labels are just one dimension for judgment; combine with title and content for comprehensive assessment.

## Non-Code Contribution Characteristics

Besides labels, the following characteristics indicate an issue may not be suitable for code contribution:

**Title Characteristics**:
- Ends with `?` (question mark)
- Starts with "How to" / "How do I" / "Why does" / "What is"
- Contains "[Question]" / "[Help]" / "[Support]" prefix

**Content Characteristics**:
- Starts with "I'm trying to..." / "I want to know..."
- No clear reproduction steps or expected behavior description
- Mainly asking about usage or concept explanation

## Common Project Label Mappings

Different projects may use different label naming conventions:

| Common Meaning | Variants |
|----------------|----------|
| Bug | `bug`, `kind/bug`, `type/bug`, `type:bug` |
| Documentation | `documentation`, `kind/documentation`, `docs`, `type/docs` |
| Beginner-friendly | `good-first-issue`, `good first issue`, `beginner`, `starter` |
| Help wanted | `help-wanted`, `help wanted`, `contributions-welcome` |
| Cleanup/Optimization | `kind/cleanup`, `cleanup`, `refactor`, `tech-debt` |
