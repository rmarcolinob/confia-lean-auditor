"""Safe domain feedback for the pilot; no raw provider response is exposed."""

MESSAGES = {
    "PROVIDER_NOT_CONFIGURED": ("Reconhecimento por foto indisponível neste ambiente.", False),
    "PROVIDER_UNAUTHORIZED": ("O serviço de reconhecimento recusou as credenciais deste ambiente. Solicite a verificação da configuração.", False),
    "PROVIDER_FORBIDDEN": ("Este ambiente não tem permissão para usar o reconhecimento por foto.", False),
    "PROVIDER_RATE_LIMITED": ("O limite do serviço de reconhecimento foi atingido. Aguarde antes de tentar novamente.", True),
    "PROVIDER_TIMEOUT": ("O reconhecimento excedeu o tempo de espera. Tente novamente.", True),
    "PROVIDER_UNAVAILABLE": ("O serviço de reconhecimento está temporariamente indisponível. Tente novamente.", True),
    "PROVIDER_TRANSPORT_ERROR": ("Não foi possível conectar ao serviço de reconhecimento. Tente novamente.", True),
    "PROVIDER_BUSY": ("O reconhecimento está ocupado neste momento. Aguarde e tente novamente.", True),
    "INVALID_PROVIDER_RESPONSE": ("O serviço de reconhecimento retornou uma resposta inválida. Tente novamente.", True),
    "INVALID_PROVIDER_OUTPUT": ("Não foi possível converter a resposta em transcrição. Tente novamente.", True),
    "INVALID_IMAGE": ("A imagem não pôde ser lida. Volte e ajuste a nitidez, o enquadramento ou o formato das páginas.", False),
    "PROVIDER_REJECTED": ("O serviço recusou o pedido de reconhecimento. Solicite a verificação da configuração.", False),
    "PROVIDER_FAILED": ("Não foi possível reconhecer esta solução agora.", True),
}


def failure_feedback(code):
    message, retryable = MESSAGES.get(code, MESSAGES["PROVIDER_FAILED"])
    return {"state": "FAILED", "error_code": code if code in MESSAGES else "PROVIDER_FAILED",
            "message": message + " As páginas foram preservadas.", "retryable": retryable}


def recognition_feedback(run=None, *, configured=True):
    if run and run.status == "NEEDS_REVIEW":
        return {"state": "RECOGNIZED", "error_code": None,
                "message": "Transcrição reconhecida. Confira cada página.", "retryable": False}
    if not configured:
        return failure_feedback("PROVIDER_NOT_CONFIGURED")
    if run:
        return failure_feedback(run.error_code)
    return {"state": "WAITING", "error_code": None,
            "message": "Páginas preservadas. Inicie o reconhecimento para transcrever a solução.", "retryable": True}
