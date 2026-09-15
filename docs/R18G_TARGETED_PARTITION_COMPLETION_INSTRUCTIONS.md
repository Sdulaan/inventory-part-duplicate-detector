# R18G-B1 targeted partition completion handoff

Status: `R18G_B1_AWAITING_TARGETED_PARTITION_HUMAN_INPUT`

1. Give only `r18g_targeted_partition_completion.xlsx` to the same Senior
   Functional Consultant.
2. Explain that the earlier whole-group judgments are not being reconsidered.
3. Ask the Senior only to assign P1/P2/P3... to the members of the two groups.
   Members with the same P-number represent the same underlying physical or
   business inventory identity; different P-numbers represent distinct
   identities.
4. `UNRESOLVED` is acceptable whenever the Senior cannot determine a member's
   partition safely. Do not guess.
5. Do not discuss GF5, current-versus-shadow identity, or system behavior.
6. Do not show or discuss the sealed holdout.
7. Return the completed targeted workbook to engineering.
8. Do not modify the original Development or Holdout workbooks.

Only `human_partition_id` and `partition_comment` on the `Partition` sheet are
editable. The prior whole-group judgment and all source fields are read-only.
The internal mapping CSV is not part of the Senior handoff.
