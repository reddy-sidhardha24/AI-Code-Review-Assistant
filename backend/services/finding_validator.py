from typing import List, Dict, Any


class FindingValidator:
    """
    Evidence-based validator for AI-generated code-review findings.

    The LLM proposes findings.
    This class verifies those findings against the source code
    actually retrieved for the CURRENT review.

    This prevents:
        - hallucinated files
        - invalid line numbers
        - unsupported evidence
        - stale project findings
    """

    def __init__(
        self,
        retrieved_chunks: List[Dict[str, Any]]
    ):
        self.retrieved_chunks = (
            retrieved_chunks or []
        )

        self.source_by_file: Dict[
            str,
            Dict[str, Any]
        ] = {}

        self._build_source_index()

    # ============================================================
    # BUILD SOURCE INDEX
    # ============================================================

    def _build_source_index(self):
        """
        Create a lookup table containing only files retrieved
        for the current review.
        """

        for chunk in self.retrieved_chunks:

            file_name = (
                chunk.get("name")
                or chunk.get("file_name")
                or ""
            )

            content = (
                chunk.get("content")
                or ""
            )

            numbered_content = (
                chunk.get("numbered_content")
                or ""
            )

            path = (
                chunk.get("relative_path")
                or chunk.get("path")
                or file_name
            )

            if not file_name:
                continue

            key = self._normalize_file(
                file_name
            )

            self.source_by_file[key] = {
                "file_name": file_name,
                "path": path,
                "content": content,
                "numbered_content": numbered_content
            }

    # ============================================================
    # NORMALIZE FILE
    # ============================================================

    @staticmethod
    def _normalize_file(
        value: str
    ) -> str:

        if not value:
            return ""

        value = str(value)

        value = value.replace(
            "\\",
            "/"
        )

        # Remove directory portion
        value = value.split(
            "/"
        )[-1]

        return value.strip().lower()

    # ============================================================
    # NORMALIZE TEXT
    # ============================================================

    @staticmethod
    def _normalize_text(
        value: str
    ) -> str:

        if not value:
            return ""

        return (
            " ".join(
                str(value)
                .split()
            )
            .strip()
            .lower()
        )

    # ============================================================
    # GET FILE
    # ============================================================

    def _get_file(
        self,
        file_name: str
    ):

        key = self._normalize_file(
            file_name
        )

        return self.source_by_file.get(
            key
        )

    # ============================================================
    # GET SOURCE
    # ============================================================

    def get_source(
        self,
        file_name: str
    ) -> str:

        source_info = self._get_file(
            file_name
        )

        if not source_info:
            return ""

        return source_info.get(
            "content",
            ""
        )

    # ============================================================
    # CHECK FILE
    # ============================================================

    def validate_file(
        self,
        file_name: str
    ) -> bool:

        return (
            self._get_file(
                file_name
            )
            is not None
        )

    # ============================================================
    # CHECK LINE
    # ============================================================

    def _valid_line(
        self,
        source: str,
        line: int | None
    ) -> bool:

        # No line supplied is allowed.
        # We cannot validate what doesn't exist.
        if line is None:
            return True

        if line < 1:
            return False

        lines = source.splitlines()

        return line <= len(lines)

    # ============================================================
    # CHECK LINE RANGE
    # ============================================================

    def _valid_line_range(
        self,
        source: str,
        line_range: str | None
    ) -> bool:

        if not line_range:
            return True

        try:

            cleaned = (
                line_range
                .replace(
                    "Lines",
                    ""
                )
                .replace(
                    "lines",
                    ""
                )
                .strip()
            )

            parts = cleaned.split(
                "-"
            )

            if len(parts) != 2:
                return True

            start = int(
                parts[0].strip()
            )

            end = int(
                parts[1].strip()
            )

            if start < 1:
                return False

            if end < start:
                return False

            total_lines = len(
                source.splitlines()
            )

            return end <= total_lines

        except (
            ValueError,
            TypeError
        ):

            # Don't reject a finding solely because
            # the LLM formatted the range strangely.
            return True

    # ============================================================
    # CHECK EVIDENCE
    # ============================================================

    def _evidence_exists(
        self,
        source: str,
        evidence: str
    ) -> bool:

        if not source:
            return False

        if not evidence:
            return False

        normalized_source = (
            self._normalize_text(
                source
            )
        )

        normalized_evidence = (
            self._normalize_text(
                evidence
            )
        )

        if not normalized_evidence:
            return False

        # --------------------------------------------------------
        # Exact normalized match
        # --------------------------------------------------------

        if (
            normalized_evidence
            in normalized_source
        ):
            return True

        # --------------------------------------------------------
        # Remove common line-number prefixes
        # --------------------------------------------------------

        cleaned_lines = []

        for line in evidence.splitlines():

            line = line.strip()

            if not line:
                continue

            # Examples:
            # 10 | return a / b
            # 10: return a / b
            # 10    return a / b

            parts = line.split(
                "|",
                1
            )

            if len(parts) == 2:

                possible_number = (
                    parts[0].strip()
                )

                if possible_number.isdigit():

                    line = parts[1].strip()

            cleaned_lines.append(
                line
            )

        # --------------------------------------------------------
        # Check meaningful evidence lines
        # --------------------------------------------------------

        meaningful_lines = [
            self._normalize_text(
                line
            )
            for line in cleaned_lines
            if line.strip()
        ]

        for line in meaningful_lines:

            if len(line) < 5:
                continue

            if line in normalized_source:

                return True

        # --------------------------------------------------------
        # Token overlap fallback
        #
        # This handles cases where the model slightly reformats
        # the evidence.
        # --------------------------------------------------------

        source_tokens = set(
            normalized_source.split()
        )

        evidence_tokens = set(
            normalized_evidence.split()
        )

        if not evidence_tokens:
            return False

        common_tokens = (
            source_tokens
            &
            evidence_tokens
        )

        overlap = (
            len(common_tokens)
            /
            len(evidence_tokens)
        )

        # Conservative threshold.
        #
        # We don't want weak evidence to pass merely because
        # common words such as "return", "file", "user" appear.
        #
        return (
            len(evidence_tokens) >= 4
            and overlap >= 0.80
        )

    # ============================================================
    # VALIDATE BUG
    # ============================================================

    def validate_bug(
        self,
        finding
    ) -> bool:

        source_info = self._get_file(
            finding.file
        )

        if not source_info:

            print(
                f"[VALIDATOR] Rejected bug: "
                f"unknown file -> "
                f"{finding.file}"
            )

            return False

        source = source_info[
            "content"
        ]

        if not self._valid_line(
            source,
            finding.line
        ):

            print(
                f"[VALIDATOR] Rejected bug: "
                f"invalid line -> "
                f"{finding.file}:"
                f"{finding.line}"
            )

            return False

        if not self._valid_line_range(
            source,
            finding.line_range
        ):

            print(
                f"[VALIDATOR] Rejected bug: "
                f"invalid line range -> "
                f"{finding.file}:"
                f"{finding.line_range}"
            )

            return False

        if not self._evidence_exists(
            source,
            finding.evidence
        ):

            print(
                f"[VALIDATOR] Rejected bug: "
                f"evidence not found -> "
                f"{finding.file}"
            )

            return False

        return True

    # ============================================================
    # VALIDATE ERROR
    # ============================================================

    def validate_error(
        self,
        finding
    ) -> bool:

        source_info = self._get_file(
            finding.file
        )

        if not source_info:

            print(
                f"[VALIDATOR] Rejected error: "
                f"unknown file -> "
                f"{finding.file}"
            )

            return False

        source = source_info[
            "content"
        ]

        if not self._valid_line(
            source,
            finding.line
        ):

            print(
                f"[VALIDATOR] Rejected error: "
                f"invalid line -> "
                f"{finding.file}:"
                f"{finding.line}"
            )

            return False

        if not self._valid_line_range(
            source,
            finding.line_range
        ):

            print(
                f"[VALIDATOR] Rejected error: "
                f"invalid line range -> "
                f"{finding.file}:"
                f"{finding.line_range}"
            )

            return False

        # ErrorFinding allows empty evidence.
        #
        # Therefore:
        #   evidence present -> validate it
        #   evidence absent  -> don't reject solely for that
        #

        if finding.evidence:

            if not self._evidence_exists(
                source,
                finding.evidence
            ):

                print(
                    f"[VALIDATOR] Rejected error: "
                    f"evidence not found -> "
                    f"{finding.file}"
                )

                return False

        return True

    # ============================================================
    # VALIDATE PERFORMANCE
    # ============================================================

    def validate_performance(
        self,
        finding
    ) -> bool:

        source_info = self._get_file(
            finding.file
        )

        if not source_info:

            print(
                f"[VALIDATOR] Rejected performance "
                f"issue: unknown file -> "
                f"{finding.file}"
            )

            return False

        source = source_info[
            "content"
        ]

        if not self._valid_line(
            source,
            finding.line
        ):

            print(
                f"[VALIDATOR] Rejected performance "
                f"issue: invalid line -> "
                f"{finding.file}:"
                f"{finding.line}"
            )

            return False

        if not self._valid_line_range(
            source,
            finding.line_range
        ):

            print(
                f"[VALIDATOR] Rejected performance "
                f"issue: invalid line range -> "
                f"{finding.file}:"
                f"{finding.line_range}"
            )

            return False

        if finding.evidence:

            if not self._evidence_exists(
                source,
                finding.evidence
            ):

                print(
                    f"[VALIDATOR] Rejected performance "
                    f"issue: evidence not found -> "
                    f"{finding.file}"
                )

                return False

        return True

    # ============================================================
    # VALIDATE SECURITY
    # ============================================================

    def validate_security(
        self,
        finding
    ) -> bool:

        # --------------------------------------------------------
        # File is mandatory for evidence-based security review.
        # --------------------------------------------------------

        if not finding.file:

            print(
                f"[VALIDATOR] Rejected security "
                f"finding: missing file -> "
                f"{finding.title}"
            )

            return False

        source_info = self._get_file(
            finding.file
        )

        if not source_info:

            print(
                f"[VALIDATOR] Rejected security "
                f"finding: unknown file -> "
                f"{finding.file}"
            )

            return False

        source = source_info[
            "content"
        ]

        # --------------------------------------------------------
        # Line
        # --------------------------------------------------------

        if not self._valid_line(
            source,
            finding.line
        ):

            print(
                f"[VALIDATOR] Rejected security "
                f"finding: invalid line -> "
                f"{finding.file}:"
                f"{finding.line}"
            )

            return False

        # --------------------------------------------------------
        # Line range
        # --------------------------------------------------------

        if not self._valid_line_range(
            source,
            finding.line_range
        ):

            print(
                f"[VALIDATOR] Rejected security "
                f"finding: invalid line range -> "
                f"{finding.file}:"
                f"{finding.line_range}"
            )

            return False

        # --------------------------------------------------------
        # Evidence is mandatory
        # --------------------------------------------------------

        if not finding.evidence:

            print(
                f"[VALIDATOR] Rejected security "
                f"finding: missing evidence -> "
                f"{finding.title}"
            )

            return False

        if not self._evidence_exists(
            source,
            finding.evidence
        ):

            print(
                f"[VALIDATOR] Rejected security "
                f"finding: evidence not found -> "
                f"{finding.file}"
            )

            return False

        return True

    # ============================================================
    # VALIDATE REVIEW
    # ============================================================

    def validate_review(
        self,
        review
    ):

        print(
            "\n"
            "========== FINDING VALIDATION =========="
        )

        # --------------------------------------------------------
        # BUGS
        # --------------------------------------------------------

        original_bug_count = len(
            review.bugs
        )

        review.bugs = [
            finding
            for finding in review.bugs
            if self.validate_bug(
                finding
            )
        ]

        print(
            "Bugs:",
            original_bug_count,
            "->",
            len(review.bugs)
        )

        # --------------------------------------------------------
        # ERRORS
        # --------------------------------------------------------

        original_error_count = len(
            review.errors
        )

        review.errors = [
            finding
            for finding in review.errors
            if self.validate_error(
                finding
            )
        ]

        print(
            "Errors:",
            original_error_count,
            "->",
            len(review.errors)
        )

        # --------------------------------------------------------
        # PERFORMANCE
        # --------------------------------------------------------

        if review.performance:

            original_performance_count = len(
                review.performance.issues
            )

            review.performance.issues = [
                finding
                for finding
                in review.performance.issues
                if self.validate_performance(
                    finding
                )
            ]

            print(
                "Performance:",
                original_performance_count,
                "->",
                len(
                    review.performance.issues
                )
            )

        # --------------------------------------------------------
        # SECURITY
        # --------------------------------------------------------

        if review.security:

            original_security_count = len(
                review.security.issues
            )

            review.security.issues = [
                finding
                for finding
                in review.security.issues
                if self.validate_security(
                    finding
                )
            ]

            review.security.issues_found = len(
                review.security.issues
            )

            print(
                "Security:",
                original_security_count,
                "->",
                len(
                    review.security.issues
                )
            )

        print(
            "========================================"
        )

        return review