---
title: Gemma 4 Hardware Agent
emoji: 🤖
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: true
license: apache-2.0
short_description: ESP32 & Arduino project agent powered by Gemma 4 + ZeroGPU
hardware: zero-a10g
suggested_hardware: zero-a10g
tags:
  - gemma
  - arduino
  - esp32
  - hardware
  - agent
  - code-generation
  - gradio
---

# 🤖 Gemma 4 — ESP32 & Arduino Hardware Project Agent

An agentic hardware assistant built on **Google Gemma 4 E4B-it**, running on **HuggingFace ZeroGPU (H200)**.

Describe what you want your ESP32 or Arduino to do, and the agent will:
- 📝 Generate a complete, ready-to-upload `.ino` sketch
- 🛒 List all components with pricing (USD + INR)
- 🔌 Explain wiring and pin connections
- 🐛 Debug broken sketches
- 💡 Suggest project ideas

## Supported Boards
ESP32 · ESP8266 · Arduino Uno · Arduino Nano · Arduino Mega

## How to Use
1. Type your hardware project request in the chat box
2. Hit **⚡ Ask** or press Enter
3. The agent responds with code, wiring info, and component lists
4. Copy the generated sketch directly from the **Code** tab
5. Download as a `.ino` file from the **Download** tab

## Example Prompts
- *"Generate an ESP32 weather station with DHT22 and OLED that uploads to ThingSpeak"*
- *"Create an Arduino Nano distance alarm with HC-SR04 and a buzzer"*
- *"Build an ESP32 MQTT smart home sensor for Home Assistant"*
- *"Give me a Bill of Materials for an automated plant watering system"*

## Architecture
```
User prompt
    │
    ▼
Gemma 4 E4B-it (ZeroGPU H200, 4-bit)
    │  ← Thinking mode: step-by-step hardware reasoning
    ▼
6 Hardware Tools (function calling)
    ├── generate_arduino_code
    ├── list_components (BOM with USD+INR)
    ├── explain_pinout
    ├── debug_code
    ├── generate_wiring_diagram_description
    └── suggest_project
    │
    ▼
Response + Auto-extracted .ino sketch
```

## Model
- **Base:** `google/gemma-4-E4B-it`
- **Quantization:** 4-bit NF4 (bitsandbytes)
- **Hardware:** HuggingFace ZeroGPU (NVIDIA H200, 40GB VRAM)
- **Context:** 128K tokens

## License
Apache 2.0
