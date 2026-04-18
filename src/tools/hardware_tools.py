"""
tools/hardware_tools.py
-----------------------
Tool definitions for the Gemma 4 Hardware Agent.
These are passed as structured function-call specs to the model,
and dispatched by the agent loop in agent/agent_loop.py.
"""

# ─── Tool Schemas (passed to Gemma 4 chat template) ──────────────────────────

HARDWARE_TOOLS = [
    {
        "name": "generate_arduino_code",
        "description": (
            "Generate a complete, ready-to-upload Arduino sketch (.ino) "
            "for the described hardware task. Always includes library imports, "
            "pin definitions, setup(), and loop() with inline comments."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Plain-English description of what the hardware should do."
                },
                "board": {
                    "type": "string",
                    "enum": ["esp32", "esp32s3", "esp8266", "arduino_uno",
                             "arduino_nano", "arduino_mega"],
                    "description": "Target microcontroller board."
                },
                "components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of hardware components to use, "
                        "e.g. ['DHT22', 'SSD1306 OLED', 'servo SG90']"
                    )
                },
                "communication": {
                    "type": "string",
                    "enum": ["none", "wifi", "bluetooth", "mqtt", "serial", "lora"],
                    "description": "Wireless / communication protocol to include."
                },
                "libraries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific Arduino libraries to use (optional)."
                }
            },
            "required": ["task", "board"]
        }
    },
    {
        "name": "list_components",
        "description": (
            "Return a bill of materials (BOM) — every component, module, and wire "
            "needed for the project — with quantity, typical price (USD), and "
            "where to buy (e.g. Amazon, Robu.in, AliExpress)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project description."
                },
                "board": {
                    "type": "string",
                    "description": "Microcontroller board."
                }
            },
            "required": ["project"]
        }
    },
    {
        "name": "explain_pinout",
        "description": (
            "Explain how to wire a specific component to the ESP32 or Arduino. "
            "Returns a pin table (board pin → component pin), wiring notes, "
            "and any I2C/SPI address information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "board": {
                    "type": "string",
                    "description": "Microcontroller board name."
                },
                "component": {
                    "type": "string",
                    "description": "Component name, e.g. 'DHT22', 'SSD1306', 'HC-SR04'."
                }
            },
            "required": ["board", "component"]
        }
    },
    {
        "name": "debug_code",
        "description": (
            "Identify and fix bugs in an Arduino/ESP32 sketch. "
            "Returns the corrected code with a diff-style summary of changes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The full broken Arduino sketch."
                },
                "error_message": {
                    "type": "string",
                    "description": "Compiler or serial monitor error message (optional)."
                },
                "board": {
                    "type": "string",
                    "description": "Target board (helps resolve board-specific issues)."
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "generate_wiring_diagram_description",
        "description": (
            "Produce a detailed textual wiring diagram — useful when you cannot "
            "render an image. Describes every wire connection step-by-step and "
            "includes a Fritzing-style summary table."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "board": {"type": "string"},
                "components": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["board", "components"]
        }
    },
    {
        "name": "suggest_project",
        "description": (
            "Given a skill level and available components, suggest 3–5 interesting "
            "hardware project ideas with difficulty rating and estimated build time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "skill_level": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"]
                },
                "components_available": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Components you already own."
                },
                "interests": {
                    "type": "string",
                    "description": "e.g. 'IoT, home automation, robotics, sensors'"
                }
            },
            "required": ["skill_level"]
        }
    }
]
