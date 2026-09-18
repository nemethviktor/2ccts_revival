import os
import warnings
import custom_tags_generator, generate_badgetable, generate_languages, generate_graphics_pnml, generate_master_pnml, generate_unified_items, generate_vehicle_id_pnml, generate_vehicle_sort, generate_vehicle_summary

from helpers.read_excel_file import load_master_data, load_vehicle_id_ranges, get_excel_path

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

if __name__ == "__main__":
    excel_path = get_excel_path()
    df_master, copyright_text, notes_lookup = load_master_data(excel_path=excel_path)
    df_ranges = load_vehicle_id_ranges(excel_path=excel_path)

    custom_tags_generator.generate_version_file()
    generate_badgetable.generate_vehicle_id_pnml(copyright_text=copyright_text)
    generate_languages.generate_languages(df_master=df_master)
    generate_graphics_pnml.generate_graphics_pnml(
        df_master=df_master, copyright_text=copyright_text, notes_lookup=notes_lookup, df_ranges=df_ranges
    )
    generate_master_pnml.generate_master_pnml(df_master=df_master, copyright_text=copyright_text)
    generate_unified_items.generate_unified_items(
        df_master=df_master, copyright_text=copyright_text, notes_lookup=notes_lookup
    )
    generate_vehicle_id_pnml.generate_vehicle_id_pnml(
        df_master=df_master, copyright_text=copyright_text, df_ranges=df_ranges
    )
    generate_vehicle_sort.generate_vehiclesort_pnml(
        df_master=df_master, copyright_text=copyright_text, df_ranges=df_ranges
    )
    generate_vehicle_summary.generate_markdown(df_master=df_master)
