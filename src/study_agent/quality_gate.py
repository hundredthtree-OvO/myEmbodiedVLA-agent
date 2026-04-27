from __future__ import annotations

from dataclasses import dataclass

from .models import StudyArtifact


@dataclass(frozen=True)
class EvidenceQualityReport:
    status: str
    reasons: list[str]

    @property
    def should_call_codex(self) -> bool:
        return self.status != "fail"


def evaluate_evidence_quality(artifact: StudyArtifact) -> EvidenceQualityReport:
    reasons: list[str] = []
    paper_text = (artifact.paper.text or "").strip()
    if not paper_text:
        reasons.append("paper_text_missing")

    repo = artifact.repo
    if not repo.architecture_entry_candidates and not repo.architecture_skeleton_candidates:
        reasons.append("architecture_entry_and_skeleton_missing")

    if not repo.entry_candidates and len(repo.hits) < 5:
        reasons.append("very_low_repo_evidence")

    if "paper_text_missing" in reasons:
        return EvidenceQualityReport(status="fail", reasons=reasons)
    if "architecture_entry_and_skeleton_missing" in reasons and "very_low_repo_evidence" in reasons:
        return EvidenceQualityReport(status="fail", reasons=reasons)
    if reasons:
        return EvidenceQualityReport(status="warn", reasons=reasons)
    return EvidenceQualityReport(status="ok", reasons=[])


def prepend_quality_gate_note(markdown: str, report: EvidenceQualityReport) -> str:
    if report.status == "ok":
        return markdown
    note_lines = [
        "> [!WARNING]",
        f"> Evidence quality gate status: `{report.status}`.",
        f"> Reasons: {', '.join(report.reasons) or 'none'}.",
        "> The run was downgraded to an offline-style result because the pre-Codex evidence looked too weak.",
        "",
    ]
    return "\n".join(note_lines) + markdown
