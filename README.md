# Aegis Recon - Intelligent Security Scanner

Aegis Recon is an advanced vulnerability scanner and OSINT gathering tool, combining powerful open-source security tools with an automated queuing system.

## 🚀 Features

- **Subdomain Enumeration**: Integrated `Sublist3r` for finding subdomains.
- **OSINT Gathering**: Uses `theHarvester` to find emails, IPs, and associated URLs.
- **Port Scanning**: `Nmap` integration for service discovery.
- **Tech Stack Detection**: `WhatWeb` fingerprinting.
- **Vulnerability Scanning**: `Nikto` integration for web server flaws.
- **Queue System**: Redis-backed job queue for handling concurrent scans.

## 🛠️ Setup & Installation

### Prerequisites

- PHP 8.0+
- Python 3.8+
- MySQL/MariaDB
- Redis (optional, for queueing)

### Configuration

1. **Clone the repository**:

   ```bash
   git clone https://github.com/vex-bit/Aegis-Recon.git
   cd Aegis-Recon
   ```

2. **Environment Setup**:
   Copy the example environment file and configure your credentials.

   ```bash
   cp .env.example .env
   ```

   **IMPORTANT**: Edit `.env` to set your Database credentials and API keys. **Never commit `.env` to version control.**

3. **Install Dependencies**:
   - Python:
     ```bash
     pip install -r ai_services/requirements.txt
     ```
   - Database:
     Run `backend/init_database.php` to create the schema.

## 🔒 Security Note

This project contains sensitive configurations in `.env`. The `.gitignore` file is configured to exclude this file.
When deploying, ensure your web server blocks access to `.env` and `.git` directories.

## 🤖 Future Roadmap

See [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) for details on:

- AI Integration (LLM-based Threat Analysis)
- Docker Swarm Support
- CI/CD Pipelines

## 📄 License

Private / Proprietary.
