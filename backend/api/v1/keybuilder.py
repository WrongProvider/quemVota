import hashlib
from datetime import date, datetime


def politico_key_builder(
    func, namespace="", request=None, response=None, args=None, kwargs=None
):
    # 1. Identificador
    prefix = f"quem-vota-cache::{func.__name__}"

    # 2. Se args ou kwargs vierem como None (padrão da lib), inicializamos
    args = args or []
    kwargs = kwargs or {}

    # 3. Filtramos dependências e objetos internos
    ignored_keys = {
        "db",
        "request",
        "response",
        "self",
        "session",
        "service",
        "background_tasks",
    }

    # Pegamos apenas tipos de dados primitivos/estruturados válidos para cache
    cache_params = []
    for k, v in sorted(kwargs.items()):
        if k in ignored_keys:
            continue
        if not (
            isinstance(
                v, (str, int, float, bool, list, tuple, set, dict, date, datetime)
            )
            or v is None
        ):
            continue
        cache_params.append(f"{k}={v}")

    arg_str = ":".join(cache_params)

    # 4. Path params
    path_str = ""
    if request and getattr(request, "path_params", None):
        path_str = ":".join(
            [f"{k}={v}" for k, v in sorted(request.path_params.items())]
        )

    full_key = f"{prefix}:{path_str}:{arg_str}".strip(":")

    if len(full_key) < 64:
        return full_key

    return hashlib.sha256(full_key.encode()).hexdigest()
