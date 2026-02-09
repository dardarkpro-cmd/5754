import { getCart, updateCartQty, removeFromCart, clearCart } from '../api.js';
import { t } from '../i18n.js';

export function renderCart(container, navigateTo) {
  const cart = getCart();

  if (cart.length === 0) {
    container.innerHTML = `
      <h2>${t('cartTitle')}</h2>
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
    itemsHtml += `
      <div class="cart-item">
        <div>
          <strong>${item.name}</strong> x ${item.qty}
          <span style="color:#666">(${item.price} ₸)</span>
        </div>
        <div>
          <span style="margin-right:12px">${subtotal} ₸</span>
          <button class="btn btn-sm qty-minus" data-id="${item.id}">-</button>
          <button class="btn btn-sm qty-plus" data-id="${item.id}">+</button>
          <button class="btn btn-sm remove-item" data-id="${item.id}" style="background:#c00">${t('remove')}</button>
        </div>
      </div>
    `;
  });

  container.innerHTML = `
    <h2>${t('cartTitle')}</h2>
    ${itemsHtml}
    <div style="margin-top:16px;padding-top:16px;border-top:2px solid #333">
      <strong>${t('total')}: ${total} ₸</strong>
    </div>
    <div style="margin-top:16px">
      <button class="btn" id="checkout-btn">${t('proceedToCheckout')}</button>
    </div>
  `;

  // Qty handlers
  container.querySelectorAll('.qty-minus').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = cart.find(c => c.id === btn.dataset.id);
      if (item) {
        updateCartQty(item.id, item.qty - 1);
        renderCart(container, navigateTo);
      }
    });
  });

  container.querySelectorAll('.qty-plus').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = cart.find(c => c.id === btn.dataset.id);
      if (item) {
        updateCartQty(item.id, item.qty + 1);
        renderCart(container, navigateTo);
      }
    });
  });

  container.querySelectorAll('.remove-item').forEach(btn => {
    btn.addEventListener('click', () => {
      removeFromCart(btn.dataset.id);
      renderCart(container, navigateTo);
    });
  });

  container.querySelector('#checkout-btn').addEventListener('click', () => navigateTo('checkout'));
}
