# 🚀 SEO MCP Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard-orange.svg)](https://modelcontextprotocol.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

An open-source **Model Context Protocol (MCP)** server that equips AI assistants (Claude, Cursor, custom agents) with actionable, data-driven SEO capabilities.

Stop relying on generic AI advice. **`seo-mcp-skills`** enables LLM agents to execute deterministic technical audits, extract real-time SERP insights, analyze page semantics, and run programmatic SEO workflows directly inside your development ecosystem.

---

## 🔥 Key Capabilities

* **Technical SEO Audits:** Extract and analyze canonicals, structured data (JSON-LD), status codes, heading hierarchy, and meta tag integrity.
* **SERP & Keyword Intent Analysis:** Connect AI agents to real SERP data to evaluate search intent, content gaps, and keyword difficulty metrics.
* **On-Page & Semantic Evaluation:** Measure term frequency, TF-IDF weights, heading relevance, and internal linking structures.
* **Programmatic SEO Tooling:** Generate data-backed metadata templates, schema markup, and sitemap validation rules dynamically.

---

## 🛠️ Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/ireunlocker/seo-mcp-skills.git
cd seo-mcp-skills
npm install # or pip install -e .
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Run the Server

```bash
# Using npm (if configured)
npm start

# Or using Python directly
python -m src.server
```

---

## 📋 Available Skills

| Skill | Description |
|-------|-------------|
| **Technical Audit** | Analyze canonicals, structured data, headings, meta tags |
| **SERP Analysis** | Keyword intent, content gaps, difficulty metrics |
| **Semantic Analysis** | TF-IDF, term frequency, heading relevance |
| **Programmatic SEO** | Metadata templates, schema markup, sitemap rules |

---

## 🔧 Configuration

Required environment variables (see `.env.example`):

```env
# AI Provider (choose one)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# SEO Data Sources
SERP_API_KEY=your_serp_api_key
GOOGLE_SEARCH_CONSOLE_CREDENTIALS=path/to/credentials.json
```

---

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Skill Development Guide](docs/SKILL_DEVELOPMENT.md)
- [API Reference](docs/API.md)

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- Open-source SEO community