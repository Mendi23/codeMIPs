# CodeMips root source directory

## CSR.py

Translating commits into sessions for sending to the MIP graph.

The CSR is responsible for translating file paths into ids and keep tracking on renames, deletes and more..

Params:
 * **SUPPORTED_FILE_TYPES** - supported file types which we will send actions on them to the MIP.
 * **ACTIONS_THRESHOLD** - if we end up with too much actions in one session, the CSR will throw an exception (because it will probably lead to memory error on the MIP graph)

### CsrFiles

The used CSR.

Keep track on files changes like rename and etc.

### CsrCode

Not in use.

Originally was created to extend CsrFiles and create actions for code segments.

## Entities.py

The entities which the MIP is familliar with.

**Session** contains several **Action** s

In addition, **Action** is hashable and comparable.


## MIP.py

The MIP implementation

