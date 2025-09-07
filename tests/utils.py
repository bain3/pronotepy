import warnings

def warn_empty(list_: list) -> None:
    if len(list_) == 0:
        warnings.warn("collection empty - cannot test properly")

def warn(predicate: bool, msg: str) -> None:
    if not predicate:
        warnings.warn(msg)
