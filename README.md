---
title: Sellica Cargo Bot
emoji: 🤖
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# 🚀 Sellica AI - Classic Cargo Edition

This Space runs the **Sellica Search Engine**, an industrial-grade RAG bot using **Gemini 768-D Embeddings** and **Groq LLM**.

## 🛡️ Production Features (2026)
* **Engine:** Gemini-embedding-001 (768-D Matryoshka)
* **Logic:** Vector similarity with confidence scoring.
* **Janitor:** Automatic temp-vault cleanup every 15 mins.
* **Infrastructure:** Dockerized background service with ghost-port health checks.

## ⚙️ Deployment Instructions

1.  **Secrets:** You MUST add these in the Space **Settings > Variables and Secrets**:
    * `TELEGRAM_TOKEN`: Your bot API key from @BotFather.
    * `GOOGLE_API_KEY`: Your Gemini API key.
    * `GITHUB_TOKEN`: To pull shop data from your private repo.

2.  **Keep Alive:** To prevent this Space from "sleeping" after 48 hours:
    * Set up a ping at [cron-job.org](https://cron-job.org) targeting:
    `https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space`

---
*Maintained by the Iron Guard Logic.*