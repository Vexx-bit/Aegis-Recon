# 🛡️ Aegis Recon

**Advanced Threat Intelligence & Reconnaissance Platform**

A modern, serverless security reconnaissance tool built for Vercel deployment. Performs subdomain enumeration, port scanning, technology fingerprinting, and OSINT gathering with AI-powered threat analysis.

## ✨ Features

- **Subdomain Discovery** - Certificate Transparency logs via crt.sh
- **Port Scanning** - Fast TCP port detection on common services
- **Technology Fingerprinting** - Detect web servers, frameworks, and CMS platforms
- **Email Harvesting** - Extract exposed email addresses
- **IP Geolocation** - Location data via IPInfo
- **AI Threat Reports** - GROQ-powered security analysis

## 🚀 Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Vexx-bit/Aegis-Recon)

### Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable          | Required | Description                     |
| ----------------- | -------- | ------------------------------- |
| `GROQ_API_KEY`    | ✅       | GROQ API key for AI analysis    |
| `IPINFO_TOKEN`    | Optional | IPInfo.io token for geolocation |
| `GOOGLE_SAFE_KEY` | Optional | Google Safe Browsing API key    |

## 🏗️ Architecture

```
/
├── api/                    # Python serverless functions
│   ├── scan.py            # Main reconnaissance endpoint
│   ├── analyze.py         # GROQ AI analysis endpoint
│   └── requirements.txt   # Python dependencies
├── frontend/              # Static web files
│   ├── index.html         # Dashboard UI
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript
└── vercel.json            # Vercel deployment config
```

## 🔧 Local Development

1. Clone the repository:

   ```bash
   git clone https://github.com/Vexx-bit/Aegis-Recon.git
   cd Aegis-Recon
   ```

2. Install Vercel CLI:

   ```bash
   npm i -g vercel
   ```

3. Set up environment:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Run locally:
   ```bash
   vercel dev
   ```

## 📡 API Endpoints

### POST /api/scan

Perform reconnaissance on a target domain.

```json
{
  "domain": "example.com"
}
```

### POST /api/analyze

Generate AI threat analysis from scan results.

```json
{
  "results": { ... scan results ... }
}
```

## ⚠️ Legal Disclaimer

This tool is intended for **authorized security testing only**. Always obtain proper permission before scanning any systems. The developers are not responsible for misuse.

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ by [Vexx-bit](https://github.com/Vexx-bit)
