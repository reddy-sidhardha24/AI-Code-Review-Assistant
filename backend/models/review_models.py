from typing import List, Optional, Literal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# Request Model
# ============================================================

class ReviewRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
)
# ============================================================
# Paste Code Request
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
# Project Information
# ============================================================

class ProjectInfo(BaseModel):

    name: Optional[str] = None

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
# File Analyzed
# ============================================================

class FileAnalyzed(BaseModel):

    file_name: str

    path: str

    language: str


# ============================================================
# Bug Finding
# ============================================================

class BugFinding(BaseModel):

    title: str

    type: Literal[
        "confirmed",
        "conditional",
        "possible_risk"
    ]

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low"
    ]

    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str

    description: str

    impact: str

    fix: str

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


# ============================================================
# Error Finding
# ============================================================

class ErrorFinding(BaseModel):

    type: str

    title: str

    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str = ""

    description: str

    impact: str = ""

    fix: str

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


# ============================================================
# Performance
# ============================================================

class PerformanceIssue(BaseModel):

    title: str = ""

    description: str = ""

    file: str = ""

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str = ""

    impact: str = ""

    suggestion: str = ""

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


class PerformanceInfo(BaseModel):

    time_complexity: str = ""

    space_complexity: str = ""

    issues: List[PerformanceIssue] = Field(
        default_factory=list
    )


# ============================================================
# Security Finding
# ============================================================

class SecurityFinding(BaseModel):

    title: str

    description: str


# ============================================================
# Security
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


# ============================================================
# Code Quality Finding
# ============================================================

class CodeQualityFinding(BaseModel):

    title: str

    description: str


# ============================================================
# Code Quality
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

# ============================================================
# Structured Review
# ============================================================

class StructuredReview(BaseModel):

    project: ProjectInfo

    question: str

    # Dynamic review types detected by PromptBuilder
    review_types: List[str] = Field(
        default_factory=list
    )

    answer_summary: str = ""

    files_analyzed: List[FileAnalyzed] = Field(
        default_factory=list
    )

    bugs: List[BugFinding] = Field(
        default_factory=list
    )

    errors: List[ErrorFinding] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # Optional analysis sections
    #
    # Explanation-only questions should not be forced to
    # generate meaningless performance/security sections.
    # --------------------------------------------------------

    performance: Optional[
        PerformanceInfo
    ] = None

    security: Optional[
        SecurityInfo
    ] = None

    code_quality: Optional[
        CodeQualityInfo
    ] = None

    key_methods: List[str] = Field(
        default_factory=list
    )

    key_classes: List[str] = Field(
        default_factory=list
    )

    libraries: List[str] = Field(
        default_factory=list
    )

    expected_output: Optional[str] = None

    score: Optional[float] = None

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )

    final_verdict: str = ""