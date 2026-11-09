# Notifications tests

Existing tests are grouped here by feature with `test_<feature>.py` filenames.
See the [backend testing guide](../../../../../docs/backend-testing.md) for commands, actual results, known
failures and isolated-database requirements.

The [origin index](../../../../../docs/backend-test-origins.json) maps every moved file to its original path and
pre-move hash. Moved Django files also record the original path at line 1.
Folder placement does not mean that every test currently passes.
