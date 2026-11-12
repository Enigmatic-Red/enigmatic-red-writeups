# Enigmatic Red: diffprivlib Logistic Regression and SciPy Compatibility

*Enigmatic Red, a research lab for AI-specialized cybersecurity agents. November 2026*

An upstream fix in IBM's `diffprivlib` removes an obsolete keyword from the SciPy optimizer used by private logistic regression. The bug does not silently weaken differential privacy: with a SciPy version that rejects the keyword, fitting stops with a `TypeError`. This write-up follows the failure from the dependency API to the small upstream change, and distinguishes what we reproduced locally from the test results reported in the PR.

## How we worked

We checked the merged change in [PR #113](https://github.com/IBM/differential-privacy-library/pull/113) against SciPy's documented API history, then reproduced the rejected keyword on SciPy 1.18.1. We also ran a minimal optimization without the keyword to confirm the optimizer still executes. This isolates and verifies the API failure; it is not an independent end-to-end rerun of diffprivlib's logistic-regression tests.

|  | diffprivlib |
| --- | --- |
| Pull request | [PR #113](https://github.com/IBM/differential-privacy-library/pull/113) |
| Broken behavior | Logistic regression cannot fit when SciPy rejects `iprint` |
| Failure mode | `TypeError` at the optimizer call |
| Impact class | Dependency compatibility and availability |
| Patch | Remove the obsolete `iprint` mapping and keyword |

## Case: Logistic regression passes a removed SciPy keyword

**Symptom.** The logistic-regression path calls `scipy.optimize.fmin_l_bfgs_b()` to minimize a noisy loss. It passed an `iprint` value derived from `verbose`. On SciPy 1.18.1, the optimizer no longer accepts that argument, so the fit raises:

```text
TypeError: fmin_l_bfgs_b() got an unexpected keyword argument 'iprint'
```

**Reproduction.** SciPy 1.15 documented `iprint` as deprecated and said it had no function. SciPy 1.17 documented its planned removal in 1.18; the current function signature omits it. The [included reproduction script](./reproduce.py) calls the optimizer both ways on SciPy 1.18.1:

```text
SciPy 1.18.1
before: TypeError: fmin_l_bfgs_b() got an unexpected keyword argument 'iprint'
after: converged with x= [0.0] value= 0.0 warnflag= 0
```

This confirms the dependency-boundary failure and that the optimizer can run without the unsupported keyword. It does not by itself prove the full diffprivlib model behavior.

**Root cause.** `diffprivlib/models/logistic_regression.py` continued passing `iprint` after SciPy had deprecated it as a no-op and scheduled its removal. The stale argument was the failure point; it was not a problem with the private loss or optimizer convergence.

**Fix.** PR #113 removes the mapping from `verbose` to `iprint` and drops the keyword from the `fmin_l_bfgs_b()` call. The noisy objective, its arguments, regularization strength, and convergence settings remain unchanged. The change removes an obsolete low-level output option.

**Proof.** The local reproduction above fails with `iprint` and converges without it on SciPy 1.18.1. The PR description reports that `python -m pytest tests/models/test_LogisticRegression.py -q` passed all 17 tests; that suite result is reported by the contributor, not independently rerun for this write-up. The merged PR changes one production file and received maintainer approval.

**Scope.** This is a compatibility and availability issue in privacy software, not an identified security vulnerability. The fit fails rather than returning a model with less noise. The patch does not change epsilon, sensitivity, privacy accounting, or the noise mechanism. We found no evidence of an attacker-controlled trigger or data exposure.

## What this shows

An API deprecation can break a privacy-preserving workflow even when the algorithm itself has not changed. Testing dependency version ranges catches failures that a test run against only one environment may miss. At the same time, a runtime failure should not be described as a weakened privacy guarantee when the evidence shows that fitting aborts.

## Status

PR #113 was merged on November 6, 2026. SciPy's [1.15 documentation](https://docs.scipy.org/doc/scipy-1.15.0/reference/generated/scipy.optimize.fmin_l_bfgs_b.html) marks `iprint` deprecated and nonfunctional; SciPy's [1.17 documentation](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.fmin_l_bfgs_b.html) documents its planned removal in 1.18. The failure was reproduced locally on SciPy 1.18.1.
