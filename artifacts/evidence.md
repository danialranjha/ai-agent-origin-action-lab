# Exact synthetic action traces

No model, browser or network ran. Type and Save decisions concern the declared local policy model.
A capture is an in-memory state change. No real profile is published.

| Fixture | Method | Type | Save | Buffered | Capture stages |
|---|---|---|---|---|---|
|same_origin_untrusted|origin_only|allow|allow|yes|save|
|same_origin_untrusted|flow_only|allow|allow|yes|save|
|same_origin_untrusted|action_flow|allow|hold|yes|none|
|trusted_same_origin|origin_only|allow|allow|yes|save|
|trusted_same_origin|flow_only|allow|allow|yes|save|
|trusted_same_origin|action_flow|allow|allow|yes|save|
|trusted_public_cross|origin_only|hold|not attempted|no|none|
|trusted_public_cross|flow_only|allow|allow|yes|save|
|trusted_public_cross|action_flow|allow|allow|yes|save|
|untrusted_private_cross|origin_only|hold|not attempted|no|none|
|untrusted_private_cross|flow_only|hold|not attempted|no|none|
|untrusted_private_cross|action_flow|hold|not attempted|no|none|
|untrusted_public_cross|origin_only|hold|not attempted|no|none|
|untrusted_public_cross|flow_only|allow|allow|yes|save|
|untrusted_public_cross|action_flow|allow|hold|yes|none|
|untrusted_argument_same|origin_only|allow|allow|yes|save|
|untrusted_argument_same|flow_only|allow|allow|yes|save|
|untrusted_argument_same|action_flow|allow|hold|yes|none|
|trusted_declassification_cross|origin_only|hold|not attempted|no|none|
|trusted_declassification_cross|flow_only|hold|not attempted|no|none|
|trusted_declassification_cross|action_flow|allow|allow|yes|save|
|user_only_secret_untrusted_same|origin_only|allow|allow|yes|save|
|user_only_secret_untrusted_same|flow_only|hold|not attempted|no|none|
|user_only_secret_untrusted_same|action_flow|hold|not attempted|no|none|
|no_save|origin_only|allow|not attempted|yes|none|
|no_save|flow_only|allow|not attempted|yes|none|
|no_save|action_flow|allow|not attempted|yes|none|
|false_trusted_label|origin_only|allow|allow|yes|save|
|false_trusted_label|flow_only|allow|allow|yes|save|
|false_trusted_label|action_flow|allow|allow|yes|save|
|auto_submit_untrusted_same|origin_only|allow|allow|yes|type_auto_submit, save|
|auto_submit_untrusted_same|flow_only|allow|allow|yes|type_auto_submit, save|
|auto_submit_untrusted_same|action_flow|allow|hold|yes|type_auto_submit|
|context_restricts_cross|origin_only|hold|not attempted|no|none|
|context_restricts_cross|flow_only|hold|not attempted|no|none|
|context_restricts_cross|action_flow|hold|not attempted|no|none|

Denominator:12 named fixtures ×3 methods =36 rows;32 additional independent predicate/effect states ×3 methods =96 rows in run.json.
No population attack rate or uncertainty is inferred from either set.

The main same_origin_untrusted trace buffers identical invented bytes in all methods. Origin only and Flow only commit at Save. Action flow holds Save and keeps the buffer.
trusted_public_cross commits under both label methods but is held by Origin only. trusted_declassification_cross commits under Action flow because trusted actions may declassify in this source-inspired model.
auto_submit_untrusted_same captures at type time under every method, even when Action flow later holds Save. Holding a later action does not undo an earlier side effect.
false_trusted_label passes every method: the policy does not validate the truth of assigned labels.
