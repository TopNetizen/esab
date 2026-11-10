from esab.adapters.hosts import connect_sketchup

def get_sketchup(path=None):
    result = connect_sketchup(work_dir=path)
    if not result.ok:
        raise RuntimeError(result.message)
    return result.details.get("value")
