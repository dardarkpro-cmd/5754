import { api, getToken } from '../api.js';
import { t } from '../i18n.js';

export function renderPickup(container, navigateTo) {
  const lastOrderId = localStorage.getItem('order_id') || '';

  container.innerHTML = `
    <h2>${t('pickupTitle')}</h2>
    
    <div class="pickup-section">
      <h3>${t('orderId')} + Код выдачи</h3>
      <div class="form-group">
        <label>${t('enterOrderId')}</label>
        <input type="text" id="order-id" placeholder="Order ID" value="${lastOrderId}">
      </div>
      <div class="form-group">
        <label>Код выдачи (6 цифр)</label>
        <input type="text" id="pickup-code" placeholder="000000" maxlength="6" inputmode="numeric">
      </div>
      <button class="btn" id="claim-btn">${t('claimOrder')}</button>
    </div>
    
    <div id="pickup-result"></div>
  `;

  const result = container.querySelector('#pickup-result');

  container.querySelector('#claim-btn').addEventListener('click', async () => {
    const orderId = container.querySelector('#order-id').value.trim();
    const pickupCode = container.querySelector('#pickup-code').value.trim();

    if (!orderId || !pickupCode) {
      result.innerHTML = `<p class="error">Введите Order ID и код выдачи</p>`;
      return;
    }

    result.innerHTML = `${t('loading')}`;

    try {
      const data = await api('/pickup/claim', {
        method: 'POST',
        body: JSON.stringify({ order_id: orderId, pickup_code: pickupCode })
      });

      result.innerHTML = `
        <div class="success" style="font-size:18px;margin-bottom:12px">✓ ${data.message}</div>
        <div class="info">
          <div><strong>${t('orderId')}:</strong> ${data.order_id}</div>
          ${data.cell_code ? `<div><strong>${t('cell')}:</strong> ${data.cell_code}</div>` : ''}
        </div>
      `;
      localStorage.removeItem('order_id');

    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message || err.error}</p>`;
    }
  });
}
