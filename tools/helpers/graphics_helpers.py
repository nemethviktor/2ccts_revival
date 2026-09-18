from functools import wraps
from typing import Literal, Optional


def scrub_nml_data(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        def clean(val):
            # 1. Handle Strings
            if isinstance(val, str):
                return val.replace(" ", "_").replace("-", "_").lower()

            if isinstance(val, list):
                # Recursively clean every item in the list
                return [clean(item) for item in val]

            return val

        # Clean all keyword arguments EXCEPT 'vid' and 'gfx_path'
        cleaned_kwargs = {k: (clean(v) if k != "extra_comment" else v) for k, v in kwargs.items()}

        # Clean positional arguments (if you use them)
        cleaned_args = [clean(a) for a in args]

        return func(*cleaned_args, **cleaned_kwargs)

    return wrapper


@scrub_nml_data
def get_visual_effect_and_powered(*, vid: str) -> str:
    """This is almost certainly not the one you're looking for."""
    if "steam_" in vid.lower() or "rbs_" in vid.lower():
        visual_effect_type = "STEAM"
    elif "diesel_" in vid.lower() or "dmu_" in vid.lower() or "rbd_" in vid.lower():
        visual_effect_type = "DIESEL"
    elif "electric_" in vid.lower() or "emu_" in vid.lower() or "rbe_" in vid.lower():
        visual_effect_type = "ELECTRIC"
    else:
        visual_effect_type = "PANIC"
    return visual_effect_type


@scrub_nml_data
def get_xmu_power_switch_position_based(
    *, vid: str, panto_pos: str = "ENDS", force_maglev_to_electric: bool = False
) -> str:
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
def get_switch_vid(
    *,
    vid: str,
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
    first_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
    second_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
    third_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
    fourth_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
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
        f"{main_task}(FEAT_TRAINS, SELF, {main_task}_{vid}, position_in_vehid_chain % {position_in_vehid_chain}) {{"
    )
    nml_code.append(f"\t{first_item_location}: {first_item_task}_{vid}_{first_item_word};")
    # Logic for the second item
    if second_item_task:
        if second_item_task != "empty":
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(f"\t{prefix}{second_item_task}_{vid}_{second_item_word};")
        else:
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if third_item_task:
        if third_item_task != "empty":
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(f"\t{prefix}{third_item_task}_{vid}_{third_item_word};")
        else:
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if fourth_item_task:
        if fourth_item_task != "empty":
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(f"\t{prefix}{fourth_item_task}_{vid}_{fourth_item_word};")
        else:
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    nml_code.append(f"}}")

    return "\n".join(nml_code)


@scrub_nml_data
def get_switch_powered_unpowered_sundry(*, vid: str) -> str:
    return f"""
    /// Livery switch for Passengers (pax)
switch(FEAT_TRAINS, SELF, switch_{vid}_middlepass_livery, 
    (vehicle_type_id == item_mu_mu_wagon_powered) || 
    (position_in_consist == 1) || 
    (position_in_consist == num_vehs_in_consist - 2)
) {{
    1: spriteset_{vid}_middlepass_l2; 
    spriteset_{vid}_middlepass_l1;
}}

/// Livery switch for Mail
switch(FEAT_TRAINS, SELF, switch_{vid}_middlemail_livery, 
    (vehicle_type_id == item_mu_mu_wagon_powered) || 
    (position_in_consist == 1) || 
    (position_in_consist == num_vehs_in_consist - 2)
) {{
    1: spriteset_{vid}_middlemail_l2; 
    spriteset_{vid}_middlemail_l1;
}}
"""


@scrub_nml_data
def get_switch_cargo_class(
    *,
    vid: str,
    task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]],
    fallback_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]],
    bitmask_label: str,
    spriteset_suffix: str,
    spriteset_suffix_fallback: str,
) -> str:
    nml_code = f"""
/// Graphics for the unit wagon based on cargo class
switch(FEAT_TRAINS, SELF, switch_{vid}_cargo_selection, cargo_classes){{
	bitmask({bitmask_label.upper()}): {task}_{vid}_{spriteset_suffix};
	{fallback_task}_{vid}_{spriteset_suffix_fallback};
}}"""

    return nml_code


@scrub_nml_data
def get_switch_length(
    *,
    vid: str,
    row,
) -> str:
    nml_code = []

    length_p1_head = int(float(row["LENGTH_P1_HEAD"]))
    length_p2 = int(float(row["LENGTH_P2"]))
    length_p3_wagon = int(float(row["LENGTH_P3_WAGON"]))

    nml_code.append(f"""
/// Length
switch(FEAT_TRAINS, SELF, switch_{vid}_length, position_in_vehid_chain % {3 if (length_p2 > 0 and length_p3_wagon > 0) else 2}) {{
    0: {length_p1_head};""")
    if length_p2 > 0:
        nml_code.append(f"""\t1: {length_p2};
\t{length_p3_wagon};
}}""")
    else:
        nml_code.append(f"""\t{length_p3_wagon};
}}""")

    return "\n".join(nml_code)


@scrub_nml_data
def get_switch_reversed(
    *,
    vid: str,
    front_switch: str,
    back_switch: str,
    fallback_switch: str,
    front_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]],
    back_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]],
    fallback_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]],
) -> str:
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
def get_switch_position(
    *,
    vid: str,
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
    first_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
    second_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
    third_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
    fourth_item_task: Optional[Literal["spriteset", "spritegroup", "switch", "empty"]] = None,
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
        f"{main_task}(FEAT_TRAINS, SELF, {main_task}_{vid}_position, position_in_vehid_chain % {position_in_vehid_chain}) {{"
    )
    nml_code.append(f"\t{first_item_location}: {first_item_task}_{vid}_{first_item_word};")
    # Logic for the second item
    if second_item_task:
        if second_item_task != "empty":
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(f"\t{prefix}{second_item_task}_{vid}_{second_item_word};")
        else:
            prefix = f"{second_item_location}: " if second_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if third_item_task:
        if third_item_task != "empty":
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(f"\t{prefix}{third_item_task}_{vid}_{third_item_word};")
        else:
            prefix = f"{third_item_location}: " if third_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    if fourth_item_task:
        if fourth_item_task != "empty":
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(f"\t{prefix}{fourth_item_task}_{vid}_{fourth_item_word};")
        else:
            prefix = f"{fourth_item_location}: " if fourth_item_location is not None else ""
            nml_code.append(f"\t{prefix}EMPTY_SPRITESET")  # no ";"
    nml_code.append(f"}}")

    return "\n".join(nml_code)


@scrub_nml_data
def get_switch_with_store(
    *,
    vid: str,
    store_value: int,
    switch_what: str,
    id_range: str,
    first_item_task: str,
    second_item_task: str,
    first_item_suffix: str,
    second_item_suffix: str,
) -> str:
    nml_code = f"""
switch(FEAT_TRAINS, SELF, switch_{vid}_{switch_what}, [STORE_TEMP({store_value}, 0x10F), var[0x61, 0, 0x0000FFFF, 0xC6]]) {{
	{id_range.upper()}: {first_item_task}_{vid}_{first_item_suffix};
	{second_item_task}_{vid}_{second_item_suffix};
}}"""

    return nml_code


@scrub_nml_data
def get_visual_effects_and_power_with_store(*, vid: str, store_value: int, id_range: str) -> str:
    visual_effect_type = get_visual_effect_and_powered(vid=vid)

    nml_code = f"""
switch(FEAT_TRAINS, SELF, switch_{vid}_visual_effect_and_powered_position, [STORE_TEMP({store_value}, 0x10F), var[0x61, 0, 0x0000FFFF, 0xC6]]) {{
	{id_range.upper()}: switch_{vid}_visual_effect_and_powered;
	visual_effect_and_powered(VISUAL_EFFECT_{visual_effect_type}, -3, DISABLE_WAGON_POWER);
}}"""

    return nml_code


@scrub_nml_data
def get_visual_effect_on_odd_even_position(
    *,
    vid: str,
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
def get_visual_effect_on_odd_even_position_with_range(
    *,
    vid: str,
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
def get_random_switch_visual_effect(
    *,
    vid: str,
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
def get_random_switch_visual_effect_w_dependent(
    *,
    vid: str,
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
