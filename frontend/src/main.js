// main.js - Hash-based router with auth guard and i18n
import { renderLogin } from './pages/login.js';
import { renderMenu } from './pages/menu.js';
import { renderCart } from './pages/cart.js';
import { renderCheckout } from './pages/checkout.js';
import { renderCook } from './pages/cook.js';
import { renderDailyMenu } from './pages/daily_menu.js';
import { renderPickup } from './pages/pickup.js';
import { renderMyOrders } from './pages/my_orders.js';
import { renderAdmin } from './pages/admin.js';
import { getToken, getUser, clearToken, clearUser } from './api.js';
import { getLang, setLang, t } from './i18n.js';

// Role-based route access lists
const ROLE_ROUTES = {
  student: ['menu', 'cart', 'checkout', 'pickup', 'my-orders'],
  cook: ['cook', 'daily-menu', 'pickup'],
  admin: ['menu', 'admin', 'daily-menu', 'my-orders']
};

function getDefaultRoute(role) {
  if (role === 'admin') return 'admin';
  if (role === 'cook') return 'cook';
  return 'menu';
}

// Check if role can access a route
function canAccessRoute(role, route) {
  if (route === 'login') return true;
  const allowed = ROLE_ROUTES[role] || ROLE_ROUTES['student'];
  return allowed.includes(route);
}

const mainContainer = document.getElementById('main');
const nav = document.getElementById('nav');
const logoutBtn = document.getElementById('logout-btn');
const langSwitcher = document.getElementById('lang-switcher');

// Update static UI texts based on language
function updateStaticTexts() {
  logoutBtn.textContent = t('logout');
  // Nav buttons
  nav.querySelector('[data-page="menu"]').textContent = t('menu');
  nav.querySelector('[data-page="cart"]').textContent = t('cart');
  nav.querySelector('[data-page="checkout"]').textContent = t('checkout');
  nav.querySelector('[data-page="cook"]').textContent = t('cook');
  const dmBtn = nav.querySelector('[data-page="daily-menu"]');
  if (dmBtn) dmBtn.textContent = 'Меню дня';
  nav.querySelector('[data-page="pickup"]').textContent = t('pickup');
  const myOrdersBtn = nav.querySelector('[data-page="my-orders"]');
  if (myOrdersBtn) myOrdersBtn.textContent = 'Мои заказы';
  const adminBtn = nav.querySelector('[data-page="admin"]');
  if (adminBtn) adminBtn.textContent = t('admin');
}

// Show/hide nav and logout based on auth state + role
function updateAuthUI() {
  const isLoggedIn = !!getToken();
  const user = getUser();
  const role = user?.role || 'student';

  if (isLoggedIn) {
    nav.classList.remove('hidden');
    logoutBtn.classList.remove('hidden');

    // Hide nav buttons based on role
    nav.querySelectorAll('button[data-page]').forEach(btn => {
      const page = btn.dataset.page;
      if (canAccessRoute(role, page)) {
        btn.classList.remove('hidden');
      } else {
        btn.classList.add('hidden');
      }
    });
  } else {
    nav.classList.add('hidden');
    logoutBtn.classList.add('hidden');
  }
}

// Navigation function
function navigateTo(page) {
  window.location.hash = page;
}

// Logout handler
function logout() {
  clearToken();
  clearUser();
  updateAuthUI();
  navigateTo('login');
}

// Route handler
async function handleRoute() {
  const hash = window.location.hash.replace('#', '').replace('/', '') || 'login';
  const isLoggedIn = !!getToken();
  const user = getUser();
  const role = user?.role || 'student';

  // Auth guard: if not logged in, force login page
  if (!isLoggedIn && hash !== 'login') {
    navigateTo('login');
    return;
  }

  // Role guard: if logged in but role can't access this route, redirect to default
  if (isLoggedIn && hash !== 'login' && !canAccessRoute(role, hash)) {
    navigateTo(getDefaultRoute(role));
    return;
  }

  // Update UI state
  updateAuthUI();
  updateStaticTexts();

  // Update nav button active state
  nav.querySelectorAll('button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === hash);
  });

  // Render the appropriate page
  switch (hash) {
    case 'login':
      renderLogin(mainContainer, navigateTo);
      break;
    case 'menu':
      await renderMenu(mainContainer, navigateTo);
      break;
    case 'cart':
      renderCart(mainContainer, navigateTo);
      break;
    case 'checkout':
      await renderCheckout(mainContainer, navigateTo);
      break;
    case 'cook':
      await renderCook(mainContainer, navigateTo);
      break;
    case 'daily-menu':
      await renderDailyMenu(mainContainer, navigateTo);
      break;
    case 'pickup':
      renderPickup(mainContainer, navigateTo);
      break;
    case 'my-orders':
      await renderMyOrders(mainContainer, navigateTo);
      break;
    case 'admin':
      await renderAdmin(mainContainer, navigateTo);
      break;
    default:
      renderLogin(mainContainer, navigateTo);
  }
}

// Setup navigation buttons
nav.querySelectorAll('button[data-page]').forEach(btn => {
  btn.addEventListener('click', () => {
    navigateTo(btn.dataset.page);
  });
});

// Logout button handler
logoutBtn.addEventListener('click', logout);

// Language switcher handler
langSwitcher.value = getLang();
langSwitcher.addEventListener('change', (e) => {
  setLang(e.target.value);
  handleRoute(); // Re-render current page
});

// Listen to hash changes
window.addEventListener('hashchange', handleRoute);

// Initial setup
updateAuthUI();
updateStaticTexts();
handleRoute();
