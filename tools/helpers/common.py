def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)
