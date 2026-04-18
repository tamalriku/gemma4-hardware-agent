# 🚀 Deployment Guide — Gemma 4 Hardware Agent

## Overview

```
Local Files
    │
    ├──▶ GitHub (source of truth, version control)
    │         │
    │         └──▶ GitHub Actions (auto-sync on every push)
    │                       │
    │                       └──▶ HuggingFace Space (live demo, ZeroGPU H200)
```

---

## PART 1 — Push to GitHub

### Step 1.1 — Create a GitHub repository

1. Go to https://github.com/new
2. Repository name: `gemma4-hardware-agent`
3. Description: `ESP32 & Arduino project agent powered by Google Gemma 4`
4. Set to **Public** (required to link with HF Spaces for free)
5. **Do NOT** initialise with a README — you have your own
6. Click **Create repository**

### Step 1.2 — Initialise Git locally

Unzip the provided `gemma4-hardware-agent-deploy.zip`, then:

```bash
cd gemma4-hardware-agent-deploy

# Initialise git
git init
git branch -M main

# Stage everything
git add .
git commit -m "feat: initial Gemma 4 Hardware Agent with ZeroGPU Gradio app"

# Link to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/gemma4-hardware-agent.git

# Push
git push -u origin main
```

### Step 1.3 — Verify on GitHub

Your repo at `github.com/YOUR_USERNAME/gemma4-hardware-agent` should show:
```
gemma4-hardware-agent/
├── .github/workflows/sync_to_hf.yml   ← Auto-deploy CI
├── src/
│   ├── agent/agent_loop.py
│   ├── tools/hardware_tools.py
│   └── utils/sketch_utils.py
├── examples/esp32_weather_station.ino
├── app.py                              ← HF Space entry point
├── requirements.txt
├── README.md                           ← HF Space card (YAML frontmatter)
└── .gitignore
```

---

## PART 2 — Deploy to HuggingFace Spaces (ZeroGPU)

### Step 2.1 — Accept the Gemma 4 model license

Go to: https://huggingface.co/google/gemma-4-E4B-it  
Click **"Agree and access repository"** — required once per account.

### Step 2.2 — Create a new Space

1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Owner:** your HF username
   - **Space name:** `gemma4-hardware-agent`
   - **License:** Apache 2.0
   - **SDK:** `Gradio` ← important
   - **Hardware:** `ZeroGPU` ← requires your PRO subscription
   - **Visibility:** Public (or Private for personal use)
3. Click **Create Space**

> ✅ ZeroGPU gives you NVIDIA H200 GPUs, allocated on-demand.  
> Your PRO subscription gives you 8× quota + highest queue priority.

### Step 2.3 — Add your HF token as a Space Secret

In your Space settings (`Settings → Repository secrets`):

| Secret Name | Value |
|---|---|
| `HF_TOKEN` | Your HuggingFace token (from https://huggingface.co/settings/tokens) |

> The app needs this at runtime to download the Gemma 4 model weights.  
> **Never hardcode tokens in code.**

### Step 2.4 — Push files to HF Space via Git

HuggingFace Spaces are Git repositories. Push directly:

```bash
# Add HF Space as a second remote
git remote add space https://YOUR_HF_USERNAME:YOUR_HF_TOKEN@huggingface.co/spaces/YOUR_HF_USERNAME/gemma4-hardware-agent

# Push to Space
git push space main
```

Your Space will automatically:
1. Detect `app.py` as the entry point
2. Install packages from `requirements.txt`
3. Start building (takes ~3-5 min on first deploy)

### Step 2.5 — Watch the build logs

In your Space, click the **Logs** tab to see:
```
⏳ Loading tokenizer: google/gemma-4-E4B-it
⏳ Loading model (4-bit quant for H200 efficiency)...
✅ Model ready!
Running on http://0.0.0.0:7860
```

Your live URL will be:
```
https://huggingface.co/spaces/YOUR_USERNAME/gemma4-hardware-agent
```

---

## PART 3 — Auto-Deploy with GitHub Actions (CI/CD)

After Part 1 and Part 2 are both done, wire them together so every GitHub push auto-deploys to HF.

### Step 3.1 — Add GitHub Secrets

In your GitHub repo: `Settings → Secrets and variables → Actions → New repository secret`

| Secret Name | Value |
|---|---|
| `HF_TOKEN` | Your HuggingFace token |
| `HF_USERNAME` | Your HuggingFace username |
| `HF_SPACE_NAME` | `gemma4-hardware-agent` |

### Step 3.2 — The workflow is already included

The file `.github/workflows/sync_to_hf.yml` in your repo handles everything:
- Triggers on every push to `main`
- Can also be triggered manually from the GitHub Actions tab

### Step 3.3 — Test the pipeline

```bash
# Make a small change
echo "# Updated" >> README.md
git add README.md
git commit -m "test: trigger CI sync"
git push origin main
```

Then go to `github.com/YOUR_USERNAME/gemma4-hardware-agent/actions` — you should see the workflow run and sync to HF within ~30 seconds.

---

## PART 4 — Using the Live Demo

Once deployed, your Space URL is shareable with anyone.

### What users see:

```
┌─────────────────────────────────────────────────────┐
│  🤖 Gemma 4 — ESP32 & Arduino Hardware Agent        │
├───────────────────────────────┬─────────────────────┤
│  💬 Chat                      │  📟 Generated Sketch │
│                               │                     │
│  [Chat history here]          │  [Code tab]         │
│                               │  [Download tab]     │
│  [Your request...]  [⚡ Ask]  │                     │
│  [🔄 Reset]                   │  Board selector     │
│                               │                     │
│  💡 Try an example:           │                     │
│  [ESP32 weather...]           │                     │
│  [Arduino alarm...]           │                     │
└───────────────────────────────┴─────────────────────┘
```

### Features:
- **Multi-turn chat** — the agent remembers context across the conversation
- **Auto sketch extraction** — any `.ino` code appears in the right panel instantly
- **Sketch analysis** — shows line count, libraries needed, validation warnings
- **Download button** — saves the sketch as a `.ino` file directly
- **Reset** — clears conversation for a fresh project

---

## PART 5 — Showcase Tips

For presenting as a prototype:

1. **Demo script:** Show these 3 scenarios back-to-back:
   - *"Generate a complete ESP32 weather station"* → full code in seconds
   - *"Explain how to wire the MPU6050"* → pin table + I2C details
   - *"Debug this broken sketch [paste code]"* → fixed code instantly

2. **Point out ZeroGPU:** Mention the H200 GPU allocates on-demand (users don't pay for idle time)

3. **Show the download:** Download the `.ino`, open Arduino IDE, paste it in — that's the full workflow

4. **GitHub link:** Show the clean repo — the CI/CD auto-deploy makes it look very professional

---

## Quick Reference

| Action | Command |
|---|---|
| First push to GitHub | `git push -u origin main` |
| Push to HF Space directly | `git push space main` |
| Trigger CI manually | GitHub → Actions → Run workflow |
| View Space logs | HF Space → Logs tab |
| Restart Space | HF Space → Settings → Restart |
| Change model size | Edit `MODEL_ID` in `app.py`, push |
