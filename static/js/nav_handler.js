// static/js/nav_handler.js

// 🔑 FUNCIÓN DE UTILIDAD PARA DECODIFICAR JWT 🔑
function parseJwt(token) {
    try {
        // El payload es la segunda parte (índice 1)
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        // Devuelve null si el token es inválido o no se puede decodificar
        return null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const authenticatedOptions = document.getElementById('authenticated-options');
    const unauthenticatedOptions = document.getElementById('unauthenticated-options');
    const logoutButton = document.getElementById('logout-button');
    //  Referencia al enlace del administrador (ID del layout.html)
    const adminDashboardLink = document.getElementById('admin-dashboard-link'); 
    const profileLink = document.querySelector('a[href="/profile"]');
    const token = localStorage.getItem('token'); 
    const cruzarDocsLink = document.getElementById('cruzar-docs-link');

    if (token) {
    // Usuario autenticado
        if (cruzarDocsLink) {
            cruzarDocsLink.style.display = 'flex'; // o 'inline-block' según tu CSS
        }
    } else {
        // Usuario no autenticado
        if (cruzarDocsLink) {
            cruzarDocsLink.style.display = 'none';
        }
    }
    
    // ----------------------------------------------------------------------
    // --- LÓGICA DE NAVEGACIÓN SEGURA AL PERFIL ---
    // ----------------------------------------------------------------------
    if (token && profileLink) {
        // Interceptamos el evento de clic SÓLO si hay un token
        profileLink.addEventListener('click', async (e) => {
            e.preventDefault(); // Detenemos la navegación estándar del navegador
            
            // 1. Usamos Fetch para obtener el contenido
            const response = await fetch('/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}` // ¡Adjuntamos el token!
                }
            });

            // 2. Si es exitoso (200 OK), mostramos el HTML
            if (response.ok) {
                // Flask responderá con el HTML de la plantilla.
                // Reemplazamos el contenido del cuerpo actual con el nuevo HTML.
                // Esto simula una navegación de página sin recargar toda la aplicación.
                const html = await response.text();
                document.open();
                document.write(html);
                document.close();
                
                // NOTA: Para que esto funcione, DEBES asegurarse de que el script
                // que maneja la lógica de perfil (profile.js o el script en profile.html)
                // se ejecute después de cargar el nuevo contenido.
                window.history.pushState({}, '', '/profile'); // Actualiza la URL
            } else if (response.status === 401) {
                // Token inválido o expirado. Limpiar sesión.
                localStorage.clear();
                window.location.href = '/login'; 
            } else {
                alert("Error al cargar el perfil.");
                window.location.href = '/'; 
            }
        });
    }

    // ----------------------------------------------------------------------
    // --- LÓGICA DE AUTENTICACIÓN Y ROLES ---
    // ----------------------------------------------------------------------

    if (token) {
        // El usuario está autenticado
        unauthenticatedOptions.style.display = 'none';
        authenticatedOptions.style.display = 'flex';

        // Decodificar token para verificar rol
        const payload = parseJwt(token);

        if (payload && payload.role === 'admin') {
            // Mostrar enlace del Dashboard para el administrador
            if (adminDashboardLink) {
                // 🔑 CAMBIO: Usar 'flex' para que se muestre correctamente en el contenedor 'flex'
                adminDashboardLink.style.display = 'flex'; 
            }
        } else {
            // Ocultar enlace del Dashboard para usuarios normales
            if (adminDashboardLink) {
                adminDashboardLink.style.display = 'none';
            }
        }

    } else {
        // El usuario NO está autenticado
        unauthenticatedOptions.style.display = 'flex';
        authenticatedOptions.style.display = 'none';

        // Asegurar que el enlace del admin esté oculto si no hay token
        if (adminDashboardLink) {
            adminDashboardLink.style.display = 'none';
        }
    }


    // ----------------------------------------------------------------------
    // --- LÓGICA INTEGRADA DEL ESTADO DEL PASO Y CAMBIO DE IMÁGENES ---
    // ----------------------------------------------------------------------

    const statusContainer = document.getElementById('pass-status-container');
    const statusText = document.getElementById('pass-status-text');
    const passImage = document.getElementById('pass-image');

    async function fetchAndUpdatePassStatus() {
        try {
            const res = await fetch("/paso/public_api"); 
            
            if (!res.ok) {
                statusContainer.style.backgroundColor = 'gray';
                statusText.textContent = 'ERROR al cargar estado';
                return;
            }

            const data = await res.json();
            
            const estado = data.estado ? data.estado.toLowerCase() : 'desconocido'; 
            
            // 1. Actualiza el estado del paso
            if (estado === "abierto" || estado === "habilitado") {
                statusContainer.style.backgroundColor = 'green';
                statusText.textContent = 'PASO ABIERTO';
            } else if (estado === "cerrado") {
                statusContainer.style.backgroundColor = 'red';
                statusText.textContent = 'PASO CERRADO';
            } else {
                statusContainer.style.backgroundColor = 'gray';
                statusText.textContent = 'ESTADO DESCONOCIDO';
            }
            
            // 2. Actualiza la imagen
            const imageFilename = data.image_filename || 'default_pass.jpg'; 
            passImage.src = `/static/images/${imageFilename}`;

        } catch (error) {
            console.error("Fallo al obtener la información del paso:", error);
            statusContainer.style.backgroundColor = 'gray';
            statusText.textContent = 'ERROR de conexión';
        }
    }

    fetchAndUpdatePassStatus();

}); // Cierre del document.addEventListener