
"""
BMI Calculator (Command-Line) - Multi-Unit Support
Oasis Infobyte Python Programming Internship - Project 1

Accepts weight in kilograms or pounds, and height in meters,
centimeters, or feet+inches. Automatically converts any of these
to the standard units BMI requires (kg and m) before calculating,
classifies the result into a health category, and supports repeated
calculations in a single session.
"""

# --- Conversion constants ---
LB_TO_KG = 0.45359237
CM_TO_M = 0.01
FT_TO_M = 0.3048
IN_TO_M = 0.0254


def get_positive_float(prompt: str) -> float:
    """Keep asking until the user enters a valid positive number."""
    while True:
        raw_value = input(prompt).strip()
        try:
            value = float(raw_value)
            if value <= 0:
                print("Please enter a number greater than 0.\n")
                continue
            return value
        except ValueError:
            print("That doesn't look like a valid number. Please try again.\n")


def get_choice(prompt: str, valid_choices: set) -> str:
    """Keep asking until the user picks one of the valid menu choices."""
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        print(f"Please enter one of: {', '.join(sorted(valid_choices))}\n")


def get_weight_in_kg() -> tuple[float, str]:
    """Ask for weight in kg or lb, return (value_in_kg, display_string)."""
    print("\nWeight unit:")
    print("  1) Kilograms (kg)")
    print("  2) Pounds (lb)")
    unit = get_choice("Choose 1 or 2: ", {"1", "2"})

    if unit == "1":
        weight = get_positive_float("Enter your weight (kg): ")
        return weight, f"{weight:.1f} kg"
    else:
        weight_lb = get_positive_float("Enter your weight (lb): ")
        weight_kg = weight_lb * LB_TO_KG
        return weight_kg, f"{weight_lb:.1f} lb  (= {weight_kg:.2f} kg)"


def get_height_in_m() -> tuple[float, str]:
    """Ask for height in m, cm, or ft+in, return (value_in_m, display_string)."""
    print("\nHeight unit:")
    print("  1) Meters (m)")
    print("  2) Centimeters (cm)")
    print("  3) Feet & inches (ft, in)")
    unit = get_choice("Choose 1, 2 or 3: ", {"1", "2", "3"})

    if unit == "1":
        height = get_positive_float("Enter your height (m): ")
        return height, f"{height:.2f} m"
    elif unit == "2":
        height_cm = get_positive_float("Enter your height (cm): ")
        height_m = height_cm * CM_TO_M
        return height_m, f"{height_cm:.1f} cm  (= {height_m:.2f} m)"
    else:
        feet = get_positive_float("Enter feet (e.g. 5): ")
        inches = get_positive_float("Enter inches (e.g. 8): ")
        height_m = (feet * FT_TO_M) + (inches * IN_TO_M)
        return height_m, f"{feet:.0f} ft {inches:.0f} in  (= {height_m:.2f} m)"


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Standard BMI formula: weight (kg) / height (m)^2"""
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi: float) -> str:
    """Classify BMI into standard WHO categories."""
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal weight"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def display_result(weight_display: str, height_display: str, bmi: float, category: str) -> None:
    print("\n" + "-" * 50)
    print(f"  Weight (as entered) : {weight_display}")
    print(f"  Height (as entered) : {height_display}")
    print(f"  BMI                 : {bmi:.2f}")
    print(f"  Category            : {category}")
    print("-" * 50 + "\n")


def main():
    print("=" * 50)
    print("        BMI CALCULATOR (multi-unit)")
    print("=" * 50)
    print("Enter your weight and height in whichever unit you")
    print("prefer — they'll be auto-converted to the standard")
    print("kg/m units before the BMI is calculated.\n")

    while True:
        weight_kg, weight_display = get_weight_in_kg()
        height_m, height_display = get_height_in_m()

        bmi = calculate_bmi(weight_kg, height_m)
        category = classify_bmi(bmi)
        display_result(weight_display, height_display, bmi, category)

        again = input("Calculate another BMI? (y/n): ").strip().lower()
        if again != "y":
            print("\nThanks for using the BMI Calculator. Stay healthy!")
            break


if __name__ == "__main__":
    main()
