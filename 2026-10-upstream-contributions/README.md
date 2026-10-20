# Enigmatic Red: Upstream Contributions Write-Up

*Enigmatic Red, a research lab for AI-specialized cybersecurity agents. October 2026*

Two upstream fixes, one in IBM's `diffprivlib` and one in CPython's `tarfile`, show the same failure pattern: code silently breaking a guarantee it advertises, with no crash to reveal it. This write-up walks through how each bug was verified and fixed, and what it suggests for AI-assisted security research.

## How we worked

We used AI assistance to navigate open, unfixed issues in widely used projects. For each candidate we cross-referenced related issues and pull requests, to avoid duplicating existing work and to match each project's conventions, and then researched a fix. We did not trust any report at face value: every bug was reproduced independently against released or current code before a patch was written.

The loop was the same for both cases:

1. Pick an open, unfixed issue and check related issues and PRs for overlap.
2. Reproduce the bug against real code, not a description of it.
3. Trace the root cause to the specific line or code path.
4. Write the smallest patch that restores the intended behavior.
5. Add a regression test and confirm it fails before the fix and passes after.

|  | diffprivlib | CPython `tarfile` |
| --- | --- | --- |
| Issue / PR | #105 / PR #110 | gh-156057 / PR #156143 |
| Broken guarantee | Epsilon-calibrated privacy noise | Corrupt archives raise `tarfile.ReadError` |
| Failure mode | Noise silently reduced or zeroed | Raw codec exception leaks past handlers |
| Impact class | Weakened privacy guarantee | Robustness on untrusted input |
| Patch size | One character | Small, mirrors existing `_Stream` pattern |

## Case 1: diffprivlib silently drops the noise

**Symptom.** Issue #105 reported that `LinearRegression` calibrated sensitivity incorrectly for diagonal terms.

**Reproduction.** We installed the released package (0.6.6, the version in the issue) and called `_construct_regression_obj` directly with `bounds_X=(0, 100)`. The sensitivity for the diagonal coefficient came back as `0.0`. With bounds of 0 to 100 the correct value is `10000.0`.

**Root cause.** In `diffprivlib/models/linear_regression.py`, the diagonal sensitivity was computed as `np.max(np.abs([bounds_X[0][i], bounds_X[0][i]])) ** 2`. The lower bound was used twice and the upper bound never. Whenever the lower bound is 0, sensitivity collapses to zero regardless of the upper bound, and `LaplaceFolded` then adds essentially no noise to that coefficient. The off-diagonal case and the `bounds_y` term nearby already paired lower and upper bounds correctly, which pointed to a copy error rather than a design choice.

**Fix.** Change the second element from `bounds_X[0][i]` to `bounds_X[1][i]`.

**Proof.** A regression test, `test_diagonal_sensitivity_uses_both_bounds`, records the sensitivity passed to `LaplaceFolded`. It fails on the old code and passes on the fix. The 13 existing `LinearRegression` tests still pass.

**Why it is hard to catch.** The model still trains, the output still looks reasonable, and no test that only checks accuracy would notice. The only symptom is a privacy guarantee weaker than the requested epsilon for that term.

## Case 2: `tarfile` leaks codec exceptions

**Symptom.** Issue gh-156057 reported that corrupted compressed data could surface as raw codec exceptions instead of `tarfile.ReadError`.

**Reproduction.** We built archives corrupted after the header, so opening succeeds and the damage appears only during `extractfile()`. On current `main`, gzip, bzip2 and xz all leaked their raw exceptions (`zlib.error`, `OSError`, `lzma.LZMAError`). We could not test zstd locally because the Python build lacked `compression.zstd`.

**Root cause.** Seekable mode reads member data through `_FileInFile.read()`, which called the underlying file object with no exception handling. The streaming path (`r|gz` and similar) already wrapped codec errors using a per-codec `exception` attribute on `_Stream`. The two modes handled the same failure differently.

**Fix.** Give `TarFile` and `_FileInFile` the same `exception` attribute. It defaults to `OSError`, `gzopen()`, `xzopen()` and `zstopen()` set the specific type, and `_FileInFile.read()` re-raises as `tarfile.ReadError`. The fix reuses an existing pattern instead of inventing a new one.

**Proof.** After the fix all three codecs raise `tarfile.ReadError`, and a write/read/extract round trip across uncompressed, gzip, bzip2 and xz showed no regression. The first version of the PR had no tests, and the maintainer asked for them. We added unit tests on `_FileInFile.read()`, including one that confirms an unconfigured exception type still propagates, plus an integration test through `gzopen()`. All fail before the fix and pass after.

**Scope.** This is a robustness issue. Code that parses untrusted archives usually catches `tarfile.ReadError`, so a leaked `zlib.error` can escape that handler and appear as an unhandled exception. We do not claim memory corruption or code execution.

## What connects them

Both bugs sit where a library makes a promise to its callers: calibrated noise in one case, a single documented error type in the other. In each, the implementation had a correct sibling elsewhere in the same codebase (the off-diagonal sensitivity, the streaming path), and the bug was the one place that diverged.

That suggests a practical detection strategy for AI-assisted tools: compare code paths that should behave alike, and flag the outlier. It also explains why neither bug was found by ordinary testing, since both produce plausible output in the normal case.

## Status

As of October 20, 2026, the `diffprivlib` PR has maintainer approval on its thread and merge status is unconfirmed. The CPython PR is open, with tests added in response to review.
