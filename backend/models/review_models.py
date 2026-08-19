# ============================================================
# backend/models/review_models.py
# ============================================================

from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# ============================================================
# REQUEST MODEL
# ============================================================

class ReviewRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
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
# FILE ANALYZED
# ============================================================

class FileAnalyzed(BaseModel):

    file_name: str

    path: str

    language: str


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

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low"
    ]

    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str = ""

    description: str

    impact: str = ""

    fix: str = ""

    confidence: int = Field(
        default=0,
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

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str = ""

    description: str

    impact: str = ""

    fix: str = ""

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


# ============================================================
# PERFORMANCE FINDING
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


# ============================================================
# PERFORMANCE INFORMATION
# ============================================================

class PerformanceInfo(BaseModel):

    time_complexity: str = ""

    space_complexity: str = ""

    issues: List[
        PerformanceIssue
    ] = Field(
        default_factory=list
    )


# ============================================================
# SECURITY FINDING
# ============================================================

class SecurityFinding(BaseModel):

    title: str

    description: str

    file: Optional[str] = None

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: Optional[str] = None

    impact: Optional[str] = None

    suggestion: Optional[str] = None

    severity: Optional[
        Literal[
            "critical",
            "high",
            "medium",
            "low"
        ]
    ] = None

    confidence: Optional[int] = Field(
        default=None,
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


# ============================================================
# CODE QUALITY FINDING
# ============================================================

class CodeQualityFinding(BaseModel):

    title: str

    description: str

    file: Optional[str] = None

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: Optional[str] = None

    impact: Optional[str] = None

    suggestion: Optional[str] = None

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


# ============================================================
# STRUCTURED REVIEW
# ============================================================

class StructuredReview(BaseModel):

    project: ProjectInfo

    question: str

    review_types: List[str] = Field(
        default_factory=list
    )

    answer_summary: str = ""

    files_analyzed: List[
        FileAnalyzed
    ] = Field(
        default_factory=list
    )

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