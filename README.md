# AI browser-agent origin and action boundaries

An independent synthetic policy experiment separates entering text from committing a form. It compares three small rules on fixed labels and in-memory actions. **No AI model, browser, network request or real profile runs.** This is not the SPIDES implementation, a SOPGuard reproduction or a test of native browser Same-Origin Policy.

In the main same-origin fixture, all three methods put identical invented text into the form buffer. Origin only and Flow only commit at Save. Action flow holds Save and leaves the buffer in place. A public cross-origin ordinary task still commits under the two label methods. Two deliberately broken assumptions expose limits: a false trusted label permits Save, and auto-submit commits during typing before a later Save can be held.

## Reproduce

Python3.10+; tested with Python3.11.6. Standard library only. No install, model account or credentials required.

```sh
python3 -B experiment.py
python3 -B -m unittest -v test_experiment
python3 -B run_checks.py
```

The first command regenerates [run.json](artifacts/run.json) and [the exact trace table](artifacts/evidence.md). The last records [normal and deliberate-fault checks](artifacts/checks.json). Run artifacts contain no timestamps or machine-specific paths, so regeneration is byte-comparable on the same implementation.

## Hypothesis and threat model

Origin equality alone does not distinguish a trusted action from an action influenced by untrusted text on that same origin. Separately checking information flow when entering text and integrity when performing a consequential Save should distinguish those cases in this finite model.

Assume attacker-influenced action choices already exist. The runner supplies a fixed type-then-Save sequence; no persuasion is attempted. The user, surrounding program, labels, destination identities and operation classification remain trusted except in two explicitly marked counterexamples. Both invented target origins are in the trusted-origin set. There is no target selection, URL parser, real website or session.

The invented private string is `invented-recovery@example.invalid`. `site-a.invalid` and `site-b.invalid` are opaque fixture identifiers and are never contacted. A local buffer and captured state stand in for the form and committed profile. Nothing is externally published.

## Technical walkthrough

### Policies and state

Each context and argument has a trusted bit, authorized reader set and source-origin set. Reader sets use a finite universe of `user`, siteA and siteB. “Public” means all three in this model. The policy cannot determine whether assigned labels are true.

- **Origin only:** Require the context and argument source origins to match the target at type and Save.
- **Flow only:** Require the target to belong to both reader sets at type and Save.
- **Action flow:** At type, require either trusted context and arguments or permitted flow; at consequential Save, require trusted context and arguments.

The predicates are `P_T = context.trusted AND argument.trusted` and `P_F = target ∈ context.readers ∩ argument.readers`. Action flow uses `P_T OR P_F` for the modeled egress-only typing and `P_T` for Save. The `OR` is deliberate: a fully trusted action can send data outside the reader set in this source-inspired policy. The `trusted_declassification_cross` fixture exposes this behavior. It is not an unconditional confidentiality guarantee.

A held type leaves the buffer empty and skips Save. An admitted type fills the buffer with exact bytes. An admitted Save copies the buffer into committed state. A held Save leaves the buffer untouched. No approval mechanism runs; “hold” means the action does not execute. This does not replace a held action with an approved alternative.

### Main paired trace

Context is untrusted, the argument is trusted, both have source siteA, target is siteA, and both reader sets permit siteA. Thus `P_T=false`, `P_F=true`. The form changes its committed state only on Save.

| Method | Type | Buffer after type | Save | Captured commit |
|---|---|---|---|---|
|Origin only|allow|invented-recovery@example.invalid|allow|same bytes at Save|
|Flow only|allow|invented-recovery@example.invalid|allow|same bytes at Save|
|Action flow|allow|invented-recovery@example.invalid|hold|none|

The observed distinction is the later integrity check, not rejection of the text entry. Flow only is an ablation showing that checking readers alone does not stop the same-origin sequence.

### Controls and limitations that change the result

The ordinary trusted same-origin control commits under all methods. The trusted public cross-origin control is held by Origin only and commits under both label methods. An untrusted private cross-origin transfer is held by all three. Argument integrity and context reader restrictions have separate fixtures. No Save means no commit even when text remains buffered.

`false_trusted_label` declares that the context label is incorrect but supplies a trusted bit to the policy. All methods commit. The extra truth annotation is evidence for the reader, not an input that silently fixes the gate.

`auto_submit_untrusted_same` deliberately breaks the assumption that typing is only an egress action. Every admitted type immediately changes committed state. Action flow still holds the later Save, but its earlier type capture remains. Origin only and Flow only also record a second capture when Save runs. These are distinct event stages, not two independent attacks. This counterexample is about the model's action classification, not a discovered SPIDES or browser defect.

### Evidence and oracle

There are12 named fixtures ×3 methods =36 rows and32 additional independent predicate/effect combinations ×3 methods =96 rows. The matrix varies destination relation, context integrity, argument integrity, reader membership and manual/auto-submit effects. It is not a sample of browser traffic and is not necessarily a set of reachable conservatively propagated context states.

Named expectations are authored as explicit tuples separately from the policy functions. Tests use a separate eight-entry truth table for Action flow and exact expected capture stages. The artifact retains every row, including counterexamples. Counts are coverage counts, not attack-success rates.

Eleven tests pass. Omitting the Save integrity rule produces21 assertion failures; requiring both trust and reader permission for typing produces22. Both faulty versions compile and run with zero test errors or skips. Failure counts include subtest failures and are not counts of distinct vulnerabilities.

## Source and interpretation

[SPIDES v1](https://arxiv.org/html/2610.24277v1), sections4.2,7 and AppendixG, motivates the action predicates and distinguishes admitted same-origin typing from a later held Save. [source.json](source.json) records the mapping. No upstream code is copied. Its linked repository returned an authenticated404 during preparation, so this is explicitly an independent model rather than an execution of released code. No benchmark percentage from the paper is reproduced here.

Origin-only and Flow-only are our diagnostic comparators. The experiment does not implement masking, quarantined inference, DOM labels, label propagation, real browser effects, trusted-origin discovery, human approvals or a production enforcement boundary. Hostile Python in this process could bypass the whole model. A trusted bit is not proof that the action matches user intent. Reader sets expressed as origins cannot distinguish every audience inside one site.

For a real agent integration, classify effects before admitting the action, carry trustworthy context and argument labels into each check, and test both the earlier data entry and the later committed result. If typing can itself submit or trigger an account action, treat it as consequential before it runs; a check attached only to a later Save cannot undo it. Verify browser behavior and label provenance separately before relying on these small predicate tests.
