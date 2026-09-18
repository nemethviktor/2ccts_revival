def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def get_role(row) -> str:
    """Categorizes train vehicle roles based on specification, cargo, and performance rules.

    Expects row access via row['HEADER'] and pre-built lookup dictionaries.
    """
    veh_code = (str(row["VEHIDCODE"]) if row["VEHIDCODE"] is not None else "").lower()
    cargo = row["CARGODEF"]
    speed = int(row["SPEED"])
    loading_speed = int(row["LOADINGSPEED_VALUE"])
    head_cap = row.get("HEAD_CAPACITY", 0)
    dual_headed = is_true(row["DUAL_HEADED"])
    weight = int(row.get("WEIGHT", 0))
    power = int(row.get("POWER", 0))
    engine_class = row["ENGINE_CLASS"]

    # --- Rule 1: Sundry Vehicles ---
    # Search for "_Powered" or "_Unpowered" substring in VEHIDCODE
    if "_powered" in veh_code or "_unpowered" in veh_code:
        return "Powered/Unpowered Sundry"

    # --- Rule 2: Wagons & Coaches (Lookup in CONTROL table) ---
    is_wagon_or_coach = is_true(row["IS_WAGON_OR_COACH"])
    if is_wagon_or_coach is True:
        if cargo in ("PASSENGERS", "PASSENGERS_ONLY"):
            if speed >= 230:
                return "Coach (HS)"
            elif speed >= 160:
                return "Coach (Express)"
            elif loading_speed >= 40:
                return "Coach (Commuter)"
            else:
                return "Coach (Regional)"
        elif cargo == "MAIL_ONLY":
            return "Coach (Mail)"
        else:
            return "Wagon"

    # --- Rule 3: Metro ---
    # Matches 'MTRO' in code, 'METRO' in control category lookup, or high loading speed
    veh_category = row["VEHID_ID_CATEGORY"].replace("ID_RANGE_", "")
    if "mtro" in veh_code or "METRO" in str(veh_category) or loading_speed >= 120:
        return "Metro"

    # --- Rule 4: Heavy Freight ---
    effective_weight = weight * (1 + dual_headed)
    if effective_weight > 140 and head_cap == 0 and speed < 140:
        return "Heavy Freight"

    # --- Rule 5: Shunting ---
    effective_power = power * (1 + dual_headed)
    if speed <= 60 and effective_power < 1200 and head_cap == 0:
        return "Shunting"

    # Track gauge lookup helper for high-speed rules
    gauge = row["GAUGE"]

    # --- Rule 6: Ultra-High-Speed ---
    uhs_standard_gauge = gauge in ("NORMAL", "BROAD", "MAGLEV") and speed >= 300
    uhs_narrow_gauge = gauge == "NARROW" and speed >= 160

    if uhs_standard_gauge or uhs_narrow_gauge:
        if head_cap == 0:
            return "Ultra-High-Speed (Universal)"
        elif cargo in ("PASSENGERS", "PASSENGERS_ONLY"):
            return "Ultra-High-Speed (Pax)"
        else:
            return "Freight"

    # --- Rule 7: Express ---
    exp_standard_gauge = gauge in ("NORMAL", "BROAD", "MAGLEV") and speed >= 160
    exp_narrow_gauge = gauge == "NARROW" and speed >= 100
    exp_steam = engine_class == "STEAM" and speed >= 120

    if exp_standard_gauge or exp_narrow_gauge or exp_steam:
        if head_cap == 0:
            return "Express"
        elif cargo in ("PASSENGERS", "PASSENGERS_ONLY"):
            return "Express Passenger"
        else:
            return "Freight"

    # --- Rule 8: Commuter / Urban / Light Freight ---
    if loading_speed >= 40 or (head_cap > 0 and speed < 120):
        if cargo in ("PASSENGERS", "PASSENGERS_ONLY"):
            return "Commuter/Urban"
        elif cargo == "MAIL_ONLY":
            return "Express Mail / Parcel"
        else:
            return "Light Freight"

    # --- Rule 9: Default Fallback Logic ---
    if head_cap > 0:
        if cargo in ("PASSENGERS", "PASSENGERS_ONLY"):
            return "Regional Passenger"
        else:
            return "Freight"

    if head_cap == 0 and effective_power < 1800 and speed <= 100:
        return "Light Freight"

    if head_cap == 0 and effective_power >= 2500:
        return "Freight"

    return "Universal"
