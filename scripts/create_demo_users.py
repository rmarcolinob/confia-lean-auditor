#!/usr/bin/env python3
"""Create local demonstration accounts without storing or echoing passwords."""
from getpass import getpass
from pathlib import Path
import hmac
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from confia_lean_auditor.auth.dependencies import auth_store  # noqa: E402
from confia_lean_auditor.auth.models import Role  # noqa: E402


DEMO_ACCOUNTS = (
    ("aluno.demo", "Aluno Demo", Role.STUDENT, ["turma.demo"]),
    ("professor.demo", "Professor Demo", Role.TEACHER, ["turma.demo"]),
    ("gestao.demo", "Gestão Demo", Role.SCHOOL_MANAGER, []),
)


def create_demo_users(prompt=getpass, output=print):
    store = auth_store()
    with store._locked():
        existing = set(store._read("users.json"))
    for login, display_name, role, classroom_ids in DEMO_ACCOUNTS:
        if login in existing:
            output(f"{login}: já existe; preservado.")
            continue
        password = prompt(f"Senha para {login}: ")
        confirmation = prompt("Repita a senha: ")
        if not password or not hmac.compare_digest(password, confirmation):
            raise ValueError(f"Senha vazia ou confirmação diferente para {login}.")
        store.create_user(login=login, display_name=display_name, role=role,
                          password=password, tenant_id="demo-pi", classroom_ids=classroom_ids)
        output(f"{login}: conta criada.")


if __name__ == "__main__":
    try:
        create_demo_users()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
