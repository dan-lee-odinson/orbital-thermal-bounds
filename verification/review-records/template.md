<!--
Copy to review-records/YYYY-MM-DD-<scope>.md for each major milestone,
formal cross-model review, or release. Not required for routine development.
-->
> **Working verification record:** This document may contain incomplete,
> provisional, or unresolved material. Its inclusion in the repository does
> not indicate validation or acceptance of the associated technical claims.
# Review Record: <Scope>
## Record Metadata
- **Record status:** draft | completed | superseded
- **Date:** YYYY-MM-DD
- **Reviewed commit:** `<full commit hash>`
- **Branch:** `<branch at time of review>`
- **Reviewer(s):** `<human role and/or model, displayed version, and effort setting>`
- **Trigger:** major milestone | cross-model review | release
- **Disposition:** accepted with limitations | changes required | informational only
## Review Basis
<Link to or identify the roadmap, requirements, review instructions, prompt,
issue, or acceptance criteria used to conduct the review.>
## Review Scope
<Describe what was reviewed and explicitly identify what was out of scope.>
## Files and Artifacts Inspected
<List repository paths, documents, generated artifacts, or external sources.
Include hashes where the identity of a non-versioned artifact matters.>
## Commands and Tests Run
<List exact commands and summarized results, or state:
"Static review only; repository state was not executed.">
If execution depended on a particular environment, record the relevant runtime,
package, operating-system, or tool versions.
## Findings
1. **[Severity] [Category] Finding title**
   
   Description and supporting evidence.
   - Category: defect | limitation | sensitivity | future work | documentation
   - Status: open | accepted | resolved | deferred
   - Relevant file or result:
   - Required action:
## Unresolved Questions
<List questions the review could not settle and identify what evidence would
be needed to resolve them.>
## Resulting Changes
<List resulting commits, pull requests, tests, documentation changes, or
mastery-ledger updates. State "none" when applicable.>
## Follow-Up
- **Owner:** `<role or name>`
- **Required action:** `<action or none>`
- **Re-review required:** yes | no
- **Target milestone:** `<milestone or not applicable>`
## Verification Limitations
<State what the review did not establish. Examples:
- Static review only; code was not executed.
- Test success was reported but not independently reproduced.
- Central equations were not independently derived.
- Physical assumptions were not reviewed by a qualified subject-matter expert.
- Generated results were not compared with experimental or flight data.
>
