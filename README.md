🤖 AI Code Review Assistant

Grounded AI Code Intelligence | Intelligent Code Auditing & Automated Fixes

<p align="center">
  <img src="https://img.shields.io/badge/AI-Powered-6C63FF?style=for-the-badge" alt="AI Powered">
  <img src="https://img.shields.io/badge/RAG-Enabled-00A884?style=for-the-badge" alt="RAG Enabled">
  <img src="https://img.shields.io/badge/Python-FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python FastAPI">
  <img src="https://img.shields.io/badge/React-TypeScript-3178C6?style=for-the-badge&logo=react&logoColor=white" alt="React TypeScript">
  <img src="https://img.shields.io/badge/GitHub-Integrated-181717?style=for-the-badge&logo=github" alt="GitHub Integration">
</p><p align="center">
  <strong>Detect bugs. Understand code. Generate fixes. Deliver intelligent reviews.</strong>
</p>---

📌 Table of Contents

- "Overview" (#-overview)
- "Project Objectives" (#-project-objectives)
- "Key Features" (#-key-features)
- "Technology Stack" (#-technology-stack)
- "System Architecture" (#-system-architecture)
- "Application Workflow" (#-application-workflow)
- "AI and RAG Pipeline" (#-ai-and-rag-pipeline)
- "GitHub Integration" (#-github-integration)
- "Gmail Report Delivery" (#-gmail-report-delivery)
- "Report Formats" (#-report-formats)
- "Project Structure" (#-project-structure)
- "Installation and Setup" (#-installation-and-setup)
- "Environment Configuration" (#-environment-configuration)
- "Example Review" (#-example-review)
- "Advantages" (#-advantages)
- "Limitations" (#-limitations)
- "Future Enhancements" (#-future-enhancements)
- "Project Team" (#-project-team)
- "Academic Information" (#-academic-information)
- "Conclusion" (#-conclusion)

---

📖 Overview

AI Code Review Assistant is an intelligent software code auditing platform that uses Artificial Intelligence, Large Language Models (LLMs), and Retrieval-Augmented Generation (RAG) to analyze source code and identify potential software defects.

The system enables developers to review individual files, complete project archives, pasted code, and GitHub repositories. It examines source code to identify bugs, runtime errors, security vulnerabilities, performance bottlenecks, and code quality issues.

Unlike traditional manual code review, the platform provides contextual explanations, suggested corrections, and corrected code through an interactive review interface.

Developers can inspect proposed changes, accept or reject individual fixes, and push accepted corrections to GitHub through dedicated branches and Pull Requests.

The application also generates professional review reports and delivers them through Gmail, allowing developers to access their review results outside the platform.

The Core Idea

«Transform code review from a time-consuming manual activity into an intelligent, context-aware, and developer-controlled workflow.»

---

🎯 Project Objectives

Objective| Description
Automated Code Review| Analyze source code and identify potential issues using AI
Bug Detection| Detect logical errors, runtime exceptions, and programming mistakes
Security Analysis| Identify potential vulnerabilities and insecure coding practices
Performance Analysis| Examine inefficient algorithms and resource usage
Code Quality Improvement| Improve readability, maintainability, and coding practices
Intelligent Code Correction| Generate suggested fixes and corrected code
Project Understanding| Analyze relationships between source files using RAG
GitHub Integration| Review repositories and create Pull Requests for accepted changes
Automated Reporting| Generate structured reports in multiple formats
Email Delivery| Deliver review reports and configured code artifacts through Gmail

---

✨ Key Features

<table>
<tr>
<td width="50%">🐛 Bug Detection

- Identify runtime errors
- Detect logical defects
- Highlight potential exceptions
- Explain the cause of each issue

</td>
<td width="50%">🛡️ Security Analysis

- Identify potential vulnerabilities
- Detect insecure coding practices
- Highlight risky operations
- Recommend safer alternatives

</td>
</tr>
<tr>
<td>⚡ Performance Analysis

- Identify inefficient operations
- Evaluate algorithmic complexity
- Detect potential bottlenecks
- Recommend optimizations

</td>
<td>✨ Code Quality

- Review readability
- Identify maintainability concerns
- Detect structural problems
- Recommend coding improvements

</td>
</tr>
<tr>
<td>🧠 RAG-Based Code Understanding

- Semantic code retrieval
- Project-aware analysis
- Contextual review generation
- Multi-file code understanding

</td>
<td>🔧 Intelligent Code Fixes

- Generate corrected code
- Explain proposed changes
- Display before-and-after diffs
- Accept or reject individual fixes

</td>
</tr>
<tr>
<td>🔗 GitHub Integration

- Repository authorization
- Branch-based corrections
- Commit accepted changes
- Automated Pull Request creation

</td>
<td>📧 Gmail Report Delivery

- Automated report emails
- PDF, HTML, and Markdown reports
- Corrected-code attachments
- Access to review results outside the app

</td>
</tr>
</table>Additional Platform Features

Feature| Description
Multiple Input Sources| ZIP archives, source files, pasted code, and GitHub repositories
Multi-Model Configuration| Configure supported cloud and local AI models
Multi-Agent Review| Execute collaborative review workflows using configured models
Dashboard| View review statistics and project analysis information
Review History| Access previously completed code reviews
Workspace Configuration| Manage themes, AI models, review settings, and integrations
Project Details| View analyzed files, methods, classes, and detected libraries
Multiple Report Formats| Generate PDF, HTML, and Markdown review reports

---

🛠️ Technology Stack

Frontend

Technology| Purpose
React| Build reusable UI components and interactive pages
TypeScript / JavaScript| Implement application logic and frontend behavior
Vite| Provide development server and production build tooling
HTML5| Structure application pages
CSS3| Create responsive layouts, themes, and visual styling
Axios| Communicate with backend APIs
React Router| Navigate between application pages

Backend

Technology| Purpose
Python| Implement backend logic and AI processing
FastAPI| Provide REST APIs for review and application services
Uvicorn| Run the FastAPI application
Pydantic| Validate structured request and response data
SQLite| Store application data where configured

Artificial Intelligence and RAG

Technology| Purpose
Large Language Models| Analyze code and generate explanations and corrections
Groq API| Provide cloud-based LLM inference where configured
Ollama| Run supported local AI models
SentenceTransformers| Generate semantic embeddings
"all-MiniLM-L6-v2"| Convert source code chunks and queries into vectors
FAISS| Store and retrieve semantically relevant code chunks
RAG| Ground AI reviews in retrieved project source code
Multi-Agent AI| Support collaborative analysis using configured models

Integrations and Reporting

Technology| Purpose
Git| Version control and source code management
GitHub API| Repository access, branches, commits, and Pull Requests
Gmail SMTP| Email delivery of generated review reports
PDF Generation Library| Create printable PDF reports
HTML / CSS| Generate formatted HTML reports
Markdown| Create portable review documentation
Environment Variables| Store API credentials and application configuration

---

🏗️ System Architecture

flowchart TD
    A[Developer / User] --> B[React Frontend]
    B --> C{Project Source}

    C --> D[ZIP Upload]
    C --> E[Source Files]
    C --> F[Paste Code]
    C --> G[GitHub Repository]

    D --> H[FastAPI Backend]
    E --> H
    F --> H
    G --> H

    H --> I[Source Code Loader]
    I --> J[Code Chunker]
    J --> K[SentenceTransformer Embeddings]
    K --> L[FAISS Vector Database]

    L --> M[Semantic Retriever]
    M --> N[Prompt Builder]
    N --> O[AI Model / Multi-Agent Pool]

    O --> P[Structured Review Findings]

    P --> Q[Bug Detection]
    P --> R[Security Analysis]
    P --> S[Performance Analysis]
    P --> T[Code Quality Analysis]

    Q --> U[Suggested Fixes]
    R --> U
    S --> U
    T --> U

    U --> V[Interactive Code Diff]
    V --> W[Accept / Reject Changes]

    W --> X[GitHub Branch and Commit]
    X --> Y[Pull Request Creation]

    P --> Z[Report Generation]
    Z --> Z1[PDF Report]
    Z --> Z2[HTML Report]
    Z --> Z3[Markdown Report]
    Z --> Z4[Corrected Code]

    Z1 --> AA[Gmail Delivery]
    Z2 --> AA
    Z3 --> AA
    Z4 --> AA

---

🔄 Application Workflow

sequenceDiagram
    actor Developer
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant RAG as RAG Pipeline
    participant AI as AI Model
    participant GitHub
    participant Gmail

    Developer->>UI: Upload code / Select repository
    UI->>API: Submit review request
    API->>RAG: Load and index source code
    RAG->>RAG: Chunk, embed, and store code
    RAG->>AI: Send retrieved context and prompt
    AI-->>API: Return structured findings
    API-->>UI: Display review results

    Developer->>UI: Inspect proposed corrections
    UI-->>Developer: Show code diff and explanations
    Developer->>UI: Accept selected fixes
    UI->>API: Submit accepted changes
    API->>GitHub: Create branch, commit, and Pull Request
    GitHub-->>UI: Return Pull Request details

    API->>API: Generate review reports
    API->>Gmail: Send report email with attachments
    Gmail-->>Developer: Deliver review results

---

🧠 AI and RAG Pipeline

The project uses Retrieval-Augmented Generation to provide AI models with relevant source code context before generating review findings.

RAG Processing Stages

Stage| Component| Responsibility
1| Loader| Extract source files from supported inputs
2| Chunker| Divide source code into manageable segments
3| Embedder| Convert code chunks into semantic vectors
4| Vector Store| Store embeddings using FAISS
5| Retriever| Retrieve relevant source code for review questions
6| Prompt Builder| Combine code context and review instructions
7| AI Pipeline| Generate contextual analysis
8| Structured Output| Organize findings into defined categories
9| Fix Generation| Suggest corrections and corrected code

RAG Architecture

flowchart LR
    A[Source Code] --> B[Loader]
    B --> C[Chunker]
    C --> D[Embedding Model]
    D --> E[FAISS Index]

    F[Review Question] --> G[Query Embedding]
    G --> H[Retriever]
    E --> H

    H --> I[Relevant Code Context]
    I --> J[Prompt Builder]
    J --> K[LLM]
    K --> L[Review Findings and Fixes]

Why RAG?

- Provides relevant source code context to the AI model.
- Helps analyze code across multiple files.
- Reduces reliance on general model knowledge alone.
- Improves the relevance of explanations and recommendations.
- Supports project-aware code review.

---

🔗 GitHub Integration

The GitHub integration connects AI code review with practical software development workflows.

Supported Workflow

1. Connect a GitHub account through the application.
2. Authorize repositories for access.
3. Select a repository and target branch.
4. Analyze repository source code.
5. Inspect AI-generated corrections.
6. Accept or reject proposed changes.
7. Create a dedicated correction branch.
8. Commit accepted corrections.
9. Open a Pull Request against the target branch.
10. Review and merge changes through GitHub.

Pull Request Workflow

flowchart TD
    A[Review GitHub Repository] --> B[Generate Proposed Fixes]
    B --> C[Developer Inspects Diff]
    C --> D{Accept Fixes?}
    D -->|No| E[Reject or Modify]
    D -->|Yes| F[Create Dedicated Branch]
    F --> G[Commit Accepted Changes]
    G --> H[Open Pull Request]
    H --> I[Human Review]
    I --> J[Merge When Approved]

Important: Accepted AI corrections are prepared for review through a Pull Request. The developer retains control over the final merge.

---

📧 Gmail Report Delivery

The application supports automated delivery of code review results through Gmail.

Email Workflow

1. Complete a code review.
2. Generate the review report and configured artifacts.
3. Prepare the email with project details and review summary.
4. Attach the generated files.
5. Send the email through the configured Gmail service.
6. The developer receives the review report in their inbox.

Email Contents

Item| Description
Email Subject| AI Code Review Report – Project Name
Project Summary| Project name, language, and health score
Review Findings| Summary of identified issues
PDF Report| Professional printable report
HTML Report| Browser-readable report
Markdown Report| Portable text-based report
Corrected Code| Generated code artifact, where configured

Gmail Configuration

The application uses Gmail SMTP with authenticated credentials.

SMTP Host: smtp.gmail.com
SMTP Port: 587
Authentication: Gmail App Password
Connection Security: STARTTLS

Security Note: Gmail App Passwords, GitHub tokens, and AI API keys must be stored securely in environment variables and must never be committed to the repository.

---

📄 Report Formats

Report File| Format| Purpose
"Review_Report.pdf"| PDF| Printable and shareable audit report
"Review_Report.md"| Markdown| Documentation and GitHub-compatible report
"Review_Report.html"| HTML| Browser-readable formatted report
"Corrected_Code.txt"| Text| Corrected code generated by the AI

Report Contents

- Project name and programming language
- Grounded project health score
- Executive summary
- Detailed findings
- Issue category and severity
- Affected file and line location
- Problem explanation
- Suggested solution
- Before-and-after code comparison
- Corrected code
- Final review verdict

---

📂 Project Structure

The following structure represents the major logical components of the application. Update filenames to match the actual repository implementation.

AI-Code-Review-Assistant/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload/
│   │   │   ├── CodeEditor/
│   │   │   ├── DiffViewer/
│   │   │   ├── ReviewFindings/
│   │   │   └── Dashboard/
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Review.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── History.jsx
│   │   │   └── Configuration.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app.py
│   │
│   ├── routes/
│   │   ├── review_routes.py
│   │   ├── upload_routes.py
│   │   ├── github_routes.py
│   │   └── report_routes.py
│   │
│   ├── services/
│   │   ├── review_service.py
│   │   ├── upload_service.py
│   │   ├── github_service.py
│   │   ├── report_service.py
│   │   └── email_service.py
│   │
│   ├── rag/
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── prompt_builder.py
│   │   └── pipeline.py
│   │
│   ├── report_generation/
│   │   ├── pdf_generator.py
│   │   ├── html_generator.py
│   │   └── markdown_generator.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── tests/
├── .gitignore
├── README.md
└── LICENSE

---

⚙️ Installation and Setup

Prerequisites

Software| Requirement
Python| 3.10+ recommended
Node.js| Compatible with the installed Vite version
npm| Node package manager
Git| For repository cloning and version control
Ollama| Required when using local models
GitHub Account| Required for GitHub integration
Gmail Account| Required for email report delivery

1. Clone the Repository

git clone https://github.com/<your-username>/AI-Code-Review-Assistant.git
cd AI-Code-Review-Assistant

2. Set Up the Backend

cd backend
python -m venv venv

Activate the virtual environment on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Start the backend:

uvicorn app:app --reload

Backend URL:

http://localhost:8000

API documentation:

http://localhost:8000/docs

3. Set Up the Frontend

Open a separate terminal:

cd frontend
npm install
npm run dev

Open the local URL displayed by Vite.

4. Configure Local AI Models

If the application uses Ollama:

ollama pull qwen2.5:3b

ollama pull llama3.2:3b

Use the exact model names configured in the application.

5. Configure GitHub

1. Open the Workspace Configuration page.
2. Connect your GitHub account.
3. Authorize the required repositories.
4. Select a repository and branch.
5. Start a code review.

6. Configure Gmail

1. Enable two-step verification on your Google account.
2. Generate a Google App Password.
3. Configure the Gmail SMTP settings.
4. Store credentials in the backend environment.
5. Complete a test review and verify email delivery.

---

🔐 Environment Configuration

Create a ".env" file in the backend directory using the application's supported environment variables.

Example:

# AI Provider
GROQ_API_KEY=your_groq_api_key

# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_google_app_password
SMTP_FROM_EMAIL=your_email@gmail.com

# Application
APP_ENV=development

Additional GitHub and model configuration variables may be required depending on the implementation.

Never upload your actual ".env" file to GitHub.

---

📊 Example Review

Sample Project

Property| Value
Project Name| "javatest1"
Programming Language| Java
Project Health Score| 75 / 100
Detected Issue| Division by Zero
Severity| Critical
Affected Method| "calculateAverage()"

Problem

The method attempts to calculate the average of an empty integer array. When the array length is zero, the division operation throws an "ArithmeticException".

Suggested Correction

public static double calculateAverage(int[] numbers) {
    if (numbers == null || numbers.length == 0) {
        return 0;
    }

    int sum = 0;

    for (int number : numbers) {
        sum += number;
    }

    return (double) sum / numbers.length;
}

Expected Review Result

- Identify the division-by-zero issue.
- Explain the cause of the exception.
- Recommend input validation.
- Generate corrected code.
- Display the proposed fix in the diff interface.
- Include the finding in the generated review report.

---

✅ Advantages

Advantage| Benefit
Automated Review| Reduces repetitive manual code inspection
Early Bug Detection| Helps identify issues before deployment
Context-Aware Analysis| Uses retrieved project code to support AI findings
Intelligent Corrections| Provides suggested fixes with explanations
Security Awareness| Helps identify potential insecure coding practices
Code Quality Improvement| Supports readable and maintainable code
Developer Control| Allows developers to accept or reject proposed changes
GitHub Workflow| Integrates review corrections with Pull Requests
Automated Documentation| Generates structured review reports
Email Delivery| Makes review results accessible through Gmail
Flexible AI Models| Supports configured local and cloud models

---

⚠️ Limitations

- AI-generated findings may include false positives or missed issues.
- Suggested fixes must be reviewed and tested by developers.
- Review quality depends on the source code context and model capabilities.
- Large projects may require additional processing time and memory.
- Local model performance depends on hardware resources.
- Cloud model usage may involve API costs and rate limits.
- AI code review does not replace testing, static analysis, or security audits.
- GitHub and Gmail integrations require valid authorization and configuration.

---

🚀 Future Enhancements

- Automated unit test generation for proposed fixes.
- Integration with CI/CD pipelines.
- Expanded programming language support.
- Advanced static analysis integration.
- Custom organization coding standards.
- Team collaboration and review assignments.
- Improved large-repository indexing.
- Security scanner integration.
- Review analytics and tre     Accept / Reject       Request Changes
             |
             v
       GitHub Branch & Commit
             |
             v
        Pull Request Creation
             
             Review Results
                    |
                    v
           Report Generation
                    |
       +------------+------------+
       |            |            |
      PDF          HTML        Markdown
                    |
                    v
             Gmail Delivery
                    |
                    v
                 Developer

---

🔄 Application Workflow

1. The user signs in and opens the code review workspace.
2. The user selects a source code input method.
3. The backend receives the uploaded files, pasted code, or repository information.
4. The source loader extracts supported files and project structure.
5. The code chunker divides source files into meaningful segments.
6. SentenceTransformer generates semantic embeddings.
7. FAISS stores the embeddings for efficient retrieval.
8. The retriever identifies relevant code sections for the review task.
9. The prompt builder combines source context, review requirements, and analysis instructions.
10. Configured AI models analyze the code and generate structured findings.
11. The application organizes findings into bugs, security, performance, and code quality categories.
12. The system generates suggested corrections and explanations.
13. The developer inspects the proposed changes through the interactive diff interface.
14. Accepted changes can be committed to a dedicated GitHub branch.
15. The system creates a Pull Request for further review.
16. The application generates reports in supported formats.
17. The reports and configured corrected-code artifacts are delivered through Gmail.

---

📂 Project Structure

The following is a logical reference structure for the application. Actual filenames and folder locations may differ depending on the current implementation.

AI-Code-Review-Assistant/
│
├── frontend/
│   ├── public/
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload/
│   │   │   ├── CodeEditor/
│   │   │   ├── DiffViewer/
│   │   │   ├── ReviewFindings/
│   │   │   ├── Dashboard/
│   │   │   └── Navbar/
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Review.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── History.jsx
│   │   │   ├── Configuration.jsx
│   │   │   ├── About.jsx
│   │   │   └── Contact.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app.py
│   │
│   ├── routes/
│   │   ├── review_routes.py
│   │   ├── upload_routes.py
│   │   ├── github_routes.py
│   │   └── report_routes.py
│   │
│   ├── services/
│   │   ├── review_service.py
│   │   ├── upload_service.py
│   │   ├── github_service.py
│   │   ├── report_service.py
│   │   └── email_service.py
│   │
│   ├── rag/
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── prompt_builder.py
│   │   └── pipeline.py
│   │
│   ├── report_generation/
│   │   ├── pdf_generator.py
│   │   ├── html_generator.py
│   │   └── markdown_generator.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── tests/
│   ├── test_review.py
│   ├── test_upload.py
│   └── test_reports.py
│
├── .gitignore
├── README.md
└── LICENSE

---

⚙️ Installation & Setup

Prerequisites

Ensure the following tools are installed:

- Python 3.10 or later
- Node.js and npm
- Git
- Ollama (if using local AI models)
- GitHub account for repository integration
- Gmail account for report delivery

1. Clone the Repository

git clone https://github.com/<your-username>/AI-Code-Review-Assistant.git

cd AI-Code-Review-Assistant

2. Backend Setup

Navigate to the backend directory:

cd backend

Create a virtual environment:

python -m venv venv

Activate the environment on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Configure the environment variables using the provided ".env.example" file.

Start the backend server:

uvicorn app:app --reload

The backend API will be available at:

http://localhost:8000

FastAPI documentation:

http://localhost:8000/docs

3. Frontend Setup

Open another terminal and navigate to the frontend directory:

cd frontend

Install dependencies:

npm install

Start the frontend development server:

npm run dev

Open the local URL displayed by Vite in your browser.

4. Configure Local AI Models

If using Ollama, install and start Ollama, then download the models configured in the application.

Example:

ollama pull qwen2.5:3b

ollama pull llama3.2:3b

Model names must match the configurations stored in the application.

5. Configure GitHub Integration

1. Open the application configuration page.
2. Connect your GitHub account using the supported authorization flow.
3. Authorize the repositories you want to analyze.
4. Select a repository and branch.
5. Start a review and inspect the proposed corrections.

6. Configure Gmail Report Delivery

For Gmail SMTP integration:

1. Enable two-step verification on the Google account.
2. Generate a Google App Password.
3. Store the SMTP configuration in the backend environment variables.
4. Configure the recipient email address through the application.
5. Complete a test review and verify the report attachments.

Example environment configuration:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_google_app_password
SMTP_FROM_EMAIL=your_email@gmail.com

Security: Never commit ".env" files, Gmail App Passwords, GitHub tokens, or AI API keys to GitHub. Use environment variables and keep credentials private.

---

📊 Example Review Output

Project: "javatest1"

Programming Language: Java

Grounded Project Health Score: 75/100

Detected Issue: Division by Zero

Severity: Critical

Affected Method: "calculateAverage()"

Problem:

The method attempts to calculate an average using an empty integer array. Since the array length is zero, the calculation can result in an "ArithmeticException".

Suggested Fix:

Validate the array length before performing division and handle empty input appropriately.

Example:

public static double calculateAverage(int[] numbers) {
    if (numbers == null || numbers.length == 0) {
        return 0;
    }

    int sum = 0;

    for (int number : numbers) {
        sum += number;
    }

    return (double) sum / numbers.length;
}

The system presents the issue explanation, suggested correction, and available review artifacts to the developer.

---

📈 Advantages

- Reduces manual code review effort.
- Helps developers identify bugs earlier.
- Provides contextual explanations rather than only error messages.
- Supports project-wide code analysis.
- Improves code readability and maintainability.
- Helps identify potential security vulnerabilities.
- Provides suggested corrections for detected issues.
- Supports human verification through interactive code diffs.
- Integrates with GitHub development workflows.
- Generates downloadable and email-delivered review reports.
- Supports configurable local and cloud AI models.
- Provides a centralized workspace for code review activities.

⚠️ Limitations

- AI-generated findings may contain false positives or false negatives.
- Suggested corrections require developer verification.
- Review quality depends on source code context and model capabilities.
- Large repositories may require additional processing time and resources.
- Local model performance depends on available hardware.
- Cloud model usage may involve API costs and rate limits.
- Static AI review cannot guarantee complete security or correctness.
- GitHub and Gmail integrations require valid authorization and configuration.

🔮 Future Enhancements

- Expand support for additional programming languages.
- Integrate automated unit testing for proposed fixes.
- Add continuous integration and deployment workflows.
- Improve analysis of large monolithic repositories.
- Introduce customizable coding standards and review policies.
- Add team collaboration and review assignment features.
- Enhance vulnerability detection using specialized security scanners.
- Support automated test generation for corrected code.
- Improve review analytics and historical trend visualization.
- Add configurable report templates and organization branding.

👥 Project Team

Project Guide

Mr Mallikharjuna S

Team Leader

K. Niharika

Team Members

- R.V.S. Sidhardha
- K. Manushri
- P. Prasanth

🎓 Academic Information

Project Title: AI Code Review Assistant

Domain: Artificial Intelligence, Software Engineering, and Generative AI

Project Type: Final-Year B.Tech Project

Department: Computer Science and Engineering – Artificial Intelligence

Institution: PBR Visvodaya Institute of Technology & Science, Kavali

University: JNTU Anantapur

📜 Conclusion

The AI Code Review Assistant demonstrates how Artificial Intelligence and Retrieval-Augmented Generation can be applied to improve software development and code quality assurance.

By combining semantic code retrieval, LLM-based analysis, interactive correction workflows, GitHub integration, and automated Gmail report delivery, the platform provides an integrated environment for reviewing software projects.

The system helps developers understand code issues, evaluate suggested fixes, and manage corrections through a structured workflow while retaining human oversight over important software changes.

The project aims to make code review more efficient, accessible, and context-aware while supporting better software quality and maintainability.

---

Developed by the AI Code Review Assistant Project Team

Building smarter, safer, and more maintainable software through grounded AI intelligence.
