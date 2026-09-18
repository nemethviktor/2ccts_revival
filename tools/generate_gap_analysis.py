#!/usr/bin/env python3
"""Roster Workbook Gap Analysis Engine
Copyright (C) 2026 V. Nemeth

This module provides native Excel compilation pipelines to track OpenTTD
vehicle availability lifespans and identify regional model gaps.
"""

import os
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import re

from helpers.role_rules import get_role

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def calculate_timeline(df_merged: pd.DataFrame) -> pd.DataFrame:
    """Simulates year-by-year vehicle model availability windows."""
    start_year: int = 1840
    end_year_limit: int = 2050
    years_range: np.ndarray = np.arange(start_year, end_year_limit + 1)

    region_columns: List[str] = [
        "AFRICA",
        "ASIA",
        "SOUTHERN_EUROPE",
        "EASTERN_EUROPE",
        "WESTERN_EUROPE",
        "NORTHERN_EUROPE",
        "NORTH_AMERICA",
        "SOUTH_AMERICA",
        "OCEANIA",
    ]

    timeline_records: List[Dict[str, Any]] = []

    for _, row in df_merged.iterrows():
        intro_year: int = int(float(row["INTRODUCTION_YEAR"]))
        model_life_raw: str = str(object=row["MODEL_LIFE"]).strip()

        retire_early = 0 if is_true(row["IS_WAGON_OR_COACH"]) else 20
        if model_life_raw == "VEHICLE_NEVER_EXPIRES" or model_life_raw == "0":
            expiry_year: int = end_year_limit
        else:
            try:
                expiry_year = intro_year + int(float(model_life_raw)) - retire_early
            except ValueError:
                expiry_year = intro_year + 45 - retire_early

        role_category: str = get_role(row=row)

        for region in region_columns:
            region_flag = row.get(region)
            if region_flag is True or str(object=region_flag).strip().lower() in ["true", "1", "1.0"]:
                # Vectorized generation of records per active region to eliminate the inner year loop
                valid_years = years_range[(years_range >= intro_year) & (years_range <= expiry_year)]
                for current_year in valid_years:
                    timeline_records.append(
                        {"Year": current_year, "Region": region, "Category": role_category, "Vehicle": row["VEHIDCODE"]}
                    )

    return pd.DataFrame(data=timeline_records)


def generate_visualization_matrix(df_timeline: pd.DataFrame, output_path: str) -> None:
    """Generates independent, region-centric dashboard grid JPG files highly optimized via Vectorization."""

    if df_timeline.empty:
        print("No records available to plot.")
        return

    # 1. Compute aggregate dense counts efficiently
    df_counts = df_timeline.groupby(by=["Region", "Category", "Year"]).size().reset_index(name="Available_Count")

    target_categories: List[str] = sorted(df_timeline["Category"].unique().tolist())

    region_columns: List[str] = [
        "AFRICA",
        "ASIA",
        "SOUTHERN_EUROPE",
        "EASTERN_EUROPE",
        "WESTERN_EUROPE",
        "NORTHERN_EUROPE",
        "NORTH_AMERICA",
        "SOUTH_AMERICA",
        "OCEANIA",
    ]
    simulation_years: np.ndarray = np.arange(1840, 2041)

    # 2. Build a comprehensive MultiIndex representing every possible combination
    full_index = pd.MultiIndex.from_product(
        [region_columns, target_categories, simulation_years], names=["Region", "Category", "Year"]
    )

    # Reindex fills all missing combinations with 0 instantly (No more nested loops!)
    df_dense = df_counts.set_index(["Region", "Category", "Year"]).reindex(full_index, fill_value=0).reset_index()

    # 3. Iterate through regions to compile plots
    for region in region_columns:
        safe_region_name: str = re.sub(pattern=r"[^a-zA-Z0-9_\-]", repl="_", string=region).lower()

        # Isolate this region's data entirely
        df_region = df_dense[df_dense["Region"] == region]

        fig, axes = plt.subplots(nrows=4, ncols=5, figsize=(24, 18), sharex=True, sharey=False)
        flat_axes = axes.flatten()

        for index, category in enumerate(target_categories):
            current_ax = flat_axes[index]

            # Fast linear slice using vectorized matching
            df_series = df_region[df_region["Category"] == category]

            current_ax.plot(df_series["Year"], df_series["Available_Count"], color="#e31a1c", linewidth=2.0)

            current_ax.set_title(label=category, fontsize=10, fontweight="bold")
            current_ax.grid(visible=True, linestyle=":", alpha=0.6)
            current_ax.tick_params(labelbottom=True)
            current_ax.set_xlabel(xlabel="Year", fontsize=8)
            current_ax.set_ylabel(ylabel="Models", fontsize=8)

            if category == "Wagon":
                ymax = 100
            elif category.startswith("Coach"):
                ymax = 30
            else:
                ymax = 25
            current_ax.set_ylim([0, ymax])

        # Clean up empty subplots
        for empty_index in range(len(target_categories), len(flat_axes)):
            fig.delaxes(ax=flat_axes[empty_index])

        clean_title: str = region.replace("_", " ").title()
        fig.suptitle(
            t=f"Regional Availability Gap Matrix - {clean_title} (All Roles)\n"
            f"Please note that Y-axis maxima aren't identical within a region but they are identical across categories for other regions.",
            fontsize=20,
            fontweight="bold",
            y=0.98,
        )

        filename: str = f"gap_analysis_region_{safe_region_name}.jpg"
        plt.savefig(
            fname=os.path.join(output_path, filename),
            format="jpg",
            dpi=72,
            pil_kwargs={"quality": 92, "optimize": True},
        )
        plt.close(fig=fig)
        print(f"---- Exported cross-platform validation asset: {filename}")


def main() -> None:
    """Execution entry point for the Excel layout compiler."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.normpath(os.path.join(project_root, "docs", "gap_analysis"))
    from helpers.read_excel_file import load_master_data, get_excel_path

    # Direct execution test logic:

    print(f"--- Extracting structured layout data from '{get_excel_path()}'...")
    df_m, _, _ = load_master_data(excel_path=get_excel_path())
    df_m = df_m[~(df_m.get("EXCLUDE", False).apply(is_true))]

    print("--- Simulating vehicle lifespans...")
    df_calculated_timeline: pd.DataFrame = calculate_timeline(df_merged=df_m)

    print("--- Generating high-resolution matrix dashboards...")
    generate_visualization_matrix(df_timeline=df_calculated_timeline, output_path=output_path)


if __name__ == "__main__":
    main()
