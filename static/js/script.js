// static/script.js
// Script unificado: login, register, dashboard, paso y clima
// - Auto-refresh clima cada 10 minutos
// - Auto-refresh paso cada 30 minutos
// - Evita bucles de redirección en /login y /register

// ---------------- Helpers ----------------
function getToken() {
  return localStorage.getItem("token");
}

function handleUnauthorized() {
  localStorage.clear();
  // solo redirigir si no estamos ya en login o register
  if (!["/login", "/register", "/"].includes(window.location.pathname)) {
    window.location.href = "/login";
  }
}

async function safeFetch(url, opts = {}) {
  // helper para fetch con try/catch
  try {
    const res = await fetch(url, opts);
    return res;
  } catch (err) {
    console.error("Network error:", err);
    return null;
  }
}

// ---------------- Logout ----------------
document.getElementById("logoutBtn")?.addEventListener("click", async () => {
  const token = getToken();
  try {
    // Notificar al backend para registrar en el log
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      }
    });
  } catch (err) {
    console.warn("No se pudo notificar el logout:", err);
  } finally {
    // Limpiar sesión local y redirigir
    localStorage.clear();
    window.location.href = "/";
  }
});
// ---------------- Login ----------------
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
 e.preventDefault();
 const form = e.target;
 const data = {
    email: form.email.value,
    password: form.password.value
 };

 // Asumo que 'safeFetch' apunta a tu API de login, por ejemplo, '/api/login' o similar
 // Si tu ruta de login es '/login' en Flask, esto es correcto si se maneja como API.
 const res = await fetch("/api/auth/login", { 
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
 });

 if (!res) {
    alert("Error de red. Intenta nuevamente.");
    return;
 }

 if (res.ok) {
    const result = await res.json();
      
    // 1. Guardar datos importantes
    localStorage.setItem("token", result.token);
    // Guarda el rol para la redirección (y uso posterior)
    const userRole = result.role || "user"; 
    localStorage.setItem("role", userRole);
    localStorage.setItem("username", result.username || "");
    localStorage.setItem("user_role", userRole);
      
    // Intentar obtener pasoId inmediatamente (opcional)
    try {
     const pasoRes = await fetch("/paso/api", {
        headers: { Authorization: "Bearer " + result.token }
     });
     if (pasoRes.ok) {
        const paso = await pasoRes.json();
        if (paso.id) localStorage.setItem("pasoId", paso.id);
     }
    } catch (err) {
     // no bloquear login si falla
     console.debug("No se pudo obtener pasoId post-login:", err);
    }
    
    // 2. LÓGICA DE REDIRECCIÓN CONDICIONAL
    if (userRole === 'admin') {
        // Redirigir a los administradores al Dashboard
        window.location.href = "/dashboard";
    } else {
        // Redirigir a usuarios normales al Perfil o a otra página de usuario
        window.location.href = "/"; 
    }

 } else {
    const err = await res.json().catch(() => ({}));
    alert(err.message || "Credenciales inválidas");
 }
});

// ---------------- Register ----------------
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = {
    username: form.username.value,
    email: form.email.value,
    password: form.password.value,
    phone: form.phone?.value || "",
    role: form.role?.value || "user"
  };

  const res = await safeFetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (!res) {
    alert("Error de red. Intenta nuevamente.");
    return;
  }

  const result = await res.json().catch(() => ({}));
  if (res.ok) {
    alert("Usuario creado. Por favor inicia sesión.");
    window.location.href = "/login";
  } else {
    alert(result.message || "Error en registro");
  }
});

// ---------------- Dashboard: funciones ----------------
async function loadUserInfo() {
  const token = getToken();
  if (!token) return; // no forzamos redirect si no hay token (ej: en login/register)

  const res = await safeFetch("/api/dashboard", {
    headers: { Authorization: "Bearer " + token }
  });

  if (!res) {
    document.getElementById("userInfo") && (document.getElementById("userInfo").innerText = "Error de red");
    return;
  }

  if (res.status === 401) {
    handleUnauthorized();
    return;
  }

  if (res.ok) {
    const data = await res.json();
    const el = document.getElementById("userInfo");
    if (el) el.innerHTML = `<strong>Usuario:</strong> ${data.username} <br> <strong>Rol:</strong> ${data.role}`;
  } else {
    document.getElementById("userInfo") && (document.getElementById("userInfo").innerText = "Error al cargar usuario.");
  }
}

async function loadPaso() {
  const token = getToken();
  if (!token) return;

  const res = await safeFetch("/paso/api", {
    headers: { Authorization: "Bearer " + token }
  });

  if (!res) {
    const container = document.getElementById("pasoInfo");
    if (container) container.innerText = "Error de red al cargar paso.";
    return;
  }

  if (res.status === 401) {
    handleUnauthorized();
    return;
  }

  const container = document.getElementById("pasoInfo");
  if (res.ok) {
    const data = await res.json();
    if (data && data.id) {
      localStorage.setItem("pasoId", data.id);
    }
    if (container) {
      container.innerHTML = `
        <strong>Nombre:</strong> ${data.nombre || "-"} <br>
        <strong>Estado:</strong> ${data.estado || "-"} <br>
        <strong>Horario de Atención:</strong> ${data.horario_atencion || "-"} <br>
        <strong>Actualizado:</strong> ${data.actualizado || "-"} <br>
      `;
    }
  } else {
    if (container) container.innerText = "No se pudo cargar el estado del paso.";
  }
}

async function loadClima() {
  const token = getToken();
  if (!token) return;

  // obtener pasoId (si no está en localStorage, pedirlo)
  let pasoId = localStorage.getItem("pasoId");
  if (!pasoId) {
    const pasoRes = await safeFetch("/paso/api", {
      headers: { Authorization: "Bearer " + token }
    });
    if (pasoRes && pasoRes.ok) {
      const paso = await pasoRes.json();
      pasoId = paso.id;
      if (pasoId) localStorage.setItem("pasoId", pasoId);
    }
  }

  const container = document.getElementById("climaInfo");
  if (!pasoId) {
    if (container) container.innerText = "No se definió un Paso.";
    return;
  }

  const res = await safeFetch(`/api/clima/ultimo/${pasoId}`, {
    headers: { Authorization: "Bearer " + token }
  });

  if (!res) {
    if (container) container.innerText = "Error de red al cargar clima.";
    return;
  }

  if (res.status === 401) {
    handleUnauthorized();
    return;
  }

  if (res.ok) {
    const data = await res.json();
    if (container) {
      container.innerHTML = `
        <strong>Temperatura:</strong> ${data.temperatura ?? "-"} °C <br>
        <strong>Descripción:</strong> ${data.descripcion ?? "-"} <br>
        <strong>Viento:</strong> ${data.viento ?? "-"} m/s <br>
        <small>${data.fecha ? new Date(data.fecha).toLocaleString() : ""}</small>
      `;
    }
  } else if (res.status === 404) {
    if (container) container.innerText = "No hay registros de clima para este paso.";
  } else {
    if (container) container.innerText = "Error al cargar el clima.";
  }
}


// ---------------- Auto-refresh timers (solo en dashboard) ----------------
let climaInterval = null;
let pasoInterval = null;

function startAutoRefresh() {
  // evitar múltiples timers
  if (!climaInterval) {
    climaInterval = setInterval(() => {
      loadClima().catch(console.error);
    }, 10 * 60 * 1000); // 10 minutos
  }
  if (!pasoInterval) {
    pasoInterval = setInterval(() => {
      loadPaso().catch(console.error);
    }, 30 * 60 * 1000); // 30 minutos
  }
}

function stopAutoRefresh() {
  if (climaInterval) { clearInterval(climaInterval); climaInterval = null; }
  if (pasoInterval) { clearInterval(pasoInterval); pasoInterval = null; }
}

// ---------------- Inicialización (segura) ----------------
function initDashboard() {
  // solo si los elementos del dashboard existen
  if (!document.getElementById("userInfo") && !document.getElementById("pasoInfo") && !document.getElementById("climaInfo")) {
    return;
  }
  loadUserInfo().catch(console.error);
  loadPaso().then(() => loadClima()).catch(console.error);
  startAutoRefresh();
}

// Ejecutar init solo si estamos en dashboard (o si existen elementos)
initDashboard();

// -----------------------------------------------------------
// Nota: Este archivo está pensado para cargarse en todas las páginas.
// - En /login y /register los handlers de login/register se ejecutan porque sus forms existen.
// - En /dashboard se ejecutan las funciones de carga y los timers.
// - handleUnauthorized() evita bucles de redirect si ya estás en /login.
// -----------------------------------------------------------
