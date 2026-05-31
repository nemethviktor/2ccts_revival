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

    # Close workbook safely
    wb.close()

    # Clean padding spaces and filter empty tracking nodes
    df_prop = df_prop.dropna(subset=["VEHIDCODE"])
    df_rost = df_rost.dropna(subset=["VEHIDCODE"])
    df_prop["VEHIDCODE"] = df_prop["VEHIDCODE"].astype(str).str.strip()
    df_rost["VEHIDCODE"] = df_rost["VEHIDCODE"].astype(str).str.strip()

    # Merge datasets, retaining separate source role contexts
    df_merged: pd.DataFrame = pd.merge(
        left=df_prop,
        right=df_rost,
        on="VEHIDCODE",
        suffixes=("_prop", "_rost")
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

        # Determine decommissioning boundaries using your 25-year retire-early index
        if model_life_raw == "VEHICLE_NEVER_EXPIRES" or model_life_raw == "0":
            expiry_year: int = end_year_limit
        else:
            try:
                expiry_year = intro_year + int(float(model_life_raw)) - 25
            except ValueError:
                expiry_year = intro_year + 45 - 25  # Structural layout fallback

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
    """ Computes dense availability counts and saves the grid tracking plot. """
    df_counts: pd.DataFrame = df_timeline.groupby(
        by=["Year", "Region", "Category"]
    ).size().reset_index(name="Available_Count")

    # target_categories: list[str] = df_timeline["Category"].unique().tolist()
    target_categories: List[str] = [
        "Commuter/Urban",
        "Express",
        "Express Passenger",
        "Freight",
        "Heavy Freight",
        "Light Freight",
        "Metro",
        "Powered/Unpowered Sundry",
        "Shunting",
        "Ultra-High-Speed (Pax)",
        "Ultra-High-Speed (Universal)",
        "Universal",
    ]

    region_columns: List[str] = [
        "AFRICA", "ASIA", "SOUTHERN_EUROPE", "EASTERN_EUROPE",
        "WESTERN_EUROPE", "NORTHERN_EUROPE", "NORTH_AMERICA",
        "SOUTH_AMERICA", "OCEANIA"
    ]

    simulation_years: np.ndarray = np.arange(1840, 2041)
    dense_grid: List[Dict[str, Any]] = []

    # Enforce strict matrix structure to explicitly expose absolute zeroes/gaps
    for region in region_columns:
        for category in target_categories:
            for year in simulation_years:
                match_slice: pd.DataFrame = df_counts[
                    (df_counts["Year"] == year) &
                    (df_counts["Region"] == region) &
                    (df_counts["Category"] == category)
                ]
                count_value: int = int(
                    match_slice["Available_Count"].values[0]) if not match_slice.empty else 0
                dense_grid.append({
                    "Year": year,
                    "Region": region,
                    "Category": category,
                    "Available_Count": count_value
                })

    df_dense_matrix: pd.DataFrame = pd.DataFrame(data=dense_grid)

    # Build a 3x3 dashboard grid layout
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(
        24, 18), sharex=True, sharey=False)
    flat_axes = axes.flatten()

    for index, region in enumerate(region_columns):
        current_ax = flat_axes[index]
        df_region_sub: pd.DataFrame = df_dense_matrix[df_dense_matrix["Region"] == region]

        for category in target_categories:
            df_category_series: pd.DataFrame = df_region_sub[df_region_sub["Category"] == category]
            current_ax.plot(
                df_category_series["Year"],
                df_category_series["Available_Count"],
                label=category,
                linewidth=1.8
            )

        clean_title: str = region.replace("_", " ").title()
        current_ax.set_title(label=clean_title, fontsize=12, fontweight="bold")
        current_ax.grid(visible=True, linestyle=":", alpha=0.6)

        current_ax.tick_params(labelbottom=True)
        current_ax.set_xlabel(xlabel="Year", fontsize=10)

        if index == 0:
            current_ax.legend(loc="upper left", fontsize=8)
        if index >= 6:
            current_ax.set_xlabel(xlabel="Year", fontsize=10)
        if index % 3 == 0:
            current_ax.set_ylabel(ylabel="Available Models", fontsize=10)

    plt.tight_layout()
    plt.savefig(fname=output_path, dpi=150)
    print(f"---- Workbook gap matrix saved successfully to: {output_path}")


def main() -> None:
    """ Execution entry point for the Excel layout compiler. """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.normpath(os.path.join(
        project_root, 'docs', 'roster_gap_analysis.png'))

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
