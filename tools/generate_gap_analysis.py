#!/usr/bin/env python3
""" Roster Workbook Gap Analysis Engine
Copyright (C) 2026 V. Nemeth

This module provides native Excel compilation pipelines to track OpenTTD 
vehicle availability lifespans and identify regional model gaps.
"""

import os
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.table import Table
import warnings
import re

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def extract_excel_table(sheet: Worksheet) -> pd.DataFrame:
    """ Detects and extracts a structured Excel Table from a worksheet.

    Falls back to parsing the entire sheet boundary data grid if no formal 
    table structures are registered within the sheet's XML schemas.
    """
    # Attempt to locate structured tables (e.g. Table1, PropertiesTable)
    tables: Dict[str, Table] = sheet.tables
    if not tables:
        # Fallback if properties is a plain sheet layout
        data_values: List[List[Any]] = list(sheet.values)
        if not data_values:
            return pd.DataFrame()
        return pd.DataFrame(data=data_values[1:], columns=data_values[0])

    # Extract the first registered structured table range coordinate matrix
    table_obj: Table = next(iter(tables.values()))
    table_range: str = table_obj.ref  # Returns boundary string like 'A1:AH650'

    # Slice the raw worksheet grid to isolate the table's exact coordinates
    data_rows: List[List[Any]] = []
    for row_cells in sheet[table_range]:
        data_rows.append([cell.value for cell in row_cells])

    # Convert into a structured dataframe using the first row as columns
    df_table: pd.DataFrame = pd.DataFrame(
        data=data_rows[1:], columns=data_rows[0])
    return df_table


def load_workbook_data(workbook_path: str) -> pd.DataFrame:
    """ Loads sheets from the source workbook and joins them via vehicle IDs. """
    wb = load_workbook(filename=workbook_path, data_only=True)

    # 1. Parse Properties Sheet (Extracting via Table schema)
    if "properties" not in wb.sheetnames:
        raise KeyError(
            "Required worksheet 'properties' missing from target workbook.")
    df_prop: pd.DataFrame = extract_excel_table(sheet=wb["properties"])

    # 2. Parse Roster Sheet (Standard unstructured sheet layout)
    if "roster" not in wb.sheetnames:
        raise KeyError(
            "Required worksheet 'roster' missing from target workbook.")
    roster_sheet: Worksheet = wb["roster"]
    roster_values: List[List[Any]] = list(roster_sheet.values)
    df_rost: pd.DataFrame = pd.DataFrame(
        data=roster_values[1:], columns=roster_values[0])

    # 2. Parse Control Sheet (Extracting via Table schema)
    if "control" not in wb.sheetnames:
        raise KeyError(
            "Required worksheet 'control' missing from target workbook.")
    df_control: pd.DataFrame = extract_excel_table(sheet=wb["control"])

    # Close workbook safely
    wb.close()

    # Clean padding spaces and filter empty tracking nodes
    df_prop = df_prop.dropna(subset=["VEHIDCODE"])
    df_rost = df_rost.dropna(subset=["VEHIDCODE"])
    df_control = df_control.dropna(subset=["VEHIDCODE"])

    df_prop["VEHIDCODE"] = df_prop["VEHIDCODE"].astype(str).str.strip()
    df_rost["VEHIDCODE"] = df_rost["VEHIDCODE"].astype(str).str.strip()
    df_control["VEHIDCODE"] = df_control["VEHIDCODE"].astype(str).str.strip()

    # Merge datasets, retaining separate source role contexts
    df_merged: pd.DataFrame = pd.merge(
        left=df_prop,
        right=df_rost,
        on="VEHIDCODE",
        suffixes=("_prop", "_rost")
    )

    df_merged: pd.DataFrame = pd.merge(
        left=df_merged,
        right=df_control,
        on="VEHIDCODE",
        suffixes=("", "_control")
    )

    return df_merged


def calculate_timeline(df_merged: pd.DataFrame) -> pd.DataFrame:
    """ Simulates year-by-year vehicle model availability windows. """
    start_year: int = 1840
    end_year_limit: int = 2050
    years_range: np.ndarray = np.arange(start_year, end_year_limit + 1)

    # Geographic region flag trackers located on the roster sheet
    region_columns: List[str] = [
        "AFRICA", "ASIA", "SOUTHERN_EUROPE", "EASTERN_EUROPE",
        "WESTERN_EUROPE", "NORTHERN_EUROPE", "NORTH_AMERICA",
        "SOUTH_AMERICA", "OCEANIA"
    ]

    timeline_records: List[Dict[str, Any]] = []

    for _, row in df_merged.iterrows():
        # Skip rows explicitly flagged for removal or exclusion overrides
        if str(object=row.get("EXCLUDE_prop")).strip().lower() == "true":
            continue
        if str(object=row.get("EXCLUDE_rost")).strip().lower() == "true":
            continue

        intro_year: int = int(float(row["INTRODUCTION_YEAR"]))
        model_life_raw: str = str(object=row["MODEL_LIFE"]).strip()

        # Determine decommissioning boundaries using your 20-year retire-early index
        retire_early = 0 if row.get(
            "IS_WAGON_OR_COACH_control") == True else 20
        if model_life_raw == "VEHICLE_NEVER_EXPIRES" or model_life_raw == "0":
            expiry_year: int = end_year_limit
        else:
            try:
                expiry_year = intro_year + \
                    int(float(model_life_raw)) - retire_early
            except ValueError:
                expiry_year = intro_year + 45 - retire_early  # Structural layout fallback

        # Rely strictly on the role allocation from the roster sheet
        role_category: str = str(object=row["ROLE_rost"])

        for region in region_columns:
            region_flag = row.get(region)
            if region_flag is True or str(object=region_flag).strip().lower() in ["true", "1", "1.0"]:
                for current_year in years_range:
                    if intro_year <= current_year <= expiry_year:
                        timeline_records.append({
                            "Year": current_year,
                            "Region": region,
                            "Category": role_category,
                            "Vehicle": row["VEHIDCODE"]
                        })

    return pd.DataFrame(data=timeline_records)


def generate_visualization_matrix(df_timeline: pd.DataFrame, output_path: str) -> None:
    """Generates independent, region-centric dashboard grid JPG files.

    Summary: Creates a single 4x5 grid layout per region showing all 17 roles 
             simultaneously, forces year labels across all sub-plots, and 
             saves as optimized high-quality JPGs.
    """
    # 1. Compute dense tracking counts across all timeline nodes
    df_counts: pd.DataFrame = df_timeline.groupby(
        by=["Year", "Region", "Category"]
    ).size().reset_index(name="Available_Count")

    # Dynamically extract all categories to capture all ~17 roles present in the data
    target_categories: List[str] = sorted(
        df_timeline["Category"].unique().tolist())

    region_columns: List[str] = [
        "AFRICA", "ASIA", "SOUTHERN_EUROPE", "EASTERN_EUROPE",
        "WESTERN_EUROPE", "NORTHERN_EUROPE", "NORTH_AMERICA",
        "SOUTH_AMERICA", "OCEANIA"
    ]

    simulation_years: np.ndarray = np.arange(1840, 2041)

    # 2. Iterate through each region individually to compile its master dashboard file
    for region in region_columns:
        # Sanitize filename: replace spaces, slashes, and characters for cross-platform safety
        safe_region_name: str = re.sub(
            pattern=r"[^a-zA-Z0-9_\-]", repl="_", string=region).lower()

        # Initialize a massive high-resolution 4x5 panel arrangement (20 slots total for 17 roles)
        fig, axes = plt.subplots(nrows=4, ncols=5, figsize=(
            24, 18), sharex=True, sharey=False)
        flat_axes = axes.flatten()

        # 3. Populate the 4x5 grid slot-by-slot for each individual vehicle role
        for index, category in enumerate(target_categories):
            current_ax = flat_axes[index]

            # Serialize the timeline for this specific coordinate block to capture absolute zeroes
            dense_grid: List[Dict[str, Any]] = []
            for year in simulation_years:
                match_slice: pd.DataFrame = df_counts[
                    (df_counts["Year"] == year) &
                    (df_counts["Region"] == region) &
                    (df_counts["Category"] == category)
                ]
                count_value: int = int(
                    match_slice["Available_Count"].values[0]) if not match_slice.empty else 0
                dense_grid.append(
                    {"Year": year, "Available_Count": count_value})

            df_series: pd.DataFrame = pd.DataFrame(data=dense_grid)

            # Plot the line for this region/category combo
            current_ax.plot(
                df_series["Year"],
                df_series["Available_Count"],
                color="#e31a1c",  # Deep high-contrast red for prominent gap tracking
                linewidth=2.0
            )

            # Sub-plot panel formatting adjustments
            current_ax.set_title(
                label=category, fontsize=10, fontweight="bold")
            current_ax.grid(visible=True, linestyle=":", alpha=0.6)

            # Force the year horizontal axis label on EVERY sub-chart panel
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

        # 4. Clean up any remaining empty grid boxes in the 4x5 grid layout (slots 18, 19, 20)
        for empty_index in range(len(target_categories), len(flat_axes)):
            fig.delaxes(ax=flat_axes[empty_index])

        # Master overall dashboard annotation title layout
        clean_title: str = region.replace("_", " ").title()
        fig.suptitle(
            t=f"Regional Availability Gap Matrix - {clean_title} (All Roles)\nPlease note that Y-axis maxima aren't identical within a region but they are identical across categories for other regions.", fontsize=20, fontweight="bold", y=0.98)

        # 5. Save file structure as high-quality, lightweight JPG format
        filename: str = f"gap_analysis_region_{safe_region_name}.jpg"

        # pil_kwargs compressed file boundaries while keeping line charts crisp
        plt.savefig(
            fname=os.path.join(output_path, filename),
            format="jpg",
            dpi=72,
            pil_kwargs={"quality": 92, "optimize": True}
        )
        plt.close(fig=fig)
        print(f"---- Exported cross-platform validation asset: {filename}")


def main() -> None:
    """ Execution entry point for the Excel layout compiler. """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.normpath(os.path.join(
        project_root, 'docs', 'gap_analysis'))

    if not os.path.exists(path=excel_path):
        print(f"[Error] Target workbook '{excel_path}' not found.")
        return

    print(
        f"--- Extracting structured layout data from '{excel_path}'...")
    df_merged_specs: pd.DataFrame = load_workbook_data(
        workbook_path=excel_path)
    df_calculated_timeline: pd.DataFrame = calculate_timeline(
        df_merged=df_merged_specs)
    generate_visualization_matrix(
        df_timeline=df_calculated_timeline, output_path=output_path)


if __name__ == "__main__":
    main()
