const API_BASE_USERS = "/api/users";
let currentPage = 1;
const perPage = 10;
let userToken = localStorage.getItem("token");

// =======================================================
// 1. LÓGICA DE INICIALIZACIÓN Y AUTENTICACIÓN
// =======================================================

async function loadDashboardData() {
    if (!userToken) {
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch("/api/dashboard", {
            headers: { 'Authorization': `Bearer ${userToken}` }
        });
        
        if (response.status === 401 || response.status === 403) {
            alert("Sesión expirada o no autorizada. Por favor, inicia sesión de nuevo.");
            localStorage.clear();
            window.location.href = '/login';
            return;
        }

        const data = await response.json();
        document.getElementById('username').textContent = data.username;
        document.getElementById('role').textContent = data.role.toUpperCase();
        
        // Guardar el ID del propio admin (útil para deshabilitar botones de auto-modificación)
        localStorage.setItem('admin_user_id', data.id); 

        // Mostrar sección de administración si el rol es 'admin'
        if (data.role === 'admin') {
            document.getElementById('adminSection').style.display = 'block';
            await loadUsers(1); // Cargar la tabla de usuarios al inicio
        } else {
             document.getElementById('adminSection').style.display = 'none';
        }

    } catch (error) {
        console.error("Error al cargar datos del dashboard:", error);
        alert("Error de conexión. Por favor, revisa la consola.");
    }
}


// =======================================================
// 2. LÓGICA DE BÚSQUEDA Y PAGINACIÓN
// =======================================================

function getSearchParameters(page) {
    const searchTerm = document.getElementById('searchTerm')?.value.trim() || '';
    const filterRole = document.getElementById('filterRole')?.value || '';
    
    let params = new URLSearchParams();
    params.set('page', page);
    params.set('per_page', perPage);

    // Detección de ID o búsqueda genérica (como lo configuramos en el backend)
    if (searchTerm) {
        // Simple chequeo para ver si parece un UUID/ID, si no, lo trata como búsqueda de texto
        const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(searchTerm);
        
        if (isUUID) {
            params.set('user_id', searchTerm);
        } else {
            params.set('search', searchTerm);
        }
    }

    // Filtro por Rol
    if (filterRole) {
        params.set('role', filterRole);
    }
    
    return params.toString();
}

async function loadUsers(page = 1) {
    currentPage = page;
    const tableBody = document.getElementById('usersTableBody');
    tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Buscando usuarios...</td></tr>';
    
    const params = getSearchParameters(page);
    
    try {
        const response = await fetch(`${API_BASE_USERS}?${params}`, {
            headers: { 'Authorization': `Bearer ${userToken}` }
        });

        if (!response.ok) {
            throw new Error('Error al obtener la lista de usuarios. Código: ' + response.status);
        }

        const result = await response.json();
        renderUsers(result.users);
        renderPagination(result.pagination);

    } catch (error) {
        console.error("Error al cargar usuarios:", error);
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${error.message}.</td></tr>`;
        // Aseguramos que los controles de paginación se reseteen
        document.getElementById('paginationControls').innerHTML = '';
        document.getElementById('paginationInfo').textContent = 'Mostrando 0 de 0 usuarios.';
    }
}

// =======================================================
// 3. RENDERIZADO DE TABLA Y PAGINACIÓN
// =======================================================

function renderUsers(users) {
    const tableBody = document.getElementById("usersTableBody");
    tableBody.innerHTML = ""; 

    if (users.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No se encontraron usuarios con esos criterios.</td></tr>';
        return;
    }
    
    const adminId = localStorage.getItem('admin_user_id');

    users.forEach(u => { 
        const status = u.is_active ? 'Activa' : 'Suspendida';
        const statusClass = u.is_active ? 'bg-success' : 'bg-danger'; 
        const toggleText = u.is_active ? 'Suspender' : 'Reactivar';
        const toggleClass = u.is_active ? 'btn-warning' : 'btn-success';
        const roleChangeText = u.role === 'admin' ? 'Degradar' : 'Ascender';
        const roleChangeClass = u.role === 'admin' ? 'btn-info' : 'btn-primary';
        
        // Deshabilitar acciones si el usuario es el propio admin
        const isSelf = u.id === adminId;
        const disableSelf = isSelf ? 'disabled' : '';
        const disableSelfTitle = isSelf ? 'title="No puedes modificar tu propia cuenta"' : '';
        
        const row = document.createElement("tr");
        
        row.innerHTML = `
            <td><small>${u.id}</small></td>
            <td>${u.username}</td>
            <td>${u.email}</td>
            <td>${u.role}</td>
            
            <td class="text-center">
                <span class="badge ${statusClass}">${status}</span>
            </td>
            
            <td class="text-center">
                <button class="btn btn-sm ${roleChangeClass} me-1 update-role" 
                        data-user-id="${u.id}" 
                        data-current-role="${u.role}"
                        ${disableSelf} ${disableSelfTitle}>
                    ${roleChangeText} Role
                </button>
                <button class="btn btn-sm ${toggleClass} me-1 toggle-status" 
                        data-user-id="${u.id}" 
                        data-current-status="${u.is_active}"
                        ${disableSelf} ${disableSelfTitle}>
                    ${toggleText}
                </button>
                <button class="btn btn-sm btn-info me-1 show-message-modal" 
                        data-user-id="${u.id}" 
                        data-username="${u.username}">
                    Message
                </button>
                <button class="btn btn-sm btn-danger delete-user" 
                        data-user-id="${u.id}"
                        ${disableSelf} ${disableSelfTitle}>
                    Delete
                </button>
            </td>
        `;
        tableBody.appendChild(row); 
    });
    
    // Bindeamos los eventos de los botones después de que se hayan creado
    bindTableEvents();
}


function renderPagination(pagination) {
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';
    
    // Info de Paginación
    const infoText = `Mostrando ${Math.min((pagination.current_page - 1) * pagination.per_page + 1, pagination.total_items)} - 
                      ${Math.min(pagination.current_page * pagination.per_page, pagination.total_items)} de 
                      ${pagination.total_items} usuarios.`;
    document.getElementById('paginationInfo').textContent = infoText;

    // Botón Anterior
    controls.innerHTML += `
        <li class="page-item ${pagination.has_prev ? '' : 'disabled'}">
            <a class="page-link" href="#" data-page="${pagination.current_page - 1}">Anterior</a>
        </li>
    `;
    
    // Botones de página (simplificado a solo 5 botones cercanos)
    let startPage = Math.max(1, pagination.current_page - 2);
    let endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        controls.innerHTML += `
            <li class="page-item ${i === pagination.current_page ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // Botón Siguiente
    controls.innerHTML += `
        <li class="page-item ${pagination.has_next ? '' : 'disabled'}">
            <a class="page-link" href="#" data-page="${pagination.current_page + 1}">Siguiente</a>
        </li>
    `;
    
    // Evento para botones de paginación
    controls.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            if (page > 0 && page <= pagination.total_pages) {
                loadUsers(page);
            }
        });
    });
}


// =======================================================
// 4. BINDEO DE EVENTOS DE LA TABLA (CRUD)
// =======================================================

function bindTableEvents() {
    // 1. Toggle Status (Suspender/Reactivar)
    document.querySelectorAll('.toggle-status').forEach(button => {
        button.addEventListener('click', (e) => {
            const userId = e.currentTarget.dataset.userId;
            const currentStatus = e.currentTarget.dataset.currentStatus === 'true';
            const newStatus = !currentStatus;
            
            if (confirm(`¿Seguro que quieres ${newStatus ? 'ACTIVAR' : 'SUSPENDER'} la cuenta?`)) {
                 toggleUserStatus(userId, newStatus);
            }
        });
    });
    
    // 2. Update Role (Ascender/Degradar)
    document.querySelectorAll('.update-role').forEach(button => {
        button.addEventListener('click', (e) => {
            const userId = e.currentTarget.dataset.userId;
            const currentRole = e.currentTarget.dataset.currentRole;
            const newRole = currentRole === 'admin' ? 'user' : 'admin';
            
            if (confirm(`¿Seguro que quieres cambiar el rol a ${newRole.toUpperCase()}?`)) {
                 updateUserRole(userId, newRole);
            }
        });
    });
    
    // 3. Delete User
     document.querySelectorAll('.delete-user').forEach(button => {
        button.addEventListener('click', (e) => {
            const userId = e.currentTarget.dataset.userId;
            if (confirm("⚠️ ¡ADVERTENCIA! ¿Estás seguro de que quieres ELIMINAR PERMANENTEMENTE a este usuario?")) {
                 deleteUser(userId);
            }
        });
    });
    
    // 4. Message Modal
    document.querySelectorAll('.show-message-modal').forEach(button => {
        button.addEventListener('click', (e) => {
            const userId = e.currentTarget.dataset.userId;
            const username = e.currentTarget.dataset.username;
            showPrivateMessageModal(userId, username);
        });
    });
}


// =======================================================
// 5. LLAMADAS A LA API DE ACCIONES (CRUD/TOGGLE)
// =======================================================

async function toggleUserStatus(userId, newStatus) {
    try {
        const response = await fetch(`${API_BASE_USERS}/${userId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({ is_active: newStatus })
        });
        
        const data = await response.json();
        alert(data.message);
        if (response.ok) {
            loadUsers(currentPage); // Recargar la tabla
        }
    } catch (error) {
        alert("Error de comunicación con el servidor.");
        console.error("Error toggling status:", error);
    }
}

async function updateUserRole(userId, newRole) {
    try {
        const response = await fetch(`${API_BASE_USERS}/${userId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({ role: newRole })
        });
        
        const data = await response.json();
        alert(data.message);
        if (response.ok) {
            loadUsers(currentPage); // Recargar la tabla
        }
    } catch (error) {
        alert("Error de comunicación con el servidor.");
        console.error("Error updating role:", error);
    }
}

async function deleteUser(userId) {
    try {
        const response = await fetch(`${API_BASE_USERS}/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${userToken}` }
        });
        
        const data = await response.json();
        alert(data.message);
        if (response.ok) {
            loadUsers(currentPage); // Recargar la tabla
        }
    } catch (error) {
        alert("Error de comunicación con el servidor.");
        console.error("Error deleting user:", error);
    }
}

// =======================================================
// 6. MENSAJERÍA Y EVENTOS GENERALES
// =======================================================

// Lógica de envío de Mensajes Privados (Admin -> Usuario)
async function sendPrivateMessage(userId, subject, body) {
    try {
        const response = await fetch(`/api/messages/user/${userId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${userToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ subject: subject, body: body })
        });
        
        const data = await response.json();
        alert(data.message);
    } catch (err) {
        console.error("Error al enviar mensaje privado:", err);
        alert("Error al enviar el mensaje privado.");
    }
}

// Función para mostrar el modal de mensaje privado (usa 'prompt' para simplicidad)
function showPrivateMessageModal(userId, username) {
    const subject = prompt(`Enviar mensaje privado a ${username}. Introduce el Asunto (Opcional):`);
    // Si el usuario cancela o no introduce asunto, puede seguir
    
    const body = prompt(`Mensaje para ${username} (Asunto: ${subject || 'Sin Asunto'}). Introduce el Cuerpo del mensaje:`);
    if (!body || body.trim() === "") {
        alert("El cuerpo del mensaje no puede estar vacío.");
        return;
    }
    
    sendPrivateMessage(userId, subject || "Mensaje de Administrador", body);
}

// 1. Manejar el envío de Alertas Globales
async function handleGlobalAlertSubmit(e) {
    e.preventDefault();
    
    const subject = document.getElementById("alertSubject").value;
    const body = document.getElementById("alertBody").value;
    
    if (!body || body.trim() === "") {
        alert("El mensaje de alerta no puede estar vacío.");
        return;
    }

    try {
        const response = await fetch("/api/messages/alert", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${userToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ subject: subject, body: body })
        });
        
        const data = await response.json();
        alert(data.message);
        
        if (response.ok) {
            document.getElementById("alertBody").value = ""; 
        }
    } catch (err) {
        console.error("Error al enviar alerta:", err);
        alert("Error al enviar la alerta global.");
    }
}


// Eventos Generales
document.addEventListener('DOMContentLoaded', () => {
    // 1. Cargar datos del dashboard
    loadDashboardData();
    
    // 2. Evento para el botón de búsqueda y filtro de Rol
    document.getElementById('searchButton')?.addEventListener('click', () => {
        loadUsers(1); // Siempre vuelve a la página 1 al aplicar filtros
    });
    
    // 3. Evento para presionar ENTER en el campo de búsqueda
    document.getElementById('searchTerm')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            loadUsers(1);
        }
    });
    
    // 4. Evento para el filtro de Rol (cambio automático)
    document.getElementById('filterRole')?.addEventListener('change', () => {
        loadUsers(1);
    });

    // 5. Evento para enviar alerta global
    document.getElementById("globalAlertForm")?.addEventListener("submit", handleGlobalAlertSubmit);
});