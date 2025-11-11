// static/js/logout_handler.js
async function logout() {
  const token = localStorage.getItem("token");

  try {
    if (token) {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
      });
    }
  } catch (err) {
    console.error("Error al registrar logout:", err);
  } finally {
    localStorage.clear();
    window.location.href = "/login";
  }
}

// Vincular el evento a todos los botones posibles
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("logoutBtn")?.addEventListener("click", logout);
  document.getElementById("logout-button")?.addEventListener("click", logout);
  document.getElementById("logout")?.addEventListener("click", logout);
});
