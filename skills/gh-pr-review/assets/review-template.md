# PR Review (Owner) — {{PR_TITLE}} (#{{PR_NUMBER}})

- PR: {{PR_URL}}
- Author: {{PR_AUTHOR}}
- Base → Head: `{{BASE_REF}}` → `{{HEAD_REF}}`
- Head SHA: `{{HEAD_SHA}}`
- Generated At: {{GENERATED_AT}}

## 总结（中文）

{{SUMMARY_ZH}}

## CI / Checks

{{CHECKS_SUMMARY}}

## 变更范围（仅本 PR 引入的修改）

说明：本 review 只针对该 PR diff 中被新增/修改/删除的行进行评审。对同文件内未触及的历史代码不做“翻旧账”，除非该历史代码因本 PR 新增的调用路径而形成了明确的新风险。

{{FILES_CHANGED_OVERVIEW}}

## 详细评审（中文叙述 + 英文可复制评论）

{{FILE_REVIEWS}}

## 结论

- Merge 倾向：{{MERGE_RECOMMENDATION}}
- 阻塞项（如有）：{{BLOCKERS_ZH}}
- 非阻塞建议（如有）：{{NON_BLOCKING_ZH}}

