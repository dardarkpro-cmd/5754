import { api, addToCart, getToken } from '../api.js';
import { t, getLang } from '../i18n.js';
import { getItemMeta, placeholderImage } from '../menu_meta.js';

// Short day names for buttons (1=Mon..5=Fri)
const dayKeys = ['mon', 'tue', 'wed', 'thu', 'fri'];
function getShortDayName(num) {
  // num: 1-5
  return t(dayKeys[num - 1] || 'mon');
}

// Helper to get weekday name from number (1=Mon, 7=Sun)
function getWeekdayName(num) {
  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  return t(days[num - 1] || 'monday');
}

// Get localized name
function getLocalizedName(item, lang) {
  if (lang === 'kz' && item.name_kz) return item.name_kz;
  if (lang === 'ru' && item.name_ru) return item.name_ru;
  return item.name || item.name_ru || item.name_kz;
}

// Get localized description from meta
function getLocalizedDesc(meta, lang) {
  if (!meta) return '';
  if (lang === 'kz' && meta.desc_kz) return meta.desc_kz;
  if (lang === 'ru' && meta.desc_ru) return meta.desc_ru;
  return meta.desc_en || meta.desc_ru || '';
}

// Calculate which days to show based on today's weekday
function getVisibleDays(todayWeekday) {
  // todayWeekday: 1=Mon..7=Sun
  if (todayWeekday >= 1 && todayWeekday <= 5) {
    // Mon-Fri: show from today to min(5, today+3)
    const end = Math.min(5, todayWeekday + 3);
    const days = [];
    for (let d = todayWeekday; d <= end; d++) {
      days.push(d);
    }
    return days;
  } else {
    // Sat/Sun: show 1,2,3 (Mon/Tue/Wed)
    return [1, 2, 3];
  }
}

export async function renderMenu(container, navigateTo) {
  if (!getToken()) {
    container.innerHTML = `<p class="error">${t('pleaseLoginFirst')}</p>`;
    return;
  }

  container.innerHTML = `<h2>${t('menuTitle')}</h2><p class="loading">${t('loading')}</p>`;

  // Initial load without day param (backend auto-determines)
  await loadMenuForDay(container, null, navigateTo);
}

async function loadMenuForDay(container, selectedDay, navigateTo) {
  try {
    const url = selectedDay ? `/menu?day=${selectedDay}` : '/menu?location_id=loc-1';
    const data = await api(url);

    if (!data.meta) {
      container.innerHTML = `<h2>${t('menuTitle')}</h2><p class="error">${t('error')}</p>`;
      return;
    }

    const todayWeekday = data.meta.today;    // 1-7
    const showingDay = data.meta.showing;    // 1-5
    const visibleDays = getVisibleDays(todayWeekday);
    const lang = getLang();

    let html = `<h2>${t('menuTitle')}</h2>`;

    // Day selector dropdown
    html += '<div class="day-selector">';
    html += '<select id="day-select" class="day-select">';
    visibleDays.forEach(d => {
      const selected = d === showingDay ? ' selected' : '';
      html += `<option value="${d}"${selected}>${getWeekdayName(d)}</option>`;
    });
    html += '</select>';
    html += '</div>';

    if (!data.items || data.items.length === 0) {
      html += `<p>${t('noItems')}</p>`;
      container.innerHTML = html;
      attachDaySelectHandler(container, navigateTo);
      return;
    }

    // Group by category
    const categories = {};
    data.items.forEach(item => {
      if (!categories[item.category]) {
        categories[item.category] = [];
      }
      categories[item.category].push(item);
    });

    // Menu cards grid
    html += '<div class="menu-grid">';
    for (const [category, items] of Object.entries(categories)) {
      html += `<h3 class="menu-category">${category}</h3>`;
      html += '<div class="menu-cards">';
      items.forEach(item => {
        const meta = getItemMeta(item);
        const image = meta?.image || placeholderImage;
        const itemName = getLocalizedName(item, lang);
        const unavailable = item.is_available === false;
        const stockText = item.stock_qty !== null && item.stock_qty !== undefined
          ? `${item.stock_qty} ${t('pcs')}` : '';

        html += `
                  <div class="menu-card${unavailable ? ' unavailable' : ''}" data-item-id="${item.id}">
                    <img class="menu-card-img" src="${image}" alt="${itemName}" loading="lazy">
                    <div class="menu-card-body">
                      <div class="menu-card-name">${itemName}</div>
                      <div class="menu-card-row">
                        <span class="menu-card-price">${item.price} ₸</span>
                        ${stockText ? `<span class="menu-card-stock">${stockText}</span>` : ''}
                      </div>
                      <button class="btn btn-sm add-btn" 
                        data-id="${item.id}" 
                        data-name="${itemName}" 
                        data-price="${item.price}"
                        ${unavailable ? 'disabled' : ''}>
                        ${t('add')}
                      </button>
                    </div>
                  </div>
                `;
      });
      html += '</div>';
    }
    html += '</div>';

    // Recommendations section (random items)
    const allItems = data.items.filter(i => i.is_available !== false);
    const shuffled = allItems.sort(() => Math.random() - 0.5).slice(0, 5);
    if (shuffled.length > 0) {
      html += `
              <div class="menu-recs">
                <h3>${t('youMayLike')}</h3>
                <div class="menu-recs-scroll">
                  ${shuffled.map(item => {
        const meta = getItemMeta(item);
        const image = meta?.image || placeholderImage;
        const itemName = getLocalizedName(item, lang);
        return `
                      <div class="rec-card" data-item-id="${item.id}">
                        <img src="${image}" alt="${itemName}" loading="lazy">
                        <div class="rec-info">
                          <div class="rec-name">${itemName}</div>
                          <div class="rec-bottom">
                            <span class="rec-price">${item.price} ₸</span>
                            <button class="rec-add-btn" data-id="${item.id}" data-name="${itemName}" data-price="${item.price}">+</button>
                          </div>
                        </div>
                      </div>
                    `;
      }).join('')}
                </div>
              </div>
            `;
    }

    html += '<div id="menu-msg"></div>';

    // Modal HTML
    html += `
          <div id="item-modal" class="modal-overlay hidden">
            <div class="modal-content">
              <button class="modal-close">&times;</button>
              <img id="modal-img" src="" alt="">
              <div class="modal-body">
                <h3 id="modal-name"></h3>
                <p id="modal-desc"></p>
                <div id="modal-nutrition" class="modal-nutrition"></div>
                <div class="modal-footer">
                  <span id="modal-price" class="modal-price"></span>
                  <button id="modal-add" class="btn">${t('addToCart')}</button>
                </div>
              </div>
            </div>
          </div>
        `;

    container.innerHTML = html;

    // Store items data for modal
    const itemsMap = {};
    data.items.forEach(item => { itemsMap[item.id] = item; });

    // Day select handler
    attachDaySelectHandler(container, navigateTo);

    // Open modal on card click
    container.querySelectorAll('.menu-card, .rec-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('.add-btn')) return;
        const itemId = card.dataset.itemId;
        const item = itemsMap[itemId];
        if (!item) return;
        openModal(item, lang, container);
      });
    });

    // Add to cart handlers
    container.querySelectorAll('.add-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const item = {
          id: btn.dataset.id,
          name: btn.dataset.name,
          price: parseInt(btn.dataset.price)
        };
        addToCart(item);
        showMessage(container, t('addedToCart'));
      });
    });

    // Recommendation add to cart handlers
    container.querySelectorAll('.rec-add-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const item = {
          id: btn.dataset.id,
          name: btn.dataset.name,
          price: parseInt(btn.dataset.price)
        };
        addToCart(item);
        showMessage(container, t('addedToCart'));
      });
    });

    // Modal close handlers
    container.querySelector('.modal-close').addEventListener('click', () => closeModal(container));
    container.querySelector('.modal-overlay').addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) closeModal(container);
    });

  } catch (err) {
    container.innerHTML = `<h2>${t('menuTitle')}</h2><p class="error">${t('error')}: ${err.message || err.error}</p>`;
  }
}

function attachDaySelectHandler(container, navigateTo) {
  const select = container.querySelector('#day-select');
  if (select) {
    select.addEventListener('change', (e) => {
      const day = parseInt(e.target.value);
      loadMenuForDay(container, day, navigateTo);
    });
  }
}

function openModal(item, lang, container) {
  const modal = container.querySelector('#item-modal');
  const meta = getItemMeta(item);
  const image = meta?.image || placeholderImage;
  const itemName = getLocalizedName(item, lang);
  const desc = getLocalizedDesc(meta, lang);

  modal.querySelector('#modal-img').src = image;
  modal.querySelector('#modal-name').textContent = itemName;
  modal.querySelector('#modal-desc').textContent = desc;
  modal.querySelector('#modal-price').textContent = `${item.price} ₸`;

  // Nutrition info
  const nutritionEl = modal.querySelector('#modal-nutrition');
  if (meta && (meta.kcal || meta.protein || meta.fat || meta.carbs)) {
    nutritionEl.innerHTML = `
          <span>${meta.kcal || 0} kcal</span>
          <span>P: ${meta.protein || 0}g</span>
          <span>F: ${meta.fat || 0}g</span>
          <span>C: ${meta.carbs || 0}g</span>
        `;
    nutritionEl.classList.remove('hidden');
  } else {
    nutritionEl.classList.add('hidden');
  }

  // Modal add button
  const addBtn = modal.querySelector('#modal-add');
  addBtn.onclick = () => {
    addToCart({ id: item.id, name: itemName, price: item.price });
    showMessage(container, t('addedToCart'));
    closeModal(container);
  };
  addBtn.disabled = item.is_available === false;

  modal.classList.remove('hidden');
}

function closeModal(container) {
  container.querySelector('#item-modal').classList.add('hidden');
}

function showMessage(container, msg) {
  const msgEl = container.querySelector('#menu-msg');
  msgEl.innerHTML = `<span class="success">${msg}</span>`;
  setTimeout(() => msgEl.innerHTML = '', 2000);
}

