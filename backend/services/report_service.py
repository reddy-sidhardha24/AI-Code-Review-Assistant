# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/report_service.py
# Multi-Format Report Generator (PDF, Markdown, HTML)
# ============================================================

import io
import html
from typing import Dict, Any, List, Optional
from xhtml2pdf import pisa


class ReportService:
    """
    Generates professional code review audit reports in PDF, Markdown, and HTML formats.
    """

    def generate_markdown(self, review_data: Dict[str, Any], category: str = "full_review") -> str:
        project = review_data.get("project") or {}
        proj_name = project.get("name") or "Code Review"
        score = review_data.get("score")
        summary = review_data.get("answer_summary") or ""
        verdict = review_data.get("final_verdict") or ""
        all_findings = self._gather_findings(review_data)

        md = [
            f"# 🛡️ AI Code Review Audit Report: {proj_name}\n",
            f"**Review Category:** {category.replace('_', ' ').title()}",
            f"**Assessed Score:** {score}/100" if score is not None else "**Status:** Evaluated",
            f"**Confidence:** {review_data.get('confidence', 90)}%\n",
            "## 📌 Executive Summary",
            f"{summary}\n",
            "## ⚖️ Final Verdict",
            f"{verdict}\n" if verdict else "No blocking compliance verdict recorded.\n",
            f"## 🔍 Detected Issues & Verified Findings ({len(all_findings)} Total)\n"
        ]

        for idx, f in enumerate(all_findings, 1):
            title = f.get("title") or f"Finding #{idx}"
            sev = (f.get("severity") or "Medium").upper()
            cat = f.get("_cat") or f.get("category") or "Code Review"
            file_path = f.get("file") or "source"
            line = f.get("line") or f.get("line_range") or "N/A"
            explanation = f.get("explanation") or f.get("description") or ""
            fix = f.get("suggested_solution") or f.get("fix") or ""
            before = f.get("before_code") or f.get("evidence") or ""
            after = f.get("after_code") or f.get("corrected_code") or ""

            md.append(f"### {idx}. {title}")
            md.append(f"- **Category:** {cat}")
            md.append(f"- **Severity:** {sev}")
            md.append(f"- **File:** `{file_path}` (Line: {line})")
            md.append(f"- **Explanation:** {explanation}")
            if fix:
                md.append(f"- **Recommendation:** {fix}")
            if before:
                md.append(f"\n```\n# Original Snippet:\n{before.strip()}\n```")
            if after:
                md.append(f"\n```\n# Suggested Correction:\n{after.strip()}\n```")
            md.append("\n---\n")

        return "\n".join(md)

    def generate_html(self, review_data: Dict[str, Any], category: str = "full_review") -> str:
        project = review_data.get("project") or {}
        proj_name = html.escape(project.get("name") or "Code Review")
        languages = html.escape(", ".join(project.get("languages") or ["Source Code"]))
        summary = html.escape(review_data.get("answer_summary") or "Review completed.")
        verdict = html.escape(review_data.get("final_verdict") or "")
        score = review_data.get("score")
        all_findings = self._gather_findings(review_data)

        score_block = ""
        if score is not None:
            color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 60 else "#ef4444")
            score_block = f"""
            <div style="background: #ffffff; border: 2px solid {color}; border-radius: 12px; padding: 20px; text-align: center; margin: 20px 0;">
                <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #64748b; text-transform: uppercase;">GROUNDED HEALTH SCORE</div>
                <div style="font-size: 44px; font-weight: 900; color: {color}; margin: 6px 0;">{score} <span style="font-size: 18px; color: #94a3b8;">/ 100</span></div>
            </div>
            """

        findings_html = []
        for idx, f in enumerate(all_findings, 1):
            title = html.escape(f.get("title") or f"Finding #{idx}")
            sev = (f.get("severity") or "medium").lower()
            cat = html.escape(f.get("_cat") or f.get("category") or "General")
            file_loc = html.escape(f.get("file") or "source")
            line = f.get("line") or f.get("line_range") or "N/A"
            explanation = html.escape(f.get("explanation") or f.get("description") or "")
            fix = html.escape(f.get("suggested_solution") or f.get("fix") or "")
            before = f.get("before_code") or f.get("evidence") or ""
            after = f.get("after_code") or f.get("corrected_code") or ""

            sev_color = "#dc2626" if sev == "critical" else ("#ea580c" if sev == "high" else ("#d97706" if sev == "medium" else "#2563eb"))

            code_box = ""
            if before or after:
                code_box = f"""
                <div style="margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    {f'<div style="background: #0f172a; color: #f8fafc; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; overflow-x: auto;"><strong>Before:</strong><pre style="margin:4px 0 0 0;">{html.escape(before)}</pre></div>' if before else ''}
                    {f'<div style="background: #0f172a; color: #34d399; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; overflow-x: auto;"><strong>After:</strong><pre style="margin:4px 0 0 0;">{html.escape(after)}</pre></div>' if after else ''}
                </div>
                """

            findings_html.append(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 16px; color: #0f172a;">{title}</strong>
                    <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; background: #f1f5f9; color: {sev_color};">{cat} • {sev}</span>
                </div>
                <div style="font-size: 13px; color: #64748b; margin-bottom: 8px;">Location: <code>{file_loc}</code> (Line {line})</div>
                <p style="color: #334155; font-size: 14px; margin: 6px 0;">{explanation}</p>
                {f'<div style="background: #f8fafc; border-left: 3px solid #4f46e5; padding: 10px 12px; font-size: 13px; color: #1e293b; margin-top: 8px;"><strong>Fix:</strong> {fix}</div>' if fix else ''}
                {code_box}
            </div>
            """)

        return f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>AI Code Review Report - {proj_name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 32px; line-height: 1.5; }}
                .report-wrap {{ max-width: 860px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 36px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); }}
                h1, h2, h3 {{ color: #0f172a; }}
                code {{ font-family: monospace; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="report-wrap">
                <div style="border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px;">
                    <h1 style="margin: 0 0 6px 0; font-size: 26px;">AI Code Review Audit Report</h1>
                    <div style="color: #64748b; font-size: 14px;">Project: <strong>{proj_name}</strong> • Languages: {languages}</div>
                </div>
                {score_block}
                <div style="background: #f1f5f9; border-radius: 10px; padding: 18px; margin-bottom: 24px;">
                    <h3 style="margin: 0 0 8px 0; font-size: 15px; text-transform: uppercase; color: #475569;">Summary</h3>
                    <p style="margin: 0; font-size: 14.5px; color: #334155; line-height: 1.6;">{summary}</p>
                </div>
                {f'<div style="background: #eef2ff; border-radius: 10px; padding: 18px; margin-bottom: 24px; color: #3730a3; font-weight: 500;"><strong>Verdict:</strong> {verdict}</div>' if verdict else ''}
                <h2 style="font-size: 20px; margin: 28px 0 16px 0;">Detailed Findings ({len(all_findings)} issues)</h2>
                {''.join(findings_html)}
            </div>
        </body>
        </html>
        """

    def generate_pdf(self, review_data: Dict[str, Any], category: str = "full_review") -> bytes:
        """
        Renders a printable PDF version of the code review audit report.
        """
        html_content = self.generate_html(review_data, category)
        pdf_stream = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_stream)

        if pisa_status.err:
            raise RuntimeError(f"Error generating PDF report: {pisa_status.err}")

        return pdf_stream.getvalue()

    def _gather_findings(self, review_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        for b in review_data.get("bugs") or []:
            b_c = dict(b)
            b_c["_cat"] = "Bug"
            findings.append(b_c)
        for e in review_data.get("errors") or []:
            e_c = dict(e)
            e_c["_cat"] = "Error"
            findings.append(e_c)
        for s in (review_data.get("security") or {}).get("issues") or []:
            s_c = dict(s)
            s_c["_cat"] = "Security"
            findings.append(s_c)
        for p in (review_data.get("performance") or {}).get("issues") or []:
            p_c = dict(p)
            p_c["_cat"] = "Performance"
            findings.append(p_c)
        for q in (review_data.get("code_quality") or {}).get("observations") or []:
            q_c = dict(q)
            q_c["_cat"] = "Code Quality"
            findings.append(q_c)
        for q in (review_data.get("code_quality") or {}).get("suggestions") or []:
            q_c = dict(q)
            q_c["_cat"] = "Suggestion"
            findings.append(q_c)

        if not findings and review_data.get("detected_issues"):
            for d in review_data.get("detected_issues"):
                findings.append(dict(d))

        return findings


report_service = ReportService()
