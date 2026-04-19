"""
app.py  ──  Gemma 4 Hardware Agent · HuggingFace Space
========================================================
ZeroGPU-compatible Gradio UI for the ESP32 / Arduino project assistant.
Requires: HF Pro account with ZeroGPU Space selected as hardware.
"""

import os
import re
import spaces          # HF ZeroGPU decorator
import gradio as gr
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from datetime import datetime

# ── Import project modules ──────────────────────────────────────────────────
from src.agent.agent_loop import SYSTEM_PROMPT
from src.tools.hardware_tools import HARDWARE_TOOLS
from src.utils.sketch_utils import (
    extract_arduino_sketch, clean_sketch,
    validate_sketch, extract_libraries, print_sketch_report
)

# ── Model config ─────────────────────────────────────────────────────────────
MODEL_ID       = "google/gemma-4-E4B-it"   # Change to E2B for faster cold starts
MAX_NEW_TOKENS = 2048

# ── Load model at startup (outside @spaces.GPU so it stays in CPU RAM) ───────
print(f"⏳ Loading tokenizer: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

print(f"⏳ Loading model (4-bit quant for H200 efficiency)...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
)
model.eval()
print("✅ Model ready!")


# ── Core inference — wrapped with @spaces.GPU for ZeroGPU ─────────────────────
@spaces.GPU(duration=120)   # Up to 120s of H200 per call
def generate_response(conversation: list[dict], user_message: str) -> tuple:
    """Run Gemma 4 inference on the Hardware Agent conversation."""

    # Build full message list: system + history + new user message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": user_message})

    inputs = tokenizer.apply_chat_template(
        messages,
        tools=HARDWARE_TOOLS,
        return_tensors="pt",
        add_generation_prompt=True,
        return_dict=True,
    ).to(model.device)

    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_ids = output_ids[0][input_len:]
    raw = tokenizer.decode(new_ids, skip_special_tokens=True)

    # Strip internal thinking tokens
    response = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Try to extract a sketch from the response
    sketch = extract_arduino_sketch(response)
    sketch_info = ""
    if sketch:
        sketch = clean_sketch(sketch)
        is_valid, warnings = validate_sketch(sketch)
        libs = extract_libraries(sketch)
        sketch_info = f"**✅ Sketch detected** ({len(sketch.splitlines())} lines)\n"
        if libs:
            sketch_info += f"**Libraries:** {', '.join(libs)}\n"
        if warnings:
            sketch_info += "\n".join(warnings)

    return response, sketch or "", sketch_info


# ── Gradio UI ─────────────────────────────────────────────────────────────────

DESCRIPTION = """
# 🤖 Gemma 4 — ESP32 & Arduino Hardware Project Agent
**Powered by Google Gemma 4 E4B · HuggingFace ZeroGPU (H200)**

Ask the agent to **generate code**, **list components**, **explain wiring**, **debug sketches**, or **suggest projects**.
Supported boards: ESP32, ESP8266, Arduino Uno/Nano/Mega
"""

EXAMPLES = [
    ["Generate a complete ESP32 weather station: DHT22 temperature/humidity sensor + SSD1306 OLED display + WiFi upload to ThingSpeak every 30 seconds. Include wiring summary."],
    ["Create an Arduino Nano sketch for an ultrasonic distance alarm using HC-SR04. Trigger a buzzer and rotate a servo to 90° when object is closer than 20cm."],
    ["Build an ESP32 MQTT smart home sensor node: BMP280 temp/humidity + PIR motion + LDR light. Publish to Home Assistant via WiFi. Include OTA update support."],
    ["Give me a Bill of Materials (BOM) for an ESP32 automated plant watering system with soil moisture sensor and relay-controlled water pump. Include prices in USD and INR."],
    ["Explain how to wire an MPU6050 accelerometer/gyroscope to an ESP32. Include I2C pin table, pull-up resistors, and the I2C address."],
    ["Suggest 5 beginner-friendly Arduino projects I can build with: ESP32, DHT22, OLED display, relay module, and NeoPixel LED strip."],
]

# Custom CSS — industrial/utilitarian dark theme with circuit-board accents
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

:root {
    --bg-primary: #0a0e17;
    --bg-card: #111827;
    --bg-input: #1a2332;
    --accent: #00d4aa;
    --accent-dim: #00a882;
    --accent-glow: rgba(0, 212, 170, 0.15);
    --warning: #f59e0b;
    --text-primary: #e2e8f0;
    --text-muted: #64748b;
    --border: #1e3a5f;
    --code-bg: #0d1117;
}

body, .gradio-container {
    background: var(--bg-primary) !important;
    font-family: 'Syne', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Header */
.prose h1 { 
    font-family: 'Syne', sans-serif !important; 
    font-weight: 800 !important;
    color: var(--accent) !important;
    font-size: 1.8rem !important;
    letter-spacing: -0.02em;
}
.prose p { color: var(--text-muted) !important; }

/* Chatbot */
.chatbot {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
.chatbot .message.user {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Syne', sans-serif !important;
}
.chatbot .message.bot {
    background: var(--bg-primary) !important;
    border: 1px solid var(--accent-dim) !important;
    border-left: 3px solid var(--accent) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}

/* Code blocks inside chat */
.chatbot code, .chatbot pre {
    background: var(--code-bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 6px !important;
}

/* Input box */
.input-row textarea {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Syne', sans-serif !important;
}
.input-row textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* Buttons */
button.primary {
    background: var(--accent) !important;
    color: #0a0e17 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
}
button.primary:hover { background: var(--accent-dim) !important; }
button.secondary {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
}

/* Sketch panel */
.sketch-box textarea {
    background: var(--code-bg) !important;
    border: 1px solid var(--accent-dim) !important;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
}

/* Tabs */
.tabs { border-bottom: 1px solid var(--border) !important; }
.tab-nav button { 
    color: var(--text-muted) !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
}
.tab-nav button.selected {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Accordion */
.accordion { 
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Labels */
label { color: var(--text-muted) !important; font-family: 'Syne', sans-serif !important; }

/* Examples */
.examples-table td {
    background: var(--bg-card) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
    font-size: 0.8rem !important;
}
.examples-table td:hover { 
    background: var(--accent-glow) !important;
    color: var(--text-primary) !important;
    cursor: pointer;
}
"""


def chat(user_message: str, history: list, conversation_state: list) -> tuple:
    """Main chat handler."""
    if not user_message.strip():
        return history, conversation_state, "", ""

    # Run inference
    response, sketch, sketch_info = generate_response(conversation_state, user_message)

    # Update history for Gradio chatbot display (messages format for Gradio 5)
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response},
    ]

    # Update conversation state for multi-turn context
    conversation_state = conversation_state + [
        {"role": "user",      "content": user_message},
        {"role": "assistant", "content": response},
    ]

    return history, conversation_state, sketch, sketch_info


def reset_chat():
    return [], [], "", "", ""


def download_sketch(sketch_text: str) -> str | None:
    """Save sketch to a temp file for download."""
    if not sketch_text.strip():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/tmp/sketch_{ts}.ino"
    with open(path, "w") as f:
        f.write(sketch_text)
    return path


# ── Build Gradio Blocks UI ────────────────────────────────────────────────────
with gr.Blocks(css=CUSTOM_CSS, title="Gemma 4 Hardware Agent") as demo:

    gr.Markdown(DESCRIPTION)

    conversation_state = gr.State([])   # Persistent multi-turn state

    with gr.Row():
        # ── Left column: chat ────────────────────────────────────────────────
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Hardware Agent",
                height=520,
                show_copy_button=True,
                render_markdown=True,
                type="messages",
                elem_classes=["chatbot"],
            )

            with gr.Row(elem_classes=["input-row"]):
                user_input = gr.Textbox(
                    placeholder="e.g. Generate an ESP32 WiFi weather station with DHT22 and OLED...",
                    lines=3,
                    label="Your Request",
                    show_label=False,
                    scale=5,
                )
                with gr.Column(scale=1, min_width=100):
                    submit_btn = gr.Button("⚡ Ask", variant="primary", size="lg")
                    reset_btn  = gr.Button("🔄 Reset", variant="secondary", size="sm")

            # Quick-select examples
            gr.Examples(
                examples=EXAMPLES,
                inputs=user_input,
                label="💡 Try an example",
            )

        # ── Right column: sketch panel ───────────────────────────────────────
        with gr.Column(scale=2):
            gr.Markdown("### 📟 Generated Sketch")

            sketch_info_box = gr.Markdown(
                value="_Sketch analysis will appear here..._",
                label="Analysis",
            )

            with gr.Tabs():
                with gr.TabItem("📝 Code"):
                    sketch_box = gr.Textbox(
                        label="Arduino Sketch (.ino)",
                        lines=22,
                        max_lines=40,
                        show_copy_button=True,
                        elem_classes=["sketch-box"],
                        interactive=True,
                        placeholder="// Generated sketch will appear here\n// Copy and paste into Arduino IDE",
                    )
                with gr.TabItem("💾 Download"):
                    gr.Markdown("Click to download the generated sketch as a `.ino` file.")
                    download_btn  = gr.Button("⬇️ Download .ino", variant="primary")
                    download_file = gr.File(label="Download", interactive=False)

            # Board quick-select chips (prepend to input)
            with gr.Accordion("🔧 Quick Board Select", open=False):
                gr.Markdown("Click a board to prepend it to your request:")
                with gr.Row():
                    for board in ["ESP32", "ESP8266", "Arduino Uno", "Arduino Nano", "Arduino Mega"]:
                        gr.Button(board, size="sm").click(
                            fn=lambda b=board: f"[Board: {b}] ",
                            outputs=user_input
                        )

    # ── Event wiring ──────────────────────────────────────────────────────────
    submit_btn.click(
        fn=chat,
        inputs=[user_input, chatbot, conversation_state],
        outputs=[chatbot, conversation_state, sketch_box, sketch_info_box],
    ).then(fn=lambda: "", outputs=user_input)   # Clear input after submit

    user_input.submit(
        fn=chat,
        inputs=[user_input, chatbot, conversation_state],
        outputs=[chatbot, conversation_state, sketch_box, sketch_info_box],
    ).then(fn=lambda: "", outputs=user_input)

    reset_btn.click(
        fn=reset_chat,
        outputs=[chatbot, conversation_state, sketch_box, sketch_info_box, user_input],
    )

    download_btn.click(
        fn=download_sketch,
        inputs=sketch_box,
        outputs=download_file,
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,    # Set True for a temporary public link during local dev
    )
