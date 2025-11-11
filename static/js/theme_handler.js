// static/js/theme_handler.js

document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Elementos adicionales que necesitan la clase .dark-mode
    const nav = document.getElementById('bottom-nav');
    const infoContainer = document.getElementById('pass-info-container');
    const mainContent = document.querySelector('main');
    const navButtons = document.querySelectorAll('.nav-button');

    // 1. Función para aplicar el tema
    function applyTheme(isDark) {
        if (isDark) {
            body.classList.add('dark-mode');
            nav.classList.add('dark-mode');
            if (infoContainer) infoContainer.classList.add('dark-mode');
            if (mainContent) mainContent.classList.add('dark-mode');
            navButtons.forEach(btn => btn.classList.add('dark-mode'));
            toggleButton.innerText = 'Modo Claro';
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark-mode');
            nav.classList.remove('dark-mode');
            if (infoContainer) infoContainer.classList.remove('dark-mode');
            if (mainContent) mainContent.classList.remove('dark-mode');
            navButtons.forEach(btn => btn.classList.remove('dark-mode'));
            toggleButton.innerText = 'Modo Oscuro';
            localStorage.setItem('theme', 'light');
        }
    }

    // 1. Función para aplicar el tema
    function applyTheme(isDark) {
        if (isDark) {
            body.classList.add('dark-mode');
            nav.classList.add('dark-mode');
            infoContainer.classList.add('dark-mode');
            navButtons.forEach(btn => btn.classList.add('dark-mode'));
            toggleButton.innerText = 'Modo Claro';
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark-mode');
            nav.classList.remove('dark-mode');
            infoContainer.classList.remove('dark-mode');
            navButtons.forEach(btn => btn.classList.remove('dark-mode'));
            toggleButton.innerText = 'Modo Oscuro';
            localStorage.setItem('theme', 'light');
        }
    }

    // 2. Cargar el tema guardado al inicio (se aplica en todas las páginas)
    const savedTheme = localStorage.getItem('theme');
    
    // Si no hay tema guardado, comprueba la preferencia del sistema
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        applyTheme(savedTheme === 'dark');
    } else if (prefersDark) {
        // Aplica el modo oscuro si el sistema lo prefiere, pero no lo guarda aún
        applyTheme(true); 
    } else {
        // Aplica el modo claro por defecto
        applyTheme(false); 
    }


    // 3. Listener para el botón de toggle
    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            const currentTheme = localStorage.getItem('theme');
            const newThemeIsDark = (currentTheme === 'light' || !currentTheme) ? true : false;
            applyTheme(newThemeIsDark);
        });
    }
});