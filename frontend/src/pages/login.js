import { api, setToken, setUser } from '../api.js';
import { t } from '../i18n.js';

export function renderLogin(container, navigateTo) {
  container.innerHTML = `
    <h2>${t('login')}</h2>
    <form id="login-form">
      <div class="form-group">
        <label>${t('loginLabel')}</label>
        <input type="text" id="login" placeholder="student1, cook, admin" required>
      </div>
      <div class="form-group">
        <label>${t('pinLabel')}</label>
        <input type="password" id="pin" placeholder="123456" required>
      </div>
      <button type="submit" class="btn">${t('loginBtn')}</button>
    </form>
    <div id="login-result"></div>
  `;

  const form = container.querySelector('#login-form');
  const result = container.querySelector('#login-result');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const login = container.querySelector('#login').value;
    const pin = container.querySelector('#pin').value;

    result.innerHTML = t('loggingIn');

    try {
      const data = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ login, pin })
      });

      setToken(data.access_token);
      setUser(data.user);

      result.innerHTML = `<p class="success">${t('loginSuccess')} ${t('welcome')}, ${data.user.display_name}</p>`;

      // Navigate based on role
      setTimeout(() => {
        if (data.user.role === 'cook') {
          navigateTo('cook');
        } else if (data.user.role === 'admin') {
          navigateTo('admin');
        } else {
          navigateTo('menu');
        }
      }, 500);

    } catch (err) {
      // Differentiate network errors from API errors
      if (err._network) {
        result.innerHTML = `<p class="error">Сервер недоступен. Проверьте подключение к интернету и попробуйте позже.</p>`;
      } else if (err.status === 401) {
        result.innerHTML = `<p class="error">Неверный логин или PIN</p>`;
      } else {
        result.innerHTML = `<p class="error">${t('error')}: ${err.message || err.error || 'Неизвестная ошибка'}</p>`;
      }
    }
  });
}
