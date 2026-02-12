import { getToken, getUser, getCatalog, getDailyMenu, saveDailyMenu } from '../api.js';
import { t, getLang } from '../i18n.js';

function formatDate(d) {
    return d.toISOString().slice(0, 10);
}

function getDateLabel(d) {
    const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    return `${days[d.getDay()]} ${d.getDate().toString().padStart(2, '0')}.${(d.getMonth() + 1).toString().padStart(2, '0')}`;
}

export async function renderDailyMenu(container, navigateTo) {
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

    // Build date options: today + 3 days forward
    const dates = [];
    for (let i = 0; i < 4; i++) {
        const d = new Date();
        d.setDate(d.getDate() + i);
        dates.push(d);
    }

    let selectedDate = formatDate(dates[0]);
    const locationId = 'loc-1';
    const mealSlot = 'lunch';

    container.innerHTML = `<h2>Меню дня</h2><p>${t('loading')}</p>`;

    await loadDailyMenuEditor(container, locationId, selectedDate, mealSlot, dates, navigateTo);
}

async function loadDailyMenuEditor(container, locationId, selectedDate, mealSlot, dates, navigateTo) {
    try {
        // Load catalog and current daily menu in parallel
        const [catalogData, dailyData] = await Promise.all([
            getCatalog(locationId),
            getDailyMenu(locationId, selectedDate, mealSlot)
        ]);

        const catalogItems = catalogData.items || [];
        const dailyItems = dailyData.items || [];

        // Build lookup: menu_item_id -> daily item data
        const dailyMap = {};
        dailyItems.forEach(di => {
            dailyMap[di.menu_item_id] = di;
        });

        let html = `<h2>Меню дня</h2>`;

        // Date selector
        html += '<div class="day-selector">';
        html += '<select id="dm-date-select" class="day-select">';
        dates.forEach(d => {
            const val = formatDate(d);
            const sel = val === selectedDate ? ' selected' : '';
            html += `<option value="${val}"${sel}>${getDateLabel(d)}</option>`;
        });
        html += '</select>';
        html += '</div>';

        if (catalogItems.length === 0) {
            html += '<p>Каталог пуст.</p>';
            container.innerHTML = html;
            attachDateHandler(container, locationId, mealSlot, dates, navigateTo);
            return;
        }

        // Group catalog by category
        const categories = {};
        catalogItems.forEach(item => {
            if (!categories[item.category]) categories[item.category] = [];
            categories[item.category].push(item);
        });

        html += '<form id="dm-form">';
        html += '<table class="dm-table"><thead><tr>';
        html += '<th>✓</th><th>Блюдо</th><th>Категория</th><th>Цена</th><th>Остаток</th>';
        html += '</tr></thead><tbody>';

        for (const [category, items] of Object.entries(categories)) {
            items.forEach(item => {
                const inDaily = !!dailyMap[item.id];
                const di = dailyMap[item.id] || {};
                const checked = inDaily ? 'checked' : '';
                const stockVal = di.stock_qty != null ? di.stock_qty : '';
                const lang = getLang();
                const name = lang === 'kz' && item.name_kz ? item.name_kz : item.name_ru;

                html += `<tr>`;
                html += `<td><input type="checkbox" class="dm-check" data-id="${item.id}" ${checked}></td>`;
                html += `<td>${name}</td>`;
                html += `<td>${category}</td>`;
                html += `<td>${item.base_price} ₸</td>`;
                html += `<td><input type="number" class="dm-stock" data-id="${item.id}" value="${stockVal}" min="0" placeholder="∞" style="width:60px"></td>`;
                html += `</tr>`;
            });
        }

        html += '</tbody></table>';
        html += '<div style="margin-top:12px">';
        html += `<button type="submit" class="btn" id="dm-save">Сохранить</button>`;
        html += ' <span id="dm-msg"></span>';
        html += '</div>';
        html += '</form>';

        container.innerHTML = html;

        // Date change handler
        attachDateHandler(container, locationId, mealSlot, dates, navigateTo);

        // Save handler
        container.querySelector('#dm-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const msgEl = container.querySelector('#dm-msg');
            const saveBtn = container.querySelector('#dm-save');

            const items = [];
            container.querySelectorAll('.dm-check').forEach(cb => {
                if (cb.checked) {
                    const itemId = cb.dataset.id;
                    const stockInput = container.querySelector(`.dm-stock[data-id="${itemId}"]`);
                    const stockVal = stockInput.value.trim();
                    items.push({
                        menu_item_id: itemId,
                        stock_qty: stockVal !== '' ? parseInt(stockVal) : null,
                        is_available: true
                    });
                }
            });

            saveBtn.disabled = true;
            msgEl.textContent = 'Сохранение...';

            try {
                await saveDailyMenu({
                    location_id: locationId,
                    menu_date: selectedDate,
                    meal_slot: mealSlot,
                    items
                });
                msgEl.innerHTML = '<span class="success">✓ Сохранено!</span>';
            } catch (err) {
                msgEl.innerHTML = `<span class="error">Ошибка: ${err.message || err.error}</span>`;
            } finally {
                saveBtn.disabled = false;
            }
        });

    } catch (err) {
        container.innerHTML = `<h2>Меню дня</h2><p class="error">Ошибка: ${err.message || err.error}</p>`;
    }
}

function attachDateHandler(container, locationId, mealSlot, dates, navigateTo) {
    const select = container.querySelector('#dm-date-select');
    if (select) {
        select.addEventListener('change', (e) => {
            loadDailyMenuEditor(container, locationId, e.target.value, mealSlot, dates, navigateTo);
        });
    }
}
