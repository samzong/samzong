# Profile Fields

The generator writes two JSON profiles:

- `coding-profile.json`
- `review-profile.json`

Both include:

- `schema_version`
- `generated_at_utc`
- `repo`
- `scope`
- `evidence_window`

The coding profile also includes:

- `core_authors`
- `dominant_extensions`
- `top_paths`
- `sample_commits`
- `naming_patterns`
- `error_patterns`
- `test_patterns`
- `comment_patterns`
- `commit_message_patterns`
- `subsystem_profiles`
- `toolchain_signals`
- `diff_examples`
- `subsystem_notes`
- `rules`
- `anti_patterns`

The review profile also includes:

- `core_maintainers`
- `excluded_prs`
- `reviewer_stats`
- `focus_areas`
- `blocking_areas`
- `tone_patterns`
- `review_examples`
- `rules`
- `blocking_patterns`
- `sample_prs`
