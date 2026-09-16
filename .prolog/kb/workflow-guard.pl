% Temporary backlog workflow dispatch invariant.

root_cause(backlog_push_import_from_zero, workflow_push_trigger,
    "Merging the resume-artifact fix modified the temporary workflow file.
Its push trigger launched an automatic import from offset zero while a
manually resumed import was in progress. Both reached the ingest server.").

invariant(temporary_backlog_import_requires_manual_dispatch,
    "The temporary full-corpus import workflow may dry-run on pull requests;
the ingest job runs only on explicit workflow_dispatch. A push event must not
launch a production import without resume_run_id.").
