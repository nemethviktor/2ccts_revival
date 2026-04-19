import re
from typing import Literal, Optional
import pandas as pd
import os
from functools import wraps
import warnings
from pandas.api.types import is_number

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# --- TEMPLATE GENERATORS ---

# Notes to whoever...
# Hex codes -> In NML, 0xFE and 0xFF refer to the Head and Tail of the consist.
# Case 1 (Thalys PBKA): The sparks (Visual Effect) are DISABLED at the Head (0xFE) and Tail (0xFF). The sparking only happens on the middle wagons (the default case at the bottom).
# Real-world reason: High-speed trains like the Thalys often have their pantographs on the first passenger coaches immediately behind the power cars, or in the middle of the set.
# Case 2 (NTV AGV Duplex): The sparks are ENABLED at the Head and Tail, but DISABLED in the middle.
# Real-world reason: This train has its pantographs located on the leading and trailing power cars/units.
# In the context of var[0xC8] (which is the variable for "position in consist"):
# 0xFE: The very first vehicle in the train (The Engine/Front).
# 0xFF: The very last vehicle in the train (The Caboose/End).
# Default (no hex code): Every vehicle that isn't the first or the last.


def scrub_nml_data(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        def clean(val):
            # 1. Handle Strings
            if isinstance(val, str):
                return val.replace(' ', '_').replace('-', '_').lower()

            if isinstance(val, list):
                # Recursively clean every item in the list
                return [clean(item) for item in val]

            return val

        # Clean all keyword arguments EXCEPT 'vid' and 'gfx_path'
        cleaned_kwargs = {
            k: (clean(v) if k != 'extra_comment' else v)
            for k, v in kwargs.items()
        }

        # Clean positional arguments (if you use them)
        cleaned_args = [clean(a) for a in args]

        return func(*cleaned_args, **cleaned_kwargs)
    return wrapper


@scrub_nml_data
def get_visual_effect_and_powered(*, vid: str) -> str:
    """ This is almost certainly not the one you're looking for. """
    if 'steam_' in vid.lower() or 'rbs_' in vid.lower():
        visual_effect_type = 'STEAM'
    elif 'diesel_' in vid.lower() or 'dmu_' in vid.lower() or 'rbd_' in vid.lower():
        visual_effect_type = 'DIESEL'
    elif 'electric_' in vid.lower() or 'emu_' in vid.lower() or 'rbe_' in vid.lower():
        visual_effect_type = 'ELECTRIC'
    else:
        visual_effect_type = "PANIC"
    return visual_effect_type


@scrub_nml_data
def get_xmu_power_switch_position_based(*, vid: str, panto_pos: str = "ENDS", force_maglev_to_electric: bool = False) -> str:
    """
    Generates visual effect and power switches for xMUs.

    :param panto_pos: "ENDS" (Head/Tail have pantos) or "MIDDLE" (Only middle wagons have pantos); if it's not an EMU, it will default to not-ENDS
    """
    nml_code = []
    visual_effect_type = get_visual_effect_and_powered(vid=vid)
    if force_maglev_to_electric and visual_effect_type == "PANIC":
        visual_effect_type = "ELECTRIC"

    if visual_effect_type != "ELECTRIC":
        panto_pos = visual_effect_type

    # Define the effects based on the position type
    if panto_pos == "ENDS":
        # Case 2/3b style: Sparks at front/back, none in middle
        head_tail_effect = f"VISUAL_EFFECT_{visual_effect_type}, -3"
        middle_effect = "VISUAL_EFFECT_DISABLE, 0"
    else:
        # Case 1 style (Thalys): No sparks at front/back, sparks in middle
        head_tail_effect = "VISUAL_EFFECT_DISABLE, 0"
        middle_effect = f"VISUAL_EFFECT_{visual_effect_type}, -3"

    nml_code.append(f"""
// Visual effect and power management
// Position-based logic: {panto_pos}
/// In the context of var[0xC8] (which is the variable for "position in consist"):
/// 0xFE: The very first vehicle in the train (The Engine/Front).
/// 0xFF: The very last vehicle in the train (The Caboose/End).
switch(FEAT_TRAINS, SELF, switch_{vid}_visual_effect_and_powered, var[0xC8]) {{
    0xFE: visual_effect_and_powered({head_tail_effect}, DISABLE_WAGON_POWER);
    0xFF: visual_effect_and_powered({head_tail_effect}, DISABLE_WAGON_POWER);
    visual_effect_and_powered({middle_effect}, DISABLE_WAGON_POWER);
}}""")

    return "\n".join(nml_code)


@scrub_nml_data
def get_motion_counter(*, vid: str, switch_name_suffix: str, state_0: str, state_default: str) -> str:
    """
    Gets the motion_counter element

    :param vid: The vehicle id
    :param switch_name_suffix: String w/o underline to be suffixed after 'vid'
    :param state_0: Name of the first state (eg -> vid_state_0)
    :param state_default: name of the default state (eg -> vid_state_default)
    """

    return f"""
/// Animation states ({switch_name_suffix})
switch(FEAT_TRAINS, SELF, switch_{vid}_{switch_name_suffix}, motion_counter % 2){{
	0: spriteset_{vid}_{state_0};
	spriteset_{vid}_{state_default};
}}"""


@scrub_nml_data
def get_switch_vid(*, vid: str,
                   position_in_vehid_chain: int,
                   first_item_word: str,
                   second_item_word: str,
                   third_item_word: str = None,
                   fourth_item_word: str = None,
                   main_task: str = "switch",
                   first_item_location: int = 0,
                   second_item_location: int = None,
                   third_item_location: int = None,
                   fourth_item_location: int = None,
                   first_item_task: Optional[Literal["spriteset",
                                                     "spritegroup", "switch", "empty"]] = None,
                   second_item_task: Optional[Literal["spriteset",
                                                      "spritegroup", "switch", "empty"]] = None,
                   third_item_task: Optional[Literal["spriteset",
                                                     "spritegroup", "switch", "empty"]] = None,
                   fourth_item_task: Optional[Literal["spriteset",
                                                      "spritegroup", "switch", "empty"]] = None
                   ) -> str:
    """
    Gets the vid switch

    :param vid: The vehicle id
    :param position_in_vehid_chain: The position
    :param first_item_word: the suffix: task_vid_suffix
    :param second_item_word: the suffix: task_vid_suffix
    :param third_item_word: the suffix: task_vid_suffix
    """
    nml_code = []
    if not first_item_task:
        first_item_task = main_task
    if not second_item_task:
        second_item_task = main_task
    nml_code.append(
        f"{main_task}(FEAT_TRAINS, SELF, {main_task}_{vid}, position_in_vehid_chain % {position_in_vehid_chain}) {{")
    nml_code.append(
        f"\t{first_item_location}: {first_item_task}_{vid}_{first_item_word};")
    # Logic for the second item
    if second_item_task:
        if second_item_task != "empty":
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(
                f"\t{prefix}{second_item_task}_{vid}_{second_item_word};")
        else:
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if third_item_task:
        if third_item_task != "empty":
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(
                f"\t{prefix}{third_item_task}_{vid}_{third_item_word};")
        else:
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if fourth_item_task:
        if fourth_item_task != "empty":
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(
                f"\t{prefix}{fourth_item_task}_{vid}_{fourth_item_word};")
        else:
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    nml_code.append(f"}}")

    return "\n".join(nml_code)


@scrub_nml_data
def get_switch_cargo_class(*, vid: str,
                           task: Optional[Literal["spriteset",
                                                  "spritegroup", "switch", "empty"]],
                           fallback_task: Optional[Literal["spriteset",
                                                           "spritegroup", "switch", "empty"]],
                           bitmask_label: str,
                           spriteset_suffix: str,
                           spriteset_suffix_fallback: str) -> str:
    nml_code = f"""
/// Graphics for the unit wagon based on cargo class
switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_classes){{
	bitmask({bitmask_label.upper()}): {task}_{vid}_{spriteset_suffix};
	{fallback_task}_{vid}_{spriteset_suffix_fallback};
}}"""

    return nml_code


@scrub_nml_data
def get_switch_length(*, vid: str, row,
                      first_position_in_vehid_chain: int = 2,
                      first_deduct_from_position_in_vehid_chain_location: int = 1,
                      second_position_in_vehid_chain: Optional[int] = None,
                      second_deduct_from_position_in_vehid_chain_location: Optional[int] = None,
                      second_deduct_from_legnth_location: Optional[int] = None,
                      fallback_length_defined: int = None) -> str:
    nml_code = []

    fallback_length = fallback_length_defined if fallback_length_defined else row['WAGON_LENGTH'] if first_position_in_vehid_chain == 2 else row[
        'WAGON_LENGTH'] if row['WAGON_LENGTH'] != 0 else row['LENGTH']
    nml_code.append(f"""
/// Length
switch(FEAT_TRAINS, SELF, switch_{vid}_length, position_in_vehid_chain % {first_position_in_vehid_chain}) {{
    {0 if first_position_in_vehid_chain == 2 else first_position_in_vehid_chain-first_deduct_from_position_in_vehid_chain_location}: {row['LENGTH']};""")
    if second_deduct_from_position_in_vehid_chain_location:
        length_to_use = row['LENGTH'] - \
            second_deduct_from_legnth_location if second_deduct_from_legnth_location else row[
                'LENGTH']
        nml_code.append(
            f"\t{0 if second_position_in_vehid_chain == 2 else second_position_in_vehid_chain-second_deduct_from_position_in_vehid_chain_location}: {length_to_use};""")
    nml_code.append(f"\t{fallback_length};\n}}")

    return "\n".join(nml_code)


@scrub_nml_data
def get_switch_reversed(*, vid: str,
                        front_switch: str,
                        back_switch: str,
                        fallback_switch: str,
                        front_task: Optional[Literal["spriteset",
                                                     "spritegroup", "switch", "empty"]],
                        back_task: Optional[Literal["spriteset",
                                                    "spritegroup", "switch", "empty"]],
                        fallback_task: Optional[Literal["spriteset",
                                                        "spritegroup", "switch", "empty"]]) -> str:
    """
    Gets the reversed switch

    :param front_switch: Used in 0xFE: spriteset_{vid}_{front_switch}
    :param back_switch: Used in 0xFE: spriteset_{vid}_{back_switch}
    :param fallback_switch: Used in the last fallback switch
    """
    nml_code = f"""
/// Dualheaded (reverse switch)
/// In the context of var[0xC8] (which is the variable for "position in consist"):
/// 0xFE: The very first vehicle in the train (The Engine/Front).
/// 0xFF: The very last vehicle in the train (The Caboose/End).
switch(FEAT_TRAINS, SELF, switch_{vid}_reversed, var[0xC8]) {{
    0xFE: {front_task}_{vid}_{front_switch};
    0xFF: {back_task}_{vid}_{back_switch};
    {fallback_task}_{vid}_{fallback_switch};
}}"""

    return nml_code


@scrub_nml_data
def get_switch_position(*, vid: str,
                        position_in_vehid_chain: int,
                        first_item_word: str,
                        second_item_word: str,
                        third_item_word: str = None,
                        fourth_item_word: str = None,
                        main_task: str = "switch",
                        first_item_location: int = 0,
                        second_item_location: int = None,
                        third_item_location: int = None,
                        fourth_item_location: int = None,
                        first_item_task: Optional[Literal["spriteset",
                                                          "spritegroup", "switch", "empty"]] = None,
                        second_item_task: Optional[Literal["spriteset",
                                                           "spritegroup", "switch", "empty"]] = None,
                        third_item_task: Optional[Literal["spriteset",
                                                          "spritegroup", "switch", "empty"]] = None,
                        fourth_item_task: Optional[Literal["spriteset",
                                                           "spritegroup", "switch", "empty"]] = None
                        ) -> str:
    """
    Gets the position switch

    :param vid: The vehicle id
    :param position_in_vehid_chain: The position
    :param first_item_word: the suffix: task_vid_suffix
    :param second_item_word: the suffix: task_vid_suffix
    :param third_item_word: the suffix: task_vid_suffix
    """
    nml_code = []
    if not first_item_task:
        first_item_task = main_task
    if not second_item_task:
        second_item_task = main_task
    nml_code.append(
        f"{main_task}(FEAT_TRAINS, SELF, {main_task}_{vid}_position, position_in_vehid_chain % {position_in_vehid_chain}) {{")
    nml_code.append(
        f"\t{first_item_location}: {first_item_task}_{vid}_{first_item_word};")
    # Logic for the second item
    if second_item_task:
        if second_item_task != "empty":
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(
                f"\t{prefix}{second_item_task}_{vid}_{second_item_word};")
        else:
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if third_item_task:
        if third_item_task != "empty":
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(
                f"\t{prefix}{third_item_task}_{vid}_{third_item_word};")
        else:
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if fourth_item_task:
        if fourth_item_task != "empty":
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(
                f"\t{prefix}{fourth_item_task}_{vid}_{fourth_item_word};")
        else:
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    nml_code.append(f"}}")

    return "\n".join(nml_code)


@scrub_nml_data
def get_switch_with_store(*, vid: str,
                          store_value: int,
                          switch_what: str,
                          id_range: str,
                          first_item_task: str,
                          second_item_task: str,
                          first_item_suffix: str,
                          second_item_suffix: str) -> str:
    nml_code = f"""
switch(FEAT_TRAINS, SELF, switch_{vid}_{switch_what}, [STORE_TEMP({store_value}, 0x10F), var[0x61, 0, 0x0000FFFF, 0xC6]]) {{
	{id_range.upper()}: {first_item_task}_{vid}_{first_item_suffix};
	{second_item_task}_{vid}_{second_item_suffix};
}}"""

    return nml_code


@scrub_nml_data
def get_visual_effects_and_power_with_store(*, vid: str, store_value: int) -> str:
    visual_effect_type = get_visual_effect_and_powered(vid=vid)

    nml_code = f"""
switch(FEAT_TRAINS, SELF, switch_{vid}_visual_effect_and_powered_position, [STORE_TEMP({store_value}, 0x10F), var[0x61, 0, 0x0000FFFF, 0xC6]]) {{
	ID_RANGE_UNIT_WAGONS: switch_{vid}_visual_effect_and_powered;
	visual_effect_and_powered(VISUAL_EFFECT_{visual_effect_type}, -3, DISABLE_WAGON_POWER);
}}"""

    return nml_code


@scrub_nml_data
def get_visual_effect_on_odd_even_position(*, vid: str,
                                           position_in_vehid_chain: int = 2,
                                           deduct_from_position_for_first_return: int = 2,
                                           ) -> str:
    visual_effect_type = get_visual_effect_and_powered(vid=vid)

    nml_code = f"""
/// Visual Effect
switch(FEAT_TRAINS, SELF, switch_{vid}_visual_effect, position_in_vehid_chain % {position_in_vehid_chain}) {{
	{position_in_vehid_chain-deduct_from_position_for_first_return}: return visual_effect_and_powered(VISUAL_EFFECT_{visual_effect_type}, -3, DISABLE_WAGON_POWER);
	return visual_effect_and_powered(VISUAL_EFFECT_DISABLE, 0, DISABLE_WAGON_POWER);
}}"""

    return nml_code


@scrub_nml_data
def get_visual_effect_on_odd_even_position_with_range(*, vid: str,
                                                      range_start: int,
                                                      range_end: int,
                                                      reverse: bool,
                                                      position_in_vehid_chain: int = 2,
                                                      ) -> str:
    visual_effect_type = get_visual_effect_and_powered(vid=vid)

    nml_code = f"\n/// Visual Effect"
    nml_code += f"\nswitch(FEAT_TRAINS, SELF, switch_{vid}_visual_effect, position_in_vehid_chain % {position_in_vehid_chain}) {{"
    first_line = f"visual_effect_and_powered(VISUAL_EFFECT_DISABLE, 0, DISABLE_WAGON_POWER)"
    second_line = f"visual_effect_and_powered(VISUAL_EFFECT_{visual_effect_type}, -3, DISABLE_WAGON_POWER)"

    if reverse:
        nml_code += f"""\n\t{range_start}..{range_end}: {first_line};
	{second_line};"""
    else:
        nml_code += f"""\n\t{range_start}..{range_end}: {second_line};
    {first_line};
        """
    nml_code += "\n}"

    return nml_code


@scrub_nml_data
def get_random_switch_visual_effect(*, vid: str,
                                    first_chance: int,
                                    second_chance: int,
                                    ) -> str:
    visual_effect_type = get_visual_effect_and_powered(vid=vid)
    nml_code = f"""
/// Visual effect, for EMU this is done on the part with the pantograph
random_switch(FEAT_TRAINS, SELF, switch_{vid}_visual_effect_and_powered) {{
	{first_chance}: visual_effect_and_powered(VISUAL_EFFECT_DISABLE, 0, DISABLE_WAGON_POWER);
	{second_chance}: visual_effect_and_powered(VISUAL_EFFECT_{visual_effect_type}, -3, DISABLE_WAGON_POWER);
}}"""

    return nml_code


@scrub_nml_data
def get_random_switch_visual_effect_w_dependent(*, vid: str,
                                                switch_what: str,
                                                dependent_on_switch: str,
                                                first_chance: int,
                                                second_chance: int,
                                                first_item_task: str,
                                                second_item_task: str,
                                                first_item_suffix: str,
                                                second_item_suffix: str,
                                                ) -> str:
    dependent_str = f"dependent: switch_{vid}_{dependent_on_switch};"
    nml_code = f"""
/// Visual effect random switch ({switch_what})
random_switch(FEAT_TRAINS, SELF, switch_{vid}_{switch_what}) {{
    {dependent_str}
    {first_chance}: {first_item_task}_{vid}_{first_item_suffix};
    {second_chance}: {second_item_task}_{vid}_{second_item_suffix};
}}"""

    return nml_code


@scrub_nml_data
def get_articulated_return(*, vid: str, endvalue: int = 1) -> str:
    """
    Automates the articulated part callback.
    :param vid: The vehicle ID (cleaned by decorator).
    :param endvalue: Total number of ADDITIONAL parts to add.
    """
    # If adding only 1 part (e.g., a tender), the check is just '1'
    # If adding multiple, it's a range like '1..3'
    callback_range = "1" if endvalue == 1 else f"1..{endvalue}"

    return f"""
/// Articulated Return
/// extra_callback_info1 is the index of the part being added.
switch(FEAT_TRAINS, SELF, switch_{vid}_articulated, extra_callback_info1) {{
    {callback_range}: return item_{vid};
    return CB_RESULT_NO_MORE_ARTICULATED_PARTS;
}}
"""


@scrub_nml_data
def get_purchase(*, vid: str, gfx_path: str, purchase_x: int, purchase_y: int, template_suffix: str = None, dont_show_main_comment: bool = False) -> str:
    if template_suffix and template_suffix[0] != "_":
        template_suffix = "_" + template_suffix
    if not template_suffix:
        template_suffix = ""
    main_comment = "\n// PURCHASE" if not dont_show_main_comment else ""
    return f"""{main_comment}
spriteset(spriteset_{vid}_purchase, "{gfx_path}") {{template_purchase{template_suffix}({purchase_x}, {purchase_y})}}
"""


@scrub_nml_data
def get_vehicle(*, vid: str,
                gfx_path: str,
                title_comment: str,
                vehicle_x: int, vehicle_y: int,
                template_suffix: str,
                use_comment_as_spritename_suffix: bool = False,
                dont_show_main_comment: bool = False,
                extra_comment: str = None) -> str:
    """
    Gets the vehicle related code

    :param title_comment: this is the title, eg. 'Engine'
    :param template_suffix: literal string to put after the 'template' word
    :param use_comment_as_spritename_suffix: if True then comment_type becomes the sprite suffix itself; if False then sprite suffix becomes ''
    :param extra_comment: Optional to show things like how the 12-len set is built up etc. Literal comment use.

    """
    sprite_suffix = f"_{title_comment}" if use_comment_as_spritename_suffix else ''
    if template_suffix[0] != "_":
        template_suffix = "_" + template_suffix
    vehicle_str = "\n// VEHICLE" if not dont_show_main_comment else ""
    if extra_comment:
        vehicle_str += "\n" + extra_comment
    vehicle_str += '\n/// ' + title_comment.replace('_', ' ').title() + '\n'
    vehicle_str += f"""spriteset(spriteset_{vid}{sprite_suffix}, "{gfx_path}") {{template{template_suffix}({vehicle_x}, {vehicle_y})}}\n"""
    return vehicle_str


@scrub_nml_data
def get_spriteset(*,
                  vid: str,
                  gfx_path: str,
                  comment_type: str,
                  template_x: int,
                  template_y: int,
                  template_name_amendment: str,
                  spritename_suffix: str = None) -> str:
    sprite_suffix = f"_{spritename_suffix}" if spritename_suffix else ''
    if template_name_amendment[0] != "_":
        template_name_amendment = "_" + template_name_amendment

    return (f"""
/// {comment_type.upper().replace('_', ' ')}
spriteset(spriteset_{vid}{sprite_suffix}, "{gfx_path}") {{template{template_name_amendment}({template_x}, {template_y})}}
""")


@scrub_nml_data
def get_spritegroup_without_loading_states(*, vid: str, livery_num: int, created_sprites: list[str], cargo_string: str, cargo_string_is_dummy: bool,
                                           ) -> str:
    """
    Automates the generation of NML spritegroup blocks.
    Handles standard loading states and special driving/loaded states.
    """

    # 1. Determine Sprite Lists
    loading_list = ", ".join(created_sprites)
    loaded_list = loading_list

    # 2. Construct Group Name and Header
    if cargo_string_is_dummy:
        group_name = f"spritegroup_{vid}_l{livery_num}"
        comment = f"/// Livery {livery_num} Spritegroup"
    else:
        group_name = f"spritegroup_{vid}_{cargo_string}_l{livery_num}"
        comment = f"/// Livery {livery_num} Spritegroup - {cargo_string}"

    group_name = group_name.lower()

    # 3. Build the NML Block
    return (f"""
{comment.upper()}
spritegroup {group_name} {{
    loading: [{loading_list}];
    loaded: [{loaded_list}];
}}""")


@scrub_nml_data
def get_spritegroup_with_loading_states(*, vid: str, livery_num: int, created_sprites: list[str], cargo_string: str, cargo_string_is_dummy: bool,
                                        has_loading_states: bool, has_driving_states: bool, cargo_with_driving_state: list[str] = []) -> str:
    """
    Automates the generation of NML spritegroup blocks.
    Handles standard loading states and special driving/loaded states.
    """
    if not has_loading_states:
        return ""

    # 1. Determine Sprite Lists
    if has_driving_states and cargo_string in cargo_with_driving_state:
        # Loading uses everything except the last (driving) sprite
        loading_list = ", ".join(created_sprites[0:-1])
        # Loaded/Driving uses First, Last, Last pattern
        loaded_list = f"{created_sprites[0]}, {created_sprites[-1]}, {created_sprites[-1]}"
    else:
        # Standard behavior: loading and loaded are identical
        loading_list = ", ".join(created_sprites)
        loaded_list = loading_list

    # 2. Construct Group Name and Header
    if cargo_string_is_dummy:
        group_name = f"spritegroup_{vid}_l{livery_num}"
        comment = f"/// Livery {livery_num} Spritegroup"
    else:
        group_name = f"spritegroup_{vid}_{cargo_string}_l{livery_num}"
        comment = f"/// Livery {livery_num} Spritegroup - {cargo_string}"

    group_name = group_name.lower()

    # 3. Build the NML Block
    return (f"""
{comment.upper()}
spritegroup {group_name} {{
    loading: [{loading_list}];
    loaded: [{loaded_list}];
}}""")


@scrub_nml_data
def get_random_livery_selector(*,
                               vid: str,
                               selector_name: str,
                               cargo_string: str,
                               list_length: int,
                               cargo_string_is_dummy: bool,
                               has_loading_states: bool,
                               first_chance: int = 7,
                               manual_suffix: str = None
                               ) -> str:
    """
    Gets the random livery selector

    :param selector_name: goes into nrandom_switch(FEAT_TRAINS, SELF, {selector_name}
    :param cargo_string: goes into spritexxx_{vid}_{cargo_string}_l{num}
    :param list_length: how many items in the list
    :param cargo_string_is_dummy: if cargo=='dummy' (ie there isn't one)
    :param has_loading_states: whether we are using loading states
    """
    nml_code = f"\n// Random Livery Selector{' ' + manual_suffix if manual_suffix else ''}"
    nml_code += f" for {cargo_string}" if not cargo_string_is_dummy else ""
    nml_code += f"\nrandom_switch(FEAT_TRAINS, SELF, {selector_name}) {{"

    for num in range(1, list_length + 1):
        weight = first_chance if num == 1 else int(
            (10-first_chance)/(list_length-1))
        if cargo_string_is_dummy:
            target = f"spritegroup_{vid}_l{num}" if has_loading_states else f"spriteset_{vid}_l{num}{'_' + manual_suffix if manual_suffix else ''}"
        else:
            target = f"spritegroup_{vid}_{cargo_string}_l{num}" if has_loading_states else f"spriteset_{vid}_{cargo_string}_l{num}"

        target = target.lower()
        nml_code += (f"\n\t{weight}: {target};")
    nml_code += "\n}"

    return nml_code


def get_tpl_controller(row, copyright_header) -> str:
    vid = row['VEHIDCODE'].lower()
    expected_fn = row['FILENAMES_EXPECTED']
    template_id = int(row['TEMPLATE_ID'][-2:])
    template_amendment_code = str(row['TEMPLATE_AMENDMENT_CODE'])

    # 1. Handle Amendment logic
    amendment = ""
    if template_amendment_code and template_amendment_code.lower() != 'nan':
        amendment = template_amendment_code

    # 2. GFX path logic
    gfx_path = f"gfx{row['SAVE_TO'][3:].replace('\\', '/')}/{expected_fn}.png"

    # 3. Template Mapping
    template_map = {
        1: get_tpl_01,
        2: get_tpl_02,
        3: get_tpl_03,
        4: get_tpl_04,
        16: get_tpl_16,
        17: get_tpl_17,
        25: get_tpl_25,
        32: get_tpl_32,
        42: get_tpl_42
    }

    func = template_map.get(template_id)

    if func:
        body = func(vid, gfx_path, row, template_amendment_code)

        # 4. Construct the FINAL string here, including the amendment
        # We don't need a list anymore, just a formatted string
        full_output = (
            f"{copyright_header}\n\n"
            f"// Template: TPL_{template_id:02}{amendment}\n"
            f"{body}"
        )
        return full_output

    return f"// Error: Template {template_id} not implemented"


def get_tpl_01(vid, gfx_path, row, template_amendment_code):
    """Simple Static (Engine/Wagon)"""

    purchase_y = 64
    if template_amendment_code in ['B', 'C', 'D']:
        purchase_y = 32
    elif template_amendment_code == 'E':
        purchase_y = 128
    elif template_amendment_code == 'F':
        purchase_y = 1

    purchase_amendment = ""
    if template_amendment_code == 'C':
        purchase_amendment = "_dualheaded"
    elif template_amendment_code == 'F':
        purchase_amendment = "_wagon_special"

    engine_amendment = "_2cc_engines_general"
    if template_amendment_code in ['D', 'E']:
        engine_amendment = "_2cc_railbus_general"
    elif template_amendment_code == 'F':
        engine_amendment = "_wagon_special"

    engine_x = 1
    if template_amendment_code == 'F':
        engine_x = 21

    nml_code = []
    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path, purchase_x=1,
                                 purchase_y=purchase_y, template_suffix=purchase_amendment))
    nml_code.append(get_vehicle(vid=vid, gfx_path=gfx_path, title_comment='engine', vehicle_x=engine_x,
                                vehicle_y=1, template_suffix=engine_amendment))

    return '\n'.join(nml_code)


def get_tpl_02(vid, gfx_path, row, template_amendment_code):
    """
    Standard MU(Front/Back/Middle/Cargo) // EMU(Long) // Metro(Front/Back/Middle/No cargo, obvs.): param template_amendment_code:
        A -> DMU/EMU/Maglev;
        B -> [this has been removed]
        C -> Metro
        D -> EMU(Long)
        E -> EMU(Even Longer): return:
    """
    visual_effect_type = get_visual_effect_and_powered(vid=vid)

    nml_code = []
    if template_amendment_code in ['A', 'D', 'F']:
        purchase_coord_y = 128
    elif template_amendment_code in ['C']:
        purchase_coord_y = 96
    elif template_amendment_code in ['E']:
        purchase_coord_y = 320

    purchase_amendment = "dualheaded"
    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path, purchase_x=1,
                                 purchase_y=purchase_coord_y, template_suffix=purchase_amendment))

    # Front and Back are common to all subtypes
    nml_code.append(get_vehicle(
        vid=vid, gfx_path=gfx_path, title_comment='front', vehicle_x=1, vehicle_y=1, template_suffix="2cc_engines_general", use_comment_as_spritename_suffix=True))
    nml_code.append(get_vehicle(
        vid=vid, gfx_path=gfx_path, title_comment='back',  vehicle_x=1, vehicle_y=32, template_suffix="2cc_engines_general", use_comment_as_spritename_suffix=True))

    if template_amendment_code in ['A', 'D', 'F']:
        levels = {'L1': 1, 'L2': 178}
    elif template_amendment_code == 'E':
        levels = {
            'Part 2 Regular': 64,
            'Part 2 Front': 96,
            'Part 2 Back': 128,
            'Double': 160
        }
    elif template_amendment_code == 'F':
        # 1. Define the X-offsets for the different liveries
        levels = {'L1': 1, 'L2': 178}
    else:
        levels = {}

    if template_amendment_code in ['A', 'D', 'E']:
        # Standardize 'A' to use a single-item loop to avoid repeating code blocks
        active_levels = {'': 1} if template_amendment_code == 'A' else levels

        for level, val in active_levels.items():
            # Setup Dynamic Suffixes
            suffix = f"_{level.lower().replace(' ', '_').replace('-', '_')}" if level else ""

            # Determine X/Y logic based on Code
            if template_amendment_code == 'D':
                tx, ty_pass, ty_mail = val, 64, 96
            elif template_amendment_code == 'E':
                tx, ty_pass, ty_mail = 1, val, val + 128
            else:  # Default for 'A'
                tx, ty_pass, ty_mail = 1, 64, 96

            # Generate 'Middlepass' Spriteset
            nml_code.append(get_spriteset(
                vid=vid, gfx_path=gfx_path,
                comment_type=f"middlepass{suffix}",
                template_name_amendment="2cc_engines_general",
                spritename_suffix=f"middlepass{suffix}",
                template_x=tx, template_y=ty_pass
            ))

            # Generate 'Middlemail' Spriteset
            nml_code.append(get_spriteset(
                vid=vid, gfx_path=gfx_path,
                comment_type=f"middlemail{suffix}",
                template_name_amendment="2cc_engines_general",
                spritename_suffix=f"middlemail{suffix}",
                template_x=tx, template_y=ty_mail
            ))

    elif template_amendment_code in ['C']:
        nml_code.append(get_spriteset(
            vid=vid, gfx_path=gfx_path,
            comment_type="middle",
            template_name_amendment="2cc_engines_general",
            spritename_suffix="middle",
            template_x=1, template_y=64
        ))

    elif template_amendment_code in ['F']:
        for level, x_offset in levels.items():
            nml_code.append(get_spriteset(
                vid=vid, gfx_path=gfx_path,
                # Extracts '1' from 'L1'
                comment_type=f"Middle - PAX - Livery {level[-1]}",
                template_name_amendment="2cc_engines_general",
                spritename_suffix=f"middlepass_{level}",
                template_x=x_offset,
                template_y=64
            ))
        # Mail has no level
        nml_code.append(get_spriteset(
            vid=vid, gfx_path=gfx_path,
            # Extracts '1' from 'L1'
            comment_type=f"Middle - MAIL - Livery",
            template_name_amendment="2cc_engines_general",
            spritename_suffix=f"middlemail",
            template_x=1,
            template_y=96
        ))

        # This comes here, rather than further down as for whichever other
        cargo_string_is_dummy = False
        cargo_string = "middlepass"
        selector_name = f"switch_{vid}_livery" if cargo_string_is_dummy else f"switch_{vid}_{cargo_string}_livery"
        nml_code.append(get_random_livery_selector(
            vid=vid,
            cargo_string=cargo_string,
            selector_name=selector_name,
            list_length=2,
            cargo_string_is_dummy=cargo_string_is_dummy,
            has_loading_states=False))

    if template_amendment_code in ['E']:
        for item in ["pass", "mail"]:
            nml_code.append(get_switch_with_store(vid=vid,
                                                  store_value=1,
                                                  switch_what=f"middle{item}_position_back",
                                                  id_range="ID_RANGE_UNIT_WAGONS",
                                                  first_item_task="spriteset",
                                                  second_item_task="spriteset",
                                                  first_item_suffix=f"middle{item}_part_2_regular",
                                                  second_item_suffix=f"middle{item}_part_2_back"))

            nml_code.append(get_switch_with_store(vid=vid,
                                                  store_value=1,
                                                  switch_what=f"middle{item}_position_front",
                                                  id_range="ID_RANGE_UNIT_WAGONS",
                                                  first_item_task="spriteset",
                                                  second_item_task="spriteset",
                                                  first_item_suffix=f"middle{item}_part_2_front",
                                                  second_item_suffix=f"middle{item}_double"))

            nml_code.append(get_switch_with_store(vid=vid,
                                                  store_value=-1,  # minus 1
                                                  switch_what=f"middle{item}_length",
                                                  id_range="ID_RANGE_UNIT_WAGONS",
                                                  first_item_task="switch",  # switch, not spriteset
                                                  second_item_task="switch",  # switch, not spriteset
                                                  first_item_suffix=f"middle{item}_position_back",
                                                  second_item_suffix=f"middle{item}_position_front"))

    if template_amendment_code in ['A', 'C', 'D', 'E', 'F']:
        nml_code.append(get_switch_reversed(
            # yes it's b/b/f not a typo
            vid=vid,
            back_switch="back",
            back_task="spriteset",
            front_switch="back",
            front_task="spriteset",
            fallback_switch="front",
            fallback_task="spriteset"
        ))

    if template_amendment_code in ['A']:
        nml_code.append(get_xmu_power_switch_position_based(
            vid=vid, force_maglev_to_electric=True))

        nml_code.append(get_switch_cargo_class(
            vid=vid,
            task="spriteset", fallback_task="spriteset",
            bitmask_label="CC_PASSENGERS",
            spriteset_suffix="middlepass", spriteset_suffix_fallback="middlemail"))

    elif template_amendment_code == 'D':
        nml_code.append(get_random_switch_visual_effect(
            vid=vid, first_chance=9, second_chance=1))

        nml_code.append(
            get_visual_effects_and_power_with_store(vid=vid, store_value=-1))

        nml_code.append(get_random_switch_visual_effect_w_dependent(
            vid=vid,
            dependent_on_switch="visual_effect_and_powered",
            switch_what="middlepass_livery",
            first_chance=9, second_chance=1,
            first_item_task="spriteset", second_item_task="spriteset",
            first_item_suffix="middlepass_l1", second_item_suffix="middlepass_l2"))

        nml_code.append(get_random_switch_visual_effect_w_dependent(
            vid=vid,
            dependent_on_switch="visual_effect_and_powered",
            switch_what="middlemail_livery",
            first_chance=9, second_chance=1,
            first_item_task="spriteset", second_item_task="spriteset",
            first_item_suffix="middlemail_l1", second_item_suffix="middlemail_l2"))

        for item in ["pass", "mail"]:

            nml_code.append(get_switch_with_store(vid=vid,
                                                  store_value=-1,  # minus 1
                                                  switch_what=f"middle{item}_position",
                                                  id_range="ID_RANGE_UNIT_WAGONS",
                                                  first_item_task="switch",  # switch, not spriteset
                                                  second_item_task="spriteset",  # spriteset!
                                                  first_item_suffix=f"middle{item}_livery",
                                                  second_item_suffix=f"middle{item}_l2"))

        nml_code.append(get_switch_cargo_class(vid=vid,
                                               task="switch", fallback_task="switch",
                                               bitmask_label="CC_PASSENGERS",
                                               spriteset_suffix="middlepass_position",
                                               spriteset_suffix_fallback="middlemail_position"))

    elif template_amendment_code in ['E', 'F']:
        suffix = "_length" if template_amendment_code == 'E' else "_livery"
        suffix_fallback = "_length" if template_amendment_code == 'E' else ""
        nml_code.append(get_xmu_power_switch_position_based(
            vid=vid, panto_pos=row['PANTOGRAPH_POSITION']))
        nml_code.append(get_switch_cargo_class(vid=vid,
                                               # fk me sideways.
                                               task="switch", fallback_task="spriteset" if template_amendment_code == 'F' else "switch",
                                               bitmask_label="CC_PASSENGERS",
                                               spriteset_suffix=f"middlepass{suffix}",
                                               spriteset_suffix_fallback=f"middlemail{suffix_fallback}")
                        )

    return '\n'.join(nml_code)


def get_tpl_03(vid, gfx_path, row, template_amendment_code):
    """
    Articulated(Engine + Tender) OR Items with 2 engine animation states.: param template_amendment_code:
        A -> Steam w / Tender
        B -> Items w 2 engine animation states
        C -> Same as B but different 'purhchase' position
        D -> Non-Steam w / Tender
        E -> Same as A but no Visual Effect
        F -> Same as B but no Visual effect
        G -> Same as A but 12 length
    """

    nml_code = []
    if template_amendment_code in ['A', 'C', 'E']:
        purchase_coord_y = 96
    elif template_amendment_code in ['B', 'D', 'F']:
        purchase_coord_y = 64
    elif template_amendment_code in ['G']:
        purchase_coord_y = 192

    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path, purchase_x=1,
                                 purchase_y=purchase_coord_y, template_suffix=None))

    if template_amendment_code in ['A', 'B', 'C', 'E']:
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='engine1',
            vehicle_x=1, vehicle_y=1,
            template_suffix="2cc_engines_general",
            use_comment_as_spritename_suffix=True))
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='engine2',
            vehicle_x=1, vehicle_y=32,
            template_suffix="2cc_engines_general",
            use_comment_as_spritename_suffix=True, dont_show_main_comment=True))
    elif template_amendment_code in ['D', 'F']:
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='engine',
            vehicle_x=1, vehicle_y=1,
            template_suffix="2cc_engines_general",
            use_comment_as_spritename_suffix=True))
    elif template_amendment_code in ['G']:
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='engine1',
            vehicle_x=1, vehicle_y=1,
            template_suffix="2cc_L12",
            use_comment_as_spritename_suffix=True))
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='engine2',
            vehicle_x=1, vehicle_y=64,
            template_suffix="2cc_L12",
            use_comment_as_spritename_suffix=True, dont_show_main_comment=True))

    if template_amendment_code in ['A', 'E']:
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='tender',
            vehicle_x=1, vehicle_y=64,
            template_suffix="2cc_engines_general",
            use_comment_as_spritename_suffix=True, dont_show_main_comment=True))
    elif template_amendment_code in ['G']:
        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment='tender',
            vehicle_x=1, vehicle_y=128,
            template_suffix="2cc_L12",
            use_comment_as_spritename_suffix=True, dont_show_main_comment=True))
    elif template_amendment_code in ['D', 'F']:
        if template_amendment_code == 'D':
            comment_type = 'tender'
        elif template_amendment_code == 'F':
            comment_type = 'b_unit'

        nml_code.append(get_vehicle(
            vid=vid, gfx_path=gfx_path, title_comment=comment_type,
            vehicle_x=1, vehicle_y=32,
            template_suffix="2cc_engines_general",
            use_comment_as_spritename_suffix=True, dont_show_main_comment=True))

        nml_code.append(get_switch_position(vid=vid, position_in_vehid_chain=2,
                                            first_item_word='engine', second_item_word=comment_type,
                                            main_task="switch",
                                            first_item_location=0, second_item_location=None,
                                            first_item_task="spriteset", second_item_task="spriteset",
                                            ))

    if template_amendment_code in ['A', 'B', 'C', 'E', 'G']:
        nml_code.append(get_motion_counter(
            vid=vid, switch_name_suffix="animation", state_0="engine1", state_default="engine2"))

    elif template_amendment_code == 'D':
        nml_code.append(
            f"{get_visual_effect_on_odd_even_position(vid=vid,  position_in_vehid_chain=2)}")
        nml_code.append(
            f"{get_switch_length(vid=vid, row=row, first_deduct_from_position_in_vehid_chain_location=2, first_position_in_vehid_chain=2)}")
        nml_code.append(
            f"{get_articulated_return(vid=vid, endvalue=1)}"
        )

    if template_amendment_code in ['A']:
        nml_code.append(get_switch_position(vid=vid, position_in_vehid_chain=2,
                                            first_item_word='animation', second_item_word='tender',
                                            main_task="switch",
                                            first_item_location=0, second_item_location=None,
                                            first_item_task="switch", second_item_task="spriteset"))

        nml_code.append(
            get_visual_effect_on_odd_even_position(vid=vid, position_in_vehid_chain=2))
        nml_code.append(
            get_switch_length(vid=vid, row=row, first_deduct_from_position_in_vehid_chain_location=2, first_position_in_vehid_chain=2))
        nml_code.append(
            get_articulated_return(vid=vid, endvalue=1))

    elif template_amendment_code in ['G']:
        nml_code.append(get_switch_position(vid=vid, position_in_vehid_chain=3,
                                            first_item_word='animation', second_item_word='tender',
                                            main_task="switch",
                                            first_item_location=0, second_item_location=2,
                                            first_item_task="switch", second_item_task="spriteset",
                                            third_item_task="empty"))

        nml_code.append(
            get_visual_effect_on_odd_even_position(vid=vid, position_in_vehid_chain=3, deduct_from_position_for_first_return=3))
        nml_code.append(
            get_switch_length(vid=vid, row=row,
                              first_position_in_vehid_chain=3,
                              first_deduct_from_position_in_vehid_chain_location=3,
                              second_position_in_vehid_chain=3,
                              second_deduct_from_position_in_vehid_chain_location=1,
                              second_deduct_from_legnth_location=1,
                              fallback_length_defined=2,

                              ))
        nml_code.append(
            get_articulated_return(vid=vid, endvalue=2))
    return '\n'.join(nml_code)


def get_tpl_04(vid, gfx_path, row, template_amendment_code):
    """
    Coaches & Wagons w / Cargo/Liveries
    Standard -> `TPL_04A` // technically it's just 'A' but I'm lazy. All of the params here are the same, 1 letter only.
    Loading States w / Cargo -> `TPL_04B`
    Box Car Type 1 -> `TPL_04C` (but not Gen 3/4 Type 2)
    Box Car Type 2 -> `TPL_04D` (but not Gen 3/4 Type 2)
    Centerbeam -> `TPL_04E`
    Container-Carrier -> `TPL_04F`
    Container-Doublestack -> `TPL_04G`
    Hopper Types 1/2 -> `TPL_04H`
    Flatcar/Flat Wagon -> `TPL_04I`
    Tanker Non-2nd Gen -> `TPL_04J`
    Tanker 2nd Gen -> `TPL_04K`
    Open Wagon Gen2/Gen3 -> `TPL_04L` - This has 'Driving State' for GRAIN only
    Box Car Gen3/4 Type 2 -> `TPL_04M`
    Gondola -> `TPL_04N` - This has 'Driving State' for GRAIN only
    Heavy Flatcar -> `TPL_04O`
    Box Car Gen2 Type 2 -> `TPL_04P`
    Open Wagon Gen1 -> `TPL_04Q`
    Service Cars -> `TPL_04R`
    DC/Push-Pull -> `TPL_04S`
    """
    gfx_purchase_amendment = "_Purchase"
    nml_code = []

    # 1. Header & Purchase
    nml_code.append(get_purchase(
        vid=vid, gfx_path=gfx_path[:-4] + gfx_purchase_amendment + ".png", purchase_x=1, purchase_y=1, template_suffix="_wagon"))
    nml_code.append(f"""
// VEHICLE""")

    # Constants for offsets
    liveries = {1: 1, 2: 179, 3: 357, 4: 535}

    # region templates for cargoes
    cargo_strings = ['Dummy']
    if template_amendment_code == 'C':
        cargo_strings = [
            'Armoured',
            'Livestock',
            'Reefer',
            'Standard',
        ]
    elif template_amendment_code == 'D':
        cargo_strings = [
            'Standard'
        ]
    elif template_amendment_code == 'E':
        cargo_strings = [
            'Crates',
            'Planks',
            'Steel',
        ]
    elif template_amendment_code == 'F':
        cargo_strings = [
            'Container',
            'Refrigerated',
            'Tanktainer',
        ]
    elif template_amendment_code == 'G':
        cargo_strings = [
            'Container',
            'Refrigerated',
        ]
    elif template_amendment_code == 'H':
        cargo_strings = [
            'Coal',
            'Ore',
            'Sand',
            'Gray',
        ]
    elif template_amendment_code == 'I':
        cargo_strings = [
            'Crates',
            'Planks',
            'Steel',
            'Wood',
            'Machinery',
            'YETI',
        ]
    elif template_amendment_code == 'J':
        cargo_strings = [
            'Oil',
            'Standard',
        ]
    elif template_amendment_code == 'K':
        cargo_strings = [
            'Oil',
            'Standard',
            'Rubber',
            'Water',
        ]
    elif template_amendment_code == 'L':
        cargo_strings = [
            'Coal',
            'Grain',
            'Ore',
            'Wood',
            'Gray',
            'Sand',
            'Crates',
        ]
    elif template_amendment_code == 'M':
        cargo_strings = [
            'Livestock',
            'Reefer',
            'Standard',
        ]
    elif template_amendment_code == 'N':
        cargo_strings = [
            'Coal',
            'Grain',
            'Ore',
            'Wood',
            'Sand',
            'Gray',
        ]
    elif template_amendment_code == 'O':
        cargo_strings = [
            'Crates',
            'Cars',
            'Machinery',
            'Steel',
            'YETI'
        ]
    elif template_amendment_code == 'P':
        cargo_strings = [
            'Livestock',
            'Reefer',
            'Standard',
        ]
    elif template_amendment_code == 'Q':
        cargo_strings = [
            'Coal',
            'Grain',
            'Ore',
            'Wood',
            'Gray',
            'Sand',
            'Fruit'
        ]

    # endregion

    has_loading_states = template_amendment_code in [
        'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']
    has_driving_states = template_amendment_code in ['L', 'N', 'Q']
    has_reverse_state = template_amendment_code in ['S']

    cargo_with_driving_state = ['grain']
    states = {1: 1}
    if has_loading_states or has_reverse_state:
        states = {1: 1, 2: 32, 3: 64}
        direction_states = {1: "Normal", 2: "Forward", 3: "Reverse"}
        # This is a total clusterf.k - so basically some of the wagons have a 'Driving State' (S4)...
        # BUT ONLY for GRAIN
        if has_driving_states:
            states = {1: 1, 2: 32, 3: 64, 4: 96}

    for cargo_string in cargo_strings:
        cargo_string = cargo_string.lower()
        cargo_string_is_dummy = cargo_string == 'dummy'
        if not cargo_string_is_dummy:
            nml_code.append(f"\n// {cargo_string}")

        # 2. Sprite Generation Loop (Liveries 1-4)
        for livery_num, x_coord in liveries.items():

            created_sprites = []

            for state_num, y_coord in states.items():
                if state_num > 3 and cargo_string not in cargo_with_driving_state:
                    # We cut the loop here if it's not a real 'Driving State' situation
                    continue

                s_suffix: str = ""
                s_suffix += f"{cargo_string}" if not cargo_string_is_dummy else ""
                s_suffix += f"{'_' if not cargo_string_is_dummy else ''}L{livery_num}"
                s_suffix += f"_s{state_num}" if has_loading_states else ""
                s_suffix += f"_dt_{direction_states.get(state_num, '')}" if has_reverse_state else ""

                comment = f"Livery {livery_num}"
                comment += f" - Loading State {state_num}" if has_loading_states else ""
                comment += f" - {direction_states.get(state_num, '')}" if has_reverse_state else ""
                comment += f" - {cargo_string}" if not cargo_string_is_dummy else ""

                if cargo_string_is_dummy or has_reverse_state:
                    nml_code.append(get_spriteset(vid=vid,
                                                  gfx_path=gfx_path,
                                                  comment_type=comment,
                                                  template_name_amendment="2cc_wagons",
                                                  template_x=x_coord,
                                                  template_y=y_coord,
                                                  spritename_suffix=s_suffix))

                else:
                    nml_code.append(get_spriteset(vid=vid,
                                                  gfx_path=f"{gfx_path[:-4]}_{cargo_string}.png",
                                                  comment_type=comment,
                                                  template_name_amendment="2cc_wagons",
                                                  template_x=x_coord,
                                                  template_y=y_coord,
                                                  spritename_suffix=s_suffix))

                sprite_name = f"spriteset_{vid}_{s_suffix}"
                created_sprites.append(sprite_name)

            # Spritegroups
            group_block = get_spritegroup_with_loading_states(
                vid=vid,
                livery_num=livery_num,
                created_sprites=created_sprites,
                cargo_string=cargo_string,
                cargo_string_is_dummy=cargo_string_is_dummy,
                has_loading_states=has_loading_states,
                has_driving_states=has_driving_states,
                cargo_with_driving_state=cargo_with_driving_state
            )
            nml_code.append(group_block)

        # 3. Livery Selector (Random Switch)
        if template_amendment_code != 'S':
            selector_name = f"switch_{vid}_livery" if cargo_string_is_dummy else f"switch_{vid}_{cargo_string}_livery"
            nml_code.append(get_random_livery_selector(
                vid=vid, cargo_string=cargo_string,
                selector_name=selector_name,
                list_length=4,
                cargo_string_is_dummy=cargo_string_is_dummy, has_loading_states=has_loading_states))

    if template_amendment_code == 'C':
        # 3. Livery Selector (Random Switch) - always 'Goods'
        nml_code.append(f"\n// Goods have multiple liveries")
        nml_code.append(f"""
                       random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_standard_livery;
	3: switch_{vid}_reefer_livery;
}}""")

        nml_code.append(f"\n// Random Goods Livery Selector")
        nml_code.append(f"""
        switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
        LVST: switch_{vid}_livestock_livery;
        GOOD: switch_{vid}_goods_livery;
        VALU: switch_{vid}_armoured_livery;
        FOOD: switch_{vid}_reefer_livery;
        GOLD: switch_{vid}_armoured_livery;
        FRUT: switch_{vid}_reefer_livery;
        DIAM: switch_{vid}_armoured_livery;
        FZDR: switch_{vid}_reefer_livery;
        BEER: switch_{vid}_reefer_livery;
        FISH: switch_{vid}_reefer_livery;
        // GRAI, PAPR, WHEA, MAIZ, SUGR, TOYS, BATT, BUBL, BDMT, BRCK, CERA, CERE, COPR, ENSP,
        // FERT, FMSP, GLAS, JAVA, MNSP, OLSD, POTA, RCYC, SGBT, SGCN, SULP, VEHI, WOOL
        switch_{vid}_standard_livery;
}}""")

    elif template_amendment_code == 'E':
        nml_code.append(f"""
                       random_switch(FEAT_TRAINS, SELF, switch_{vid}_supplies_livery) {{
	1: switch_{vid}_crates_livery;
	1: switch_{vid}_planks_livery;
	1: switch_{vid}_steel_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	STEL: switch_{vid}_steel_livery;
	BDMT: switch_{vid}_supplies_livery;
	MNSP: switch_{vid}_supplies_livery;
	WDPR: switch_{vid}_planks_livery;
    // Goods, Paper
	switch_{vid}_crates_livery;
}}""")

    elif template_amendment_code == 'F':
        nml_code.append(f"""
// Goods have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_container_livery;
	2: switch_{vid}_refrigerated_livery;
	1: switch_{vid}_tanktainer_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	GOOD: switch_{vid}_goods_livery;
	FOOD: switch_{vid}_refrigerated_livery;
	RUBR: switch_{vid}_tanktainer_livery;
	FRUT: switch_{vid}_refrigerated_livery;
	WATR: switch_{vid}_tanktainer_livery;
	COLA: switch_{vid}_tanktainer_livery;
	PLST: switch_{vid}_tanktainer_livery;
	FZDR: switch_{vid}_refrigerated_livery;
	BEER: switch_{vid}_tanktainer_livery;
	DYES: switch_{vid}_tanktainer_livery;
	FISH: switch_{vid}_refrigerated_livery;
	PETR: switch_{vid}_tanktainer_livery;
	PLAS: switch_{vid}_tanktainer_livery;
	RFPR: switch_{vid}_tanktainer_livery;
	switch_{vid}_container_livery;
}}""")

    elif template_amendment_code == 'G':
        nml_code.append(f"""

// Goods have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_container_livery;
	3: switch_{vid}_refrigerated_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	GOOD: switch_{vid}_goods_livery;
	FOOD: switch_{vid}_refrigerated_livery;
	FRUT: switch_{vid}_refrigerated_livery;
	FZDR: switch_{vid}_refrigerated_livery;
	FISH: switch_{vid}_refrigerated_livery;
    // PAPR, TOYS, BATT, SWET, BUBL, BDMT, BRCK, CERA, CERE, COPR, ENSP, FERT,
    // FICR, FMSP, GLAS, JAVA, MNSP, RCYC, WDPR, WOOL, URAN
	switch_{vid}_container_livery;
}}""")

    elif template_amendment_code == 'H':
        nml_code.append(f"""
        switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	COAL: switch_{vid}_coal_livery;
	CLAY: switch_{vid}_gray_livery;
	CMNT: switch_{vid}_gray_livery;
	GRVL: switch_{vid}_sand_livery;
	LIME: switch_{vid}_sand_livery;
	SAND: switch_{vid}_sand_livery;
	SGBT: switch_{vid}_sand_livery; // Use Sand livery for Sugar Beets
	switch_{vid}_ore_livery; // IORE, CORE, AORE
}}""")

    elif template_amendment_code == 'I':
        nml_code.append(f"""

// Goods and Engineering Supplies have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_crates_livery;
	3: switch_{vid}_machinery_livery;
}}

// Building materials can be planks or steel rolls
random_switch(FEAT_TRAINS, SELF, switch_{vid}_building_materials_livery) {{
	1: switch_{vid}_planks_livery;
	1: switch_{vid}_steel_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	GOOD: switch_{vid}_goods_livery;
	WOOD: switch_{vid}_wood_livery;
	STEL: switch_{vid}_steel_livery;
	BDMT: switch_{vid}_building_materials_livery;
	ENSP: switch_{vid}_goods_livery;
	WDPR: switch_{vid}_planks_livery;
	YETI: switch_{vid}_yeti_livery;
	YETY: switch_{vid}_yeti_livery;
    // TOYS, BATT, SWET, BUBL, FZDR, BRCK, CERA, COPR, FICR, FMSP, JAVA, MNSP
	switch_{vid}_crates_livery;
}}""")

    elif template_amendment_code == 'J':
        nml_code.append(f"""
random_switch(FEAT_TRAINS, SELF, switch_{vid}_oil_livery_selection) {{
	7: switch_{vid}_oil_livery;
	3: switch_{vid}_standard_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	OIL_: switch_{vid}_oil_livery_selection;
	PETR: switch_{vid}_oil_livery_selection;
	RFPR: switch_{vid}_oil_livery_selection;
    // GOOD, RUBR, WATR, COLA, PLST, BEER, DYES, MILK, PLAS
	switch_{vid}_standard_livery;
}}
""")

    elif template_amendment_code == 'K':
        nml_code.append(f"""


// Goods can have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	1: switch_{vid}_oil_livery;
	1: switch_{vid}_rubber_livery;
	1: switch_{vid}_water_livery;
}}

// Plastic can have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_plastic_livery) {{
	1: switch_{vid}_oil_livery;
	1: switch_{vid}_rubber_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	OIL_: switch_{vid}_oil_livery;
	GOOD: switch_{vid}_goods_livery;
	RUBR: switch_{vid}_rubber_livery;
	PLST: switch_{vid}_plastic_livery;
	PETR: switch_{vid}_oil_livery;
	PLAS: switch_{vid}_plastic_livery;
	RFPR: switch_{vid}_oil_livery;
	switch_{vid}_water_livery; // WATR, COLA, BEER, DYES, MILK
}}
""")

    elif template_amendment_code == 'L':
        nml_code.append(f"""

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	COAL: switch_{vid}_coal_livery;
	IORE: switch_{vid}_ore_livery;
	FRUT: switch_{vid}_crates_livery;
	CORE: switch_{vid}_ore_livery;
	WOOD: switch_{vid}_wood_livery;
	SUGR: switch_{vid}_crates_livery;
	CTCD: switch_{vid}_crates_livery;
	BUBL: switch_{vid}_gray_livery;
	AORE: switch_{vid}_ore_livery;
	CERE: switch_{vid}_crates_livery;
	CLAY: switch_{vid}_gray_livery;
	CMNT: switch_{vid}_gray_livery;
	GRVL: switch_{vid}_sand_livery;
	LIME: switch_{vid}_sand_livery;
	OLSD: switch_{vid}_crates_livery;
	POTA: switch_{vid}_wood_livery; // Potash is light brown-ish, so uses the Wood livery
	SAND: switch_{vid}_sand_livery;
	SCMT: switch_{vid}_gray_livery;
    // GRAI, MAIZ, TOFF
	switch_{vid}_grain_livery;
}}""")

    elif template_amendment_code == 'M':
        nml_code.append(f"""
// Goods have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_standard_livery;
	3: switch_{vid}_reefer_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	LVST: switch_{vid}_livestock_livery;
	GOOD: switch_{vid}_goods_livery;
	VALU: switch_{vid}_goods_livery;
	FOOD: switch_{vid}_reefer_livery;
	GOLD: switch_{vid}_goods_livery;
	FRUT: switch_{vid}_reefer_livery;
	DIAM: switch_{vid}_goods_livery;
	FZDR: switch_{vid}_reefer_livery;
	BEER: switch_{vid}_reefer_livery;
	FISH: switch_{vid}_reefer_livery;
    // GRAI, PAPR, WHEA, MAIZ, SUGR, TOYS, BATT, BUBL, BDMT, BRCK, CERA, CERE, COPR, ENSP, FERT, FMSP, GLAS, JAVA, MNSP, OLSD, POTA, RCYC, SGBT, SGCN, SULP, VEHI, WOOL
	switch_{vid}_standard_livery;
}}""")

    elif template_amendment_code == 'N':
        nml_code.append(f"""
                       switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	COAL: switch_{vid}_coal_livery;
	IORE: switch_{vid}_ore_livery;
	CORE: switch_{vid}_ore_livery;
	WOOD: switch_{vid}_wood_livery;
	SUGR: switch_{vid}_sand_livery;
	TOFF: switch_{vid}_sand_livery;
	CTCD: switch_{vid}_sand_livery;
	AORE: switch_{vid}_ore_livery;
	CERE: switch_{vid}_sand_livery;
	CLAY: switch_{vid}_gray_livery;
	CMNT: switch_{vid}_gray_livery;
	GRVL: switch_{vid}_sand_livery;
	LIME: switch_{vid}_sand_livery;
	POTA: switch_{vid}_wood_livery;
	SAND: switch_{vid}_sand_livery;
	SCMT: switch_{vid}_gray_livery;
	WDPR: switch_{vid}_wood_livery;
	switch_{vid}_grain_livery;
}}""")

    elif template_amendment_code == 'O':
        nml_code.append(f"""
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_crates_livery;
	2: switch_{vid}_cars_livery;
	1: switch_{vid}_machinery_livery;
}}

random_switch(FEAT_TRAINS, SELF, switch_{vid}_supplies_livery) {{
	7: switch_{vid}_crates_livery;
	3: switch_{vid}_machinery_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	GOOD: switch_{vid}_goods_livery;
	STEL: switch_{vid}_steel_livery;
	BDMT: switch_{vid}_goods_livery;
	ENSP: switch_{vid}_supplies_livery;
	FMSP: switch_{vid}_supplies_livery;
	VEHI: switch_{vid}_cars_livery;
	YETI: switch_{vid}_yeti_livery;
	YETY: switch_{vid}_yeti_livery;
	switch_{vid}_crates_livery;
}}
""")

    elif template_amendment_code == 'P':
        nml_code.append(f"""
// Goods have multiple liveries
random_switch(FEAT_TRAINS, SELF, switch_{vid}_goods_livery) {{
	7: switch_{vid}_standard_livery;
	3: switch_{vid}_reefer_livery;
}}

switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	LVST: switch_{vid}_livestock_livery;
	GOOD: switch_{vid}_goods_livery;
	VALU: switch_{vid}_goods_livery;
	FOOD: switch_{vid}_reefer_livery;
	GOLD: switch_{vid}_goods_livery;
	FRUT: switch_{vid}_reefer_livery;
	DIAM: switch_{vid}_goods_livery;
	FZDR: switch_{vid}_reefer_livery;
	BEER: switch_{vid}_reefer_livery;
	FISH: switch_{vid}_reefer_livery;
    // GRAI, PAPR, WHEA, MAIZ, SUGR, TOYS, BATT, BUBL, BDMT, BRCK, CERA, CERE, COPR, ENSP, FERT, FMSP, GLAS, JAVA, MNSP, OLSD, POTA, RCYC, SGBT, SGCN, SULP, VEHI, WOOL
	switch_{vid}_standard_livery;
}}""")

    elif template_amendment_code == 'Q':
        nml_code.append(f"""
switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_type_in_veh) {{
	COAL: switch_{vid}_coal_livery;
	IORE: switch_{vid}_ore_livery;
	FRUT: switch_{vid}_fruit_livery;
	CORE: switch_{vid}_ore_livery;
	WOOD: switch_{vid}_wood_livery;
	SUGR: switch_{vid}_fruit_livery;
	CTCD: switch_{vid}_fruit_livery;
	BUBL: switch_{vid}_gray_livery;
	AORE: switch_{vid}_ore_livery;
	CERE: switch_{vid}_fruit_livery;
	CLAY: switch_{vid}_gray_livery;
	CMNT: switch_{vid}_gray_livery;
	GRVL: switch_{vid}_sand_livery;
	LIME: switch_{vid}_sand_livery;
	OLSD: switch_{vid}_fruit_livery;
	POTA: switch_{vid}_wood_livery; // Potash is light brown-ish, so uses the Wood livery
	SAND: switch_{vid}_sand_livery;
	SCMT: switch_{vid}_gray_livery;
    // GRAI, MAIZ, TOFF
	switch_{vid}_grain_livery;
}}
""")

    elif template_amendment_code == 'S':
        selector_name = f"switch_{vid}_livery" if cargo_string_is_dummy else f"switch_{vid}_{cargo_string}_livery"

        for _, direction_state in direction_states.items():
            nml_code.append(get_random_livery_selector(
                vid=vid,
                cargo_string=direction_state,
                selector_name=f"{selector_name}_dt_{direction_state}",
                list_length=4,
                cargo_string_is_dummy=cargo_string_is_dummy,
                has_loading_states=has_loading_states,
                manual_suffix=f"dt_{direction_state}"
            ))

        nml_code.append(f"""
// Driving backwards switch
switch(FEAT_TRAINS, PARENT, switch_{vid}_direction, train_is_driving_backwards) {{
    1: switch_{vid}_livery_dt_forward;
    switch_{vid}_livery_dt_reverse;
}}

// Consist position switch
switch(FEAT_TRAINS, SELF, switch_{vid}_position, position_in_consist_from_end) {{
    0: switch_{vid}_direction;
    switch_{vid}_livery_dt_normal;
}}
""")

    return "\n".join(nml_code)


def get_tpl_16(vid, gfx_path, row, template_amendment_code):
    """
    12-Length Vehicles(TPL_16): param template_amendment_code:
        A -> Generic 12L (articulated)
        B -> Turbobus only
    """

    if template_amendment_code == "A":
        purchase_y = 128
    elif template_amendment_code == "B":
        purchase_y = 64

    engine_amendment = "engine"

    extra_comment = """
//// This vehicle uses the template for length 12.
//// The vehicle is built with 3 pieces of length 8+4
//// The middle part gets the graphics, the other parts are left blank
"""
    nml_code = []
    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path,
                                 template_suffix=None, purchase_x=1, purchase_y=purchase_y))
    nml_code.append(get_vehicle(vid=vid, gfx_path=gfx_path,
                                title_comment="engine", template_suffix="_2cc_L12",
                                use_comment_as_spritename_suffix=True,
                                vehicle_x=1, vehicle_y=1,
                                extra_comment=extra_comment))

    nml_code.append(get_switch_position(
        vid=vid, position_in_vehid_chain=2,
        first_item_task="spriteset",
        second_item_task="empty",
        first_item_word=engine_amendment,
        second_item_word=""))

    if template_amendment_code == "A":
        nml_code.append(get_visual_effect_on_odd_even_position(
            vid=vid, position_in_vehid_chain=2))

    nml_code.append(get_switch_length(vid=vid, row=row))

    nml_code.append(get_articulated_return(vid=vid))

    return "\n".join(nml_code)


def get_tpl_17(vid, gfx_path, row, template_amendment_code):
    """
    Normal length vehicles with front and back parts(TPL_17)

    :param template_amendment_code:
        A -> Normal Front/Back (articulated)
        B -> A/B Front/Back (not articulated?)
        C -> Front 1/2; Middle, Back 1/2 (articulated)
        D -> Front 1/2; Middle 1/2, Back 1/2 (articulated)
        E -> Front 1/2; No Middle, Back 1/2 (articulated)

    """
    nml_code = []

    if template_amendment_code == "A":
        purchase_y_coord = 64
    elif template_amendment_code in ["B", "E"]:
        purchase_y_coord = 128
    elif template_amendment_code == "C":
        purchase_y_coord = 160
    elif template_amendment_code == "D":
        purchase_y_coord = 192

    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path,
                                 purchase_x=1, purchase_y=purchase_y_coord))

    # 2. Coordinate Mapping
    if template_amendment_code == "A":
        all_sprites = {
            "front": (1, 1),
            "back": (1, 32),
        }
    elif template_amendment_code == "B":
        all_sprites = {
            "A_Front": (1, 1),
            "B_Front": (1, 32),
            # Bit of an obscure order here but it's legacy.
            "B_Back": (1, 64),
            "A_Back": (1, 96),
        }
    elif template_amendment_code == "C":
        all_sprites = {
            "front1": (1, 1),
            "front2": (1, 32),
            "middle": (1, 64),
            "back1": (1, 96),
            "back2": (1, 128),
        }
    elif template_amendment_code == "D":
        all_sprites = {
            "front1": (1, 1),
            "front2": (1, 32),
            "middle1": (1, 64),
            "middle2": (1, 96),
            "back1": (1, 128),
            "back2": (1, 160),
        }
    elif template_amendment_code == "E":
        all_sprites = {
            # yes these have an underline...legacy stuff
            "front_1": (1, 1),
            "front_2": (1, 32),
            "back_1": (1, 64),
            "back_2": (1, 96),
        }

    # 3. Sprite & Group Generation
    for name, coords in all_sprites.items():
        nml_code.append(get_vehicle(vid=vid, gfx_path=gfx_path,
                                    title_comment=name,
                                    use_comment_as_spritename_suffix=True,
                                    dont_show_main_comment=True,
                                    template_suffix="2cc_engines_general",
                                    vehicle_x=coords[0], vehicle_y=coords[1]))

    if template_amendment_code == "A":
        nml_code.append(get_switch_position(
            vid=vid, position_in_vehid_chain=2,
            first_item_task="spriteset",
            second_item_task="spriteset",
            first_item_word="front",
            second_item_word="back"))

        nml_code.append(get_visual_effect_on_odd_even_position(
            vid=vid, position_in_vehid_chain=2))

        nml_code.append(get_articulated_return(vid=vid, endvalue=1))

    elif template_amendment_code == "B":
        # Yes the order of things here is a little odd.
        nml_code.append(get_switch_position(vid=vid, position_in_vehid_chain=4,
                                            first_item_location=1,
                                            second_item_location=2,
                                            third_item_location=3,
                                            fourth_item_location=None,
                                            first_item_task="spriteset",
                                            second_item_task="spriteset",
                                            third_item_task="spriteset",
                                            first_item_word="B_Front",
                                            second_item_word="B_Back",
                                            third_item_word="A_Back",
                                            fourth_item_word="A_Front",
                                            fourth_item_task="spriteset",
                                            ))

        nml_code.append(get_visual_effect_on_odd_even_position_with_range(
            vid=vid, range_start=2, range_end=3, reverse=True, position_in_vehid_chain=4))

    elif template_amendment_code in ["C", "D", "E"]:
        nml_code.append(get_motion_counter(
            vid=vid, switch_name_suffix="animation_front",
            state_0="front1" if template_amendment_code != "E" else "front_1",  # underline!
            state_default="front2"if template_amendment_code != "E" else "front_2",  # underline!
        ))
        if template_amendment_code == "D":
            nml_code.append(get_motion_counter(
                vid=vid,
                switch_name_suffix="animation_middle",
                state_0="middle1",
                state_default="middle2",
            ))
        nml_code.append(get_motion_counter(
            vid=vid,
            switch_name_suffix="animation_back",
            state_0="back1" if template_amendment_code != "E" else "back_1",  # underline!
            state_default="back2" if template_amendment_code != "E" else "back_2",  # underline!
        ))

        if template_amendment_code == "C":
            nml_code.append(get_switch_position(
                vid=vid, position_in_vehid_chain=3,
                first_item_location=0, first_item_task="switch", first_item_word="animation_front",
                second_item_location=1, second_item_task="spriteset", second_item_word="middle",
                third_item_location=None, third_item_task="switch", third_item_word="animation_back")

            )
        elif template_amendment_code == "D":
            nml_code.append(get_switch_position(
                vid=vid, position_in_vehid_chain=3,
                first_item_location=0, first_item_task="switch", first_item_word="animation_front",
                second_item_location=1, second_item_task="switch", second_item_word="animation_middle",
                third_item_location=None, third_item_task="switch", third_item_word="animation_back",
            ))

        elif template_amendment_code == "E":
            nml_code.append(get_switch_position(
                vid=vid, position_in_vehid_chain=2,
                first_item_location=0, first_item_task="switch", first_item_word="animation_front",
                second_item_location=None, second_item_task="switch", second_item_word="animation_back",
            ))

        if template_amendment_code == "C":
            nml_code.append(
                get_visual_effect_on_odd_even_position(vid=vid, position_in_vehid_chain=3))
            nml_code.append(
                get_switch_length(vid=vid, row=row, first_deduct_from_position_in_vehid_chain_location=1, first_position_in_vehid_chain=3))
            nml_code.append(get_articulated_return(vid=vid, endvalue=2))
        elif template_amendment_code == "D":
            nml_code.append(
                get_visual_effect_on_odd_even_position(vid=vid, position_in_vehid_chain=3, deduct_from_position_for_first_return=3))
            nml_code.append(
                get_switch_length(vid=vid, row=row, first_deduct_from_position_in_vehid_chain_location=2, first_position_in_vehid_chain=3))
            nml_code.append(get_articulated_return(vid=vid, endvalue=2))
        elif template_amendment_code == "E":
            nml_code.append(
                get_visual_effect_on_odd_even_position(vid=vid, position_in_vehid_chain=2, deduct_from_position_for_first_return=2))
            nml_code.append(
                get_switch_length(vid=vid, row=row, first_deduct_from_position_in_vehid_chain_location=2, first_position_in_vehid_chain=2))
            nml_code.append(get_articulated_return(vid=vid, endvalue=1))

    return "\n".join(nml_code)


def get_tpl_25(vid, gfx_path, row, template_amendment_code):
    """
    Automation for the Superheavy Wagon(TPL_25).
    Handles static Front/Back/Empty parts and 4 liveried middle sections.

    :param vid: The vehicle id
    :param gfx_path: The png path
    :param row: The row
    :param template_amendment_code: A-> Superheavy Wagon (articulated); no others atm.
    """

    nml_code = []

    # 1. Header & Purchase
    nml_code.append(get_purchase(vid=vid,
                                 gfx_path=f"{gfx_path[:-4]}_Purchase.png",
                                 template_suffix="_wagon",
                                 purchase_x=1, purchase_y=1))

    # 2. Coordinate Mapping
    all_sprites = {
        "front": (1, 1),
        "back": (1, 64),
        "middle_empty": (1, 32),
        "middle_l1": (1, 126),
        "middle_l2": (179, 126),
        "middle_l3": (357, 126),
        "middle_l4": (535, 126)
    }

    # 3. Sprite & Group Generation
    for sprite_name, coords in all_sprites.items():
        # Check if it's a livery (ends with L1, L2, etc)
        is_livery = re.search(r'l\d+$', sprite_name)

        if not is_livery:
            # Static parts (front, back, middle_empty)
            nml_code.append(get_vehicle(vid=vid,
                                        gfx_path=gfx_path,
                                        title_comment=sprite_name,
                                        use_comment_as_spritename_suffix=True,
                                        dont_show_main_comment=True,
                                        template_suffix="2cc_wagons",
                                        vehicle_x=coords[0], vehicle_y=coords[1]))

        else:
            # 1. Generate the spriteset for the current livery (e.g., middle_L1)
            nml_code.append(get_vehicle(vid=vid,
                                        gfx_path=gfx_path,
                                        title_comment=sprite_name,
                                        use_comment_as_spritename_suffix=True,
                                        dont_show_main_comment=True,
                                        template_suffix="2cc_wagons",
                                        vehicle_x=coords[0], vehicle_y=coords[1]))

            # 2. Build the specific list for THIS livery's spritegroup
            # We want: [spriteset_mu_vid_middle_empty, spriteset_mu_vid_middle_LX, spriteset_mu_vid_middle_LX]

            # The 'middle_empty' name is constant
            empty_name = f"spriteset_{vid}_middle_empty"
            # The current livery name (e.g., spriteset_mu_vid_middle_L1)
            current_livery_name = f"spriteset_{vid}_{sprite_name}"

            # This list will be used by your helper method to create the [First, Last, Last] pattern
            # Or you can pass them directly if your helper supports it.
            # Here we provide the two unique pieces needed:
            # Twice.
            current_group_sprites = [empty_name,
                                     current_livery_name, current_livery_name]

            # 3. Call your spritegroup helper
            nml_code.append(get_spritegroup_without_loading_states(
                vid=vid,
                livery_num=sprite_name[-1],  # extracts '1' from 'middle_L1'
                created_sprites=current_group_sprites,
                # group_name = f"spritegroup_{vid}_{cargo_string}_l{livery_num}"
                cargo_string="middle",
                cargo_string_is_dummy=False
            ))

    # 4. Final Random Switch
    nml_code.append(get_random_livery_selector(vid=vid,
                                               selector_name=f"switch_{vid}_middle_livery",
                                               # Yeah that's not a cargo but alas.
                                               cargo_string="middle",
                                               cargo_string_is_dummy=False,
                                               has_loading_states=True,  # Force True
                                               list_length=4
                                               ))

    nml_code.append(get_switch_vid(vid=vid, position_in_vehid_chain=3,
                                   first_item_location=1, first_item_task="switch", first_item_word="middle_livery",
                                   second_item_location=2, second_item_task="spriteset", second_item_word="back",
                                   third_item_location=None, third_item_task="spriteset", third_item_word="front",
                                   ))

    nml_code.append(get_articulated_return(vid=vid, endvalue=2))

    return "\n".join(nml_code)


def get_tpl_32(vid, gfx_path, row, template_amendment_code):
    """
    10-Length Vehicles(TPL_32): param template_amendment_code:
        A -> No animation
        B -> With animation
        C -> B + Length
    """

    purchase_y = 128

    nml_code = []
    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path,
                                 purchase_x=1, purchase_y=purchase_y))

    extra_comment = f"""
//// This vehicle uses the template for length 10.
//// The vehicle is built with 3 pieces of length 3+4+3
//// The middle part gets the graphics, the other parts are left blank
"""

    vehicles = {"engine1": (1, 1), "engine2": (1, 64)}
    for name, coords in vehicles.items():
        nml_code.append(get_vehicle(vid=vid, gfx_path=gfx_path,
                                    title_comment=name,
                                    dont_show_main_comment=name != "engine1",
                                    template_suffix="_2cc_L12",
                                    use_comment_as_spritename_suffix=True,
                                    vehicle_x=coords[0], vehicle_y=coords[1],
                                    extra_comment=extra_comment if name == "engine1" else ""))

    if template_amendment_code in ['B', 'C']:
        nml_code.append(get_motion_counter(
            vid=vid, switch_name_suffix="animation", state_0="engine1", state_default="engine2"))

    if template_amendment_code == 'A':
        nml_code.append(get_switch_position(
            vid=vid, position_in_vehid_chain=4,
            first_item_task="spriteset",
            first_item_word="engine1",
            first_item_location=0,
            second_item_task="spriteset",
            second_item_word="engine2",
            second_item_location=2,
            third_item_task="empty",
        ))

    elif template_amendment_code in ['B', 'C']:
        nml_code.append(get_switch_position(
            vid=vid, position_in_vehid_chain=2,
            first_item_task="switch",
            first_item_word="animation",
            first_item_location=0,
            second_item_task="empty",
            second_item_word=None
        ))

    if template_amendment_code == 'A':
        position_in_vehid_chain = 4
        deduct_from_position_for_first_return = 4
        deduct_from_position_for_second_return = 2
    elif template_amendment_code in ['B', 'C']:
        position_in_vehid_chain = 2
        deduct_from_position_for_first_return = 2

    nml_code.append(
        get_visual_effect_on_odd_even_position(vid=vid,
                                               position_in_vehid_chain=position_in_vehid_chain,
                                               deduct_from_position_for_first_return=deduct_from_position_for_first_return))
    if template_amendment_code in ['B', 'C']:
        nml_code.append(
            get_switch_length(vid=vid,
                              row=row,
                              first_deduct_from_position_in_vehid_chain_location=deduct_from_position_for_first_return,
                              first_position_in_vehid_chain=position_in_vehid_chain))

    if template_amendment_code == 'A':
        nml_code.append(
            get_switch_length(vid=vid,
                              row=row,
                              first_deduct_from_position_in_vehid_chain_location=deduct_from_position_for_first_return,
                              first_position_in_vehid_chain=position_in_vehid_chain,
                              second_deduct_from_position_in_vehid_chain_location=deduct_from_position_for_second_return,
                              second_position_in_vehid_chain=position_in_vehid_chain,
                              fallback_length_defined=f"{row['WAGON_LENGTH']}"))

    nml_code.append(f"""{get_articulated_return(
        vid=vid, endvalue=3 if template_amendment_code == 'A' else 1)}
""")

    return "\n".join(nml_code)


def get_tpl_42(vid, gfx_path, row, template_amendment_code):
    """
    This is for the CargoDMU

    :param template_amendment_code:
    -> A: CargoDMU
    -> B: Test
    """
    nml_code = []

    nml_code.append(get_purchase(vid=vid, gfx_path=gfx_path, template_suffix='dualheaded',
                    purchase_x=1, purchase_y=192))

    # Position base offsets (The "Starting Y" for each section)
    if template_amendment_code in ['A']:
        position_strings = {
            'Front': 0,    # Block 1 starts at 0 (we add 1 later)
            'Back': 64,   # Block 2 starts at 64
            'Middle': 128  # Block 3 starts at 128
        }
    elif template_amendment_code in ['B']:
        position_strings = {
            'Front E1': 0,    # Block 1 starts at 0 (we add 1 later)
            'Front E2': 64,   # Block 2 starts at 64
            'Back E1': 0,
            'Back E2': 64,
            'Trailer': 128  # Block 3 starts at 128
        }

    # 2. State X-offsets (Horizontal)
    states = {1: 1, 2: 178, 3: 356}

    if template_amendment_code == 'A':
        for position_string, position_base_y in position_strings.items():
            position_string_is_dummy = True if position_string == 'dummy' else False
            has_loading_states = True
            created_sprites = []

            nml_code.append(f"\n// {position_string}")

            # We use (livery_num - 1) * 32 to get 0 for L1 and 32 for L2
            for livery_num in [1, 2]:
                livery_offset = (livery_num - 1) * 32

                for state_num, x_coord in states.items():
                    calculated_y = position_base_y + \
                        livery_offset

                    final_y = position_base_y + livery_offset
                    if final_y == 0:
                        final_y = 1  # Force 1 for the very first row

                    s_suffix = ""
                    s_suffix += f"{position_string}" if not position_string_is_dummy else ""
                    s_suffix += f"{'_' if not position_string_is_dummy else ''}L{livery_num}"
                    s_suffix += f"_s{state_num}" if has_loading_states else ""
                    s_suffix = s_suffix.lower()

                    comment = ""
                    comment += f"{position_string.upper()}" if not position_string_is_dummy else "N/A"
                    comment += f" - Livery {livery_num}"
                    comment += f" - Loading State {state_num}" if has_loading_states else ""

                    nml_code.append(get_spriteset(
                        vid=vid,
                        gfx_path=gfx_path,
                        comment_type=comment,
                        template_name_amendment="2cc_engines_general",
                        template_x=x_coord,
                        template_y=calculated_y,
                        spritename_suffix=s_suffix
                    ))

                    sprite_name = f"spriteset_{vid}_{s_suffix}"
                    created_sprites.append(sprite_name.lower())

                # Spritegroups
                group_block = get_spritegroup_with_loading_states(
                    vid=vid,
                    livery_num=livery_num,
                    created_sprites=created_sprites,
                    cargo_string=position_string,
                    cargo_string_is_dummy=position_string_is_dummy,
                    has_loading_states=has_loading_states,
                    has_driving_states=False,
                    cargo_with_driving_state=[]
                )
                nml_code.append(group_block)

            # 3. Livery Selector (Random Switch)
            selector_name = f"switch_{vid}_livery" if position_string_is_dummy else f"switch_{vid}_{position_string}_livery"
            nml_code.append(get_random_livery_selector(
                vid=vid, cargo_string=position_string,
                selector_name=selector_name,
                list_length=2,
                cargo_string_is_dummy=position_string_is_dummy,
                has_loading_states=has_loading_states,
                first_chance=5))

        nml_code.append(get_switch_reversed(vid=vid,
                                            front_switch="Back_livery",
                                            front_task="switch",
                                            back_switch="Back_livery",
                                            back_task="switch",
                                            fallback_switch="Front_livery",
                                            fallback_task="switch"
                                            ))

    elif template_amendment_code == 'B':
        # 1. Define vertical blocks
        # Row 1: E1 Front, Row 2: E2 Front
        # Row 3: E1 Back, Row 4: E2 Back
        # Row 5: Trailer
        pos_offsets = {
            'engine1': 1,      # Row 1
            'engine2': 32,     # Row 2
            'engine1_rev': 64,  # Row 3
            'engine2_rev': 96,  # Row 4
            'trailer': 128     # Row 5
        }

        # 3. Create Spritegroups for each component
        for p_name, y_offset in pos_offsets.items():
            created_sprites = []
            for s_idx, x_offset in states.items():
                suffix = f"{p_name}_s{s_idx}"
                nml_code.append(get_spriteset(
                    vid=vid,
                    gfx_path=gfx_path,
                    comment_type=f"{p_name} State {s_idx}",
                    template_x=x_offset,
                    template_y=y_offset,
                    template_name_amendment="2cc_engines_general",
                    spritename_suffix=suffix
                ))
                created_sprites.append(f"spriteset_{vid}_{suffix}")

            # unique cargo_string avoids "already defined" errors
            nml_code.append(get_spritegroup_with_loading_states(
                vid=vid,
                livery_num=1,
                created_sprites=created_sprites,
                cargo_string=p_name,
                cargo_string_is_dummy=False,
                has_loading_states=True,
                has_driving_states=False))

        # 4. Consist Logic
        # We use 'position_in_consist' for the front and 'from_end' for the tail.
        # Note: 'engine1_rev_l1' etc. are the groups created by the loop above.
        nml_code.append(f"""
// 1. Rear-facing Wagon Logic (The "Reversed" Look)
// This handles the tail of the sandwich using Row 3 and Row 4 sprites.
switch(FEAT_TRAINS, SELF, switch_{vid}_check_back, position_in_consist_from_end) {{
    0: spritegroup_{vid}_engine1_rev_l1; // The actual tail cab (Pointing Backwards)
    1: spritegroup_{vid}_engine2_rev_l1; // The panto-car before the tail (Pointing Backwards)
    default: spritegroup_{vid}_trailer_l1;
}}

// 2. Front-facing Wagon Logic
// This handles the units immediately following the lead engine.
switch(FEAT_TRAINS, SELF, switch_{vid}_wagon_logic, position_in_consist) {{
    1: spritegroup_{vid}_engine2_l1; // Unit after front cab (Forward)
    default: switch_{vid}_check_back;
}}
""")

        # Add the articulated callback return
        nml_code.append(f"{get_articulated_return(vid=vid, endvalue=2)}")

    nml_code.append(get_xmu_power_switch_position_based(vid=vid))

    return "\n".join(nml_code)


def generate_graphics_pnml():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')

    # Reading sheets
    df_control = pd.read_excel(excel_path, sheet_name='control')
    df_properties = pd.read_excel(excel_path, sheet_name='properties')
    df_gfx_props = pd.read_excel(excel_path, sheet_name='graphics_properties')
    df_copyright = pd.read_excel(excel_path, sheet_name='copyright_text')

    # 2. Merge data to get a full view of each vehicle's needs
    # Join control (paths) with gfx_props (template IDs)
    df_master = (
        df_control[['VEHIDCODE', 'FILENAMES_EXPECTED', 'SAVE_TO']]
        .merge(df_properties[['VEHIDCODE', 'LENGTH', 'WAGON_LENGTH']], on='VEHIDCODE')
        .merge(df_gfx_props[['VEHIDCODE', 'PANTOGRAPH_POSITION', 'TEMPLATE_ID', 'TEMPLATE_AMENDMENT_CODE']], on='VEHIDCODE')
    )

    min_templateID = 1
    max_templateID = 42

    print(f"Starting generation for {len(df_master)} vehicles...")

    for _, row in df_master.iterrows():
        # Extract copyright header text
        copyright_header = df_copyright.columns[0] if not df_gfx_props.empty else ""
        template_id_int = int(row['TEMPLATE_ID'][-2:])

        if (min_templateID <= template_id_int <= max_templateID):
            save_path = row['SAVE_TO']
            expected_fn = row['FILENAMES_EXPECTED']

            nml_code = (get_tpl_controller(row, copyright_header))

            # 5. Save the file
            # ensure directories exist (e.g., src/Coaches/Gen1)
            full_output_dir = os.path.join(project_root, save_path)
            if not os.path.exists(full_output_dir):
                os.makedirs(full_output_dir)

            pnml_filename = f"{expected_fn}_graphics.pnml"
            with open(os.path.join(full_output_dir, pnml_filename), 'w', encoding='utf-8') as f:
                f.writelines(nml_code)

    print("Success: PNML graphics files generated based on Excel tables.")


if __name__ == "__main__":
    generate_graphics_pnml()
