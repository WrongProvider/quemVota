import hashlib

def politico_key_builder(func, namespace, request=None, response=None, args=None, kwargs=None):
    # 1. Identificador
    prefix = f"quem-vota-cache::{func.__name__}"
    
    # 2. Se args ou kwargs vierem como None (padrão da lib), inicializamos
    args = args or []
    kwargs = kwargs or {}
    
    # 3. Filtramos o DB e outros objetos
    ignored_keys = {"db", "request", "response", "self", "session"}
    
    # Pegamos apenas o que importa dos kwargs
    cache_params = [
        f"{k}={v}" for k, v in sorted(kwargs.items()) 
        if k not in ignored_keys
    ]
    
    arg_str = ":".join(cache_params)
    
    # 4. Path params
    path_str = ""
    if request and request.path_params:
        path_str = ":".join([f"{k}={v}" for k, v in sorted(request.path_params.items())])

    full_key = f"{prefix}:{path_str}:{arg_str}".strip(":")
    
    # debug
    #print(f"--- NOVA CHAVE DETECTADA: {full_key} ---")
    
    if len(full_key) < 64:
        return full_key
    
    return hashlib.sha256(full_key.encode()).hexdigest()