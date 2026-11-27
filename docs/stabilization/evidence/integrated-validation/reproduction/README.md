# Reprodução local da validação integrada

Snapshot dos scripts usados nesta sessão, sem alterações de produção. Execute apenas em um worktree isolado da versão combinada, com dados sintéticos.

Copie os seis scripts desta pasta para `artifacts/integrated-validation/` na raiz do worktree. O caminho `PYTHON` de `run.py` identifica o venv local utilizado; em outra máquina, aponte-o para um ambiente com as dependências registradas no relatório. A execução dos scripts assume a raiz do repositório como diretório atual. O runner remove credenciais herdadas e desabilita os três providers LLM.

Prepare o toolchain, o cache fixado nos manifests e execute `lake build` antes da suíte completa. Não use `lake update`.

```sh
python3 artifacts/integrated-validation/run.py lean
python3 artifacts/integrated-validation/run.py javascript
python3 artifacts/integrated-validation/run.py python-full
python3 artifacts/integrated-validation/run.py p4
python3 artifacts/integrated-validation/p4_controls_v2.py
```

O controle V2 executa o teste P4 original, sem mudar suas asserções. O Budget anterior é substituído somente em memória no processo de controle. Esperam-se falhas na condição original e aprovação na combinada; examine os códigos individuais dos JSONs e os logs. O script comparativo continua para registrar todas as execuções, não representa por seu próprio código de saída uma suíte integralmente aprovada. A V1 também está preservada: a pausa única não reproduziu a falha e não fundamenta a conclusão.

Para o fluxo textual, use o mesmo Python do runner e seus flags/PYTHONPATH, com `platform_flow.py seed`, depois `platform_flow.py verify` em outro subprocesso. O modo seed exige que `artifacts/integrated-validation/platform-data` ainda não exista; ele não sobrescreve um runtime anterior. O modo serve é apenas local, opcional, com contas sintéticas da fixture `test_core_auth`, providers desligados e sem OCR. Não exponha esse servidor na rede.

O snapshot final de `platform_flow.py` inclui o alinhamento do diretório `audits` e o retry idempotente em novo processo. A primeira execução de retomada, anterior ao alinhamento, permanece documentada como falha do harness. O teste completo do repositório não foi modificado.
