import { getToken } from '../api.js';
import { t } from '../i18n.js';

export function renderPickup(container, navigateTo) {
  const token = getToken();
  const lastOrderId = localStorage.getItem('order_id') || '';

  container.innerHTML = `
    <h2>${t('pickupTitle')}</h2>
    
    <div class="pickup-section">
      <h3>${t('orderId')} + ${t('pin')}</h3>
      <div class="form-group">
        <label>${t('enterOrderId')}</label>
        <input type="text" id="order-id" placeholder="Order ID" value="${lastOrderId}">
      </div>
      <div class="form-group">
        <label>${t('enterPin')}</label>
        <input type="text" id="pin-code" placeholder="6-digit PIN">
      </div>
      <button class="btn" id="claim-pin">${t('claimOrder')}</button>
    </div>
    
    <div id="pickup-result"></div>
  `;

  const result = container.querySelector('#pickup-result');

  async function doClaim(body) {
    result.innerHTML = `${t('loading')}`;

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/pickup/claim', {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (response.ok) {
        result.innerHTML = `
          <div class="success" style="font-size:18px;margin-bottom:12px">✓ ${t('claimed')}</div>
          <div class="info">
            <div><strong>${t('orderId')}:</strong> ${data.order_id}</div>
            <div><strong>${t('cell')}:</strong> ${data.cell_code}</div>
          </div>
        `;
        localStorage.removeItem('order_id');
      } else {
        result.innerHTML = `<p class="error">${t('error')}: ${data.message || data.error}</p>`;
      }

    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
    }
  }

  container.querySelector('#claim-pin').addEventListener('click', () => {
    const orderId = container.querySelector('#order-id').value.trim();
    const pinCode = container.querySelector('#pin-code').value.trim();
    if (!orderId || !pinCode) {
      result.innerHTML = `<p class="error">${t('enterOrderId')} / ${t('enterPin')}</p>`;
      return;
    }
    doClaim({ order_id: orderId, pin_code: pinCode });
  });
}
