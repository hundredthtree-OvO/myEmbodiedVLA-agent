from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .card_models import CardArtifact
from .graph import GraphEdge, GraphNode, GraphNodeRef
from .paper import build_paper_slug, build_paper_understanding
from .parser_backend import CompositeParserBackend, detect_language
from .qa_models import AnswerBundle, EvidenceItem, QuestionPlan
from .repo import ingest_paper, ingest_repo
from .repo.ingest import REPO_TEXT_SUFFIXES, SKIP_DIRS
from .workspace_models import PaperAttachment, RepoIndex, WorkspaceManifest
from .workspace_store import (
    WORKSPACES_ROOT,
    create_or_update_workspace,
    latest_session,
    load_manifest,
    load_paper_attachments,
    record_paper_attachment,
    save_card,
    save_manifest,
    save_question_answer,
    utc_now_iso,
    workspace_root,
)


MAX_CODE_EVIDENCE = 5
MAX_PAPER_EVIDENCE = 4


@dataclass(frozen=True)
class WorkspaceIndexResult:
    manifest: WorkspaceManifest
    repo_index: RepoIndex


def index_workspace(
    repo_source: str,
    workspace_name: str,
    root: Path = WORKSPACES_ROOT,
) -> WorkspaceIndexResult:
    repo_info = ingest_repo(repo_source, [])
    nodes, edges, languages = _build_workspace_graph(repo_info.path)
    manifest = create_or_update_workspace(
        name=workspace_name,
        repo_source=repo_source,
        repo_path=str(repo_info.path),
        graph_node_count=len(nodes),
        graph_edge_count=len(edges),
        root=root,
    )
    base = workspace_root(manifest.workspace_id, root)
    _write_jsonl(base / "graph_nodes.jsonl", [asdict(node) for node in nodes])
    _write_jsonl(base / "graph_edges.jsonl", [_edge_to_json(edge) for edge in edges])
    repo_index = RepoIndex(
        workspace_id=manifest.workspace_id,
        repo_source=repo_source,
        repo_path=str(repo_info.path),
        files_scanned=repo_info.files_scanned,
        languages=sorted(languages),
        graph_nodes_path=str((base / "graph_nodes.jsonl").as_posix()),
        graph_edges_path=str((base / "graph_edges.jsonl").as_posix()),
        top_files=_top_files(repo_info),
    )
    (base / "repo_index.json").write_text(
        json.dumps(asdict(repo_index), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return WorkspaceIndexResult(manifest=manifest, repo_index=repo_index)


def attach_paper_to_workspace(
    workspace_id: str,
    paper_source: str,
    root: Path = WORKSPACES_ROOT,
) -> PaperAttachment:
    manifest = load_manifest(workspace_id, root)
    paper = ingest_paper(paper_source)
    understanding = build_paper_understanding(paper, [])
    paper_id = build_paper_slug(paper_source, paper.title)
    paper_dir = workspace_root(workspace_id, root) / "papers" / paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "paper_text.md").write_text(paper.text or paper.raw_excerpt, encoding="utf-8")
    (paper_dir / "paper_understanding.json").write_text(
        json.dumps(_safe_asdict(understanding), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if Path(paper_source).exists():
        source_path = Path(paper_source)
        target = paper_dir / source_path.name
        if not target.exists():
            target.write_bytes(source_path.read_bytes())
    attachment = PaperAttachment(
        paper_id=paper_id,
        title=paper.title,
        source=paper_source,
        attached_at=utc_now_iso(),
        claims=[claim.claim for claim in understanding.claims[:8]],
        named_modules_or_concepts=[concept.concept for concept in understanding.concepts[:12]],
        design_rationales=[claim.claim for claim in understanding.claims if claim.claim_type in {"proposal", "architecture", "method"}][:6],
        open_alignment_questions=understanding.questions[:8],
    )
    record_paper_attachment(workspace_id, attachment, root)
    _merge_paper_graph(workspace_id, attachment, root)
    return attachment


def ask_workspace(
    workspace_id: str,
    question: str,
    root: Path = WORKSPACES_ROOT,
) -> AnswerBundle:
    manifest = load_manifest(workspace_id, root)
    plan = build_question_plan(question)
    repo_info = ingest_repo(manifest.repo_path, plan.keywords)
    paper_attachments = load_paper_attachments(workspace_id, root)
    code_evidence = _collect_code_evidence(repo_info, plan)
    paper_evidence = _collect_paper_evidence(paper_attachments, plan) if plan.needs_paper else []
    answer = _build_answer_bundle(plan, code_evidence, paper_evidence)
    save_question_answer(workspace_id, plan, answer, root)
    return answer


def build_card(
    workspace_id: str,
    topic: str,
    root: Path = WORKSPACES_ROOT,
) -> CardArtifact:
    latest = latest_session(workspace_id, root)
    if latest is None:
        raise ValueError("No Q/A session found for this workspace. Run `ask` first.")
    session_id, session_dir = latest
    answer_data = json.loads((session_dir / "answer.json").read_text(encoding="utf-8"))
    answer = AnswerBundle(
        question=answer_data["question"],
        answer=answer_data["answer"],
        answer_type=answer_data["answer_type"],
        code_evidence=[EvidenceItem(**item) for item in answer_data.get("code_evidence", [])],
        paper_evidence=[EvidenceItem(**item) for item in answer_data.get("paper_evidence", [])],
        confidence=answer_data["confidence"],
        uncertainty=list(answer_data.get("uncertainty", [])),
        follow_up_questions=list(answer_data.get("follow_up_questions", [])),
    )
    card_type = _card_type_for_topic(topic, answer)
    title = topic.strip() or answer.question
    markdown = _render_card_markdown(card_type, title, answer)
    card_id = _slugify(title)
    card = CardArtifact(
        card_id=card_id,
        card_type=card_type,
        title=title,
        topic=topic,
        markdown=markdown,
        source_session_id=session_id,
    )
    save_card(workspace_id, card, root)
    return card


def export_note(
    workspace_id: str,
    output_path: Path | None = None,
    root: Path = WORKSPACES_ROOT,
) -> Path:
    manifest = load_manifest(workspace_id, root)
    base = workspace_root(workspace_id, root)
    sessions_dir = base / "sessions"
    cards_dir = base / "cards"
    lines = [
        f"# {manifest.name} Research Workspace",
        "",
        "## Repo",
        f"- Source: `{manifest.repo_source}`",
        f"- Path: `{manifest.repo_path}`",
        f"- Graph nodes: `{manifest.graph_node_count}`",
        f"- Graph edges: `{manifest.graph_edge_count}`",
        "",
    ]
    attachments = load_paper_attachments(workspace_id, root)
    lines.append("## Papers")
    if attachments:
        for item in attachments:
            lines.append(f"- `{item.title}`")
            if item.design_rationales:
                lines.append(f"  - rationale cues: {'; '.join(item.design_rationales[:2])}")
    else:
        lines.append("- none")
    lines.extend(["", "## Sessions"])
    if sessions_dir.exists():
        for session_dir in sorted((item for item in sessions_dir.iterdir() if item.is_dir()), key=lambda item: item.name):
            answer_path = session_dir / "answer.json"
            if not answer_path.exists():
                continue
            answer_data = json.loads(answer_path.read_text(encoding="utf-8"))
            lines.append(f"### {answer_data['question']}")
            lines.append("")
            lines.append(answer_data["answer"])
            lines.append("")
    else:
        lines.append("- none")
    lines.append("## Cards")
    if cards_dir.exists():
        cards = sorted(cards_dir.glob("*.md"))
        if cards:
            for card in cards:
                lines.append(f"- `{card.stem}`")
        else:
            lines.append("- none")
    else:
        lines.append("- none")
    lines.append("")
    target = output_path or (base / "exported-note.md")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def build_question_plan(question: str) -> QuestionPlan:
    lowered = question.lower()
    keywords = _question_keywords(question)
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    if any(token in lowered for token in ("implementation", "implement", "具体实现", "实现细节")):
        return QuestionPlan(question=question, answer_type="implementation", keywords=keywords, needs_paper=False)
    if "为什么" in question or "设计" in question or any(token in tokens for token in ("why", "design", "motivation", "rationale")):
        return QuestionPlan(question=question, answer_type="rationale", keywords=keywords, needs_paper=True)
    if "生成" in question or "路径" in question or "流程" in question or any(token in tokens for token in ("path", "trace", "flow", "how")):
        return QuestionPlan(question=question, answer_type="trace", keywords=keywords, needs_paper=False)
    if "论文" in question or "对应" in question or "存在" in question or any(token in tokens for token in ("paper", "align", "alignment")):
        return QuestionPlan(question=question, answer_type="comparison", keywords=keywords, needs_paper=True)
    return QuestionPlan(question=question, answer_type="implementation", keywords=keywords, needs_paper=False)


def _build_workspace_graph(repo_root: Path) -> tuple[list[GraphNode], list[GraphEdge], set[str]]:
    parser = CompositeParserBackend()
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    languages: set[str] = set()
    seen_nodes: set[tuple[str, str]] = set()
    seen_edges: set[tuple[str, str, str, str, str]] = set()

    def add_node(node: GraphNode) -> None:
        key = (node.node_type, node.node_id)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(node)

    def add_edge(edge: GraphEdge) -> None:
        key = (edge.edge_type, edge.src.node_type, edge.src.node_id, edge.dst.node_type, edge.dst.node_id)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(edge)

    for file_path in _iter_repo_files(repo_root):
        rel = file_path.relative_to(repo_root).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="replace")
        result = parser.parse_file(Path(rel), text)
        language = result.language or detect_language(file_path)
        languages.add(language)
        file_node = GraphNode("File", f"file:{rel}", {"path": rel, "language": language})
        add_node(file_node)
        if language == "config":
            config_node = GraphNode("Config", f"config:{rel}", {"path": rel})
            add_node(config_node)
            add_edge(GraphEdge("configured_by", file_node.ref, config_node.ref, {"confidence": "medium"}))
        for symbol in result.parsed.symbols:
            node_type = "Class" if symbol.kind == "class" else "Function"
            symbol_id = f"symbol:{rel}::{symbol.name}"
            symbol_node = GraphNode(
                node_type,
                symbol_id,
                {
                    "name": symbol.name,
                    "kind": symbol.kind,
                    "file": rel,
                    "line_start": symbol.line_start,
                    "line_end": symbol.line_end,
                },
            )
            add_node(symbol_node)
            add_edge(GraphEdge("defines", file_node.ref, symbol_node.ref, {"line": symbol.line_start}))
            excerpt = _excerpt_by_line(text, symbol.line_start, symbol.line_end)
            span_node = GraphNode(
                "EvidenceSpan",
                f"span:{rel}:{symbol.line_start}:{symbol.name}",
                {
                    "path": rel,
                    "line_start": symbol.line_start,
                    "line_end": symbol.line_end,
                    "excerpt": excerpt,
                    "symbol": symbol.name,
                },
            )
            add_node(span_node)
            add_edge(GraphEdge("defines", symbol_node.ref, span_node.ref, {"confidence": "high"}))
        for item in result.parsed.imports:
            import_name = item.module or item.imported_name or "unknown"
            import_node = GraphNode("ImportTarget", f"import:{import_name}", {"name": import_name})
            add_node(import_node)
            add_edge(GraphEdge("imports", file_node.ref, import_node.ref, {"line": item.line}))
        for relation in result.parsed.relations:
            source_ref = file_node.ref
            if relation.source_symbol:
                source_ref = GraphNodeRef("Class" if "." not in relation.source_symbol and relation.source_symbol[:1].isupper() else "Function", f"symbol:{rel}::{relation.source_symbol}")
            target_ref = GraphNodeRef("SymbolRef", f"ref:{relation.target_name}")
            add_node(GraphNode("SymbolRef", target_ref.node_id, {"name": relation.target_name}))
            add_edge(GraphEdge(relation.relation_type, source_ref, target_ref, {"line": relation.line}))
    return nodes, edges, languages


def _merge_paper_graph(workspace_id: str, attachment: PaperAttachment, root: Path) -> None:
    base = workspace_root(workspace_id, root)
    nodes = _load_graph_nodes(base / "graph_nodes.jsonl")
    edges = _load_graph_edges(base / "graph_edges.jsonl")
    symbol_targets = [node for node in nodes if node.node_type in {"Class", "Function", "File"}]
    for claim in attachment.claims:
        claim_node = GraphNode("PaperClaim", f"claim:{attachment.paper_id}:{_slugify(claim)[:40]}", {"claim": claim, "paper_id": attachment.paper_id})
        nodes.append(claim_node)
        for concept in attachment.named_modules_or_concepts:
            if concept.lower() not in claim.lower():
                continue
            concept_node = GraphNode("Concept", f"concept:{_slugify(concept)}", {"name": concept, "paper_id": attachment.paper_id})
            nodes.append(concept_node)
            edges.append(GraphEdge("mentioned_in_paper", concept_node.ref, claim_node.ref, {"paper_id": attachment.paper_id}))
            for target in symbol_targets:
                haystack = " ".join(str(value) for value in target.attributes.values()).lower()
                if concept.lower() in haystack:
                    edges.append(GraphEdge("supports_claim", concept_node.ref, target.ref, {"status": "INFERRED", "confidence": "medium"}))
    deduped_nodes = _dedupe_nodes(nodes)
    deduped_edges = _dedupe_edges(edges)
    _write_jsonl(base / "graph_nodes.jsonl", [asdict(node) for node in deduped_nodes])
    _write_jsonl(base / "graph_edges.jsonl", [_edge_to_json(edge) for edge in deduped_edges])
    manifest = load_manifest(workspace_id, root)
    save_manifest(
        WorkspaceManifest(
            workspace_id=manifest.workspace_id,
            name=manifest.name,
            repo_source=manifest.repo_source,
            repo_path=manifest.repo_path,
            created_at=manifest.created_at,
            updated_at=utc_now_iso(),
            parser_backend=manifest.parser_backend,
            graph_node_count=len(deduped_nodes),
            graph_edge_count=len(deduped_edges),
            papers=manifest.papers,
            sessions=manifest.sessions,
            cards=manifest.cards,
        ),
        root,
    )


def _collect_code_evidence(repo_info, plan: QuestionPlan) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    keywords = [keyword.lower() for keyword in plan.keywords]
    symbol_scores: list[tuple[int, object]] = []
    for symbol in repo_info.symbols:
        haystack = f"{symbol.name} {symbol.path}".lower()
        score = sum(3 for keyword in keywords if keyword and keyword in haystack)
        if score:
            symbol_scores.append((score, symbol))
    for _, symbol in sorted(symbol_scores, key=lambda item: (-item[0], item[1].path, item[1].line))[:MAX_CODE_EVIDENCE]:
        evidence.append(
            EvidenceItem(
                source_type="code",
                path=symbol.path,
                symbol=symbol.name,
                line_start=symbol.line,
                line_end=symbol.line,
                excerpt=_excerpt_for_path(repo_info.path / symbol.path, symbol.line),
                rationale="symbol match",
                confidence="high",
            )
        )
    if evidence:
        return evidence
    for hit in repo_info.hits[:MAX_CODE_EVIDENCE]:
        evidence.append(
            EvidenceItem(
                source_type="code",
                path=hit.path,
                line_start=hit.line,
                line_end=hit.line,
                excerpt=_excerpt_for_path(repo_info.path / hit.path, hit.line),
                rationale=f"keyword hit: {hit.term}",
                confidence="medium",
            )
        )
    return evidence


def _collect_paper_evidence(attachments: list[PaperAttachment], plan: QuestionPlan) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for attachment in attachments:
        for claim in attachment.claims:
            if _text_matches_keywords(claim, plan.keywords):
                evidence.append(
                    EvidenceItem(
                        source_type="paper",
                        path=attachment.paper_id,
                        excerpt=claim,
                        rationale="paper claim match",
                        confidence="medium",
                    )
                )
        for rationale in attachment.design_rationales:
            if _text_matches_keywords(rationale, plan.keywords):
                evidence.append(
                    EvidenceItem(
                        source_type="paper",
                        path=attachment.paper_id,
                        excerpt=rationale,
                        rationale="design rationale cue",
                        confidence="medium",
                    )
                )
    return evidence[:MAX_PAPER_EVIDENCE]


def _build_answer_bundle(
    plan: QuestionPlan,
    code_evidence: list[EvidenceItem],
    paper_evidence: list[EvidenceItem],
) -> AnswerBundle:
    uncertainty: list[str] = []
    follow_up: list[str] = []
    confidence = "high" if code_evidence else "low"
    lines: list[str] = []
    if plan.answer_type == "implementation":
        lines.append("Code-backed implementation summary:")
        if code_evidence:
            for item in code_evidence[:3]:
                location = f"{item.path}:{item.line_start}" if item.path else "unknown"
                symbol = f" `{item.symbol}`" if item.symbol else ""
                lines.append(f"- {location}{symbol}: {item.rationale}.")
            follow_up.append("这个模块在训练和推理路径里分别由谁调用？")
        else:
            lines.append("- No direct implementation evidence was confirmed from the current repo scan.")
            uncertainty.append("No direct code evidence found for the requested implementation.")
            confidence = "low"
    elif plan.answer_type == "rationale":
        lines.append("Code facts:")
        if code_evidence:
            for item in code_evidence[:3]:
                lines.append(f"- `{item.path}:{item.line_start}` shows `{item.symbol or 'local logic'}`.")
        else:
            lines.append("- No direct code fact was confirmed yet.")
            uncertainty.append("Design explanation is weak because no direct code evidence was confirmed.")
        lines.append("")
        lines.append("Design rationale:")
        if paper_evidence:
            for item in paper_evidence[:2]:
                lines.append(f"- Paper evidence suggests: {item.excerpt}")
            confidence = "medium" if code_evidence else "low"
        else:
            lines.append("- No attached paper evidence matched this question, so the rationale below is code-only inference.")
            uncertainty.append("No attached paper evidence matched; rationale is inferred from code structure only.")
            confidence = "medium" if code_evidence else "low"
        follow_up.append("这部分设计在论文里对应哪一段主张？")
    elif plan.answer_type == "trace":
        lines.append("Likely path trace:")
        if code_evidence:
            for item in code_evidence[:4]:
                lines.append(f"- `{item.path}:{item.line_start}` -> {item.symbol or item.rationale}")
            follow_up.append("这条路径里的 loss / sample / decode 分别在哪一步？")
        else:
            lines.append("- No direct path trace was confirmed from the current repo scan.")
            uncertainty.append("Trace evidence is missing.")
            confidence = "low"
    else:
        lines.append("Paper-code alignment summary:")
        if code_evidence:
            lines.append("- Code evidence exists for at least part of the requested concept.")
        else:
            lines.append("- No direct code evidence was confirmed for the requested concept.")
        if paper_evidence:
            lines.append("- Related paper-side concept or claim was found in attached paper material.")
            confidence = "medium"
        else:
            lines.append("- No related paper-side evidence was found in attached paper material.")
            uncertainty.append("No attached paper evidence matched the alignment target.")
        follow_up.append("这个概念在代码里是显式模块还是隐式实现？")

    if not code_evidence:
        uncertainty.append("Answer may be incomplete because retrieval fell back to sparse signals.")

    return AnswerBundle(
        question=plan.question,
        answer="\n".join(lines).strip(),
        answer_type=plan.answer_type,
        code_evidence=code_evidence,
        paper_evidence=paper_evidence,
        confidence=confidence,
        uncertainty=uncertainty[:4],
        follow_up_questions=follow_up[:4],
    )


def _card_type_for_topic(topic: str, answer: AnswerBundle) -> str:
    lowered = topic.lower()
    if lowered in {"repo", "overview", "architecture"}:
        return "RepoCard"
    if topic.strip() and topic.strip() != answer.question.strip():
        return "ModuleCard"
    return "QuestionCard"


def _render_card_markdown(card_type: str, title: str, answer: AnswerBundle) -> str:
    lines = [
        f"# {card_type}: {title}",
        "",
        f"- Question: {answer.question}",
        f"- Confidence: {answer.confidence}",
        "",
        "## Answer",
        answer.answer,
        "",
        "## Code Evidence",
    ]
    if answer.code_evidence:
        for item in answer.code_evidence[:4]:
            lines.append(f"- `{item.path}:{item.line_start}` `{item.symbol}`")
            if item.excerpt:
                lines.append(f"  - {item.excerpt}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Paper Evidence")
    if answer.paper_evidence:
        for item in answer.paper_evidence[:3]:
            lines.append(f"- `{item.path}` {item.excerpt}")
    else:
        lines.append("- none")
    if answer.follow_up_questions:
        lines.extend(["", "## Follow-up"])
        lines.extend(f"- {item}" for item in answer.follow_up_questions[:4])
    return "\n".join(lines).strip() + "\n"


def _iter_repo_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in REPO_TEXT_SUFFIXES or path.name.lower().startswith("readme"):
            yield path


def _write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _load_graph_nodes(path: Path) -> list[GraphNode]:
    if not path.exists():
        return []
    items: list[GraphNode] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        items.append(GraphNode(**data))
    return items


def _load_graph_edges(path: Path) -> list[GraphEdge]:
    if not path.exists():
        return []
    items: list[GraphEdge] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        items.append(
            GraphEdge(
                edge_type=data["edge_type"],
                src=GraphNodeRef(**data["src"]),
                dst=GraphNodeRef(**data["dst"]),
                attributes=data.get("attributes", {}),
            )
        )
    return items


def _edge_to_json(edge: GraphEdge) -> dict:
    return {
        "edge_type": edge.edge_type,
        "src": {"node_type": edge.src.node_type, "node_id": edge.src.node_id},
        "dst": {"node_type": edge.dst.node_type, "node_id": edge.dst.node_id},
        "attributes": dict(edge.attributes),
    }


def _dedupe_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    unique: dict[tuple[str, str], GraphNode] = {}
    for node in nodes:
        unique[(node.node_type, node.node_id)] = node
    return list(unique.values())


def _dedupe_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    unique: dict[tuple[str, str, str, str, str], GraphEdge] = {}
    for edge in edges:
        key = (edge.edge_type, edge.src.node_type, edge.src.node_id, edge.dst.node_type, edge.dst.node_id)
        unique[key] = edge
    return list(unique.values())


def _safe_asdict(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, list):
        return [_safe_asdict(item) for item in obj]
    if isinstance(obj, tuple):
        return [_safe_asdict(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _safe_asdict(value) for key, value in obj.items()}
    try:
        data = asdict(obj)
    except TypeError:
        return obj
    return {key: _safe_asdict(value) for key, value in data.items()}


def _excerpt_by_line(text: str, line_start: int, line_end: int) -> str:
    lines = text.splitlines()
    start = max(1, line_start - 2)
    end = min(len(lines), line_end + 2)
    return "\n".join(lines[start - 1 : end]).strip()[:500]


def _excerpt_for_path(path: Path, line_number: int) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return _excerpt_by_line(text, line_number, line_number)


def _text_matches_keywords(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords if keyword)


def _question_keywords(question: str) -> list[str]:
    matches = re.findall(r"[A-Za-z_][A-Za-z0-9_./-]*", question)
    stopwords = {"the", "and", "for", "with", "this", "that", "from", "into", "what", "which", "when", "where"}
    keywords: list[str] = []
    for item in matches:
        if len(item) < 3:
            continue
        normalized = item.strip("`'\".,:;!?()[]{}")
        if normalized.lower() in stopwords:
            continue
        if normalized and normalized.lower() not in {value.lower() for value in keywords}:
            keywords.append(normalized)
    if not keywords:
        keywords.append(question.strip())
    return keywords[:8]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:80] or "artifact"


def _top_files(repo_info) -> list[str]:
    ordered: list[str] = []
    for bucket in (
        repo_info.architecture_entry_candidates,
        repo_info.architecture_skeleton_candidates,
        repo_info.train_candidates,
        repo_info.inference_candidates,
        repo_info.config_entry_candidates,
    ):
        for item in bucket:
            if item not in ordered:
                ordered.append(item)
    return ordered[:10]
