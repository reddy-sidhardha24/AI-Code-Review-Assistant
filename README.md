AI Code Review Assistant

Grounded AI Code Intelligence | Automated Code Auditing & Intelligent Bug Detection

An AI-powered code review platform that analyzes source code and entire software projects to identify bugs, runtime errors, security vulnerabilities, performance bottlenecks, and code quality issues. It uses Retrieval-Augmented Generation (RAG), multi-model AI analysis, and GitHub integration to provide context-aware reviews, explain problems, suggest corrections, and deliver professional review reports through Gmail.

---

📌 Project Overview

The AI Code Review Assistant is designed to automate and improve the software code review process using Artificial Intelligence and Large Language Models (LLMs).

Traditional code review requires developers to manually inspect source code, identify potential problems, understand their impact, and implement corrections. This process can be time-consuming, especially when working with large projects containing multiple files and dependencies.

Our system provides an intelligent review environment where developers can upload source code, submit project archives, paste code, or connect GitHub repositories. The system analyzes the code, retrieves relevant project context, identifies potential issues, and generates actionable recommendations with corrected code.

The platform also supports an interactive correction workflow, allowing developers to inspect proposed changes, accept or reject fixes, and create GitHub Pull Requests. Review reports can be generated in multiple formats and automatically delivered to the user's Gmail account.

🎯 Project Objectives

- Automate source code review using AI-based analysis.
- Detect bugs, runtime errors, and logical issues.
- Identify potential security vulnerabilities.
- Analyze performance bottlenecks and inefficient algorithms.
- Improve code readability, maintainability, and coding standards.
- Generate context-aware explanations and suggested code corrections.
- Support project-wide analysis across multiple source files.
- Integrate with GitHub for repository analysis and Pull Request creation.
- Generate professional code review reports in multiple formats.
- Deliver review reports and corrected code through Gmail.
- Provide an interactive interface for reviewing and accepting AI-generated fixes.

✨ Key Features

1. Intelligent Code Review

- Analyze individual source files and complete software projects.
- Review code using AI-powered analysis.
- Identify bugs, errors, security risks, performance issues, and code quality concerns.
- Provide issue descriptions, severity levels, affected locations, and suggested solutions.
- Generate corrected code with explanations.

2. Multiple Code Input Methods

- Upload project ZIP archives.
- Upload individual source files.
- Paste source code directly into the application.
- Connect and analyze GitHub repositories.
- Perform project-wide reviews across supported source files.

3. RAG-Based Project Understanding

The system uses Retrieval-Augmented Generation to improve the relevance of AI-generated reviews.

- Load and process source code files.
- Split code into manageable chunks.
- Generate semantic embeddings.
- Store embeddings in a vector database.
- Retrieve relevant code sections based on review queries.
- Provide retrieved context to the AI model.
- Generate grounded and context-aware review findings.

4. Multi-Model AI Configuration

- Configure multiple AI models and providers.
- Support local Ollama models.
- Configure cloud-based AI providers where supported.
- Select models for review execution.
- Support single-agent and multi-agent review workflows.
- Customize model parameters such as temperature.

5. Interactive Code Preview & Diff

- Display original and proposed corrected code.
- Compare changes using a side-by-side diff interface.
- Accept or reject individual proposed corrections.
- Request additional modifications from the AI agent.
- Review corrections before committing them.
- Push accepted changes to GitHub through a separate branch.

6. GitHub Integration

- Authenticate with GitHub.
- Access authorized repositories.
- Select repositories and branches for analysis.
- Review repository source code.
- Inspect proposed code changes.
- Create dedicated branches for accepted fixes.
- Commit accepted corrections.
- Automatically open Pull Requests against the target branch.
- Review changes before merging them into the main branch.

7. Automated Review Report Generation

Generate structured reports containing:

- Project name and programming language.
- Project health score.
- Executive summary.
- Detailed review findings.
- Issue severity and category.
- File paths and line locations.
- Problem descriptions and explanations.
- Suggested fixes and corrected code.
- Security and performance observations.
- Code quality recommendations.
- Final review verdict.

8. Gmail-Based Report Delivery

The system provides automated email delivery of code review results.

- Send review reports directly to the user's Gmail address.
- Deliver reports after the review process is completed.
- Attach generated report files.
- Include the project name and review summary in the email.
- Deliver corrected code and review artifacts where configured.
- Support convenient access to reports outside the application.

Supported report attachments:

File| Purpose
"Review_Report.pdf"| Professional, printable review report
"Review_Report.md"| Markdown report for documentation and GitHub
"Review_Report.html"| Browser-readable interactive report
"Corrected_Code.txt"| Corrected code generated from the review

9. Dashboard & Review History

- View code review statistics.
- Track review activity.
- Access previous review results.
- Monitor detected issues and project health.
- Navigate between completed reviews.
- View project details and analysis summaries.

10. Workspace Configuration

- Customize workspace themes.
- Configure AI models and providers.
- Select review execution modes.
- Manage GitHub integration.
- Configure review preferences.
- Access application settings through a centralized configuration interface.

---

🛠️ Technology Stack

Frontend Technologies

Technology| Purpose
React| Build the interactive and component-based user interface
TypeScript / JavaScript| Implement frontend logic and application functionality
Vite| Provide frontend development server and optimized builds
HTML5| Structure application pages and components
CSS3| Implement responsive layouts, styling, and themes
Axios| Communicate with backend APIs
React Router| Handle navigation between application pages
Diff Viewer| Display original and proposed code changes

Backend Technologies

Technology| Purpose
Python| Implement AI processing and backend logic
FastAPI| Provide REST APIs for code review and application services
Flask| Used in applicable supporting services or earlier application components, if retained in the deployed version
Uvicorn| Run the FastAPI application server
Pydantic| Validate request data and structured AI responses

Artificial Intelligence & RAG

Technology| Purpose
Large Language Models (LLMs)| Analyze code and generate explanations and fixes
Groq API| Provide cloud-based LLM inference where configured
Ollama| Run supported local language models
SentenceTransformers| Convert code chunks and queries into semantic embeddings
"all-MiniLM-L6-v2"| Generate vector representations for semantic retrieval
FAISS| Store and search vector embeddings efficiently
RAG| Retrieve relevant source code context before AI generation
Multi-Agent AI| Support collaborative analysis using configured models

Database & Version Control

Technology| Purpose
SQLite| Store application data where configured
Git| Track source code changes
GitHub API| Access repositories, branches, commits, and Pull Requests

Report Generation & Communication

Technology| Purpose
Python PDF libraries| Generate downloadable PDF reports
HTML / CSS| Generate formatted HTML reports
Markdown| Generate portable review documentation
SMTP / Gmail| Send review reports through email
Environment Variables| Store API credentials and configuration securely

---

🏗️ System Architecture

                 Developer / User
                        |
                        v
          React + TypeScript Frontend
                        |
       +----------------+----------------+
       |                |                |
   ZIP Upload       Paste Code      GitHub Repo
       |                |                |
       +----------------+----------------+
                        |
                        v
               FastAPI Backend
                        |
                        v
                Source Code Loader
                        |
                        v
                 Code Chunking
                        |
                        v
              SentenceTransformer
                 Embeddings
                        |
                        v
                 FAISS Vector DB
                        |
                        v
             Semantic Code Retrieval
                        |
                        v
               Prompt Construction
                        |
                        v
             AI Review / Agent Pool
                        |
                        v
              Structured Review Output
                        |
       +----------------+----------------+
       |                |                |
   Bug Detection   Security Review   Performance
       |                |                |
       +----------------+----------------+
                        |
                        v
             Code Quality Analysis
                        |
                        v
           Suggested Fixes & Corrected Code
                        |
                        v
              Interactive Code Diff
                        |
             +----------+-----------+
             |                      |
        Accept / Reject       Request Changes
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
