"""
agent/agent_loop.py
-------------------
Core agentic loop for the Gemma 4 Hardware Assistant.
Handles: system prompt construction, tool dispatch,
multi-turn conversation, and sketch file saving.
"""

import json
import os
import re
import torch
from datetime import datetime
from typing import Optional

# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert embedded systems engineer specializing in ESP32, \
ESP8266, and Arduino hardware projects. You have deep knowledge of:
- Arduino C++ programming (setup/loop paradigm, interrupts, timers)
- ESP32 WiFi, Bluetooth, BLE, MQTT, and OTA updates
- Common sensors: DHT11/22, BMP280, MPU6050, HC-SR04, PIR, MQ-series
- Displays: SSD1306 OLED, ST7735 TFT, LCD1602 I2C
- Actuators: servos, DC motors with L298N, stepper motors
- Communication: I2C, SPI, UART, OneWire, RS485
- IoT platforms: ThingSpeak, Blynk, Home Assistant, Node-RED

When generating code:
1. Always include all required #include statements
2. Define all pins as const int at the top
3. Add clear inline comments explaining each section
4. Handle errors gracefully (WiFi reconnect, sensor read failures)
5. Use non-blocking patterns (millis() instead of delay()) when possible
6. Include Serial.begin(115200) for debugging

When listing components, always include:
- Exact component model numbers
- Quantity needed
- Estimated price in USD and INR (for Indian makers)

Always think step-by-step before writing code to ensure correctness."""


# ─── Agent Class ──────────────────────────────────────────────────────────────

class HardwareAgent:
    """Gemma 4 powered agentic assistant for ESP32 / Arduino projects."""

    def __init__(self, model, tokenizer, tools: list,
                 max_new_tokens: int = 2048,
                 output_dir: str = "/content/output_sketches"):
        self.model = model
        self.tokenizer = tokenizer
        self.tools = tools
        self.max_new_tokens = max_new_tokens
        self.output_dir = output_dir
        self.conversation_history = []
        os.makedirs(output_dir, exist_ok=True)
        print(f"🤖 HardwareAgent initialised. Sketches → {output_dir}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def chat(self, user_message: str, verbose: bool = True) -> str:
        """Send a message and get a hardware-focused response."""
        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )
        response = self._generate()
        self.conversation_history.append(
            {"role": "assistant", "content": response}
        )
        if verbose:
            self._pretty_print(response)
        return response

    def reset(self):
        """Clear conversation history for a fresh project."""
        self.conversation_history = []
        print("🔄 Conversation reset.")

    def save_sketch(self, code: str, filename: Optional[str] = None) -> str:
        """Save an Arduino sketch to disk and return the file path."""
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sketch_{ts}.ino"
        if not filename.endswith(".ino"):
            filename += ".ino"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w") as f:
            f.write(code)
        print(f"💾 Sketch saved → {path}")
        return path

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _build_messages(self) -> list:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        return messages

    def _generate(self) -> str:
        messages = self._build_messages()
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tools=self.tools,
            return_tensors="pt",
            add_generation_prompt=True,
            return_dict=True,
        ).to(self.model.device)

        input_len = inputs["input_ids"].shape[-1]

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        new_ids = output_ids[0][input_len:]
        raw = self.tokenizer.decode(new_ids, skip_special_tokens=True)

        # Strip <think>...</think> blocks from final output (keep reasoning internal)
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        return raw

    @staticmethod
    def _pretty_print(text: str):
        print("\n" + "═" * 60)
        print("🤖 HARDWARE AGENT RESPONSE")
        print("═" * 60)

        # Highlight code blocks
        parts = re.split(r"(```[\w]*\n[\s\S]*?```)", text)
        for part in parts:
            if part.startswith("```"):
                lang_line = part.split("\n")[0].replace("```", "").strip()
                code = "\n".join(part.split("\n")[1:-1])
                print(f"\n[CODE — {lang_line.upper() or 'TEXT'}]")
                print("─" * 40)
                print(code)
                print("─" * 40)
            else:
                print(part)
        print("═" * 60 + "\n")

    # ── Convenience wrappers ───────────────────────────────────────────────────

    def generate_project(self, task: str, board: str = "esp32",
                         components: list = None,
                         communication: str = "none") -> str:
        """One-shot project generation."""
        components_str = ", ".join(components) if components else "no external components"
        prompt = (
            f"Generate a complete Arduino project:\n"
            f"Task: {task}\n"
            f"Board: {board}\n"
            f"Components: {components_str}\n"
            f"Communication: {communication}\n\n"
            f"Please provide:\n"
            f"1. Complete .ino sketch with comments\n"
            f"2. Required libraries (Arduino Library Manager names)\n"
            f"3. Wiring summary\n"
            f"4. Serial monitor expected output"
        )
        return self.chat(prompt)

    def debug_sketch(self, code: str, error: str = "") -> str:
        """Debug a broken sketch."""
        prompt = (
            f"Debug and fix this Arduino sketch:\n\n"
            f"```cpp\n{code}\n```\n"
        )
        if error:
            prompt += f"\nCompiler / Serial error:\n```\n{error}\n```"
        prompt += "\n\nProvide the corrected full sketch and explain what was wrong."
        return self.chat(prompt)

    def get_bom(self, project: str, board: str = "esp32") -> str:
        """Get bill of materials for a project."""
        prompt = (
            f"Create a detailed Bill of Materials (BOM) for this project:\n"
            f"Project: {project}\n"
            f"Board: {board}\n\n"
            f"Format as a table with: Component | Model | Qty | USD Price | INR Price | Buy From"
        )
        return self.chat(prompt)

    def explain_wiring(self, board: str, component: str) -> str:
        """Get wiring instructions for a component."""
        prompt = (
            f"Explain how to wire a {component} to an {board}.\n"
            f"Include:\n"
            f"- Pin connection table (board pin → component pin)\n"
            f"- I2C address or SPI settings if applicable\n"
            f"- Any pull-up/pull-down resistors needed\n"
            f"- Common mistakes to avoid"
        )
        return self.chat(prompt)

    def suggest_projects(self, skill_level: str = "intermediate",
                         components: list = None, interests: str = "") -> str:
        """Suggest project ideas based on skill and components."""
        comp_str = ", ".join(components) if components else "basic components"
        prompt = (
            f"Suggest 5 interesting hardware projects for a {skill_level} maker.\n"
            f"Available components: {comp_str}\n"
            f"Interests: {interests or 'general IoT and automation'}\n\n"
            f"For each project include:\n"
            f"- Project name & description\n"
            f"- Difficulty: ⭐ to ⭐⭐⭐⭐⭐\n"
            f"- Estimated build time\n"
            f"- Key learning outcomes"
        )
        return self.chat(prompt)
