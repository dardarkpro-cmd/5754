import { api, getCart, clearCart, getToken } from '../api.js';
import { t, tStatus } from '../i18n.js';

export async function renderCheckout(container, navigateTo) {
    if (!getToken()) {
        container.innerHTML = `<p class="error">${t('pleaseLoginFirst')}</p>`;
        return;
    }

    const cart = getCart();

    if (cart.length === 0) {
        container.innerHTML = `
      <h2>${t('checkoutTitle')}</h2>
      <p>${t('emptyCart')}</p>
      <button class="btn" id="go-menu">${t('menu')}</button>
    `;
        container.querySelector('#go-menu').addEventListener('click', () => navigateTo('menu'));
        return;
    }

    let total = 0;
    let itemsHtml = '';
    cart.forEach(item => {
        const subtotal = item.price * item.qty;
        total += subtotal;
        itemsHtml += `<div>${item.name} x ${item.qty} = ${subtotal} ₸</div>`;
    });

    container.innerHTML = `
    <h2>${t('checkoutTitle')}</h2>
    <div style="margin-bottom:16px">
      ${itemsHtml}
      <div style="margin-top:8px;font-weight:bold">${t('total')}: ${total} ₸</div>
    </div>
    <button class="btn" id="place-order">${t('placeOrder')}</button>
    <div id="checkout-result" style="margin-top:16px"></div>
  `;

    container.querySelector('#place-order').addEventListener('click', async () => {
        const result = container.querySelector('#checkout-result');
        result.innerHTML = `${t('loading')}`;

        try {
            // 1. Create order
            const orderData = await api('/orders', {
                method: 'POST',
                body: JSON.stringify({
                    location_id: 'loc-1',
                    scheduled_for: null,
                    items: cart.map(item => ({
                        menu_item_id: item.id,
                        qty: item.qty
                    }))
                })
            });

            // Store order_id for later use
            localStorage.setItem('order_id', orderData.order_id);

            result.innerHTML = `${t('orderId')}: ${orderData.order_id}. ${t('loading')}`;

            // 2. Fake payment
            const paymentData = await api('/payments/fake', {
                method: 'POST',
                body: JSON.stringify({
                    order_id: orderData.order_id
                })
            });

            clearCart();

            result.innerHTML = `
        <div class="success" style="margin-bottom:12px">✓ ${t('orderPlaced')}</div>
        <div class="info">
          <div><strong>${t('orderId')}:</strong> ${orderData.order_id}</div>
          <div><strong>${t('status')}:</strong> ${tStatus('PAID')}</div>
          <div><strong>${t('total')}:</strong> ${orderData.total} ₸</div>
        </div>
      `;

            // Store last order for pickup
            localStorage.setItem('lastOrderId', orderData.order_id);

        } catch (err) {
            result.innerHTML = `<p class="error">${t('error')}: ${err.message || err.error}</p>`;
        }
    });
}
