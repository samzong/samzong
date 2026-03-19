# Vulnerability Checklist by Language

Quick-reference checklist for Phase 2 auditing. Check each item that applies to the target language.

## Universal (All Languages)

### Input Handling
- [ ] User input used in SQL without parameterized queries
- [ ] User input reflected in HTML without escaping (XSS)
- [ ] User input used in shell commands without sanitization (command injection)
- [ ] User input used in file paths without canonicalization (path traversal)
- [ ] User input used in regex without escaping (ReDoS)
- [ ] Deserialization of untrusted data (RCE via pickle/yaml/Java serialization)
- [ ] Integer overflow/underflow in size calculations
- [ ] Missing or insufficient input length limits (buffer overflow / OOM)

### State & Data
- [ ] Non-atomic read-modify-write on shared state
- [ ] Missing rollback on partial failure (data left in inconsistent state)
- [ ] Write operation without fsync/flush (data loss on crash)
- [ ] Concurrent access to mutable collection without synchronization
- [ ] TOCTOU: check-then-act with gap where state can change
- [ ] Double-free or use-after-free patterns

### Error Handling
- [ ] Empty catch/except block swallowing critical errors
- [ ] Error path that skips resource cleanup (file handles, DB connections, locks)
- [ ] Catch-all that masks specific errors requiring different handling
- [ ] Missing error check after fallible operation (unchecked return value)

### Auth & Crypto
- [ ] Hardcoded credentials or API keys in source
- [ ] Missing auth check on privileged endpoint
- [ ] JWT/token validation that can be bypassed (alg=none, weak secret)
- [ ] Use of Math.random() / rand() for security-sensitive values
- [ ] Timing-vulnerable string comparison for secrets
- [ ] CORS misconfiguration allowing credential theft

### Concurrency
- [ ] Lock ordering inconsistency (deadlock risk)
- [ ] Missing await/then on async operation (fire-and-forget with side effects)
- [ ] Shared mutable state accessed from multiple goroutines/threads/tasks without protection
- [ ] Unbounded queue/channel growth (OOM)

## TypeScript / JavaScript

- [ ] `eval()`, `new Function()`, or `vm.runInNewContext()` with user input
- [ ] `innerHTML`, `dangerouslySetInnerHTML` with unsanitized data
- [ ] Prototype pollution via `Object.assign` or spread with user-controlled keys
- [ ] Missing `await` on Promise that affects control flow or error propagation
- [ ] `JSON.parse()` without try-catch on external input
- [ ] Buffer allocation with user-controlled size without bounds check
- [ ] `child_process.exec()` with string interpolation from user input
- [ ] `RegExp` constructor with user input (ReDoS)
- [ ] Event listener leak (addEventListener without removeEventListener in cleanup)
- [ ] `fs.writeFile` without error callback or await

## Python

- [ ] `pickle.loads()` / `yaml.load()` on untrusted data
- [ ] `os.system()` / `subprocess.call(shell=True)` with user input
- [ ] `exec()` / `eval()` with external data
- [ ] Mutable default argument (shared state across calls)
- [ ] `except:` or `except Exception:` that silences `KeyboardInterrupt` / `SystemExit`
- [ ] `open()` without context manager in error-prone code path (resource leak)
- [ ] `datetime.now()` vs `datetime.utcnow()` in timezone-sensitive logic
- [ ] `==` comparison on floats for equality checks in financial/critical math
- [ ] SQLAlchemy raw text queries with f-string interpolation

## Go

- [ ] Ignored error return: `result, _ := riskyFunction()`
- [ ] Goroutine leak (spawned without cancellation context)
- [ ] Data race: shared variable accessed from multiple goroutines without mutex/channel
- [ ] Deferred `rows.Close()` after error check that returns early
- [ ] `sync.WaitGroup` Add/Done mismatch
- [ ] Nil map write (panic)
- [ ] Slice append aliasing (unexpected mutation of shared backing array)
- [ ] Missing `context.WithTimeout` on external calls (hang forever)

## Rust

- [ ] `unwrap()` / `expect()` on `Result`/`Option` in non-test code without guaranteed invariant
- [ ] Unsafe block with incorrect lifetime or aliasing assumptions
- [ ] `Arc<Mutex<T>>` deadlock from nested lock acquisition
- [ ] Missing `Drop` implementation for resource cleanup
- [ ] Integer overflow in release mode (wraps silently)

## Java / Kotlin

- [ ] `String.format()` or concatenation in SQL queries
- [ ] `ObjectInputStream.readObject()` on untrusted data
- [ ] `synchronized` block ordering inconsistency across methods
- [ ] Resource not closed in finally block (pre-try-with-resources)
- [ ] `ConcurrentModificationException` risk from iterating + modifying collection
- [ ] `hashCode`/`equals` contract violation causing HashMap corruption

## SQL / Database

- [ ] String concatenation in query construction
- [ ] Missing transaction around multi-step write operations
- [ ] SELECT ... FOR UPDATE without timeout (deadlock risk)
- [ ] DROP/TRUNCATE without safeguard in migration code
- [ ] Missing index on foreign key used in DELETE CASCADE (table lock escalation)
