import re

from fastapi import HTTPException


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password should be not shorter than 8 characters"
        )

    symbols = "/.!&?,"

    if set(symbols).isdisjoint(password):
        raise HTTPException(
            status_code=400,
            detail=f"Password should consist one of these symbols {"/.!&?,"}"
        )

    int_pattern = r"[0-9]"
    letters = re.findall(int_pattern, password)
    if not letters:
        raise HTTPException(
            status_code=400,
            detail=f"Password should consist at least one digit"
        )

    upper_pattern = r"[A-Z]"
    letters = re.findall(upper_pattern, password)
    if not letters:
        raise HTTPException(
            status_code=400,
            detail=f"Password should consist at least one upper-case letter"
        )

    lower_pattern = r"[a-z]"
    letters = re.findall(lower_pattern, password)
    if not letters:
        raise HTTPException(
            status_code=400,
            detail=f"Password should consist at least one lower-case letter"
        )




