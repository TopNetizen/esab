from esab.adapters.hosts import connect_abaqus

def connect(workspace_dir=None):
    result = connect_abaqus(work_dir=workspace_dir)
    if not result.ok:
        raise RuntimeError(result.message)
    return result.details.get("value")
