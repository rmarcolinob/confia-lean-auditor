# CORE-AUTH-01 — autenticação local do ConfIA

CORE-AUTH-01 oferece autenticação e RBAC local para MVP e demonstração. Ainda não é uma implantação institucional exposta à internet.

## Iniciar a demo

Na raiz do repositório:

```sh
.venv/bin/python scripts/create_demo_users.py
CONFIA_AUTH_ENABLED=1 CONFIA_COOKIE_SECURE=0 .venv/bin/uvicorn confia_lean_auditor.main:app --app-dir app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000/`. `CONFIA_COOKIE_SECURE=0` serve apenas HTTP local. Com HTTPS, omita a variável (o padrão é `Secure=true`). O navegador deve acessar a mesma origem do servidor; os POSTs exigem `Origin` idêntico ao esquema e `Host` da requisição. Se a demo for acessada pelo tablet, use HTTPS e um hostname alcançável por ele.

O script solicita senhas sem eco e cria `aluno.demo`, `professor.demo` e `gestao.demo`. Contas existentes são preservadas. Os três usuários compartilham o tenant de demonstração `demo-pi`; aluno e professor usam `turma.demo`. Não há cadastro público nem senha padrão.

Para usar a prévia HMER, configure `CONFIA_MATHPIX_APP_ID` e `CONFIA_MATHPIX_APP_KEY` **no mesmo processo do servidor antes de iniciá-lo**, conforme [P2_HMER_MATHPIX_STROKES.md](P2_HMER_MATHPIX_STROKES.md). A autenticação não fornece essas credenciais. Sem elas, `mathpix` não é registrado e `/submissions/recognition-preview` responde 503 por configuração ausente; não é um erro 422 do payload do tablet.

## Arquitetura e armazenamento

`runtime/auth/users.json` contém identidade, role, escopo, salt aleatório, hash de senha e parâmetros do derivador. `runtime/auth/sessions.json` contém somente o SHA-256 do token opaco de sessão, o ID do usuário e a expiração. O token original existe apenas no cookie. Ambos os arquivos estão fora do Git, com modo 0600; o diretório usa 0700. Escritas usam arquivo temporário, sincronização e substituição atômica sob lock local. O arquivo de sessões não exige `CONFIA_SESSION_SECRET`, pois não há token assinado nem JWT.

O hashing usa `hashlib.scrypt` (N=16384, r=8, p=1) quando o Python oferece essa função. No Python 3.9 do ambiente macOS testado, `hashlib.scrypt` está ausente; nesse caso, o store usa PBKDF2-HMAC-SHA256 com 600 mil iterações. O algoritmo e seus parâmetros acompanham cada conta, permitindo verificação sem migração implícita. As senhas não entram em respostas da API ou logs.

`POST /auth/login` recebe somente login e senha e responde com identidade pública. Falhas de credenciais usam `401 Credenciais inválidas.` sem revelar se a conta existe. `GET /auth/me` retorna a identidade pública vinculada à sessão. `POST /auth/logout` revoga a sessão no store e apaga o cookie. O cookie `confia_session` é `HttpOnly`, `SameSite=Lax`, `Path=/`, tem `Max-Age` de 8 horas e `Secure=true` por padrão. `Secure=false` é rejeitado quando `CONFIA_ENV=production`.

## Papéis e permissões

| Recurso | STUDENT | TEACHER | SCHOOL_MANAGER |
| --- | --- | --- | --- |
| Catálogo, workspace e prática `/audit` | Sim | Catálogo e prática | Não |
| Prévia HMER e reconhecimento oficial | Prévia e própria Submission | Não | Não |
| Criar Submission | Própria, autoria derivada da sessão | Não | Não |
| Listar e ler Submission | Próprias | Mesmo tenant | Não |
| Transcrever, revisar, aceitar | Não | Mesmo tenant | Não |
| Audit Bridge e AuditRuns | Não | Mesmo tenant | Não |
| Visão agregada local `/management/overview` | Não | Não | Sim |

`NETWORK_MANAGER` e `ADMIN` estão reservados, sem permissões nesta fase. Uma Submission nova registra `submitted_by_user_id`, `tenant_id` e, se houver, o primeiro `classroom_id` do aluno autenticado. O corpo enviado pelo cliente não pode escolher esses campos. A idempotência do snapshot rejeita o reenvio por outra conta. As rotas de objeto verificam role e proprietário ou tenant antes de ler manuscrito, revisão ou análise. A estrutura permite restringir professores por turma depois, sem trocar a interface dos routers.

Submissions antigas continuam sem proprietário e não são reescritas. Um professor só pode lê-las em desenvolvimento/teste com `CONFIA_AUTH_LEGACY_READ=1`; aluno nunca ganha acesso por essa flag. A flag é ignorada em produção. Testes de protocolos anteriores usam explicitamente `CONFIA_AUTH_ENABLED=0`; a configuração não pode ser usada em `CONFIA_ENV=production`. A autenticação vem ligada por padrão.

## Interface e fluxo HMER

Sem sessão, `/` serve a tela institucional de login. Após login, o shell consulta `/auth/me`, mostra nome e papel, remove do DOM os links e menus de outros papéis e disponibiliza **Sair**. Um hash manual de outro papel volta ao início do papel autenticado. O seletor de perfis de demonstração também é removido no modo autenticado. Isso melhora a navegação; a autorização efetiva permanece nas dependências FastAPI.

Os HTMLs acessados diretamente em `/static/index.html` e `/static/capture/tablet.html` redirecionam para `/` e `/capture` no modo autenticado, respectivamente, preservando a proteção das rotas canônicas. CSS, JavaScript e outros assets estáticos continuam públicos e não contêm dados pessoais.

O caderno `/capture` exige STUDENT. A sequência S Pen → prévia Mathpix → Submission → reconhecimento oficial → revisão `NEEDS_REVIEW` → conferência pelo professor → Audit Bridge permanece a mesma. A prévia não vira registro oficial; a criação da Submission vincula a conta da sessão. O professor no mesmo tenant recebe a Submission e suas revisões pela lista autorizada. Nenhuma revisão é aceita automaticamente.

## Limitações e próxima fase

O armazenamento de usuários/sessões é local, para uma instância e um disco. Não há PostgreSQL, turmas completas, cadastro público, recuperação de senha, OAuth, gov.br, MFA ou rate limiting de login. A proteção CSRF desta fase exige `Origin` same-origin para todas as mutações e usa cookie `SameSite=Lax`; proxy reverso deverá preservar esquema e host externos de forma confiável. Antes de qualquer exposição institucional, serão necessários TLS, rate limiting, observabilidade segura, gestão de contas, política de senha, revogação operacional, banco compartilhado e escopo formal de turmas e rede. TeacherDecision e gestão real permanecem fora deste incremento.
