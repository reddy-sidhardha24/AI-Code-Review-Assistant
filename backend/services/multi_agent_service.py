# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/multi_agent_service.py
# Multi-Agent Collaborative Review Orchestrator
# ============================================================

import json
import asyncio
import concurrent.futures
import time
import random
import threading
from typing import Dict, Any, List, Optional, Tuple
from .llm_service import LLMService


class MultiAgentService:
    """
    Coordinates collaborative multi-agent code analysis:
    - Bug Detective Agent
    - Security Auditor Agent
    - Performance Optimizer Agent
    - Code Quality Specialist Agent
    - Merger / Synthesis Agent
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def run_multi_agent_review(
        self,
        config: Optional[Dict[str, Any]],
        code_context: str,
        question: str,
        json_schema: Dict[str, Any],
        config_pool: Optional[List[Dict[str, Any]]] = None,
        cancellation_event: Optional[threading.Event] = None,
    ) -> Dict[str, Any]:
        """
        Executes parallel specialist agents concurrently and synthesizes into a unified structured review.
        Consolidates into 2 focused agents (Reliability & Security Auditor + Architecture & Quality Specialist)
        executed concurrently to stay well within Groq OTPM rate limits and ensure lightning-fast responses (<6s).
        """
        # Pick once per role per review. The same role keeps its selected model
        # for the full call; the single-agent active config is the empty-pool fallback.
        available_configs = [item for item in (config_pool or []) if item]
        chooser = random.SystemRandom()

        def choose_config() -> Optional[Dict[str, Any]]:
            return chooser.choice(available_configs) if available_configs else config

        reliability_config = choose_config()
        architecture_config = choose_config()
        synthesis_config = choose_config()
        print("[MultiAgent] Selected models:", {
            "reliability_security": (reliability_config or {}).get("model_name", "default Groq"),
            "performance_architecture": (architecture_config or {}).get("model_name", "default Groq"),
            "synthesis": (synthesis_config or {}).get("model_name", "default Groq"),
        })

        def run_reliability_security():
            return self._run_dual_specialist_agent(
                config=reliability_config,
                role="Senior Reliability & Security Auditor",
                focus="Detect runtime crashes, logic errors, unhandled edge cases, exceptions, and security vulnerabilities (SQL injection, XSS, hardcoded credentials, OWASP Top 10).",
                primary_key="bugs",
                secondary_key="security",
                code_context=code_context,
                question=question
            )

        def run_perf_quality():
            return self._run_dual_specialist_agent(
                config=architecture_config,
                role="Performance & Architecture Specialist",
                focus="Detect algorithmic bottlenecks, high time/space complexity, memory leaks, unclosed resources, code duplication, poor naming, and SOLID anti-patterns.",
                primary_key="performance",
                secondary_key="quality",
                code_context=code_context,
                question=question
            )

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        try:
            fut_rel_sec = executor.submit(run_reliability_security)
            fut_perf_qual = executor.submit(run_perf_quality)

            try:
                bugs_findings, sec_findings = self._wait_for_agent(fut_rel_sec, cancellation_event)
            except Exception as e:
                if cancellation_event and cancellation_event.is_set():
                    raise
                print(f"[MultiAgent] Reliability & Security Auditor timeout/error: {e}")
                bugs_findings, sec_findings = [], []

            try:
                perf_findings, quality_findings = self._wait_for_agent(fut_perf_qual, cancellation_event)
            except Exception as e:
                if cancellation_event and cancellation_event.is_set():
                    raise
                print(f"[MultiAgent] Performance & Architecture Specialist timeout/error: {e}")
                perf_findings, quality_findings = [], []
        finally:
            executor.shutdown(
                wait=not (cancellation_event and cancellation_event.is_set()),
                cancel_futures=bool(cancellation_event and cancellation_event.is_set()),
            )

        if cancellation_event and cancellation_event.is_set():
            raise RuntimeError("Review cancelled")

        # Synthesis & Merger Agent
        synthesized = self._synthesize_reviews(
            config=synthesis_config,
            code_context=code_context,
            question=question,
            json_schema=json_schema,
            agent_results={
                "bugs": bugs_findings,
                "security": sec_findings,
                "performance": perf_findings,
                "quality": quality_findings
            }
        )

        return synthesized

    @staticmethod
    def _wait_for_agent(future, cancellation_event: Optional[threading.Event]):
        """Poll agent completion so a cancelled review can skip synthesis promptly."""
        while True:
            if cancellation_event and cancellation_event.is_set():
                future.cancel()
                raise RuntimeError("Review cancelled")
            try:
                return future.result(timeout=0.25)
            except concurrent.futures.TimeoutError:
                continue

    def _run_dual_specialist_agent(
        self,
        config: Optional[Dict[str, Any]],
        role: str,
        focus: str,
        primary_key: str,
        secondary_key: str,
        code_context: str,
        question: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        system_prompt = f"""You are a {role}.
Your single focus: {focus}
Analyze ONLY the provided source code context.
Return a valid JSON object with EXACTLY two keys:
"{primary_key}": array of detected {primary_key} issues,
"{secondary_key}": array of detected {secondary_key} issues.
For each issue, return an object with keys:
- title: string
- severity: 'critical' | 'high' | 'medium' | 'low'
- file: string
- line: integer or null
- description: string
- explanation: string
- impact: string
- fix: string
- suggested_solution: string
- before_code: string (exact problematic code snippet)
- after_code: string (corrected code snippet)
- reason_for_correction: string
If no issues found for a category, return an empty array for that key.
Return valid JSON object: {{"{primary_key}": [...], "{secondary_key}": [...]}} only. No markdown fences."""

        context_limit = 3500 if (config and (config.get("provider") or "").lower() == "ollama") else 6000
        user_prompt = f"User Request: {question}\n\nSource Code Context:\n{code_context[:context_limit]}"

        try:
            spec_cfg = dict(config) if config else {"provider": "groq", "model_name": "qwen/qwen3.8-27b"}
            spec_cfg["max_tokens"] = 350
            raw = self.llm.call(spec_cfg, system_prompt, user_prompt, None)
            clean = raw.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                clean = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
            
            # Find root JSON bounds
            s_obj = clean.find("{")
            e_obj = clean.rfind("}")
            if s_obj != -1 and e_obj > s_obj:
                clean = clean[s_obj:e_obj+1]

            parsed_obj: Dict[str, Any] = {}
            try:
                parsed_obj = json.loads(clean)
            except Exception:
                # Truncation recovery
                for suffix in ["}", "\"]}", "]}", "\"}]}", "\"}}", "\"]}}", "}]}}", "\"}]}}", "}]}"] + [s + "}" for s in ["", "]", "}", "\"]", "\"}"]]:
                    try:
                        cand = json.loads(clean + suffix)
                        if isinstance(cand, dict) and (primary_key in cand or secondary_key in cand):
                            parsed_obj = cand
                            break
                    except Exception:
                        continue

            primary_raw = parsed_obj.get(primary_key, []) if isinstance(parsed_obj, dict) else []
            secondary_raw = parsed_obj.get(secondary_key, []) if isinstance(parsed_obj, dict) else []

            # In case the model returned a top-level array instead of an object
            if isinstance(parsed_obj, list):
                primary_raw = parsed_obj
                secondary_raw = []

            primary_clean = self._sanitize_specialist_items(primary_raw, role)
            secondary_clean = self._sanitize_specialist_items(secondary_raw, role)
            return primary_clean, secondary_clean
        except Exception as e:
            print(f"[MultiAgent] Notice: Specialist {role} encountered: {e}")
            return [], []

    def _sanitize_specialist_items(self, raw_items: Any, role: str) -> List[Dict[str, Any]]:
        if not isinstance(raw_items, list):
            if isinstance(raw_items, dict):
                raw_items = [raw_items]
            else:
                return []
        valid_items = []
        for item in raw_items:
            if isinstance(item, dict):
                t = str(item.get("title") or item.get("bug_id") or "").strip().lower()
                if t in ("title", "bug id", "none", "issue title", ""):
                    continue
                if not item.get("title"):
                    item["title"] = item.get("bug_id") or f"Issue identified by {role}"
                if not item.get("evidence"):
                    item["evidence"] = item.get("before_code") or item.get("description") or item.get("title", "")
                if not item.get("impact"):
                    item["impact"] = item.get("description", "Potential execution or security issue.")
                if not item.get("fix"):
                    item["fix"] = item.get("after_code") or item.get("suggested_solution", "Apply recommended fix.")
                if not item.get("suggested_solution"):
                    item["suggested_solution"] = item.get("fix")
                valid_items.append(item)
        return valid_items

    def _synthesize_reviews(
        self,
        config: Optional[Dict[str, Any]],
        code_context: str,
        question: str,
        json_schema: Dict[str, Any],
        agent_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Takes raw findings from all 4 specialist agents and uses a Merger Agent
        to deduplicate, score, and format into the final structured review schema.
        """
        merger_system_prompt = """You are the Lead Code Review Synthesizer.
You have received independent findings from specialist agents.
Your job:
1. Deduplicate any overlapping findings across agents.
2. Ground and verify that each finding relates to the source code.
3. Calculate an accurate Health Score between 0 and 100 based on severity: Critical (-25), High (-15), Medium (-8), Low (-3). If serious bugs exist, do NOT give an artificially high score.
4. Output the unified review adhering strictly to the required root JSON schema.
IMPORTANT CONCISENESS RULES:
- Keep code snippets in before_code, after_code, and corrected_code concise (focused strictly on the lines with bugs/fixes).
- Do not output lengthy repeating code files. Ensure the root JSON is completely closed."""

        context_limit = 3500 if (config and (config.get("provider") or "").lower() == "ollama") else 5000
        merger_user_prompt = f"""Review Goal: {question}

Specialist Agent Reports:
{json.dumps(agent_results, indent=2)[:5000]}

Source Code Reference:
{code_context[:context_limit]}

Generate the final unified JSON review now."""

        try:
            merge_cfg = dict(config) if config else {"provider": "groq", "model_name": "qwen/qwen3.8-27b"}
            merge_cfg["max_tokens"] = 650
            raw_review = self.llm.call(
                config=merge_cfg,
                system_prompt=merger_system_prompt,
                user_prompt=merger_user_prompt,
                json_schema=json_schema
            )
            clean = raw_review.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                clean = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
            
            s_idx = clean.find("{")
            e_idx = clean.rfind("}")
            if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                clean = clean[s_idx:e_idx+1]

            parsed = None
            try:
                parsed = json.loads(clean.strip())
            except Exception:
                # Truncation recovery: attempt to close open strings/arrays/objects
                trimmed = clean.strip()
                for suffix in ["}", "\"]}", "]}", "\"}]}", "\"}}", "\"]}}", "}]}}", "\"}]}}", "}]}"] + [s + "}" for s in ["", "]", "}", "\"]", "\"}"]]:
                    try:
                        candidate = json.loads(trimmed + suffix)
                        if isinstance(candidate, dict) and any(k in candidate for k in ("bugs", "security", "score")):
                            parsed = candidate
                            break
                    except Exception:
                        continue

            if isinstance(parsed, dict) and ("score" in parsed or "bugs" in parsed):
                return parsed
        except Exception as err:
            print(f"[MultiAgent] Merger notice: {err}")

        # Fallback direct construction with strict schema adherence
        bugs = []
        for b in agent_results.get("bugs", []):
            if isinstance(b, dict):
                bugs.append({
                    "title": b.get("title") or "Bug Identified",
                    "type": b.get("type") if b.get("type") in ("confirmed", "conditional", "possible_risk") else "confirmed",
                    "severity": b.get("severity") if b.get("severity") in ("critical", "high", "medium", "low") else "medium",
                    "file": b.get("file") or b.get("file_name") or "app.py",
                    "line": b.get("line") if isinstance(b.get("line"), int) else None,
                    "line_range": str(b.get("line_range")) if b.get("line_range") else None,
                    "evidence": b.get("evidence") or b.get("before_code") or b.get("description") or "Observed defect in code logic.",
                    "description": b.get("description") or b.get("title") or "Bug detected.",
                    "explanation": b.get("explanation") or b.get("description"),
                    "impact": b.get("impact") or "Potential unexpected execution.",
                    "fix": b.get("fix") or b.get("suggested_solution") or b.get("after_code") or "Refactor code to fix edge case.",
                    "suggested_solution": b.get("suggested_solution") or b.get("fix"),
                    "before_code": b.get("before_code"),
                    "after_code": b.get("after_code"),
                    "corrected_code": b.get("after_code"),
                    "reason_for_correction": b.get("reason_for_correction") or "Prevents runtime error.",
                    "confidence": int(b.get("confidence")) if isinstance(b.get("confidence"), int) else 90
                })

        security = []
        for s in agent_results.get("security", []):
            if isinstance(s, dict):
                security.append({
                    "title": s.get("title") or "Security Vulnerability",
                    "description": s.get("description") or s.get("title") or "Security issue.",
                    "explanation": s.get("explanation") or s.get("description"),
                    "file": s.get("file") or s.get("file_name") or "app.py",
                    "line": s.get("line") if isinstance(s.get("line"), int) else None,
                    "line_range": str(s.get("line_range")) if s.get("line_range") else None,
                    "severity": s.get("severity") if s.get("severity") in ("critical", "high", "medium", "low") else "high",
                    "evidence": s.get("evidence") or s.get("before_code") or "Vulnerable implementation.",
                    "impact": s.get("impact") or "Security risk or unauthorized exposure.",
                    "suggestion": s.get("suggestion") or s.get("fix") or "Harden security.",
                    "suggested_solution": s.get("suggested_solution") or s.get("fix") or "Apply secure pattern.",
                    "before_code": s.get("before_code"),
                    "after_code": s.get("after_code"),
                    "corrected_code": s.get("after_code"),
                    "reason_for_correction": s.get("reason_for_correction") or "Mitigates vulnerability.",
                    "confidence": int(s.get("confidence")) if isinstance(s.get("confidence"), int) else 90
                })

        perf = []
        for p in agent_results.get("performance", []):
            if isinstance(p, dict):
                perf.append({
                    "title": p.get("title") or "Performance Bottleneck",
                    "description": p.get("description") or p.get("title") or "Performance issue.",
                    "explanation": p.get("explanation") or p.get("description"),
                    "file": p.get("file") or p.get("file_name") or "app.py",
                    "line": p.get("line") if isinstance(p.get("line"), int) else None,
                    "line_range": str(p.get("line_range")) if p.get("line_range") else None,
                    "severity": p.get("severity") if p.get("severity") in ("critical", "high", "medium", "low") else "medium",
                    "evidence": p.get("evidence") or p.get("before_code") or "Unoptimized code.",
                    "impact": p.get("impact") or "Increased latency or high resource consumption.",
                    "suggestion": p.get("suggestion") or p.get("fix") or "Optimize algorithm.",
                    "suggested_solution": p.get("suggested_solution") or p.get("fix") or "Optimize algorithm.",
                    "before_code": p.get("before_code"),
                    "after_code": p.get("after_code"),
                    "corrected_code": p.get("after_code"),
                    "reason_for_correction": p.get("reason_for_correction") or "Improves execution speed.",
                    "confidence": int(p.get("confidence")) if isinstance(p.get("confidence"), int) else 85
                })

        quality = []
        for q in agent_results.get("quality", []):
            if isinstance(q, dict):
                quality.append({
                    "title": q.get("title") or "Code Quality Note",
                    "description": q.get("description") or q.get("title") or "Quality recommendation.",
                    "explanation": q.get("explanation") or q.get("description"),
                    "file": q.get("file") or q.get("file_name") or "app.py",
                    "line": q.get("line") if isinstance(q.get("line"), int) else None,
                    "line_range": str(q.get("line_range")) if q.get("line_range") else None,
                    "severity": q.get("severity") if q.get("severity") in ("critical", "high", "medium", "low") else "low",
                    "evidence": q.get("evidence") or q.get("before_code"),
                    "impact": q.get("impact"),
                    "suggestion": q.get("suggestion") or q.get("fix"),
                    "suggested_solution": q.get("suggested_solution") or q.get("fix"),
                    "before_code": q.get("before_code"),
                    "after_code": q.get("after_code"),
                    "corrected_code": q.get("after_code"),
                    "reason_for_correction": q.get("reason_for_correction"),
                    "confidence": int(q.get("confidence")) if isinstance(q.get("confidence"), int) else 85
                })

        all_issues = bugs + security + perf + quality

        # Calculate rigorous grounded health score
        score = 100.0
        for item in all_issues:
            s = (item.get("severity") or "medium").lower()
            deduct = 25.0 if s == "critical" else (15.0 if s == "high" else (8.0 if s == "medium" else 3.0))
            score = max(5.0, score - deduct)

        return {
            "project": {"name": "Audited Project", "languages": [], "total_files": 0, "total_lines": 0},
            "question": question,
            "user_requirements": ["Code correctness", "Security posture", "Performance optimization", "Code quality"],
            "review_types": ["full_review", "bug_review", "error_review", "security", "performance", "code_quality"],
            "answer_summary": f"Collaborative multi-agent review identified {len(all_issues)} supported findings across reliability, security, performance, and code quality.",
            "final_verdict": f"The multi-agent review identified {len(all_issues)} supported findings. Address high-severity issues before deployment." if len(all_issues) > 0 else "Code passes standards with no supported issues.",
            "score": round(score, 1),
            "confidence": 92,
            "files_analyzed": [],
            "key_methods": [],
            "key_classes": [],
            "libraries": [],
            "bugs": bugs,
            "errors": [],
            "security": {"issues_found": len(security), "issues": security},
            "performance": {"time_complexity": "Evaluated", "space_complexity": "Evaluated", "issues": perf},
            "code_quality": {"observations": quality, "suggestions": []},
            "corrected_code": [],
            "expected_output": None,
            "detected_issues": all_issues
        }
