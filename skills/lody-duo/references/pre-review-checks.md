# Pre-review checks

Build Standard runs these checks during self-testing, before it requests independent review. A module Build Standard runs them too.

1. Read the repository configuration, the Git hooks, and the commit tooling. List the gates that run at commit time. For the final staged target, run in advance every gate that does not depend on the result of the independent review. These gates include the size limit of the commit tooling. Other gates, for example format, secret scan, and generated files, follow the actual configuration of the repository. Prefer the official check entrypoint of the tool, and do not test a gate by making a commit. If you cannot find the entrypoint or the runtime to run it, report the gate as unverified.
2. If a check fails, correct the target, stage it again, and rerun the affected checks. The evidence packet reports the commands that ran, their results, the size of each changed file in bytes, and the fingerprint of the staged target. For a check that did not run, state the reason. Gates that depend on the review result, for example a review receipt, run after the review. Never forge a receipt. A pre-review check does not replace the independent review or the commit-time gate.
3. Request the independent review only after the checks pass. Otherwise a commit gate can force a change of structure after the review and change the target fingerprint.

## Independent review and corrections

The host opens a new Review session to complete the final-target independent review packet in [independent-review.md](../../liability-review/references/independent-review.md). If a fresh-context review that satisfies the contract already exists for the same fingerprint, reuse it and do not start a duplicate review. A consultation, a self-test, and a Fast report do not replace the packet. When the review finds a problem, Build Standard corrects it in its original session.
