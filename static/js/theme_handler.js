// static/js/theme_handler.js - CÓDIGO CORREGIDO

document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Elementos adicionales que necesitan la clase .dark-mode (usados si el CSS no cubre la herencia)
    const nav = document.getElementById('bottom-nav');
    const infoContainer = document.getElementById('pass-info-container');
    const mainContent = document.querySelector('main');
    
    // 🔑 CORRECCIÓN: Buscamos el <i> directamente, ya que es el hijo del botón
    const themeIcon = toggleButton ? toggleButton.querySelector('i') : null;

    // 1. Función para aplicar el tema y el ICONO
    function applyTheme(isDark) {
        if (!themeIcon) {
            console.error("Ícono de tema no encontrado. El botón no funcionará.");
            return;
        }

        // Si el CSS usa variables en :root y body.dark-mode, estos pasos son opcionales
        // Pero los mantenemos por si el CSS necesita estas clases explícitas.
        if (isDark) {
            // Aplicar clases de modo oscuro
            body.classList.add('dark-mode');
            nav.classList.add('dark-mode');
            // Nota: En CSS puro, body.dark-mode ya debería cambiar todo.
            
            // 🔑 LÓGICA DEL ÍCONO: Si estamos en modo OSCURO, mostramos el SOL (para cambiar a CLARO)
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            
            localStorage.setItem('theme', 'dark');
            
        } else {
            // Eliminar clases de modo oscuro (Modo Claro)
            body.classList.remove('dark-mode');
            nav.classList.remove('dark-mode');
            
            // 🔑 LÓGICA DEL ÍCONO: Si estamos en modo CLARO, mostramos la LUNA (para cambiar a OSCURO)
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            
            localStorage.setItem('theme', 'light');
        }
    }

    // 2. Cargar el tema guardado al inicio
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme !== null) {
        // Usar la preferencia guardada
        applyTheme(savedTheme === 'dark');
    } else if (prefersDark) {
        // Usar la preferencia del sistema (modo oscuro)
        applyTheme(true); 
    } else {
        // Usar modo claro por defecto
        applyTheme(false); 
    }


    // 3. Listener para el botón de toggle
    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            // Obtiene el estado actual del body
            const isCurrentlyDark = body.classList.contains('dark-mode');
            
            // Aplica el tema opuesto
            applyTheme(!isCurrentlyDark); 
        });
    } else {
        console.error("Error: El botón de tema (theme-toggle) no se encontró en el DOM.");
    }
});