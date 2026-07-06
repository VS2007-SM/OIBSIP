<div align="center">

# 🧮 Task 1 — BMI Calculator

**Oasis Infobyte Python Programming Internship (OIBSIP)**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Level](https://img.shields.io/badge/Level-Beginner-brightgreen?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)

[Features](#-features) • [Setup](#-how-to-run) • [Example](#-example-run) • [Concepts](#-key-concepts-demonstrated)

</div>

---

## 📌 Overview

A command-line BMI (Body Mass Index) Calculator that accepts weight and height in **any common unit** — not just kg and meters. It automatically converts whatever unit you enter into the standard units the BMI formula requires, calculates the result, and classifies it into a WHO-standard health category.

## ✨ Features

| Feature | Description |
|---|---|
| ⚖️ **Multi-unit weight input** | Kilograms (kg) or pounds (lb) |
| 📏 **Multi-unit height input** | Meters (m), centimeters (cm), or feet & inches (ft/in) |
| 🔄 **Automatic conversion** | Converts any entered unit to standard kg/m before calculating — transparently shows both the original and converted value |
| 🛡️ **Input validation** | Rejects non-numeric and non-positive values, re-prompting until valid |
| 🏷️ **WHO-standard classification** | Underweight / Normal weight / Overweight / Obese |
| 🔁 **Repeat-calculation loop** | Calculate multiple BMIs in one session without restarting the program |

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

Python 3 (standard library only). No external dependencies.

## 🚀 How to Run
```bash
python bmi_calculator.py
```
Follow the prompts: choose your weight unit, enter weight, choose your height unit, enter height. The program displays your BMI and category.

## 📂 Example Run
```
Weight unit:
  1) Kilograms (kg)
  2) Pounds (lb)
Choose 1 or 2: 2
Enter your weight (lb): 155

Height unit:
  1) Meters (m)
  2) Centimeters (cm)
  3) Feet & inches (ft, in)
Choose 1, 2 or 3: 3
Enter feet (e.g. 5): 5
Enter inches (e.g. 8): 8

--------------------------------------------------
  Weight (as entered) : 155.0 lb  (= 70.31 kg)
  Height (as entered) : 5 ft 8 in  (= 1.73 m)
  BMI                 : 23.57
  Category             : Normal weight
--------------------------------------------------
```

## 🧠 Key Concepts Demonstrated

- 🔄 **Unit conversion logic** — real-world conversion factors (`1 lb = 0.45359237 kg`, `1 ft = 0.3048 m`, `1 in = 0.0254 m`), applied before any calculation happens
- 🛡️ **Robust input validation** — handles non-numeric input, non-positive values, and invalid menu selections, all with retry loops rather than crashing
- 🧩 **Function decomposition** — each responsibility (getting weight, getting height, calculating, classifying, displaying) lives in its own function
- 🏷️ **Standards-based classification** — BMI categories follow the WHO scale exactly, not arbitrary thresholds
- 🔍 **Transparency over black-box conversion** — the result screen always shows both what was typed and the converted standard value, so the conversion is never hidden from the user

## 📹 Demo
[Link to demo video / LinkedIn post — add after recording]

---
<div align="center">

Part of the **[OIBSIP](../)** repository — Oasis Infobyte Python Programming Internship

</div>
