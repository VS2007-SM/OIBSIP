"""
Random Password Generator (Medium Level - CLI)
Oasis Infobyte Python Programming Internship - Project 2

Generates cryptographically-random passwords based on user-defined
criteria: length, character types, and optional exclusion of
visually ambiguous characters. Guarantees at least one character
from each selected type and reports an estimated strength rating.

Uses the `secrets` module (not `random`) for all randomness, since
`secrets` is designed for security-sensitive work like password and
token generation, while `random` is only suitable for non-security
purposes such as simulations or games.
"""

import secrets
import string

# Characters that are easy to confuse with each other visually
AMBIGUOUS_CHARS = "l1IO0"


def get_positive_int(prompt: str, min_value: int = 1, max_value: int = 128) -> int:
    """Keep asking until the user enters a valid integer within range."""
    while True:
        raw_value = input(prompt).strip()
        try:
            value = int(raw_value)
            if value < min_value or value > max_value:
                print(f"Please enter a number between {min_value} and {max_value}.\n")
                continue
            return value
        except ValueError:
            print("That doesn't look like a valid whole number. Please try again.\n")


def get_yes_no(prompt: str, default: str = "y") -> bool:
    """Ask a yes/no question. Pressing Enter uses the default."""
    default_hint = "Y/n" if default == "y" else "y/N"
    while True:
        raw_value = input(f"{prompt} ({default_hint}): ").strip().lower()
        if raw_value == "":
            raw_value = default
        if raw_value in ("y", "yes"):
            return True
        if raw_value in ("n", "no"):
            return False
        print("Please answer y or n.\n")


def build_character_pools(use_lower: bool, use_upper: bool, use_digits: bool,
                           use_symbols: bool, exclude_ambiguous: bool) -> dict:
    """
    Build a dict of {pool_name: characters} for every character type
    the user selected. Ambiguous characters are stripped if requested.
    """
    pools = {}

    if use_lower:
        pools["lowercase"] = string.ascii_lowercase
    if use_upper:
        pools["uppercase"] = string.ascii_uppercase
    if use_digits:
        pools["digits"] = string.digits
    if use_symbols:
        pools["symbols"] = "!@#$%^&*()-_=+[]{};:,.?"

    if exclude_ambiguous:
        cleaned = {}
        for name, chars in pools.items():
            cleaned[name] = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
        pools = cleaned

    return pools


def secure_shuffle(items: list) -> None:
    """
    Shuffle a list in place using the Fisher-Yates algorithm, drawing
    randomness from `secrets.randbelow`. `secrets` has no built-in
    shuffle (unlike `random`), so this fills that gap securely.
    """
    for i in range(len(items) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        items[i], items[j] = items[j], items[i]


def generate_password(length: int, pools: dict) -> str:
    """
    Generate one password of the given length, guaranteeing at least
    one character from every selected pool, then filling the rest
    randomly from the combined pool and shuffling.
    """
    all_chars = "".join(pools.values())

    # Guarantee coverage: one character from each selected type first
    password_chars = [secrets.choice(chars) for chars in pools.values()]

    # Fill the remaining length randomly from the combined pool
    remaining = length - len(password_chars)
    password_chars += [secrets.choice(all_chars) for _ in range(remaining)]

    secure_shuffle(password_chars)
    return "".join(password_chars)


def estimate_strength(length: int, pool_count: int) -> str:
    """
    Rough strength heuristic based on length and character-set variety.
    Not a substitute for real entropy calculation, but a useful signal.
    """
    if length < 8 or pool_count == 1:
        return "Weak"
    elif length < 12 and pool_count <= 2:
        return "Medium"
    elif length < 12:
        return "Strong"
    else:
        return "Very Strong"


def main():
    print("=" * 50)
    print("        RANDOM PASSWORD GENERATOR")
    print("=" * 50)

    length = get_positive_int("Password length (4-128): ", min_value=4, max_value=128)

    print("\nSelect character types to include:")
    use_lower = get_yes_no("  Include lowercase letters (a-z)?")
    use_upper = get_yes_no("  Include uppercase letters (A-Z)?")
    use_digits = get_yes_no("  Include digits (0-9)?")
    use_symbols = get_yes_no("  Include symbols (!@#$...)?")

    if not any([use_lower, use_upper, use_digits, use_symbols]):
        print("\nYou must select at least one character type. Defaulting to lowercase + digits.\n")
        use_lower = use_digits = True

    exclude_ambiguous = get_yes_no(
        "\nExclude ambiguous characters (l, 1, I, O, 0)?", default="n"
    )

    pools = build_character_pools(use_lower, use_upper, use_digits, use_symbols, exclude_ambiguous)

    # Safety check: length must be able to fit at least one char per pool
    if length < len(pools):
        print(f"\nLength too short for {len(pools)} selected character types. "
              f"Increasing length to {len(pools)}.")
        length = len(pools)

    how_many = get_positive_int(
        "\nHow many passwords would you like to generate? (1-20): ", min_value=1, max_value=20
    )

    print("\n" + "-" * 50)
    for i in range(1, how_many + 1):
        password = generate_password(length, pools)
        strength = estimate_strength(length, len(pools))
        print(f"  [{i}] {password}   (Strength: {strength})")
    print("-" * 50 + "\n")


if __name__ == "__main__":
    main()
