from datetime import datetime


def str_to_stamp(s: str) -> float:
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S').timestamp()
    except ValueError:
        return 0


def stamp_to_str(t: float) -> str:
    return datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
