# ============================================================
# backend/models/review_models.py
# ============================================================

from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field, field_validator


# ============================================================
# REQUEST MODEL
# ============================================================

class ReviewRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
    )

    category: Optional[str] = Field(
        default=None,
        description="Review category: 'bugs', 'security', 'performance', 'code_quality', or 'full_review'"
    )


# ============================================================
# PASTE CODE REQUEST
# ============================================================

class PasteCodeRequest(BaseModel):

    filename: str = Field(
        default="main.py",
        min_length=1,
        max_length=255
    )

    code: str = Field(
        min_length=1
    )


# ============================================================
# PROJECT INFORMATION
# ============================================================

class ProjectInfo(BaseModel):

    # Required property, but nullable.
    name: Optional[str]

    languages: List[str] = Field(
        default_factory=list
    )

    total_files: int = Field(
        default=0,
        ge=0
    )

    total_lines: int = Field(
        default=0,
        ge=0
    )


# ============================================================
# FILE ANALYZED
# ============================================================

class FileAnalyzed(BaseModel):

    file_name: str

    path: str

    language: str


# ============================================================
# CORRECTED CODE
# ============================================================

class CorrectedCode(BaseModel):

    file_name: str

    code: str


# ============================================================
# BUG FINDING
# ============================================================

class BugFinding(BaseModel):

    title: str

    type: Literal[
        "confirmed",
        "conditional",
        "possible_risk"
    ]

    severity: Literal["critical", "high", "medium", "low"]
    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str

    description: str

    explanation: Optional[str] = None

    impact: str

    fix: str

    suggested_solution: Optional[str] = None

    before_code: Optional[str] = None

    after_code: Optional[str] = None

    corrected_code: Optional[str] = None

    reason_for_correction: Optional[str] = None

    confidence: int = Field(
        ge=0,
        le=100
    )


# ============================================================
# ERROR FINDING
# ============================================================

class ErrorFinding(BaseModel):

    type: str

    title: str

    file: str

    line: Optional[int]

    line_range: Optional[str]

    evidence: str

    description: str

    explanation: Optional[str] = None

    severity: Literal["critical", "high", "medium", "low"] = "high"

    impact: str

    fix: str

    suggested_solution: Optional[str] = None

    before_code: Optional[str] = None

    after_code: Optional[str] = None

    corrected_code: Optional[str] = None

    reason_for_correction: Optional[str] = None

    confidence: int = Field(
        ge=0,
        le=100
    )


# ============================================================
# PERFORMANCE FINDING
# ============================================================

class PerformanceIssue(BaseModel):

    title: str

    description: str

    explanation: Optional[str] = None

    file: Optional[str] = None

    line: Optional[int] = None

    line_range: Optional[str] = None

    severity: Literal["critical", "high", "medium", "low"] = "medium"

    evidence: Optional[str] = None

    impact: Optional[str] = None

    suggestion: Optional[str] = None

    suggested_solution: Optional[str] = None

    before_code: Optional[str] = None

    after_code: Optional[str] = None

    corrected_code: Optional[str] = None

    reason_for_correction: Optional[str] = None

    confidence: Optional[int] = Field(default=None, ge=0, le=100)


# ============================================================
# PERFORMANCE INFORMATION
# ============================================================

class PerformanceInfo(BaseModel):

    time_complexity: Optional[str] = None

    space_complexity: Optional[str] = None

    issues: List[PerformanceIssue] = Field(default_factory=list)

# ============================================================
# SECURITY FINDING
# ============================================================

class SecurityFinding(BaseModel):

    title: str

    description: str

    explanation: Optional[str] = None

    file: Optional[str] = None

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: Optional[str] = None

    impact: Optional[str] = None

    suggestion: Optional[str] = None

    suggested_solution: Optional[str] = None

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low"
    ] = "medium"

    before_code: Optional[str] = None

    after_code: Optional[str] = None

    corrected_code: Optional[str] = None

    reason_for_correction: Optional[str] = None

    confidence: int = Field(
        default=80,
        ge=0,
        le=100
    )


# ============================================================
# SECURITY INFORMATION
# ============================================================

class SecurityInfo(BaseModel):

    issues_found: int = Field(
        default=0,
        ge=0
    )

    issues: List[
        SecurityFinding
    ] = Field(
        default_factory=list
    )

    @field_validator("issues_found", mode="before")
    @classmethod
    def coerce_issues_found(cls, v):
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, (int, float)):
            return int(v)
        return 0


# ============================================================
# CODE QUALITY FINDING
# ============================================================

class CodeQualityFinding(BaseModel):

    title: str = "Code Quality Note"

    description: str

    explanation: Optional[str] = None

    file: Optional[str] = None

    line: Optional[int] = None

    line_range: Optional[str] = None

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low"
    ] = "low"

    evidence: Optional[str] = None

    impact: Optional[str] = None

    suggestion: Optional[str] = None

    suggested_solution: Optional[str] = None

    before_code: Optional[str] = None

    after_code: Optional[str] = None

    corrected_code: Optional[str] = None

    reason_for_correction: Optional[str] = None

    confidence: Optional[int] = Field(
        default=None,
        ge=0,
        le=100
    )


# ============================================================
# CODE QUALITY INFORMATION
# ============================================================

class CodeQualityInfo(BaseModel):

    observations: List[
        CodeQualityFinding
    ] = Field(
        default_factory=list
    )

    suggestions: List[
        CodeQualityFinding
    ] = Field(
        default_factory=list
    )

    @field_validator("observations", "suggestions", mode="before")
    @classmethod
    def coerce_findings(cls, v):
        if isinstance(v, str):
            return [{"title": "Code Quality Note", "description": v, "severity": "low"}]
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append({"title": "Code Quality Note", "description": item, "severity": "low"})
                elif isinstance(item, dict):
                    if "title" not in item:
                        item["title"] = "Code Quality Note"
                    if "description" not in item:
                        item["description"] = item.get("title", "Observation")
                    res.append(item)
                else:
                    res.append(item)
            return res
        return []


# ============================================================
# UNIFIED DETECTED ISSUE (8-POINT SOLUTION MODEL)
# ============================================================

class DetectedIssue(BaseModel):

    title: str

    category: str

    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    description: str

    explanation: Optional[str] = None

    severity: Literal["critical", "high", "medium", "low"] = "medium"

    suggested_solution: Optional[str] = None

    before_code: Optional[str] = None

    after_code: Optional[str] = None

    corrected_code: Optional[str] = None

    reason_for_correction: Optional[str] = None

    impact: Optional[str] = None

    confidence: Optional[int] = None


# ============================================================
# STRUCTURED REVIEW
# ============================================================

class StructuredReview(BaseModel):

    # --------------------------------------------------------
    # PROJECT
    # --------------------------------------------------------

    project: ProjectInfo

    detected_issues: Optional[List[DetectedIssue]] = None

    # --------------------------------------------------------
    # USER REVIEW REQUEST
    # --------------------------------------------------------

    question: str

    user_requirements: List[str] = Field(
        default_factory=list
    )

    review_types: List[str] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    answer_summary: str

    # --------------------------------------------------------
    # FILE INFORMATION
    # --------------------------------------------------------

    files_analyzed: List[
        FileAnalyzed
    ] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # CODE STRUCTURE
    # --------------------------------------------------------

    key_methods: List[str] = Field(
        default_factory=list
    )

    key_classes: List[str] = Field(
        default_factory=list
    )

    libraries: List[str] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # FINDINGS
    # --------------------------------------------------------

    bugs: List[
        BugFinding
    ] = Field(
        default_factory=list
    )

    errors: List[
        ErrorFinding
    ] = Field(
        default_factory=list
    )

    performance: Optional[
        PerformanceInfo
    ] = None

    security: Optional[
        SecurityInfo
    ] = None

    code_quality: Optional[
        CodeQualityInfo
    ] = None

    best_practices: Optional[
        List[DetectedIssue]
    ] = None

    # --------------------------------------------------------
    # CORRECTED CODE
    # --------------------------------------------------------

    corrected_code: List[
        CorrectedCode
    ] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # OUTPUT / SCORING
    # --------------------------------------------------------

    expected_output: Optional[str] = None

    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )

    confidence: Optional[int] = Field(
        default=None,
        ge=0,
        le=100
    )

    final_verdict: str


# ============================================================
# SEND EMAIL REQUEST
# ============================================================

class SendEmailRequest(BaseModel):

    email: str = Field(
        min_length=3,
        max_length=255
    )

    category: Optional[str] = Field(
        default="full_review"
    )

    review_id: Optional[str] = None

    review_data: Optional[Dict[str, Any]] = None

    report_markdown: Optional[str] = None

    corrected_code: Optional[List[Dict[str, Any]]] = None