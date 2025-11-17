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
        
        // Guardar el ID del propio admin
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

    // Detección de ID o búsqueda genérica
    if (searchTerm) {
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
    
    // Usamos clases Tailwind para el texto de carga y la celda
    tableBody.innerHTML = '<tr><td colspan="6" class="px-4 py-4 text-center text-gray-400">Buscando usuarios...</td></tr>';
    
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
        
        // LLAMADA A LA FUNCIÓN DE VISIBILIDAD CORREGIDA
        toggleTableVisibility(); 
        

    } catch (error) {
        console.error("Error al cargar usuarios:", error);
        // Usamos clase Tailwind para el texto de error
        tableBody.innerHTML = `<tr><td colspan="6" class="px-4 py-4 text-center text-red-500">Error: ${error.message}.</td></tr>`;
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
        // Usamos clases Tailwind para el mensaje de no resultados
        tableBody.innerHTML = '<tr><td colspan="6" class="px-4 py-4 text-center text-gray-400">No se encontraron usuarios con esos criterios.</td></tr>';
        return;
    }
    
    const adminId = localStorage.getItem('admin_user_id');

    users.forEach(u => { 
        const status = u.is_active ? 'Activa' : 'Suspendida';
        
        // CLASES TAILWIND PARA EL BADGE DE ESTADO
        const statusClass = u.is_active 
            ? 'bg-green-600 text-white' 
            : 'bg-danger text-white'; 
        
        const toggleText = u.is_active ? 'Suspender' : 'Reactivar';
        
        // CLASES TAILWIND PARA EL BOTÓN DE ESTADO (Suspender/Reactivar)
        const toggleClasses = u.is_active 
            ? 'bg-yellow-600 hover:bg-yellow-700 text-gray-900 font-semibold' 
            : 'bg-green-600 hover:bg-green-700 text-white'; 
        
        const roleChangeText = u.role === 'admin' ? 'Degradar' : 'Ascender';
        
        // CLASES TAILWIND PARA EL BOTÓN DE ROL (Ascender/Degradar)
        const roleChangeClasses = u.role === 'admin' 
            ? 'bg-primary hover:bg-indigo-700 text-white' 
            : 'bg-indigo-400 hover:bg-indigo-500 text-gray-900'; 
        
        // Clases TAILWIND para botones fijos
        const messageClasses = 'bg-blue-600 hover:bg-blue-700 text-white';
        const deleteClasses = 'bg-danger hover:bg-red-600 text-white'; 
        
        // Deshabilitar acciones si el usuario es el propio admin
        const isSelf = u.id === adminId;
        const disableSelf = isSelf ? 'opacity-50 cursor-not-allowed' : ''; 
        const disableSelfAttr = isSelf ? 'disabled' : ''; 
        const disableSelfTitle = isSelf ? 'title="No puedes modificar tu propia cuenta"' : '';
        
        const row = document.createElement("tr");
        // Clases base para celdas de tabla (padding) 
        const cellClasses = 'px-4 py-3 text-sm border-t border-gray-700'; 
        
        row.innerHTML = `
            <td class="${cellClasses} td-id hidden lg:table-cell"><small class="text-xs text-gray-500">${u.id}</small></td>
            
            <td class="${cellClasses} font-medium">${u.username}</td>
            
            <td class="${cellClasses} td-email text-gray-400 hidden lg:table-cell">${u.email}</td>
            
            <td class="${cellClasses} td-role capitalize hidden lg:table-cell">${u.role}</td>
            
            <td class="${cellClasses} text-center">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusClass}">${status}</span>
            </td>
            
            <td class="${cellClasses} text-center">
                <div class="flex flex-wrap gap-1 justify-center"> 
                    
                    <button class="px-2 py-1 text-xs font-medium rounded transition duration-200 ${roleChangeClasses} ${disableSelf} update-role" 
                            data-user-id="${u.id}" 
                            data-current-role="${u.role}"
                            ${disableSelfAttr} ${disableSelfTitle}>
                        ${roleChangeText} Role
                    </button>
                    
                    <button class="px-2 py-1 text-xs font-medium rounded transition duration-200 ${toggleClasses} ${disableSelf} toggle-status" 
                            data-user-id="${u.id}" 
                            data-current-status="${u.is_active}"
                            ${disableSelfAttr} ${disableSelfTitle}>
                        ${toggleText}
                    </button>
                    
                    <button class="px-2 py-1 text-xs font-medium rounded transition duration-200 ${messageClasses} show-message-modal" 
                            data-user-id="${u.id}" 
                            data-username="${u.username}">
                        Message
                    </button>
                    
                    <button class="px-2 py-1 text-xs font-medium rounded transition duration-200 ${deleteClasses} ${disableSelf} delete-user" 
                            data-user-id="${u.id}"
                            ${disableSelfAttr} ${disableSelfTitle}>
                        Delete
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row); 
    });
    
    bindTableEvents();
}


function renderPagination(pagination) {
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';
    
    // Info de Paginación
    const infoText = `Mostrando ${Math.min((pagination.current_page - 1) * pagination.per_page + 1, pagination.total_items)} - 
                     ${Math.min(pagination.current_page * pagination.per_page, pagination.total_items)} de 
                     ${pagination.total_items} usuarios.`;
    // Usamos clases Tailwind en el elemento <small>
    document.getElementById('paginationInfo').textContent = infoText;

    // Clases Tailwind para paginación
    const pageLinkClasses = "px-3 py-1 leading-tight text-gray-400 bg-gray-800 border border-gray-700 hover:bg-gray-700 hover:text-white transition duration-150";
    const activePageClasses = "px-3 py-1 leading-tight text-white bg-primary border border-primary hover:bg-indigo-600 transition duration-150";
    const disabledPageClasses = "px-3 py-1 leading-tight text-gray-600 bg-gray-800 border border-gray-700 cursor-not-allowed";

    // Botón Anterior
    controls.innerHTML += `
        <li class="${pagination.has_prev ? '' : 'cursor-not-allowed'} rounded-l-lg overflow-hidden">
            <a class="${pagination.has_prev ? pageLinkClasses : disabledPageClasses}" href="#" data-page="${pagination.current_page - 1}">Anterior</a>
        </li>
    `;
    
    // Botones de página (simplificado a solo 5 botones cercanos)
    let startPage = Math.max(1, pagination.current_page - 2);
    let endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        controls.innerHTML += `
            <li>
                <a class="${i === pagination.current_page ? activePageClasses : pageLinkClasses}" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // Botón Siguiente
    controls.innerHTML += `
        <li class="${pagination.has_next ? '' : 'cursor-not-allowed'} rounded-r-lg overflow-hidden">
            <a class="${pagination.has_next ? pageLinkClasses : disabledPageClasses}" href="#" data-page="${pagination.current_page + 1}">Siguiente</a>
        </li>
    `;
    
    // Evento para botones de paginación
    controls.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            // Aseguramos que no se haga clic en un botón deshabilitado
            if (!e.target.closest('li').classList.contains('cursor-not-allowed')) {
                loadUsers(page);
            }
        });
    });
}


// VERSIÓN CORREGIDA: GESTIÓN DE VISIBILIDAD DE COLUMNAS
function toggleTableVisibility() {
    const searchTerm = document.getElementById('searchTerm')?.value.trim();
    const isSearchActive = searchTerm && searchTerm !== "";

    const columns = [
        // IDs usados en dashboard.html para <th> y clases usadas en renderUsers para <td>
        { id: 'th-id', selector: '.td-id' }, 
        { id: 'th-email', selector: '.td-email' }, 
        { id: 'th-role', selector: '.td-role' }
    ];

    columns.forEach(col => {
        const thElement = document.getElementById(col.id);
        // Seleccionamos todas las celdas <td> de esa columna
        const tdElements = document.querySelectorAll(col.selector); 

        if (thElement) {
            if (isSearchActive) {
                // AL BUSCAR: MOSTRAR la columna
                thElement.classList.remove('hidden');
                // Hacemos explícito que es una celda de tabla (para pantallas no-lg)
                thElement.classList.add('table-cell'); 
            } else {
                // VISTA NORMAL: OCULTAR la columna
                thElement.classList.add('hidden');
                thElement.classList.remove('table-cell'); 
            }
        }
        
        tdElements.forEach(cell => {
            if (isSearchActive) {
                // AL BUSCAR: MOSTRAR la celda
                cell.classList.remove('hidden');
                cell.classList.add('table-cell'); // Hacemos explícito que es una celda de tabla
            } else {
                // VISTA NORMAL: OCULTAR la celda
                cell.classList.add('hidden');
                cell.classList.remove('table-cell'); // Limpiamos la visualización explícita
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
            if (e.currentTarget.classList.contains('opacity-50')) return; // Evitar clic si está deshabilitado
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
            if (e.currentTarget.classList.contains('opacity-50')) return; // Evitar clic si está deshabilitado
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
            if (e.currentTarget.classList.contains('opacity-50')) return; // Evitar clic si está deshabilitado
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
    
    // Añadimos latitud y longitud con valores por defecto (0.0)
    const payload = {
        subject: subject,
        body: body,
        latitude: 0.0, 
        longitude: 0.0
    };


    try {
        const response = await fetch("/api/messages/alert", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${userToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
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