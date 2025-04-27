// Sistema de bloqueio automático
let inactivityTimer;
let inactivityTimeout = 90000; // 90 segundos em milissegundos
let lockUrl = '/login';
let isLocked = false;

function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(lockScreen, inactivityTimeout);
}

function lockScreen() {
    if (!isLocked) {
        isLocked = true;
        window.location.href = lockUrl;
    }
}

function setupLockSystem() {
    // Iniciar o timer de inatividade
    resetInactivityTimer();
    
    // Resetar o timer quando houver qualquer atividade do usuário
    document.addEventListener('mousemove', resetInactivityTimer);
    document.addEventListener('mousedown', resetInactivityTimer);
    document.addEventListener('keypress', resetInactivityTimer);
    document.addEventListener('touchstart', resetInactivityTimer);
    document.addEventListener('scroll', resetInactivityTimer);
    
    // Detectar quando a janela é minimizada (visibilitychange)
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') {
            // Janela minimizada ou mudança para outra aba
            // Não esperamos o tempo completo, bloqueamos mais rapidamente
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(lockScreen, 5000); // 5 segundos quando minimizado
        } else {
            // Janela restaurada
            resetInactivityTimer();
        }
    });
    
    // Configurar botão de bloqueio manual
    const lockButton = document.getElementById('lock-button');
    if (lockButton) {
        lockButton.addEventListener('click', function(e) {
            e.preventDefault();
            lockScreen();
        });
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', setupLockSystem);