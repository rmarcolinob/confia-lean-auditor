const form = document.querySelector("#login-form");
const error = document.querySelector("#login-error");
form.addEventListener("submit", async event => {
  event.preventDefault();
  error.textContent = "";
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const response = await fetch("/auth/login", {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login: document.querySelector("#login").value.trim(),
        password: document.querySelector("#password").value }),
    });
    document.querySelector("#password").value = "";
    if (!response.ok) { error.textContent = "Credenciais inválidas."; return; }
    location.replace("/");
  } catch (_exception) {
    document.querySelector("#password").value = "";
    error.textContent = "Não foi possível entrar. Tente novamente.";
  } finally {
    button.disabled = false;
  }
});
