from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceItem:
    source_type: str
    path: str = ""
    symbol: str = ""
    line_start: int = 0
    line_end: int = 0
    excerpt: str = ""
    rationale: str = ""
    confidence: str = "medium"


@dataclass(frozen=True)
class EvidenceBundle:
    code_evidence: list[EvidenceItem] = field(default_factory=list)
    paper_evidence: list[EvidenceItem] = field(default_factory=list)


@dataclass(frozen=True)
class QuestionPlan:
    question: str
    answer_type: str
    keywords: list[str]
    needs_code: bool = True
    needs_paper: bool = False


@dataclass(frozen=True)
class AnswerBundle:
    question: str
    answer: str
    answer_type: str
    code_evidence: list[EvidenceItem]
    paper_evidence: list[EvidenceItem]
    confidence: str
    uncertainty: list[str] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)
