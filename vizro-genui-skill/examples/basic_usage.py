"""Basic usage example: Generate a Vizro dashboard from an analytical objective.

This demonstrates the full flow:
1. Register data
2. Invoke the skill with an objective
3. Get back validated config + executable Python code
"""

import pandas as pd

from vizro_genui import VizroGenUISkill


def main():
    # --- Step 1: Initialize the skill ---
    skill = VizroGenUISkill(
        model="claude-sonnet-4-20250514",
        theme="vizro_dark",
        max_pages=3,
    )

    # --- Step 2: Register your datasets ---
    # In practice, these come from your data warehouse, APIs, etc.
    sales_df = pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"] * 3,
        "region": ["APAC"] * 4 + ["EMEA"] * 4 + ["Americas"] * 4,
        "revenue": [120, 135, 148, 160, 95, 102, 110, 118, 200, 215, 230, 245],
        "costs": [80, 85, 90, 95, 70, 72, 75, 78, 140, 145, 150, 155],
        "margin": [40, 50, 58, 65, 25, 30, 35, 40, 60, 70, 80, 90],
    })

    skill.register_data("sales", sales_df)

    # --- Step 3: Generate the dashboard ---
    result = skill.invoke(
        analytical_objective=(
            "Create a quarterly business review dashboard showing revenue trends "
            "by region, cost analysis, and margin evolution. Include filters for "
            "region drill-down."
        ),
        dataset_names=["sales"],
        additional_context="Use McKinsey blue color palette. Keep it clean and executive-ready.",
    )

    # --- Step 4: Use the results ---
    if result.is_valid:
        print("Dashboard generated successfully!")
        print("\n--- Executable Python Code ---")
        print(result.python_code)
        print("\n--- JSON Config ---")
        import json
        print(json.dumps(result.config, indent=2))
    else:
        print(f"Generation had validation issues: {result.errors}")
        print("Best-effort code:")
        print(result.python_code)


if __name__ == "__main__":
    main()
