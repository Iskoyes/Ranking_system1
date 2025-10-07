def time_to_seconds(time_str):
    """Convert a time string to seconds as float.

    Supports:
    - seconds as a number string, comma or dot decimal (e.g., "76,74" or "76.74")
    - mm:ss,fraction or mm:ss.fraction (fraction length determines precision)
    """
    if time_str is None:
        raise ValueError("time_str is required")
    s = str(time_str).strip()
    # Fast path: plain seconds (allow comma as decimal separator)
    try:
        return float(s.replace(',', '.'))
    except Exception:
        pass
    # Fallback: mm:ss,fraction or mm:ss.fraction
    if ':' not in s:
        raise ValueError(f"Unsupported time format: {time_str}")
    minutes, rest = s.split(':', 1)
    if ',' in rest:
        seconds_str, frac_str = rest.split(',', 1)
    elif '.' in rest:
        seconds_str, frac_str = rest.split('.', 1)
    else:
        seconds_str, frac_str = rest, '0'
    minutes = int(minutes)
    seconds = int(seconds_str)
    digits = ''.join(ch for ch in frac_str if ch.isdigit()) or '0'
    frac = int(digits) / (10 ** len(digits))
    return minutes * 60 + seconds + frac