import json
import time
from pathlib import Path

import pytest

from skills_testing.eval_runner import EvalResult, EvalRun
from skills_testing.report_generator import ReportGenerator, _normalize_error


@pytest.fixture
def sample_run():
    return EvalRun(
        run_id="test-001",
        timestamp=time.time(),
        results=[
            EvalResult("scenario_a", "skill_alpha", True, 100.0, cost_usd=0.001),
            EvalResult("scenario_b", "skill_alpha", True, 150.0, cost_usd=0.002),
            EvalResult(
                "scenario_c", "skill_alpha", False, 200.0,
                errors=["Missing required tool: bash"],
                cost_usd=0.0,
            ),
            EvalResult("scenario_d", "skill_beta", True, 50.0, cost_usd=0.001),
            EvalResult(
                "scenario_e", "skill_beta", False, 300.0,
                errors=["Missing required tool: bash"],
                cost_usd=0.0,
            ),
            EvalResult(
                "scenario_f", "skill_beta", False, 400.0,
                errors=["Missing required tool: lsp_diagnostics"],
                cost_usd=0.0,
            ),
        ],
        total_cost_usd=0.004,
        total_duration_ms=1200.0,
    )


class TestErrorNormalize:
    def test_strips_numbers(self):
        norm = _normalize_error("found 42 errors at line 100")
        assert norm == "found N errors at line N"

    def test_strips_quoted_strings(self):
        norm = _normalize_error("module 'foo.bar' not found with \"key_123\"")
        assert norm == "module '' not found with \"\""

    def test_is_case_insensitive(self):
        a = _normalize_error("Missing Required Tool: Bash")
        b = _normalize_error("missing required tool: bash")
        assert a == b


class TestReportGeneratorMarkdown:
    def test_overview_stats(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        assert "test-001" in md
        assert "Passed:** 3" in md
        assert "Failed:** 3" in md
        assert "$0.0040" in md

    def test_per_skill_summary_present(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        assert "Per-Skill Summary" in md
        assert "skill_alpha" in md
        assert "skill_beta" in md
        assert "66.7%" in md  # skill_alpha: 2/3 passed
        assert "33.3%" in md  # skill_beta: 1/3 passed

    def test_per_skill_summary_has_correct_columns(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        assert "| Skill | Scenarios | Passed | Failed | Pass Rate | Avg Duration | Total Cost |" in md

    def test_error_clusters_present(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        assert "Error Clusters" in md

    def test_error_clusters_group_similar_errors(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        missing_bash_lines = [l for l in md.split("\n") if "Missing required tool: bash" in l]
        # Should appear at least 3 times: cluster header + 2 examples
        assert len(missing_bash_lines) >= 2

    def test_failures_section(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        assert "## Failures" in md
        assert "scenario_c" in md
        assert "scenario_e" in md
        assert "scenario_f" in md

    def test_no_crash_with_all_passing(self):
        gen = ReportGenerator()
        run = EvalRun(
            run_id="all-pass",
            timestamp=time.time(),
            results=[EvalResult("s1", "sk1", True, 10.0)],
            total_duration_ms=10.0,
        )
        md = gen.generate_markdown(run)
        assert "**Passed:** 1" in md
        assert "**Failed:** 0" in md
        assert "Error Clusters" not in md
        assert "## Failures" not in md

    def test_results_table(self, sample_run):
        gen = ReportGenerator()
        md = gen.generate_markdown(sample_run)
        assert "## Results" in md
        assert "| Scenario | Skill | Status | Duration | Cost |" in md
        assert "PASS" in md
        assert "FAIL" in md

    def test_no_crash_with_empty_errors(self):
        gen = ReportGenerator()
        run = EvalRun(
            run_id="empty-err",
            timestamp=time.time(),
            results=[EvalResult("s1", "sk1", False, 10.0, errors=[])],
            total_duration_ms=10.0,
        )
        md = gen.generate_markdown(run)
        assert "## Failures" in md


class TestReportGeneratorJson:
    def test_structure(self, sample_run):
        gen = ReportGenerator()
        js = gen.generate_json(sample_run)
        d = json.loads(js)
        assert d["run_id"] == "test-001"
        assert d["total_scenarios"] == 6
        assert d["passed"] == 3
        assert d["failed"] == 3

    def test_per_skill_in_json(self, sample_run):
        gen = ReportGenerator()
        d = json.loads(gen.generate_json(sample_run))
        skills = d["per_skill"]
        assert len(skills) == 2
        alpha = next(s for s in skills if s["skill"] == "skill_alpha")
        assert alpha["total"] == 3
        assert alpha["passed"] == 2
        assert alpha["pass_rate"] == 66.7
        assert alpha["avg_duration_ms"] == 150.0
        assert alpha["total_cost_usd"] == 0.003

    def test_results_in_json(self, sample_run):
        gen = ReportGenerator()
        d = json.loads(gen.generate_json(sample_run))
        results = d["results"]
        assert len(results) == 6
        r = results[2]
        assert r["scenario"] == "scenario_c"
        assert r["passed"] == False
        assert r["errors"] == ["Missing required tool: bash"]

    def test_error_clusters_in_json(self, sample_run):
        gen = ReportGenerator()
        d = json.loads(gen.generate_json(sample_run))
        clusters = d["error_clusters"]
        assert len(clusters) == 2
        bash_cluster = next(c for c in clusters if "bash" in c["representative"])
        assert bash_cluster["count"] == 2

    def test_trend_no_baseline(self, sample_run):
        gen = ReportGenerator()
        d = json.loads(gen.generate_json(sample_run))
        assert d["trend"]["has_baseline"] == False


class TestReportGeneratorTrendDelta:
    def test_trend_delta_with_baseline(self, tmp_path):
        gen = ReportGenerator(output_dir=tmp_path)

        # Write a previous run as baseline
        prev_data = {
            "run_id": "prev-001",
            "total_scenarios": 4,
            "passed": 2,
            "failed": 2,
            "total_cost_usd": 0.010,
            "total_duration_ms": 800.0,
        }
        (tmp_path / "run_prev-001.json").write_text(json.dumps(prev_data))

        run = EvalRun(
            run_id="curr-001",
            timestamp=time.time(),
            results=[
                EvalResult("s1", "sk1", True, 100.0),
                EvalResult("s2", "sk1", True, 100.0),
                EvalResult("s3", "sk1", True, 100.0),
            ],
            total_cost_usd=0.000,
            total_duration_ms=300.0,
        )

        d = json.loads(gen.generate_json(run))
        trend = d["trend"]
        assert trend["has_baseline"] == True
        assert trend["previous_run_id"] == "prev-001"
        assert trend["scenario_delta"] == -1  # 3 - 4
        assert trend["pass_count_delta"] == 1  # 3 - 2
        assert trend["pass_rate_delta"] == 50.0  # 100% - 50%
        assert trend["duration_delta_ms"] == -500.0
        assert trend["cost_delta_usd"] == -0.010

    def test_trend_in_markdown(self, tmp_path):
        gen = ReportGenerator(output_dir=tmp_path)

        prev_data = {
            "run_id": "prev-001",
            "total_scenarios": 2,
            "passed": 1,
            "failed": 1,
            "total_cost_usd": 0.0,
            "total_duration_ms": 500.0,
        }
        (tmp_path / "run_prev-001.json").write_text(json.dumps(prev_data))

        run = EvalRun(
            run_id="curr-001",
            timestamp=time.time(),
            results=[EvalResult("s1", "sk1", True, 100.0)],
            total_duration_ms=100.0,
        )

        md = gen.generate_markdown(run)
        assert "## Trend vs Baseline" in md
        assert "prev-001" in md
        assert "Scenarios:** -1" in md


class TestReportGeneratorSave:
    def test_save_json_writes_both_paths(self, tmp_path):
        gen = ReportGenerator(output_dir=tmp_path)
        run = EvalRun(
            run_id="save-test",
            timestamp=time.time(),
            results=[EvalResult("s1", "sk1", True, 50.0)],
            total_duration_ms=50.0,
        )
        path = gen.save_json(run)
        assert path.name == "report_save-test.json"
        assert (tmp_path / "run_save-test.json").exists()

    def test_save_markdown(self, tmp_path):
        gen = ReportGenerator(output_dir=tmp_path)
        run = EvalRun(
            run_id="md-test",
            timestamp=time.time(),
            results=[EvalResult("s1", "sk1", True, 50.0)],
            total_duration_ms=50.0,
        )
        path = gen.save_markdown(run)
        assert path.name == "report_md-test.md"
        content = path.read_text()
        assert "Skill Eval Report" in content

    def test_save_junit_xml(self, tmp_path):
        gen = ReportGenerator(output_dir=tmp_path)
        run = EvalRun(
            run_id="junit-test",
            timestamp=time.time(),
            results=[
                EvalResult("s1", "sk1", True, 50.0),
                EvalResult("s2", "sk1", False, 75.0, errors=["fail"]),
            ],
            total_duration_ms=125.0,
        )
        path = gen.save_junit_xml(run)
        assert path.suffix == ".xml"


class TestReportGeneratorJunitXml:
    def test_junit_unchanged_behavior(self, sample_run):
        gen = ReportGenerator()
        xml = gen.generate_junit_xml(sample_run)
        assert "<testsuite" in xml
        assert 'name="skill-eval"' in xml
        assert 'tests="6"' in xml
        assert 'failures="3"' in xml
        assert "<testcase" in xml
        assert "<failure" in xml

    def test_junit_all_pass_no_failures(self):
        gen = ReportGenerator()
        run = EvalRun(
            run_id="all-pass-xml",
            timestamp=time.time(),
            results=[EvalResult("s1", "sk1", True, 10.0)],
            total_duration_ms=10.0,
        )
        xml = gen.generate_junit_xml(run)
        assert 'failures="0"' in xml
        assert "<failure" not in xml
