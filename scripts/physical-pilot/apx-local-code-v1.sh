#!/usr/bin/bash
set -euo pipefail

if ! /usr/bin/systemctl is-active --quiet apx-model-store-v1.service; then
    echo "APX Local Coder indisponivel: conecta o SSD Samsung APX e aguarda a ativacao." >&2
    exit 3
fi

if ! /usr/bin/systemctl is-active --quiet apx-ollama-v1.service; then
    echo "APX Local Coder indisponivel: o servico local do modelo nao esta ativo." >&2
    exit 4
fi

if ! /usr/bin/curl --fail --silent --max-time 3 http://127.0.0.1:11434/api/version >/dev/null; then
    echo "APX Local Coder indisponivel: a API local nao respondeu." >&2
    exit 5
fi

export OLLAMA_API_KEY=ollama
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export QWEN_CODE_API_TIMEOUT_MS=600000
selection="fast"
if [[ -r /var/lib/apx/model-selection-v1/selected ]]; then
    IFS= read -r selection < /var/lib/apx/model-selection-v1/selected
fi
case "$selection" in
    fast) model="qwen2.5-coder:3b" ;;
    balanced) model="qwen2.5-coder:7b" ;;
    quality) model="qwen3-coder:30b" ;;
    *) echo "APX Local Coder recusou uma seleção persistente inválida." >&2; exit 7 ;;
esac
if [[ ${1:-} == "--quality" ]]; then
    model="qwen3-coder:30b"
    shift
fi
for argument in "$@"; do
    case "$argument" in
        -y|--yolo|--approval-mode|--approval-mode=*|--allowed-tools|--allowed-tools=*|\
        --model|--model=*|-m|--auth-type|--auth-type=*|--openai-base-url|--openai-base-url=*|\
        --system-prompt|--system-prompt=*|--append-system-prompt|--append-system-prompt=*|\
        --core-tools|--core-tools=*|--include-directories|--include-directories=*|\
        --add-dir|--add-dir=*|--bare)
            echo "APX Local Coder recusou uma opcao que altera o perfil local protegido." >&2
            exit 6
            ;;
    esac
done

cd /root
exec /usr/bin/qwen \
    --bare \
    --approval-mode default \
    --auth-type openai \
    --model "$model" \
    --system-prompt "És o agente local de programação APX no Host e trabalhas em /root. Inspeciona antes de agir, usa apenas as ferramentas necessárias, pede confirmação antes de qualquer alteração e valida o resultado. Não leias ficheiros extensos por inteiro: localiza e lê apenas os trechos necessários. Responde em português claro e de forma concisa." \
    "$@"
