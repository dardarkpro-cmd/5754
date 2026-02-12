import { api, getToken, getUser } from '../api.js';
import { t, tStatus } from '../i18n.js';

export async function renderCook(container, navigateTo) {
    const token = getToken();
    const user = getUser();

    if (!token) {
        container.innerHTML = `<p class="error">${t('pleaseLoginFirst')}</p>`;
        return;
    }

    if (user && user.role !== 'cook' && user.role !== 'admin') {
        container.innerHTML = `<p class="error">${t('cookOnly')}</p>`;
        return;
    }

    container.innerHTML = `<h2>${t('cookTitle')}</h2><p>${t('loading')}</p>`;

    try {
        const data = await api('/cook/orders/queue?location_id=loc-1');

        if (!data.orders || data.orders.length === 0) {
            container.innerHTML = `
        <h2>${t('cookTitle')}</h2>
        <p>${t('noOrders')}</p>
        <button class="btn" id="refresh-queue">${t('refresh')}</button>
      `;
            container.querySelector('#refresh-queue').addEventListener('click', () => renderCook(container, navigateTo));
            return;
        }

        let html = `<h2>${t('cookTitle')}</h2>`;

        data.orders.forEach(order => {
            const items = order.items.map(i => `${i.name} x${i.qty}`).join(', ');
            html += `
        <div class="order-card">
          <div><strong>${t('order')}:</strong> ${order.id}</div>
          <div><strong>${t('status')}:</strong> ${tStatus(order.status)}</div>
          <div><strong>${t('user')}:</strong> ${order.user.display_name}</div>
          <div><strong>${t('items')}:</strong> ${items}</div>
          <div><strong>${t('scheduled')}:</strong> ${new Date(order.scheduled_for).toLocaleString()}</div>
          <button class="btn mark-ready" data-id="${order.id}" style="margin-top:8px">
            ${t('markReady')}
          </button>
          <span class="ready-result" data-id="${order.id}"></span>
        </div>
      `;
        });

        html += `<button class="btn" id="refresh-queue" style="margin-top:16px">${t('refresh')}</button>`;

        container.innerHTML = html;

        // Mark ready handlers
        container.querySelectorAll('.mark-ready').forEach(btn => {
            btn.addEventListener('click', async () => {
                const orderId = btn.dataset.id;
                const resultSpan = container.querySelector(`.ready-result[data-id="${orderId}"]`);

                btn.disabled = true;
                resultSpan.innerHTML = ` ${t('loading')}`;

                try {
                    const result = await api(`/cook/orders/${orderId}/ready`, {
                        method: 'POST',
                        body: JSON.stringify({})
                    });

                    resultSpan.innerHTML = `<span class="success"> ✓ ${t('ready')} | Код выдачи: <strong style="font-size:18px;letter-spacing:2px">${result.pickup_code}</strong>${result.cell_code ? ` | ${t('cell')}: ${result.cell_code}` : ''}</span>`;
                    btn.style.display = 'none';

                } catch (err) {
                    resultSpan.innerHTML = `<span class="error"> ${t('error')}: ${err.message || err.error}</span>`;
                    btn.disabled = false;
                }
            });
        });

        container.querySelector('#refresh-queue').addEventListener('click', () => renderCook(container, navigateTo));

    } catch (err) {
        container.innerHTML = `<h2>${t('cookTitle')}</h2><p class="error">${t('error')}: ${err.message || err.error}</p>`;
    }
}
