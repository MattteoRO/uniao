/**
 * Sistema de Bloqueio Automático
 * 
 * Bloqueia o sistema após inatividade de 90 segundos
 * e permite o bloqueio manual através de botão
 */

document.addEventListener('DOMContentLoaded', function() {
    let inactivityTimer;
    const lockTimeoutSeconds = 90; // 90 segundos de inatividade
    
    // Função para bloquear o sistema (redirecionar para login)
    function lockSystem() {
        window.location.href = '/logout';
    }
    
    // Reiniciar o contador de inatividade
    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(lockSystem, lockTimeoutSeconds * 1000);
    }
    
    // Configurar eventos para resetar o temporizador
    const eventsToMonitor = ['mousemove', 'mousedown', 'keypress', 'scroll', 'touchstart'];
    eventsToMonitor.forEach(eventType => {
        document.addEventListener(eventType, resetInactivityTimer);
    });
    
    // Configurar botão de bloqueio manual
    const lockButton = document.getElementById('lock-button');
    if (lockButton) {
        lockButton.addEventListener('click', function(e) {
            e.preventDefault();
            lockSystem();
        });
    }
    
    // Iniciar o temporizador de inatividade
    resetInactivityTimer();
});