"""
utils/sketch_utils.py
---------------------
Utilities for extracting, cleaning, and saving Arduino sketches
from Gemma 4 model responses.
"""

import re
import os
from datetime import datetime
from typing import Optional, Tuple


def extract_code_blocks(text: str) -> list[dict]:
    """
    Extract all code blocks from a markdown-formatted LLM response.

    Returns a list of dicts: [{'lang': 'cpp', 'code': '...'}, ...]
    """
    pattern = r"```(\w*)\n([\s\S]*?)```"
    matches = re.findall(pattern, text)
    blocks = []
    for lang, code in matches:
        lang = lang.strip().lower()
        # Normalise language aliases
        if lang in ("c++", "c", "ino", "arduino"):
            lang = "cpp"
        blocks.append({"lang": lang or "text", "code": code.strip()})
    return blocks


def extract_arduino_sketch(response: str) -> Optional[str]:
    """
    Extract the primary Arduino sketch from an LLM response.
    Returns the largest cpp/ino code block, or None if not found.
    """
    blocks = extract_code_blocks(response)
    cpp_blocks = [b["code"] for b in blocks if b["lang"] in ("cpp", "ino", "text")]

    if not cpp_blocks:
        return None

    # Return the longest block (most likely the complete sketch)
    return max(cpp_blocks, key=len)


def clean_sketch(sketch: str) -> str:
    """
    Clean common LLM artefacts from generated sketches:
    - Remove markdown bold/italic inside comments
    - Normalise line endings
    - Remove leading/trailing whitespace
    """
    # Normalise line endings
    sketch = sketch.replace("\r\n", "\n").replace("\r", "\n")

    # Remove markdown bold (**text**) inside comments
    sketch = re.sub(r"\*\*(.*?)\*\*", r"\1", sketch)

    # Remove markdown italic (*text*) inside comments
    sketch = re.sub(r"\*(.*?)\*", r"\1", sketch)

    # Ensure sketch ends with a newline
    sketch = sketch.strip() + "\n"

    return sketch


def validate_sketch(sketch: str) -> Tuple[bool, list[str]]:
    """
    Perform basic structural validation of an Arduino sketch.

    Returns (is_valid: bool, warnings: list[str])
    """
    warnings = []

    if "void setup()" not in sketch:
        warnings.append("⚠️  Missing void setup() — required by Arduino framework")

    if "void loop()" not in sketch:
        warnings.append("⚠️  Missing void loop() — required by Arduino framework")

    if "#include" not in sketch and any(
        kw in sketch for kw in ["WiFi", "DHT", "Wire", "SPI", "Servo"]
    ):
        warnings.append("⚠️  No #include statements but library keywords detected — may be missing imports")

    if "delay(" in sketch:
        count = sketch.count("delay(")
        if count > 3:
            warnings.append(
                f"💡 Tip: {count} delay() calls found — consider using millis() for non-blocking code"
            )

    is_valid = not any("Missing" in w for w in warnings)
    return is_valid, warnings


def save_sketch(sketch: str, output_dir: str,
                filename: Optional[str] = None,
                project_name: Optional[str] = None) -> str:
    """
    Save a sketch to disk. Creates a subfolder per project if project_name is given.
    Returns the full file path.
    """
    os.makedirs(output_dir, exist_ok=True)

    if project_name:
        # Sanitise project name for filesystem
        safe_name = re.sub(r"[^\w\-]", "_", project_name).strip("_")
        output_dir = os.path.join(output_dir, safe_name)
        os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sketch_name = project_name or "sketch"
        safe = re.sub(r"[^\w]", "_", sketch_name)[:30]
        filename = f"{safe}_{ts}.ino"

    if not filename.endswith(".ino"):
        filename += ".ino"

    path = os.path.join(output_dir, filename)
    with open(path, "w") as f:
        f.write(sketch)

    print(f"💾 Sketch saved → {path}")
    return path


def extract_libraries(sketch: str) -> list[str]:
    """
    Parse #include statements from a sketch and return library names
    suitable for the Arduino Library Manager.
    """
    includes = re.findall(r'#include\s+[<"]([\w./]+)[>"]', sketch)
    # Filter out standard Arduino headers
    standard = {"Arduino.h", "avr/pgmspace.h", "math.h", "string.h",
                 "stdlib.h", "stdio.h", "stdint.h"}
    external = [lib.split(".h")[0] for lib in includes if lib not in standard]
    return list(dict.fromkeys(external))  # Deduplicate, preserve order


def extract_bom_table(response: str) -> Optional[str]:
    """
    Extract a markdown table from the response (usually the BOM).
    Returns the raw markdown table string or None.
    """
    lines = response.split("\n")
    table_lines = []
    in_table = False

    for line in lines:
        if re.match(r"^\s*\|", line):
            in_table = True
            table_lines.append(line)
        elif in_table:
            break  # Stop at first non-table line after table started

    return "\n".join(table_lines) if table_lines else None


def print_sketch_report(response: str):
    """
    Parse an agent response and print a structured report:
    sketch validity, detected libraries, and any warnings.
    """
    sketch = extract_arduino_sketch(response)

    print("\n" + "─" * 50)
    print("📋 SKETCH ANALYSIS REPORT")
    print("─" * 50)

    if not sketch:
        print("❌ No Arduino sketch found in response.")
        return

    cleaned = clean_sketch(sketch)
    is_valid, warnings = validate_sketch(cleaned)
    libs = extract_libraries(cleaned)

    status = "✅ Valid" if is_valid else "❌ Issues found"
    print(f"Status    : {status}")
    print(f"Lines     : {len(cleaned.splitlines())}")
    print(f"Characters: {len(cleaned)}")

    if libs:
        print(f"\n📦 Libraries to install (Arduino Library Manager):")
        for lib in libs:
            print(f"   • {lib}")

    if warnings:
        print(f"\n⚠️  Warnings:")
        for w in warnings:
            print(f"   {w}")

    print("─" * 50)
