import { api, getToken, getMyOrders } from '../api.js';
import { t, tStatus } from '../i18n.js';

export async function renderMyOrders(container, navigateTo) {
    const token = getToken();

    if (!token) {
        container.innerHTML = `<p class="error">${t('pleaseLoginFirst')}</p>`;
        return;
    }

    container.innerHTML = `<h2>Мои заказы</h2><p>${t('loading')}</p>`;

    try {
        const data = await getMyOrders();

        if (!data.orders || data.orders.length === 0) {
            container.innerHTML = `
                <h2>Мои заказы</h2>
                <p>У вас пока нет заказов</p>
                <button class="btn" id="go-menu">Перейти в меню</button>
            `;
            container.querySelector('#go-menu').addEventListener('click', () => navigateTo('menu'));
            return;
        }

        let html = `<h2>Мои заказы</h2>`;

        data.orders.forEach(order => {
            const items = order.items.map(i => `${i.name} x${i.qty}`).join(', ');
            const statusClass = order.status === 'READY' ? 'success' : (order.status === 'PICKED_UP' ? 'info' : 'warning');

            html += `
            <div class="order-card" style="margin-bottom:12px">
              <div class="order-card-header">
                <span class="order-card-id">#${order.id.slice(-8)}</span>
                <span class="order-card-status" style="background:${order.status === 'READY' ? '#d1fae5' : '#fef3c7'};color:${order.status === 'READY' ? '#065f46' : '#92400e'}">${tStatus(order.status)}</span>
              </div>
              <div><strong>${t('items')}:</strong> ${items}</div>
              <div><strong>${t('total')}:</strong> ${order.total} ₸</div>
              <div style="font-size:13px;color:#666">${new Date(order.created_at).toLocaleString()}</div>
            `;

            // Show pickup code prominently when order is READY
            if (order.status === 'READY' && order.pickup_code) {
                html += `
                <div style="margin-top:10px;padding:12px;background:#d1fae5;border:2px solid #065f46;border-radius:8px;text-align:center">
                  <div style="font-size:13px;color:#065f46;margin-bottom:4px">Код выдачи:</div>
                  <div style="font-size:28px;font-weight:700;letter-spacing:4px;color:#065f46">${order.pickup_code}</div>
                  <div style="font-size:12px;color:#065f46;margin-top:4px">Назовите этот код для получения заказа</div>
                </div>
                `;
            }

            html += `</div>`;
        });

        html += `<button class="btn" id="refresh-orders" style="margin-top:16px">${t('refresh')}</button>`;

        container.innerHTML = html;

        container.querySelector('#refresh-orders').addEventListener('click', () => renderMyOrders(container, navigateTo));

    } catch (err) {
        container.innerHTML = `<h2>Мои заказы</h2><p class="error">${t('error')}: ${err.message || err.error}</p>`;
    }
}
