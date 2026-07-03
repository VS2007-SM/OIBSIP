# Task 1 — BMI Calculator

**Oasis Infobyte Python Programming Internship (OIBSIP)**

## 📌 Overview
A command-line BMI (Body Mass Index) Calculator that accepts weight and height in **any common unit** (kg/lb for weight; m/cm/ft+in for height), automatically converts them to the standard units the BMI formula requires, calculates the BMI, and classifies the result into a health category.

## ✨ Features
- **Multi-unit input support**
  - Weight: kilograms (kg) or pounds (lb)
  - Height: meters (m), centimeters (cm), or feet & inches (ft/in)
- Automatic conversion to standard BMI units (kg, m) before calculation
- Input validation — rejects non-numeric and non-positive values, re-prompts until valid
- BMI classification into WHO-standard categories:
  - Underweight (< 18.5)
  - Normal weight (18.5 – 24.9)
  - Overweight (25 – 29.9)
  - Obese (≥ 30)
- Repeat-calculation loop — calculate multiple BMIs in one session without restarting
- Clear, formatted result display showing both the entered value and converted standard value

## 🛠️ Tech Stack
- Python 3 (standard library only — no external dependencies)

## 🚀 How to Run
```bash
python bmi_calculator.py
```
Follow the on-screen prompts to select your weight unit, enter weight, select your height unit, and enter height. The program will display your BMI and category.

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
  Category            : Normal weight
--------------------------------------------------
```

## 🧠 Key Concepts Demonstrated
- Function decomposition and single-responsibility design
- Unit conversion logic
- Robust input validation with retry loops
- Type hints for readability

## 📹 Demo
[Link to demo video / LinkedIn post — add after recording]

---
*Part of the [OIBSIP](../) repository — Oasis Infobyte Python Programming Internship.*
