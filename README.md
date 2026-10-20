# Write-ups

Independent write-ups from the [Enigmatic Red](https://enigmaticred.com/) research
lab. One folder per write-up, each with its own `README.md`; this file is only the
index.

Every piece here is about a real defect in real code, released or current: how it
was found, how it was reproduced against the code as published, and how it was
fixed. Nothing is written up before it is reproduced, and nothing is claimed that
the reproduction does not show.

## Index

| Folder | Write-up | Where it went | Status |
| --- | --- | --- | --- |
| [`2026-10-upstream-contributions/`](2026-10-upstream-contributions/) | Two libraries that silently broke a guarantee they advertise: epsilon-calibrated privacy noise in `diffprivlib`, and a leaked codec exception in CPython's `tarfile` | `diffprivlib` issue #105, PR #110; CPython `gh-156057`, PR `gh-156143` | `diffprivlib`: approved on the thread, merge unconfirmed. CPython: open, tests added in response to review |

## How this is organised

```
writeups/
  README.md                          <- this index, the collection
  2026-10-upstream-contributions/
    README.md                        <- the write-up itself
  2026-10-<slug>/
    README.md                        <- the next one, same shape
```

* Folder name: `<year>-<month>-<slug>`. The date is when the piece was written,
  not when the bug was found.
* A folder holds the write-up plus whatever it needs to be checkable — a patch, a
  reproduction script, a captured trace. A write-up that can only be verified on
  the author's machine is not finished.
* A case enters the index only once it has been reproduced against a released or
  current revision and the reproduction has been recorded.

## Adding one

1. Make the folder and write its `README.md`.
2. Add the row to the index above — folder, one-line subject, where it went
   upstream, and its status.
3. Put anything the piece leans on in the same folder, next to the write-up.
4. Push: this collection is mirrored to GitHub, see below.

## Scope and conduct

Every reproduction here was run against software installed locally, or against a
project's own test suite. Nothing in this collection was produced by testing a
system without written authorisation, and no case describes an unreported
vulnerability: each one is either already public or already fixed upstream.

Only test what you own or have written authorisation for.
