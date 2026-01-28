# Aegis Recon - Improvement Plan

## 1. AI API Polish (Analysis Engine)

The current "AI" components rely on deterministic tools (Sublist3r, Nikto, etc.). To "polish" this into a true AI-powered Recon tool, we will integrate a Large Language Model (LLM) to analyze the raw output and generate human-readable Threat Reports.

### Recommended "Best Free" Solution (Non-Gemini)

**Groq API (Llama 3 70B / Mixtral 8x7b)**

- **Why**: Currently offers a generous free tier with extremely fast inference speeds. Llama 3 70B competes with GPT-4 class models.
- **Alternative**: **Hugging Face Inference API** (access to various open models).

### Implementation Strategy

1. **Aggregator**: Create a Python service that collects JSON outputs from `scan_worker_enhanced.py`.
2. **Prompt Engineering**: Feed the raw vulnerabilities and OSINT data into the LLM with a system prompt like:
   _"You are a Senior Cybersecurity Analyst. Analyze the following scan results for target {target}. Prioritize vulnerabilities by risk, explain impact, and suggest remediation."_
3. **Integration**: Expose this analysis via a new endpoint `/api.php?action=analysis&job_id={id}`.

## 2. Professional Development & Architecture

To move from a "script-based" project to a professional application:

### A. Dockerization (Containerization)

Stop relying on local XAMPP. Create a `docker-compose.yml` stack:

- **App**: PHP 8.2 + Apache
- **Worker**: Python 3.10 image with security tools pre-installed (nmap, nikto, etc.)
- **Database**: MariaDB/MySQL container
- **Cache**: Redis container (for queue management)

### B. Testing Frameworks

- **Backend (PHP)**: Implement **PHPUnit** for API endpoint testing.
- **Worker (Python)**: Implement **PyTest** for the parser and scan logic.
- **CI/CD**: specific GitHub Actions to run these tests on every push.

### C. Code Quality

- Add **Linters**: `flake8` for Python, `phpcs` for PHP.
- **Type Hinting**: Enforce strict types in Python and PHP for reliability.

## 3. "Let Out" Features (Release Strategy) version 1.0.0

To professionally release features:

1. **Semantic Versioning**: Adopt `v1.0.0` tagging.
2. **Changelog**: Maintain a `CHANGELOG.md`.
3. **GitHub Actions**:
   - Auto-create Releases on tag push.
   - Build a Docker image and push to GitHub Container Registry (optional).

## 4. Security & Credentials

**Goal**: Zero secrets in source code.

- **Action**: All credentials (DB, API Keys) must be in `.env`.
- **Validation**: Add a pre-commit hook or CI check to scan for committed secrets (using tools like `trufflehog` or `git-secrets`).
