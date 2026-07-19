import os
import shutil
import zipfile
from pathlib import Path

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from groq import Groq
from rag.pipeline import RAGPipeline

# ===========================
# Load Environment Variables
# ===========================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise Exception("GROQ_API_KEY not found in .env")

# ===========================
# Configure Groq
# ===========================

client = Groq(api_key=API_KEY)

rag_pipeline = RAGPipeline()

# ===========================
# FastAPI App
# ===========================

app = FastAPI(title="AI Code Review Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# Project Directories
# ===========================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

EXTRACT_DIR = Path("extracted")
EXTRACT_DIR.mkdir(exist_ok=True)

# ===========================
# Request Model
# ===========================

class ReviewRequest(BaseModel):
    question: str

# ===========================
# Home API
# ===========================

@app.get("/")
def home():
    return {
        "message": "AI Code Review Assistant Backend Running Successfully"
    }

# ===========================
# Upload Project API
# ===========================

@app.post("/upload-project")
async def upload_project(file: UploadFile = File(...)):

    try:

        if not file.filename.endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a ZIP file."
            )

        # Save uploaded zip
        zip_path = UPLOAD_DIR / file.filename

        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract project
        project_name = Path(file.filename).stem
        project_folder = EXTRACT_DIR / project_name

        if project_folder.exists():
            shutil.rmtree(project_folder)

        project_folder.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(project_folder)

        # Build Vector Database
        rag_pipeline.build_vector_database(str(project_folder))

        return {
            "success": True,
            "message": "Project uploaded and indexed successfully.",
            "project_name": project_name
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ===========================
# Review Project API (RAG)
# ===========================

@app.post("/review")
def review_project(data: ReviewRequest):

    try:

        # Check whether project is indexed
        if not rag_pipeline.vector_database_exists():

            raise HTTPException(
                status_code=400,
                detail="Please upload a project first."
            )

        # Generate RAG Prompt
        prompt = rag_pipeline.generate_prompt(data.question)

        # Ask Groq
        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Senior Software Engineer and AI Code Review Assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )

        return {

            "question": data.question,

            "answer": response.choices[0].message.content

        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )