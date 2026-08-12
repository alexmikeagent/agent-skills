from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "uipath_style_lint.py"
SPEC = importlib.util.spec_from_file_location("uipath_style_lint", SCRIPT)
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lint
SPEC.loader.exec_module(lint)


ANNOTATION = "&#10;".join(
    (
        "Purpose: Set the terminal timeout.",
        "Runs in: Invision process stage.",
        "Inputs: in_intTimeoutMS - approved terminal timeout.",
        "Outputs: None",
        "Side effects: Updates an in-memory setting.",
        "Assumptions: The timeout was validated by the caller.",
        "Expectations: intTimeoutMS contains the approved timeout.",
        "Static values: milliseconds - timeout unit.",
        "Failure behavior: Propagates unexpected failures.",
        "Sensitive data: None",
    )
)


def activity_document(stem: str, members: str, variables: str, body: str, annotation: str = ANNOTATION) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<Activity xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          xmlns:ui="http://schemas.uipath.com/workflow/activities"
          xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation">
  <x:Members>{members}</x:Members>
  <Sequence DisplayName="{stem}" sap2010:Annotation.AnnotationText="{annotation}">
    <Sequence.Variables>{variables}</Sequence.Variables>
    {body}
  </Sequence>
</Activity>
'''


def boundary_start(stem: str) -> str:
    return (
        '<ui:LogMessage DisplayName="Log Message - Start process" Level="Info" '
        f'Message="[&quot;Start: {stem} | Set the approved terminal timeout.&quot;]" />'
    )


def boundary_end(stem: str) -> str:
    return (
        '<ui:LogMessage DisplayName="Log Message - End process" Level="Info" '
        f'Message="[&quot;End: {stem} | Set the approved terminal timeout.&quot;]" />'
    )


def assign(target: str, type_name: str, display: str) -> str:
    return f'''
    <Assign DisplayName="{display}">
      <Assign.To><OutArgument x:TypeArguments="{type_name}">[{target}]</OutArgument></Assign.To>
      <Assign.Value><InArgument x:TypeArguments="{type_name}">[Nothing]</InArgument></Assign.Value>
    </Assign>'''


def assign_value(target: str, type_name: str, value: str, display: str) -> str:
    return f'''
    <Assign DisplayName="{display}">
      <Assign.To><OutArgument x:TypeArguments="{type_name}">[{target}]</OutArgument></Assign.To>
      <Assign.Value><InArgument x:TypeArguments="{type_name}">[{value}]</InArgument></Assign.Value>
    </Assign>'''


class LinterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, source: str) -> Path:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def audit(self, relative: str) -> lint.AuditResult:
        return lint.audit_project(self.project, "selected", (relative,))

    def rules(self, result: lint.AuditResult, severity: str | None = None) -> set[str]:
        return {
            item.rule
            for item in result.findings
            if severity is None or item.severity == severity
        }

    def test_compliant_assign_uses_dynamic_safe_value(self) -> None:
        stem = "Invision_SetTimeout"
        source = activity_document(
            stem,
            '<x:Property Name="in_intTimeoutMS" Type="InArgument(x:Int32)" />',
            '<Variable x:TypeArguments="x:Int32" Name="intTimeoutMS" />',
            boundary_start(stem)
            + assign("intTimeoutMS", "x:Int32", "Assign - Set terminal timeout")
            + '''
    <ui:LogMessage DisplayName="Log Message - Assigned terminal timeout" Level="Info"
      Message="[&quot;Assigned the terminal timeout intTimeoutMS to &quot; + intTimeoutMS.ToString + &quot; milliseconds.&quot;]" />'''
            + boundary_end(stem),
        )
        self.write(f"{stem}.xaml", source)

        result = self.audit(f"{stem}.xaml")

        self.assertFalse(result.operational_errors)
        self.assertEqual([], [item for item in result.findings if item.severity == "error"])
        self.assertEqual(0, lint.exit_code(result, "error"))

    def test_sensitive_assignment_names_variable_without_interpolating_value(self) -> None:
        stem = "Invision_SetAccount"
        safe_source = activity_document(
            stem,
            "",
            '<Variable x:TypeArguments="x:String" Name="strPatientAccountNumber" />',
            boundary_start(stem)
            + assign("strPatientAccountNumber", "x:String", "Assign - Set patient account number")
            + '''
    <ui:LogMessage DisplayName="Log Message - Assigned patient account number" Level="Info"
      Message="[&quot;Assigned the patient account number to strPatientAccountNumber.&quot;]" />'''
            + boundary_end(stem),
        )
        self.write(f"{stem}.xaml", safe_source)
        safe_result = self.audit(f"{stem}.xaml")
        self.assertNotIn("SEC-LOG-001", self.rules(safe_result, "error"))

        unsafe_source = safe_source.replace(
            "strPatientAccountNumber.&quot;]",
            "strPatientAccountNumber to &quot; + strPatientAccountNumber + &quot;.&quot;]",
        )
        self.write(f"{stem}.xaml", unsafe_source)
        unsafe_result = self.audit(f"{stem}.xaml")
        self.assertIn("SEC-LOG-001", self.rules(unsafe_result, "error"))

    def test_multiple_assign_requires_one_newline_per_assignment(self) -> None:
        stem = "InitSetRetryValues"
        multiple_assign = '''
    <ui:MultipleAssign DisplayName="Multiple Assign - Set retry values">
      <ui:MultipleAssign.AssignOperations>
        <ui:AssignOperation>
          <ui:AssignOperation.To><OutArgument x:TypeArguments="x:Int32">[intRetryCount]</OutArgument></ui:AssignOperation.To>
        </ui:AssignOperation>
        <ui:AssignOperation>
          <ui:AssignOperation.To><OutArgument x:TypeArguments="x:String">[strPatientStatus]</OutArgument></ui:AssignOperation.To>
        </ui:AssignOperation>
      </ui:MultipleAssign.AssignOperations>
    </ui:MultipleAssign>
    <ui:LogMessage DisplayName="Log Message - Assigned retry values" Level="Info"
      Message="[&quot;Assigned the retry count intRetryCount to &quot; + intRetryCount.ToString + &quot;. Assigned the patient status to strPatientStatus.&quot;]" />'''
        source = activity_document(
            stem,
            "",
            '<Variable x:TypeArguments="x:Int32" Name="intRetryCount" />'
            '<Variable x:TypeArguments="x:String" Name="strPatientStatus" />',
            boundary_start(stem) + multiple_assign + boundary_end(stem),
        )
        self.write(f"{stem}.xaml", source)

        result = self.audit(f"{stem}.xaml")

        self.assertIn("HOUSE-LOG-009", self.rules(result, "error"))
        self.assertNotIn("SEC-LOG-001", self.rules(result, "error"))

    def test_sensitive_identifier_is_blocked_in_any_action_log(self) -> None:
        stem = "Invision_EnterAccount"
        source = activity_document(
            stem,
            '<x:Property Name="in_strPatientAccountNumber" Type="InArgument(x:String)" />',
            "",
            boundary_start(stem)
            + '''
    <ui:TypeInto DisplayName="Type Into - Enter patient account number" Text="[in_strPatientAccountNumber]" />
    <ui:LogMessage DisplayName="Log Message - Entered patient account number" Level="Info"
      Message="[&quot;Entered patient account number: &quot; + in_strPatientAccountNumber]" />'''
            + boundary_end(stem),
        )
        self.write(f"{stem}.xaml", source)

        result = self.audit(f"{stem}.xaml")

        self.assertIn("SEC-LOG-001", self.rules(result, "error"))
        messages = [item.message for item in result.findings if item.rule == "SEC-LOG-001"]
        self.assertTrue(any("in_strPatientAccountNumber" in message for message in messages))

    def test_assigned_constant_cannot_be_copied_into_log(self) -> None:
        stem = "InitRetryCounter"
        source = activity_document(
            stem,
            "",
            '<Variable x:TypeArguments="x:Int32" Name="intRetryCount" />',
            boundary_start(stem)
            + assign_value("intRetryCount", "x:Int32", "0", "Assign - Initialize retry counter")
            + '''
    <ui:LogMessage DisplayName="Log Message - Initialized retry counter" Level="Info"
      Message="[&quot;Assigned the retry counter intRetryCount to 0.&quot;]" />'''
            + boundary_end(stem),
        )
        self.write(f"{stem}.xaml", source)

        result = self.audit(f"{stem}.xaml")

        self.assertIn("HOUSE-LOG-018", self.rules(result, "error"))

    def test_invoke_workflow_uses_child_boundaries_without_caller_completion_log(self) -> None:
        stem = "Invision_RunSearch"
        source = activity_document(
            stem,
            "",
            "",
            boundary_start(stem)
            + '''
    <ui:InvokeWorkflowFile DisplayName="Invoke Workflow File - Search patient"
      WorkflowFileName="Invision_SearchPatient.xaml" />'''
            + boundary_end(stem),
        )
        self.write(f"{stem}.xaml", source)

        result = self.audit(f"{stem}.xaml")

        self.assertNotIn("HOUSE-LOG-013", self.rules(result))
        self.assertNotIn("HOUSE-LOG-003", self.rules(result))

    def test_filename_shortener_preserves_structure_and_stops_under_limit(self) -> None:
        stem = "Invision_SearchPatientAccountVerificationTerminal"

        suggestion, changes = lint.shorten_workflow_stem(stem)

        self.assertTrue(suggestion.startswith("Invision_Search"))
        self.assertLessEqual(len(suggestion + ".xaml"), 40)
        self.assertTrue(changes)
        self.assertNotRegex(suggestion, r"(?:1|2|New)$")

    def test_more_than_twenty_arguments_is_an_error(self) -> None:
        stem = "UtilMapValues"
        members = "".join(
            f'<x:Property Name="in_intValue{index}" Type="InArgument(x:Int32)" />'
            for index in range(21)
        )
        source = activity_document(stem, members, "", boundary_start(stem) + boundary_end(stem))
        self.write(f"{stem}.xaml", source)

        result = self.audit(f"{stem}.xaml")

        self.assertIn("HOUSE-ARG-004", self.rules(result, "error"))

    def test_active_waiver_converts_house_error_to_info(self) -> None:
        finding = lint.Finding(
            "HOUSE-WF-006",
            "error",
            "House",
            "Components/ProLegacyExtract.xaml",
            "Workflow is too large.",
        )
        config = lint.StyleConfig(
            waivers=(
                lint.Waiver(
                    rule="HOUSE-WF-006",
                    workflow="Components/*.xaml",
                    rationale="Bounded legacy exception.",
                    approver="COE architecture",
                    expiration=date.today() + timedelta(days=30),
                ),
            )
        )

        result = lint.apply_waivers((finding,), config)

        self.assertEqual("info", result[0].severity)
        self.assertTrue(result[0].waived)
        self.assertEqual("error", result[0].original_severity)

    def test_security_findings_cannot_be_waived(self) -> None:
        finding = lint.Finding(
            "SEC-LOG-001",
            "error",
            "Security",
            "Invision_SetAccount.xaml",
            "Sensitive value was interpolated.",
        )
        config = lint.StyleConfig(
            waivers=(
                lint.Waiver(
                    rule="SEC-*",
                    workflow="*.xaml",
                    rationale="Not allowed to take effect.",
                    approver="Nobody",
                    expiration=date.today() + timedelta(days=30),
                ),
            )
        )

        result = lint.apply_waivers((finding,), config)

        self.assertEqual("error", result[0].severity)
        self.assertFalse(result[0].waived)

    def test_test_case_workflows_are_excluded_in_v1(self) -> None:
        self.write("TC_Invision_SetTimeout.xaml", "<not-xml")

        result = self.audit("TC_Invision_SetTimeout.xaml")

        self.assertEqual([], result.files)
        self.assertFalse(result.operational_errors)

    def test_parse_failure_returns_operational_exit_code(self) -> None:
        self.write("UtilBrokenWorkflow.xaml", "<Activity>")

        result = self.audit("UtilBrokenWorkflow.xaml")

        self.assertTrue(result.operational_errors)
        self.assertEqual(2, lint.exit_code(result, "error"))

    def test_changed_scope_finds_modified_xaml(self) -> None:
        stem = "UtilMoveFile"
        relative = f"Components/Utility/{stem}.xaml"
        source = activity_document(stem, "", "", boundary_start(stem) + boundary_end(stem))
        self.write(relative, source)
        for command in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "style-test@example.invalid"),
            ("git", "config", "user.name", "Style Test"),
            ("git", "add", relative),
            ("git", "commit", "-qm", "fixture"),
        ):
            subprocess.run(command, cwd=self.project, check=True, capture_output=True)
        self.write(relative, source.replace("Set the terminal timeout.", "Move one file."))

        result = lint.audit_project(self.project, "changed")

        self.assertEqual([relative], result.files)

    def test_native_reframework_main_is_protected(self) -> None:
        self.write("Main.xaml", "<not-xml")

        result = self.audit("Main.xaml")

        self.assertEqual([], result.files)
        self.assertFalse(result.operational_errors)

    def test_json_configuration_supports_explicit_safe_values(self) -> None:
        config_path = self.project / ".uipath-style.json"
        config_path.write_text(
            json.dumps(
                {
                    "safe_value_classifications": {
                        "safe": ["strWorkflowName"],
                        "sensitive": ["strPatient*"],
                    }
                }
            ),
            encoding="utf-8",
        )

        config = lint.load_config(self.project)

        self.assertEqual("safe", lint.value_classification("strWorkflowName", config))
        self.assertEqual("sensitive", lint.value_classification("strPatientStatus", config))


if __name__ == "__main__":
    unittest.main()
