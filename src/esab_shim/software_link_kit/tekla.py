from esab.adapters.hosts import connect_tekla as _do_connect


def connect_tekla():
    result = _do_connect()
    if not result.ok:
        raise RuntimeError(result.message)
    return result.details.get("value")
