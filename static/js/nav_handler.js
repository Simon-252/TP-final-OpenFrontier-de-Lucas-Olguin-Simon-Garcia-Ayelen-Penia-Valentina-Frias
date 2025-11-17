// static/js/nav_handler.js

// 🔑 FUNCIÓN DE UTILIDAD PARA DECODIFICAR JWT 🔑
function parseJwt(token) {
    try {
        // El payload es la segunda parte (índice 1)
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        // Devuelve null si el token es inválido o no se puede decodificar
        console.error("Error decodificando token JWT:", e);
        return null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------------------------
    // --- REFERENCIAS DE NAVEGACIÓN (TOP & BOTTOM) ---
    // ----------------------------------------------------------------------

    // Referencias al Token y al Payload
    const token = localStorage.getItem('token'); 
    const payload = token ? parseJwt(token) : null;
    // userRole contendrá 'admin', 'user', o null
    const userRole = payload ? payload.role : null;

    // Referencias para la BARRA INFERIOR (#bottom-nav)
    const bottomUnauthOptions = document.getElementById('bottom-nav').querySelector('#unauthenticated-options');
    const bottomAuthOptions = document.getElementById('bottom-nav').querySelector('#authenticated-options');
    const bottomAdminLink = document.getElementById('admin-dashboard-link'); 
    const cruzarDocsLink = document.getElementById('cruzar-docs-link'); 
    const logoutButtonBottom = document.getElementById('logoutBtn'); 


    // Referencias para la BARRA SUPERIOR (#top-nav)
    const topAuthContainer = document.getElementById('top-auth-options');
    const topUnauthOptions = topAuthContainer ? topAuthContainer.querySelector('#unauthenticated-options') : null;
    const topAuthOptions = topAuthContainer ? topAuthContainer.querySelector('#authenticated-options') : null;
    const topAdminLink = topAuthOptions ? topAuthOptions.querySelector('#admin-dashboard-link') : null;
    const topLogoutButton = topAuthOptions ? topAuthOptions.querySelector('#logoutBtn') : null;

    // Referencia al botón de Reportar Suceso (no está en ninguna nav)
    const reportIncidentBtn = document.getElementById('report-incident-btn');

    // 🔑 REFERENCIA: El mensaje interactivo que queremos controlar
    const unauthenticatedReportPrompt = document.getElementById('unauthenticated-report-prompt'); 


    // ----------------------------------------------------------------------
    // --- LÓGICA DE VISIBILIDAD DE BARRAS Y ROLES ---
    // ----------------------------------------------------------------------

    if (token && payload) {
        // El usuario está autenticado (registrado, puede ser 'user' o 'admin')
        
        // 1. Ocultar opciones No Autenticadas (Top y Bottom)
        if (bottomUnauthOptions) bottomUnauthOptions.style.display = 'none';
        if (topUnauthOptions) topUnauthOptions.style.display = 'none';
        
        // 2. Mostrar opciones Autenticadas (Top y Bottom)
        if (bottomAuthOptions) bottomAuthOptions.style.display = 'flex';
        if (topAuthOptions) topAuthOptions.style.display = 'flex';

        // 3. Gestión de Enlace de Administrador y Botón de Reporte
        if (userRole === 'admin') {
            // Si es ADMIN: Mostrar dashboard, Ocultar botón de reporte.
            if (bottomAdminLink) bottomAdminLink.style.display = 'flex';
            if (topAdminLink) topAdminLink.style.display = 'flex';
            
            // AÑADIDO: Ocultar el botón Reportar Suceso a los administradores
            if (reportIncidentBtn) reportIncidentBtn.style.display = 'none';
            
        } else {
            // Si es USUARIO REGISTRADO (NO admin): Ocultar dashboard, Mostrar botón de reporte.
            if (bottomAdminLink) bottomAdminLink.style.display = 'none';
            if (topAdminLink) topAdminLink.style.display = 'none';
            
            // AÑADIDO: Mostrar el botón Reportar Suceso a los usuarios normales
            if (reportIncidentBtn) reportIncidentBtn.style.display = 'block'; // O 'flex', dependiendo de tu CSS
        }
        
        // 🔑 Ocultar el prompt de registro si está autenticado
        if (unauthenticatedReportPrompt) {
            unauthenticatedReportPrompt.style.display = 'none';
        }

    } else {
        // El usuario NO está autenticado (Invitado)
        
        // 1. Mostrar opciones No Autenticadas (Top y Bottom)
        if (bottomUnauthOptions) bottomUnauthOptions.style.display = 'flex';
        if (topUnauthOptions) topUnauthOptions.style.display = 'flex';
        
        // 2. Ocultar opciones Autenticadas (Top y Bottom)
        if (bottomAuthOptions) bottomAuthOptions.style.display = 'none';
        if (topAuthOptions) topAuthOptions.style.display = 'none';
        
        // 3. Asegurar que los enlaces de administrador estén ocultos
        if (bottomAdminLink) bottomAdminLink.style.display = 'none';
        if (topAdminLink) topAdminLink.style.display = 'none';
        
        // AÑADIDO: Mostrar el botón Reportar Suceso a los no registrados
        if (reportIncidentBtn) reportIncidentBtn.style.display = 'block'; // O 'flex'
        
        // 🔑 Mostrar el prompt de registro si NO está autenticado
        if (unauthenticatedReportPrompt) {
            // Asumo que quieres que se muestre, ajusta 'block' por 'flex' o 'inline-block' si es necesario
            unauthenticatedReportPrompt.style.display = 'block'; 
        }
    }

    // ----------------------------------------------------------------------
    // --- LÓGICA DE BOTONES Y ENLACES (Se mantiene su código) ---
    // ----------------------------------------------------------------------

    // LÓGICA DEL BOTÓN REPORTAR SUCESO (usando el token)
    // El comportamiento de redirección es correcto:
    // Con token -> /report_incident
    // Sin token -> /register
    if (reportIncidentBtn) {
        reportIncidentBtn.addEventListener('click', (e) => {
            e.preventDefault(); 
            if (token) {
                window.location.href = '/report_incident'; 
            } else {
                window.location.href = '/register';
            }
        });
    }

    // LÓGICA DE NAVEGACIÓN SEGURA AL PERFIL (usando el token)
    const profileLinkTop = topAuthOptions ? topAuthOptions.querySelector('a[title="Mi Perfil"]') : null;
    const profileLinkBottom = bottomAuthOptions ? bottomAuthOptions.querySelector('a[href="/profile"]') : null;

    [profileLinkTop, profileLinkBottom].forEach(link => {
        if (token && link) {
            link.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const response = await fetch('/profile', {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const html = await response.text();
                    document.open();
                    document.write(html);
                    document.close();
                    window.history.pushState({}, '', '/profile');
                } else if (response.status === 401) {
                    localStorage.clear();
                    window.location.href = '/login'; 
                } else {
                    alert("Error al cargar el perfil.");
                    window.location.href = '/'; 
                }
            });
        }
    });
});