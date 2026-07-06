<div align="center">

# 🔐 Task 2 — Random Password Generator

**Oasis Infobyte Python Programming Internship (OIBSIP)**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Level](https://img.shields.io/badge/Level-Medium-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Security](https://img.shields.io/badge/Randomness-secrets%20module-critical?style=for-the-badge&logo=python&logoColor=white)

[Features](#-features) • [Setup](#-how-to-run) • [Example](#-example-run) • [Concepts](#-key-concepts-demonstrated)

</div>

---

## 📌 Overview
A command-line password generator that creates strong, random passwords based on user-defined criteria — length, character types, and ambiguous-character exclusion. Built with security as a first-class concern: it uses Python's `secrets` module rather than `random`, and guarantees every selected character type actually appears in the output.

## ✨ Features

| Feature | Description |
|---|---|
| 📏 **Custom length** | Anywhere from 4 to 128 characters |
| 🔤 **Selectable character types** | Lowercase, uppercase, digits, symbols — mix and match |
| ✅ **Guaranteed coverage** | Every selected type is guaranteed to appear at least once — not left to chance |
| 👓 **Ambiguous character exclusion** | Optional — strips visually confusing characters like `l`, `1`, `I`, `O`, `0` |
| 🔢 **Batch generation** | Generate 1–20 passwords in a single run |
| 💪 **Strength estimation** | Rates each password Weak / Medium / Strong / Very Strong |
| 🔒 **Cryptographically secure** | Uses `secrets`, not `random`, for all character selection and shuffling |

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![secrets](https://img.shields.io/badge/secrets-standard%20library-2b2b2b?style=flat-square)
![string](https://img.shields.io/badge/string-standard%20library-2b2b2b?style=flat-square)

Python 3 (standard library only — `secrets`, `string`). No external dependencies.

## 🚀 How to Run
```bash
python password_generator.py
```
Follow the prompts to set password length, choose which character types to include, optionally exclude ambiguous characters, and specify how many passwords to generate.

## 📂 Example Run
```
Password length (4-128): 14

Select character types to include:
  Include lowercase letters (a-z)? (Y/n): y
  Include uppercase letters (A-Z)? (Y/n): y
  Include digits (0-9)? (Y/n): y
  Include symbols (!@#$...)? (Y/n): y

Exclude ambiguous characters (l, 1, I, O, 0)? (y/N): y

How many passwords would you like to generate? (1-20): 3

--------------------------------------------------
  [1] 2K[4Gr&]jK?$%y   (Strength: Very Strong)
  [2] SN(HqT,*.]96MK   (Strength: Very Strong)
  [3] =P,#Czk8FSN4+w   (Strength: Very Strong)
--------------------------------------------------
```

## 🧠 Key Concepts Demonstrated

- 🔑 **`secrets` vs. `random`** — deliberately chose `secrets` over `random` because password generation is security-sensitive; `random` is predictable enough to be unsuitable, while `secrets` draws from the OS's cryptographically secure random source
- 🔀 **Fisher-Yates shuffle** — `secrets` has no built-in `shuffle()` (unlike `random`), so implemented an in-place Fisher-Yates shuffle using `secrets.randbelow()` to fill that gap
- ✅ **Guaranteed-coverage generation logic** — avoids the common bug where "selected" character types don't actually appear in the output
- 🛡️ **Input validation** with sensible defaults and safety checks (e.g. auto-adjusting length if it's too short to fit all selected character types)
- 🧩 **Function decomposition** for readability and testability

## 📹 Demo
[Link to demo video / LinkedIn post — add after recording]

---
<div align="center">

Part of the **[OIBSIP](../)** repository — Oasis Infobyte Python Programming Internship

</div>
