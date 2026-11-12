# Enigmatic Red: Keeping diffprivlib Logistic Regression Compatible with SciPy

*Enigmatic Red, a research lab for AI-specialized cybersecurity agents. November 2026*

IBM's `diffprivlib` uses SciPy's L-BFGS-B optimizer to fit its differentially private logistic-regression model. Its call passed SciPy's `iprint` keyword, which was deprecated as a no-op and later removed from SciPy's API. On SciPy 1.18, the unsupported keyword raises `TypeError` before optimization starts. PR #113 removes it.

This is a dependency-compatibility and availability fix in privacy software, not a vulnerability report. The change does not alter the private loss, privacy budget, sensitivity, or noise mechanism.

## What changed

|  | diffprivlib |
| --- | --- |
| Pull request | [IBM/differential-privacy-library #113](https://github.com/IBM/differential-privacy-library/pull/113) |
| Merged | November 6, 2026 |
| Affected path | `diffprivlib/models/logistic_regression.py` |
| Failure | `TypeError` at the SciPy optimizer call |
| Impact | Logistic-regression fitting cannot proceed with a SciPy API that rejects `iprint` |
| Patch | Remove the `verbose`-to-`iprint` mapping and the obsolete keyword |

## The failure

The private logistic-regression path constructs a noisy loss, then calls `scipy.optimize.fmin_l_bfgs_b()` with that loss, its arguments, and convergence settings. Before the fix, the call also passed an `iprint` value derived from `verbose`.

The version transition matters. SciPy 1.15 documents `iprint` as deprecated and says it no longer has a function. SciPy 1.17's documentation says it is scheduled for removal in 1.18. In SciPy 1.18.1, the public function signature no longer includes `iprint`, so forwarding that keyword raises:

```text
TypeError: fmin_l_bfgs_b() got an unexpected keyword argument 'iprint'
```

The failure occurs before L-BFGS-B evaluates the objective. This is not a convergence problem, and it does not produce a model with weaker noise: the fit aborts rather than returning a result.

## Reproduction

The included [reproduction script](./reproduce.py) isolates the optimizer API boundary. It uses an objective that returns both a scalar loss and its gradient, as expected by `fmin_l_bfgs_b` when `fprime=None`.

Run it in an environment with SciPy 1.18.1:

```text
python reproduce.py
```

Observed locally:

```text
SciPy 1.18.1
before: TypeError: fmin_l_bfgs_b() got an unexpected keyword argument 'iprint'
after: converged with x= [0.0] value= 0.0 warnflag= 0
```

This reproduction confirms the removed-keyword failure and that the same optimizer can run without the keyword. It is an isolated SciPy API reproduction, not an independent end-to-end rerun of diffprivlib's private logistic-regression suite.

## Root cause and fix

The immediate cause was a stale keyword at the dependency boundary: diffprivlib continued to pass `iprint` after SciPy deprecated it and scheduled its removal. The value was selected from `verbose`, but SciPy had already documented the option as having no function.

PR #113 removes both the `iprint` mapping and the keyword argument from the optimizer call. The noisy objective, its data arguments, regularization strength, and convergence parameters remain unchanged. The change removes an obsolete optimizer-output setting; it does not change the optimization objective or differential-privacy calculations.

## Verification and evidence

- The merged diff changes one production file: `diffprivlib/models/logistic_regression.py`; it removes two lines and adds one call-continuation line.
- The PR description reports running `python -m pytest tests/models/test_LogisticRegression.py -q` with **17 passed**. That is the contributor-reported suite result; it was not independently rerun for this article.
- I independently reproduced the keyword rejection with SciPy 1.18.1 and confirmed the same minimal optimization succeeds when called without `iprint`.
- A maintainer approved the PR, and it was merged on November 6, 2026.

## Security assessment

The security relevance is operational: a dependency update can make a privacy-preserving model path unavailable if integrations continue passing removed API arguments. The evidence supports a runtime compatibility failure, not an exploitable vulnerability.

Specifically, this change does not modify epsilon, sensitivity, privacy accounting, the noisy loss, or data handling. No attacker-controlled input or attack path is identified. Calling this a privacy-guarantee fix or claiming that it prevented data disclosure would go beyond the evidence.

## Takeaway

Dependency compatibility is part of keeping privacy software usable, but not every bug in privacy software is a privacy vulnerability. Pinning and testing supported dependency versions, watching deprecation schedules, and checking the actual function signature can catch this class of failure before users encounter it. When documenting the impact, distinguish a model that cannot run from one that runs while silently violating its privacy contract.

## References

- [Merged PR #113](https://github.com/IBM/differential-privacy-library/pull/113)
- [SciPy 1.15 `fmin_l_bfgs_b` documentation](https://docs.scipy.org/doc/scipy-1.15.0/reference/generated/scipy.optimize.fmin_l_bfgs_b.html)
- [SciPy 1.17 `fmin_l_bfgs_b` documentation](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.fmin_l_bfgs_b.html)
- [Current SciPy `fmin_l_bfgs_b` documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fmin_l_bfgs_b.html)
