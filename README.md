# confia_lean_auditor

## Piloto de correção ConfIA

A interface dedicada de dupla entrada está em `/tme`, autenticada por padrão para usuários `TEACHER`.
Para apresentação local, `CONFIA_TME_DEMO_NO_AUTH=1` libera somente o fluxo TME;
a flag é rejeitada em produção e não muda o acesso aos módulos escolares.
Ela aceita escrita digital no caderno existente e fotos multipágina com
originais preservados, convergindo na mesma transcrição aceita e auditoria.
A apresentação usa **ConfIA — Confiabilidade e Explicabilidade**, com a identificação
discreta **PILOTO ConfIA** e os tokens da identidade visual existente. O caderno
mantém enunciado e ferramentas de escrita visíveis durante a rolagem.
Consulte [docs/TME_PILOT_01.md](docs/TME_PILOT_01.md) para arquitetura, operação,
limitações e credenciais necessárias ao OCR real.

## GitHub configuration

To set up your new GitHub repository, follow these steps:

* Under your repository name, click **Settings**.
* In the **Actions** section of the sidebar, click "General".
* Check the box **Allow GitHub Actions to create and approve pull requests**.
* Click the **Pages** section of the settings sidebar.
* In the **Source** dropdown menu, select "GitHub Actions".

After following the steps above, you can remove this section from the README file.
