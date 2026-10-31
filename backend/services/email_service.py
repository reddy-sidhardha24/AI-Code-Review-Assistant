# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/email_service.py
# Hosted Mail API Integration (technovacseai.pythonanywhere.com)
# ============================================================

import os
import html
import base64
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class EmailService:
    """
    Handles generation of comprehensive review reports, refactored code packages,
    and direct delivery via the hosted PythonAnywhere email API:
    https://technovacseai.pythonanywhere.com/send-email
    """

    API_URL = "https://technovacseai.pythonanywhere.com/send-email"

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / "data"
        self.outbox_dir = self.data_dir / "client_outbox"
        self.outbox_dir.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        """The hosted email API is ready out of the box."""
        return True

    def get_config_status(self) -> Dict[str, Any]:
        """Returns delivery service status."""
        return {
            "configured": True,
            "service": "Hosted Cloud Email API",
            "api_endpoint": self.API_URL
        }

    def send_review_email(
        self,
        recipient_email: str,
        review_data: Dict[str, Any],
        category: str = "full_review",
        report_markdown: Optional[str] = None,
        corrected_code_list: Optional[List[Dict[str, Any]]] = None,
        pdf_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Generates full HTML report, compiles attachments (Markdown, HTML, Corrected Code, and PDF),
        saves a local outbox archive, and delivers via the hosted email API.
        """
        recipient_email = recipient_email.strip()
        if not recipient_email or "@" not in recipient_email:
            raise ValueError(f"Invalid recipient email address: '{recipient_email}'")

        project = review_data.get("project") or {}
        proj_name = project.get("name") or "Code Review"
        subject = f"AI Code Review Report: {proj_name} [{category.replace('_', ' ').title()}]"

        # Generate HTML content
        html_content = self.generate_full_html_email(
            review_data=review_data,
            category=category,
            report_markdown=report_markdown
        )

        # Generate Markdown report
        if not report_markdown:
            report_markdown = self.generate_markdown_report(review_data, category)

        # Generate Corrected code document
        corrected_code_text = self.generate_corrected_code_content(review_data)

        # Prepare attachments
        attachments = [
            {
                "filename": "Review_Report.md",
                "content": base64.b64encode(report_markdown.encode("utf-8")).decode("utf-8"),
                "content_type": "text/markdown"
            },
            {
                "filename": "Review_Report.html",
                "content": base64.b64encode(html_content.encode("utf-8")).decode("utf-8"),
                "content_type": "text/html"
            },
            {
                "filename": "Corrected_Code.txt",
                "content": base64.b64encode(corrected_code_text.encode("utf-8")).decode("utf-8"),
                "content_type": "text/plain"
            }
        ]

        if pdf_bytes:
            attachments.append({
                "filename": "Review_Report.pdf",
                "content": base64.b64encode(pdf_bytes).decode("utf-8"),
                "content_type": "application/pdf"
            })

        # Save local outbox copy
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_email = recipient_email.replace("@", "_at_").replace(".", "_")
        session_outbox = self.outbox_dir / f"{timestamp_str}_{safe_email}"
        session_outbox.mkdir(parents=True, exist_ok=True)
        try:
            (session_outbox / "Review_Report.md").write_text(report_markdown, encoding="utf-8")
            (session_outbox / "email.html").write_text(html_content, encoding="utf-8")
            (session_outbox / "Corrected_Code.txt").write_text(corrected_code_text, encoding="utf-8")
            if pdf_bytes:
                (session_outbox / "Review_Report.pdf").write_bytes(pdf_bytes)
        except Exception as file_err:
            print(f"[Outbox] Notice: Could not save local outbox copy: {file_err}")

        # Dispatch via hosted API
        payload = {
            "to": recipient_email,
            "subject": subject,
            "html": html_content,
            "message": f"Please view your AI Code Review Report for {proj_name}.",
            "from_name": "AI Code Review Assistant",
            "attachments": attachments
        }

        try:
            resp = requests.post(self.API_URL, json=payload, timeout=45)
            api_res = resp.json() if resp.status_code == 200 else {}
            if resp.status_code == 200 and api_res.get("success"):
                return {
                    "success": True,
                    "recipient": recipient_email,
                    "subject": subject,
                    "message": "Review report successfully delivered to inbox!",
                    "attachments_count": len(attachments),
                    "outbox_path": str(session_outbox)
                }
            else:
                err_msg = api_res.get("error") or f"Hosted API returned status {resp.status_code}"
                return {
                    "success": False,
                    "recipient": recipient_email,
                    "error": err_msg,
                    "outbox_path": str(session_outbox)
                }
        except Exception as net_err:
            return {
                "success": False,
                "recipient": recipient_email,
                "error": f"Network delivery error: {str(net_err)}",
                "outbox_path": str(session_outbox)
            }

    def send_contact_message(
        self,
        from_name: str,
        from_email: str,
        subject: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Dispatches a contact form submission to support via the hosted email API.
        """
        target_inbox = "nihak1813@gmail.com"  # Deliver to project administrator
        clean_subject = f"[Contact Request] {subject.strip()}"
        html_msg = f"""
        <div style="font-family: sans-serif; padding: 24px; background: #f8fafc; color: #0f172a;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
                <h2 style="color: #4f46e5; margin-top: 0;">New Contact Form Message</h2>
                <p><strong>From:</strong> {html.escape(from_name)} &lt;{html.escape(from_email)}&gt;</p>
                <p><strong>Subject:</strong> {html.escape(subject)}</p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;" />
                <h3 style="color: #475569; font-size: 14px; text-transform: uppercase;">Message Content:</h3>
                <div style="background: #f1f5f9; padding: 16px; border-radius: 8px; line-height: 1.6; white-space: pre-wrap;">{html.escape(message)}</div>
            </div>
        </div>
        """

        payload = {
            "to": target_inbox,
            "subject": clean_subject,
            "html": html_msg,
            "message": f"From: {from_name} ({from_email})\n\n{message}",
            "reply_to": from_email,
            "from_name": from_name
        }

        try:
            resp = requests.post(self.API_URL, json=payload, timeout=30)
            res = resp.json() if resp.status_code == 200 else {}
            if resp.status_code == 200 and res.get("success"):
                return {"success": True, "message": "Your message was sent successfully! We will get back to you shortly."}
            else:
                return {"success": False, "error": res.get("error", "Failed to deliver contact message")}
        except Exception as e:
            return {"success": False, "error": f"Failed to send message: {str(e)}"}

    def generate_corrected_code_content(self, review_data: Dict[str, Any]) -> str:
        corrected_files = review_data.get("corrected_code") or []
        sections = []

        if corrected_files:
            for f in corrected_files:
                fname = f.get("file_name") if isinstance(f, dict) else "corrected_code.py"
                code = f.get("code") if isinstance(f, dict) else str(f)
                sections.append(f"# ============================================================\n# File: {fname}\n# ============================================================\n{code.strip()}\n")
        else:
            detected = review_data.get("detected_issues") or []
            snippets = []
            for item in detected:
                after = item.get("after_code") or item.get("corrected_code")
                if after and after.strip():
                    fname = item.get("file") or "source"
                    title = item.get("title") or "Fix"
                    snippets.append(f"# --- Fix for: {title} ({fname}) ---\n{after.strip()}\n")

            if snippets:
                sections.append("# Refactored / Corrected Snippets:\n\n" + "\n".join(snippets))
            else:
                sections.append("# All code checked. No refactored code changes were required.")

        return "\n\n".join(sections)

    def _gather_all_findings(self, review_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_findings = []
        for b in review_data.get("bugs") or []:
            b_copy = dict(b)
            b_copy["_cat"] = "Bug"
            all_findings.append(b_copy)

        for e in review_data.get("errors") or []:
            e_copy = dict(e)
            e_copy["_cat"] = "Error"
            all_findings.append(e_copy)

        sec_info = review_data.get("security") or {}
        for s in sec_info.get("issues") or []:
            s_copy = dict(s)
            s_copy["_cat"] = "Security"
            all_findings.append(s_copy)

        perf_info = review_data.get("performance") or {}
        for p in perf_info.get("issues") or []:
            p_copy = dict(p)
            p_copy["_cat"] = "Performance"
            all_findings.append(p_copy)

        qual_info = review_data.get("code_quality") or {}
        for o in qual_info.get("observations") or []:
            o_copy = dict(o)
            o_copy["_cat"] = "Quality Observation"
            all_findings.append(o_copy)
        for sq in qual_info.get("suggestions") or []:
            sq_copy = dict(sq)
            sq_copy["_cat"] = "Quality Suggestion"
            all_findings.append(sq_copy)

        if not all_findings and review_data.get("detected_issues"):
            for d in review_data.get("detected_issues"):
                all_findings.append(dict(d))

        return all_findings

    def generate_full_html_email(
        self,
        review_data: Dict[str, Any],
        category: str = "full_review",
        report_markdown: Optional[str] = None
    ) -> str:
        project = review_data.get("project") or {}
        proj_name = html.escape(project.get("name") or "Code Review")
        languages = html.escape(", ".join(project.get("languages") or ["Source Code"]))
        summary = html.escape(review_data.get("answer_summary") or "Review completed.")
        verdict = html.escape(review_data.get("final_verdict") or "")
        score = review_data.get("score")
        files = review_data.get("files_analyzed") or []

        score_html = ""
        if score is not None:
            score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 60 else "#ef4444")
            score_html = f"""
            <div style="background: #ffffff; border: 2px solid {score_color}; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                <span style="font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #64748b; text-transform: uppercase;">GROUNDED PROJECT HEALTH SCORE</span>
                <div style="font-size: 48px; font-weight: 900; color: {score_color}; margin: 8px 0; line-height: 1;">
                    {score} <span style="font-size: 20px; font-weight: 600; color: #94a3b8;">/ 100</span>
                </div>
            </div>
            """

        all_findings = self._gather_all_findings(review_data)
        findings_html = []
        for idx, item in enumerate(all_findings, 1):
            title = html.escape(item.get("title") or f"Finding #{idx}")
            cat = html.escape(item.get("_cat") or item.get("category") or "Finding")
            sev = (item.get("severity") or "medium").lower()
            explanation = html.escape(item.get("explanation") or item.get("description") or "")
            solution = html.escape(item.get("suggested_solution") or item.get("fix") or "")

            findings_html.append(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 16px; color: #0f172a;">{title}</strong>
                    <span style="font-size: 12px; font-weight: 700; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; background: #eef2ff; color: #4f46e5;">{cat} • {sev}</span>
                </div>
                <p style="color: #475569; font-size: 14px; margin: 8px 0;">{explanation}</p>
                {f'<div style="background: #f8fafc; border-left: 3px solid #4f46e5; padding: 10px 14px; font-size: 13.5px; color: #334155; margin-top: 10px;"><strong>Suggested Fix:</strong> {solution}</div>' if solution else ''}
            </div>
            """)

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8" /></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px;">
            <div style="max-width: 720px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 16px;">
                    <div style="width: 36px; height: 36px; background: #4f46e5; border-radius: 8px; color: #fff; font-weight: 800; display: flex; align-items: center; justify-content: center;">&lt;/&gt;</div>
                    <div>
                        <h2 style="margin: 0; font-size: 20px; color: #0f172a;">AI Code Review Report</h2>
                        <span style="font-size: 13px; color: #64748b;">Project: {proj_name} • {languages}</span>
                    </div>
                </div>
                {score_html}
                <div style="background: #f1f5f9; border-radius: 10px; padding: 18px; margin-bottom: 24px;">
                    <h4 style="margin: 0 0 6px 0; color: #334155; font-size: 13px; text-transform: uppercase;">Executive Summary</h4>
                    <p style="margin: 0; font-size: 14.5px; color: #475569; line-height: 1.6;">{summary}</p>
                </div>
                <h3 style="font-size: 18px; margin: 24px 0 14px 0;">Detailed Findings ({len(all_findings)} issues)</h3>
                {''.join(findings_html)}
                <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 13px; color: #94a3b8;">
                    Delivered securely by AI Code Review Assistant • Attached files: Markdown Report, Offline HTML, Refactored Code
                </div>
            </div>
        </body>
        </html>
        """

    def generate_markdown_report(self, review_data: Dict[str, Any], category: str = "full_review") -> str:
        project = review_data.get("project") or {}
        proj_name = project.get("name") or "Code Review"
        score = review_data.get("score")
        summary = review_data.get("answer_summary") or ""
        verdict = review_data.get("final_verdict") or ""
        all_findings = self._gather_all_findings(review_data)

        md = [
            f"# AI Code Review Report: {proj_name}",
            f"\n**Category:** {category.replace('_', ' ').title()}",
            f"**Score:** {score}/100" if score is not None else "**Score:** Evaluated",
            f"\n## Executive Summary\n{summary}\n",
            f"## Final Verdict\n{verdict}\n" if verdict else "",
            f"## Findings ({len(all_findings)} Detected Issues)\n"
        ]

        for idx, item in enumerate(all_findings, 1):
            title = item.get("title") or f"Issue #{idx}"
            sev = (item.get("severity") or "Medium").upper()
            file_path = item.get("file") or "source"
            line = item.get("line") or item.get("line_range") or "N/A"
            explanation = item.get("explanation") or item.get("description") or ""
            fix = item.get("suggested_solution") or item.get("fix") or ""

            md.append(f"### {idx}. {title}")
            md.append(f"- **Severity:** {sev}")
            md.append(f"- **Location:** `{file_path}` (Line: {line})")
            md.append(f"- **Explanation:** {explanation}")
            if fix:
                md.append(f"- **Recommendation:** {fix}\n")

        return "\n".join(md)


email_service = EmailService()
