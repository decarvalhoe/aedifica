"""Workspace services — durable project object, brief, report, index.

Re-exported from ``pilot.workspace`` so the API/UI/demo layers depend on a
stable namespace instead of importing the pilot script directly.
"""
from __future__ import annotations

from . import _bootstrap  # noqa: F401

import workspace as _workspace

WORKSPACE_VERSION = _workspace.WORKSPACE_VERSION
WorkspaceValidationReport = _workspace.WorkspaceValidationReport

create_project_workspace = _workspace.create_project_workspace
validate_project = _workspace.validate_project
validate_all = _workspace.validate_all
generate_offline_parcel_brief = _workspace.generate_offline_parcel_brief
render_brief_html = _workspace.render_brief_html
write_brief_html_report = _workspace.write_brief_html_report
record_report = _workspace.record_report
project_manifest_path = _workspace.project_manifest_path
report_index_path = _workspace.report_index_path
report_memory_path = _workspace.report_memory_path
iter_project_dirs = _workspace.iter_project_dirs

__all__ = [
    "WORKSPACE_VERSION",
    "WorkspaceValidationReport",
    "create_project_workspace",
    "validate_project",
    "validate_all",
    "generate_offline_parcel_brief",
    "render_brief_html",
    "write_brief_html_report",
    "record_report",
    "project_manifest_path",
    "report_index_path",
    "report_memory_path",
    "iter_project_dirs",
]
