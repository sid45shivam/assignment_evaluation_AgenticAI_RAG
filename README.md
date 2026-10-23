# Agentic AI + RAG Assignment Evaluation System

An academic assignment evaluation architecture combining **multi-agent orchestration**, **deterministic mathematical verification**, and a **local Retrieval-Augmented Generation (RAG) pipeline**. 

Designed for university-level coursework, this system assists faculty by discovering submissions, retrieving supporting academic context with exact source and page citations, independently verifying quantitative calculations, applying quality control audits, and escalating non-standard or creative solutions to faculty for academic review.

---

## 1. Executive Summary & Core Philosophy

University assignment grading often suffers from either **manual grading fatigue** or **naive LLM evaluation hallucinations**. This project solves both issues through a structured, process-aware architecture:

1. **Rubric Primacy**: The approved academic rubric is the sole authoritative scoring standard. Course reference materials provide supporting evidence, never an unchallengeable model answer.
2. **Citation Integrity**: Retrieved citations are strictly attributed to actual course materials with file names and page numbers. The system never invents sources.
3. **Deterministic Verification**: Mathematical calculations (e.g., Economic Order Quantity calculations) are independently verified using deterministic Python scripts, completely isolated from LLM probabilistic reasoning.
4. **Human-in-the-Loop Faculty Approval**: AI produces proposed marks and structured rationales; faculty retains final academic approval. Unlisted or creative answers (e.g. Student C's hybrid model) are escalated to an academic review queue.
5. **100% Local & Free Embeddings**: Uses local Sentence Transformers (`all-MiniLM-L6-v2`) via ChromaDB / ONNX Runtime. Requires no paid embedding APIs and runs fully offline.

---

## 2. System Architecture & Integrated Workflow

The workflow integrates document chunking, vector indexing, semantic retrieval, and five specialist agent skills:

```text
Approved Course Reference Materials (PDF, TXT, MD)
           │
           ▼
 [RAG Ingestion] ──► Overlapping Chunker ──► Sentence-Transformers ──► Local Persistent ChromaDB
                                                                                    │
Student Submissions (Data/submissions/)                                             │
           │                                                                        │
           ▼                                                                        │
 [Skill 1: submission-analysis] ──────────────────────────────────────────┐         │
           │                                                              │         │
           ▼                                                              ▼         │
 [RAG Semantic Retrieval] ◄─────────────────────────────────────────────────────────┘
           │  (Top 3–5 chunks per criterion with filename and page attribution)
           ▼
 [Skill 2: rubric-evaluation] (Authoritative rubric; RAG context as supporting evidence)
           │
           ├──► Numerical Work Detected ──► [Skill 3: numerical-verification] (Deterministic Python)
           │                                              │
           ▼                                              ▼
 [Skill 4: quality-control] ◄─────────────────────────────┘
           │
           ├──► QC Passed ──► [Skill 5: feedback-generation] ──► [Consolidated Batch Summary]
           │
           └──► Ambiguity / Creative Solution ──► Escalation Queue for Faculty Review
```

---

## 3. Specialist Skills Breakdown

The system organizes evaluation responsibilities into five modular, decoupled skills:

| Skill | Role & Responsibility | Trigger Condition | Output Folder |
|---|---|---|---|
| **`submission-analysis`** | Parses student files, maps answers to assignment questions, classifies response types (theory, numerical, case), and flags calculation sections. | Every submission | `evaluation_findings/` |
| **`rubric-evaluation`** | Evaluates student responses against rubric bands, quoting student text and citing retrieved RAG context as supporting evidence. | Every submission | `evaluation_findings/` |
| **`numerical-verification`** | Executes deterministic calculation scripts to independently verify formulas, intermediate arithmetic, and score consistency. | Quantitative content detected (e.g., EOQ) | `verification_findings/` |
| **`quality-control`** | Audits evaluations for rubric alignment, score boundary compliance, calculation consistency, and citation veracity; assigns confidence (HIGH/MEDIUM/LOW). | After evaluation & verification | `quality_findings/` |
| **`feedback-generation`** | Translates validated evaluation rationales into constructive, personalized student feedback with strengths and actionable next steps. | Validated evaluation | `feedback/` |

---

## 4. The RAG Pipeline in Detail

The Retrieval-Augmented Generation engine is implemented in `rag_pipeline.py`:

- **Multi-Format Document Parsing**:
  - **PDF (`.pdf`)**: Uses `pypdf` to extract text page-by-page, recording 1-indexed page numbers.
  - **Text (`.txt`) & Markdown (`.md`)**: Ingests files with multi-encoding fallback (`utf-8`, `utf-8-sig`, `latin-1`).
- **Boundary-Aware Overlapping Chunker**:
  - Implements sliding-window chunking (default ~500 chars with 100 chars overlap) that snaps to natural paragraph breaks (`\n\n`), newlines (`\n`), or sentence endings (`. `) rather than splitting words.
- **Local Embedding Engine**:
  - Model: `all-MiniLM-L6-v2` (384-dimensional dense semantic vectors).
  - Robust Environment Support: Uses ChromaDB's ONNX Runtime implementation (`DefaultEmbeddingFunction`) which executes entirely locally without relying on native PyTorch dynamic libraries, ensuring execution across standard OS environments and restricted Windows systems (e.g., Application Control / AppLocker policies).
- **Persistent Local ChromaDB**:
  - Stores vectors in a persistent SQLite/Parquet local store (`chroma_db/`).
  - Idempotent upserting with deterministic chunk identifiers (`{source}_p{page}_c{chunk_index}`).
- **Context Retrieval & Attribution**:
  - Queries top 3–5 relevant chunks per question/criterion.
  - Returns structured results with source file name, page number, and similarity score.
  - Explicitly flags when reference context is unavailable (`UNAVAILABLE`) so the system scores strictly on the rubric without hallucinating.

---

## 5. Scope & Verification: Automated Suite vs. Live LLM Integration

To maintain academic and professional transparency:

### What Is Fully Implemented, Automated, and Verified:
- **Local RAG Pipeline**: Ingestion, overlapping chunking, local 384-d vector embeddings, ChromaDB indexing, and multi-format semantic retrieval with file/page attribution.
- **Automated Test Suite**: 12 comprehensive unit and integration tests in `test_rag.py` verifying document parsers, chunk overlap, vector dimensionality, query retrieval, and edge cases (100% passing).
- **Independent Numerical Verifier**: Pure deterministic Python scripts (`numerical_verifier.py`, `consistency_checker.py`, `score_calculator.py`) calculating EOQ, testing bounds, and detecting arithmetic discrepancies independently of any LLM.
- **End-to-End Orchestrator**: `workflow_orchestrator.py` discovering submissions, querying RAG context, performing rubric evaluation with RAG citations, running numerical verification, checking quality control, and generating batch summaries.

### Role of Live LLM Integration:
- The specialist skills provide prompt specifications, structured inputs, output schemas, and guardrails ready for LLM consumption.
- If integrating with a live cloud LLM API (e.g., OpenAI, Google Gemini, Anthropic):
  - API keys must be loaded from environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`). Never hardcode credentials.
  - The deterministic numerical verification scripts must remain the sole authority on math calculations, preventing LLM arithmetic errors.
  - The AI evaluation outputs remain **proposed evaluations** subject to final faculty sign-off.

---

## 6. Project Structure

```text
Agent/
├── .gitignore                               # Clean git ignore for bytecode, vector DBs & secrets
├── README.md                                # Project documentation & setup instructions
├── requirements.txt                         # Python dependencies
├── rag_pipeline.py                          # Reusable RAG ingestion, embedding & retrieval engine
├── test_rag.py                              # Automated unit & integration test suite (12 tests)
├── workflow_orchestrator.py                 # End-to-end batch workflow runner
├── Agents.md                                # Orchestrator batch instructions & guardrails
├── SkillRegistry.md                         # Skill routing and output mapping specification
├── chroma_db/                               # Persistent local vector database (generated on ingest)
├── Data/
│   ├── assignment_question.md               # Assignment prompt (Supply Chain Management)
│   ├── assignment_rubric.md                 # Authoritative 100-mark grading rubric
│   ├── reference_materials/                 # Approved course notes, handouts, and PDFs
│   │   ├── lecture_notes_distribution_networks.md
│   │   ├── inventory_theory_handout.txt
│   │   └── supply_chain_strategy_reference.pdf
│   └── submissions/                         # Safe, representative sample submissions
│       ├── student_submission_A.md          # High mastery benchmark
│       ├── student_submission_B.md          # Calculation error & brief case benchmark
│       └── student_submission_C.md          # Creative hybrid network benchmark
├── evaluation_findings/                     # Submission analyses & rubric evaluations with RAG citations
├── verification_findings/                   # Independent mathematical verification reports
├── quality_findings/                        # Quality control validation checklists
├── feedback/                                # Student-facing constructive feedback reports
├── Summary/                                 # Individual summaries & consolidated batch summary
└── skills/                                  # Specialist skill configurations and scripts
    ├── submission-analysis/                 # Structure and section parsing
    ├── rubric-evaluation/                   # Evidence-grounded scoring
    ├── numerical-verification/scripts/      # Deterministic calculation scripts
    ├── quality-control/                     # Audit checklists & confidence rules
    └── feedback-generation/                 # Pedagogical feedback generator
```

---

## 7. Windows Setup & Installation

### Prerequisites
- Python 3.10 or 3.11 (tested on Windows 64-bit)

### Installation
Open Windows PowerShell in the project directory:

```powershell
# 1. (Optional) Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install required dependencies
pip install -r requirements.txt
```

---

## 8. Exact Windows Terminal Execution Commands

### Step 1: Ingest Reference Documents into ChromaDB
Indexes `.pdf`, `.txt`, and `.md` files from `Data/reference_materials/` into persistent local ChromaDB:
```powershell
python rag_pipeline.py ingest --data-dir Data/reference_materials --db-dir chroma_db
```

### Step 2: Query the Vector Database (CLI Semantic Search)
Verify semantic retrieval across course topics with exact source and page attribution:
```powershell
# Query Distribution Network concepts (Question 1)
python rag_pipeline.py query "trade-off between responsiveness and cost in distribution networks" --top-k 3

# Query EOQ calculation formulas (Question 2)
python rag_pipeline.py query "economic order quantity formula annual holding cost and ordering cost" --top-k 3

# Query Centralized vs. Regional vs. Hybrid architectures (Question 3)
python rag_pipeline.py query "centralized vs regional warehouse risk pooling hybrid architecture" --top-k 3
```

### Step 3: Run the Automated Test Suite
Executes 12 automated unit and integration tests verifying parsers, chunking, embeddings, ChromaDB, retrieval accuracy, page attribution, and guardrails:
```powershell
python test_rag.py
```

### Step 4: Execute the End-to-End Batch Workflow
Runs the complete multi-agent evaluation workflow across all student submissions in `Data/submissions/`:
```powershell
python workflow_orchestrator.py
```
To force a fresh re-indexing of reference materials before evaluating:
```powershell
python workflow_orchestrator.py --reindex
```

---

## 9. Benchmark Evaluation Results

The sample dataset represents three distinct academic scenarios:

| Student ID | Q1 (25) | Q2 (35) | Q3 (40) | Proposed Total | Confidence | Numerical Verifier | QC Status | Faculty Escalation | Reason / Scenario |
|---|---|---|---|---|---|---|---|---|---|
| **Student A** | 25 | 35 | 36 | **96/100** | **HIGH** | **PASS** | **PASS** | **NO** | High mastery; thorough definitions, exact math, strong Option B rationale. |
| **Student B** | 13 | 21 | 10 | **44/100** | **HIGH** | **FAIL** | **PASS** | **NO** | Arithmetic mistake ($\sqrt{500,000} \neq 500$); awarded carry-forward method credit; brief Q3 case. |
| **Student C** | 19 | 31 | 36 | **86/100** | **MEDIUM** | **PASS** | **PASS** | **YES** | Proposed an unlisted **Hybrid Network** in Q3. Escalated to faculty for academic judgment on creative synthesis. |

---

## 10. Limitations & Future Roadmap

1. **Handwritten Submissions**: Currently parses markdown and text submissions. Integrating an OCR pre-processing skill (e.g. via Tesseract or vision models) is planned for handwritten exam sheets.
2. **Formula OCR**: Complex LaTeX/handwritten mathematical expressions benefit from specialized mathematical AST parsers.
3. **Plagiarism & Collusion Detection**: Cross-submission vector similarity search across student cohorts to identify unoriginal work.
4. **Multi-Rubric Weighting**: Supporting section-level modular rubrics with dynamic penalty capping.