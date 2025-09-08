// JavaScript for BalanceCore Admin Panel

function processRequest(requestId, status) {
    document.getElementById('requestId').value = requestId;
    document.getElementById('requestStatus').value = status;
    
    const modal = new bootstrap.Modal(document.getElementById('processModal'));
    modal.show();
}

function showDetails(requestId) {
    // Здесь можно добавить AJAX запрос для получения деталей заявки
    // Пока что просто показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
    modal.show();
    
    // Заглушка для деталей
    document.getElementById('detailsContent').innerHTML = `
        <div class="text-center">
            <p>Детали заявки #${requestId}</p>
            <p class="text-muted">Функция в разработке</p>
        </div>
    `;
}

// Автоматическое обновление страницы каждые 30 секунд для ожидающих заявок
if (window.location.search.includes('status=pending')) {
    setInterval(function() {
        window.location.reload();
    }, 30000);
}

// Подтверждение действий
document.addEventListener('DOMContentLoaded', function() {
    const processForm = document.getElementById('processForm');
    if (processForm) {
        processForm.addEventListener('submit', function(e) {
            const status = document.getElementById('requestStatus').value;
            const action = status === 'approved' ? 'одобрить' : 'отклонить';
            
            if (!confirm(`Вы уверены, что хотите ${action} эту заявку?`)) {
                e.preventDefault();
            }
        });
    }
});
