// Admin page - menu management + users CRUD + groups management
import {
  api, adminGetUsers, adminCreateUser, adminUpdateUser, adminDeleteUser,
  adminGetGroups, adminCreateGroup, adminAssignGroup
} from '../api.js';
import { t, getLang } from '../i18n.js';

let currentTab = 'menu';

export async function renderAdmin(container, navigateTo) {
  container.innerHTML = `
    <h2>${t('adminTitle')}</h2>
    <div class="admin-tabs">
      <button id="tab-menu" class="tab-btn active">${t('menuSection')}</button>
      <button id="tab-users" class="tab-btn">${t('usersSection')}</button>
      <button id="tab-groups" class="tab-btn">${t('groupsSection')}</button>
    </div>
    <div id="admin-content"></div>
  `;

  const contentContainer = container.querySelector('#admin-content');
  const tabMenuBtn = container.querySelector('#tab-menu');
  const tabUsersBtn = container.querySelector('#tab-users');
  const tabGroupsBtn = container.querySelector('#tab-groups');

  function setTab(tab) {
    currentTab = tab;
    tabMenuBtn.classList.toggle('active', tab === 'menu');
    tabUsersBtn.classList.toggle('active', tab === 'users');
    tabGroupsBtn.classList.toggle('active', tab === 'groups');
    if (tab === 'menu') {
      renderMenuTab(contentContainer);
    } else if (tab === 'users') {
      renderUsersTab(contentContainer);
    } else {
      renderGroupsTab(contentContainer);
    }
  }

  tabMenuBtn.addEventListener('click', () => setTab('menu'));
  tabUsersBtn.addEventListener('click', () => setTab('users'));
  tabGroupsBtn.addEventListener('click', () => setTab('groups'));

  setTab('menu');
}

// ==================== Menu Tab ====================

async function renderMenuTab(container) {
  container.innerHTML = `
    <div id="admin-actions">
      <button id="reload-btn" class="btn">${t('reload')}</button>
      <button id="save-btn" class="btn btn-primary">${t('save')}</button>
    </div>
    <div id="admin-result"></div>
    <div id="admin-table-container">
      <p>${t('loading')}</p>
    </div>
  `;

  const tableContainer = container.querySelector('#admin-table-container');
  const result = container.querySelector('#admin-result');
  const reloadBtn = container.querySelector('#reload-btn');
  const saveBtn = container.querySelector('#save-btn');

  let menuItems = [];

  function getLocalizedName(item) {
    const lang = getLang();
    if (lang === 'kz' && item.name_kz) return item.name_kz;
    if (lang === 'ru' && item.name_ru) return item.name_ru;
    if (lang === 'en' && item.name_en) return item.name_en;
    return item.name_ru || item.name_kz || item.name_en || '—';
  }

  function renderTable() {
    if (menuItems.length === 0) {
      tableContainer.innerHTML = `<p>${t('noItems')}</p>`;
      return;
    }

    tableContainer.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>${t('name')}</th>
            <th>${t('category')}</th>
            <th>${t('price')}</th>
            <th>${t('qty')}</th>
            <th>${t('available')}</th>
          </tr>
        </thead>
        <tbody>
          ${menuItems.map((item, idx) => `
            <tr data-id="${item.id}">
              <td>${getLocalizedName(item)}</td>
              <td>${item.category}</td>
              <td>${item.price} ₸</td>
              <td><input type="number" class="qty-input" data-idx="${idx}" value="${item.qty}" min="0" style="width:60px"></td>
              <td><input type="checkbox" class="avail-input" data-idx="${idx}" ${item.available ? 'checked' : ''}></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    tableContainer.querySelectorAll('.qty-input').forEach(input => {
      input.addEventListener('change', (e) => {
        const idx = parseInt(e.target.dataset.idx);
        menuItems[idx].qty = parseInt(e.target.value) || 0;
      });
    });

    tableContainer.querySelectorAll('.avail-input').forEach(input => {
      input.addEventListener('change', (e) => {
        const idx = parseInt(e.target.dataset.idx);
        menuItems[idx].available = e.target.checked;
      });
    });
  }

  async function loadMenu() {
    result.innerHTML = '';
    tableContainer.innerHTML = `<p>${t('loading')}</p>`;

    try {
      const data = await api('/admin/menu');
      menuItems = data.items || [];
      renderTable();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message || err.error}</p>`;
      tableContainer.innerHTML = '';
    }
  }

  async function saveMenu() {
    result.innerHTML = `<p>${t('saving')}</p>`;

    try {
      const itemsToSave = menuItems.map(item => ({
        id: item.id,
        qty: item.qty,
        available: item.available
      }));

      const data = await api('/admin/menu', {
        method: 'PUT',
        body: JSON.stringify({ items: itemsToSave })
      });

      menuItems = data.items || [];
      renderTable();
      result.innerHTML = `<p class="success">${t('saved')}</p>`;
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message || err.error}</p>`;
    }
  }

  reloadBtn.addEventListener('click', loadMenu);
  saveBtn.addEventListener('click', saveMenu);

  await loadMenu();
}

// ==================== Users Tab ====================

async function renderUsersTab(container) {
  container.innerHTML = `
    <div id="users-result"></div>
    <div class="users-create-form">
      <h4>${t('createUser')}</h4>
      <div class="form-row">
        <input type="text" id="new-login" placeholder="${t('loginLabel')}" />
        <input type="password" id="new-pin" placeholder="${t('pinLabel')}" />
        <select id="new-role">
          <option value="user">${t('roleUser')}</option>
          <option value="cook">${t('roleCook')}</option>
          <option value="admin">${t('roleAdmin')}</option>
        </select>
        <input type="text" id="new-display-name" placeholder="${t('displayName')}" />
        <button id="create-user-btn" class="btn btn-primary">${t('createUser')}</button>
      </div>
    </div>
    <div id="users-table-container">
      <p>${t('loading')}</p>
    </div>
  `;

  const tableContainer = container.querySelector('#users-table-container');
  const result = container.querySelector('#users-result');
  const createBtn = container.querySelector('#create-user-btn');

  let users = [];
  let editingId = null;

  function getRoleName(role) {
    if (role === 'admin') return t('roleAdmin');
    if (role === 'cook') return t('roleCook');
    return t('roleUser');
  }

  function renderUsersTable() {
    if (users.length === 0) {
      tableContainer.innerHTML = `<p>${t('noItems')}</p>`;
      return;
    }

    tableContainer.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>${t('loginLabel')}</th>
            <th>${t('displayName')}</th>
            <th>${t('role')}</th>
            <th>${t('group')}</th>
            <th>${t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          ${users.map(user => {
      if (editingId === user.id) {
        return `
                <tr data-id="${user.id}">
                  <td>${user.login}</td>
                  <td><input type="text" class="edit-display-name" value="${user.display_name || ''}" /></td>
                  <td>
                    <select class="edit-role">
                      <option value="user" ${user.role === 'user' ? 'selected' : ''}>${t('roleUser')}</option>
                      <option value="cook" ${user.role === 'cook' ? 'selected' : ''}>${t('roleCook')}</option>
                      <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>${t('roleAdmin')}</option>
                    </select>
                  </td>
                  <td>${user.group ? user.group.name : '—'}</td>
                  <td>
                    <input type="password" class="edit-pin" placeholder="${t('pinLabel')}" style="width:80px" />
                    <button class="btn btn-sm save-edit-btn">${t('save')}</button>
                    <button class="btn btn-sm cancel-edit-btn">${t('cancel')}</button>
                  </td>
                </tr>
              `;
      }
      return `
              <tr data-id="${user.id}">
                <td>${user.login}</td>
                <td>${user.display_name || '—'}</td>
                <td>${getRoleName(user.role)}</td>
                <td>${user.group ? user.group.name : '—'}</td>
                <td>
                  <button class="btn btn-sm edit-btn">${t('editUser')}</button>
                  <button class="btn btn-sm btn-danger delete-btn">${t('deleteUser')}</button>
                </td>
              </tr>
            `;
    }).join('')}
        </tbody>
      </table>
    `;

    // Edit button handlers
    tableContainer.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        editingId = row.dataset.id;
        renderUsersTable();
      });
    });

    // Save edit handlers
    tableContainer.querySelectorAll('.save-edit-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const row = e.target.closest('tr');
        const userId = row.dataset.id;
        const role = row.querySelector('.edit-role').value;
        const displayName = row.querySelector('.edit-display-name').value;
        const pin = row.querySelector('.edit-pin').value;

        const payload = { role, display_name: displayName };
        if (pin) payload.pin = pin;

        try {
          await adminUpdateUser(userId, payload);
          result.innerHTML = `<p class="success">${t('userUpdated')}</p>`;
          editingId = null;
          await loadUsers();
        } catch (err) {
          result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
        }
      });
    });

    // Cancel edit handlers
    tableContainer.querySelectorAll('.cancel-edit-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        editingId = null;
        renderUsersTable();
      });
    });

    // Delete handlers
    tableContainer.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const row = e.target.closest('tr');
        const userId = row.dataset.id;

        if (!confirm(t('confirmDeleteUser'))) return;

        try {
          await adminDeleteUser(userId);
          result.innerHTML = `<p class="success">${t('userDeleted')}</p>`;
          await loadUsers();
        } catch (err) {
          let msg = err.message;
          if (err.error === 'cannot_delete_self') msg = t('cannotDeleteSelf');
          if (err.error === 'last_admin') msg = t('cannotDeleteLastAdmin');
          result.innerHTML = `<p class="error">${msg}</p>`;
        }
      });
    });
  }

  async function loadUsers() {
    tableContainer.innerHTML = `<p>${t('loading')}</p>`;

    try {
      const data = await adminGetUsers();
      users = data.users || [];
      renderUsersTable();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('errorLoadingUsers')}: ${err.message}</p>`;
      tableContainer.innerHTML = '';
    }
  }

  // Create user handler
  createBtn.addEventListener('click', async () => {
    const login = container.querySelector('#new-login').value.trim();
    const pin = container.querySelector('#new-pin').value;
    const role = container.querySelector('#new-role').value;
    const displayName = container.querySelector('#new-display-name').value.trim();

    if (!login || !pin) {
      result.innerHTML = `<p class="error">${t('error')}: Login and PIN required</p>`;
      return;
    }

    try {
      await adminCreateUser({ login, pin, role, display_name: displayName });
      result.innerHTML = `<p class="success">${t('userCreated')}</p>`;
      container.querySelector('#new-login').value = '';
      container.querySelector('#new-pin').value = '';
      container.querySelector('#new-role').value = 'user';
      container.querySelector('#new-display-name').value = '';
      await loadUsers();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
    }
  });

  await loadUsers();
}

// ==================== Groups Tab ====================

function getTypeName(type) {
  if (type === 'school') return t('groupTypeSchool');
  if (type === 'university') return t('groupTypeUniversity');
  if (type === 'business') return t('groupTypeBusiness');
  return type;
}

async function renderGroupsTab(container) {
  container.innerHTML = `
    <div id="groups-result"></div>

    <div class="groups-create-form" style="margin-bottom:20px; padding:12px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
      <h4 style="margin-top:0">${t('createGroup')}</h4>
      <div class="form-row" style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
        <input type="text" id="new-group-name" placeholder="${t('groupName')}" style="flex:1; min-width:120px" />
        <select id="new-group-type" style="min-width:120px">
          <option value="school">${t('groupTypeSchool')}</option>
          <option value="university">${t('groupTypeUniversity')}</option>
          <option value="business">${t('groupTypeBusiness')}</option>
        </select>
        <button id="create-group-btn" class="btn btn-primary">${t('createGroup')}</button>
      </div>
    </div>

    <div id="groups-table-container">
      <p>${t('loading')}</p>
    </div>

    <div class="assign-section" style="margin-top:24px; padding:12px; border:1px solid #ddd; border-radius:8px; background:#fafafa;">
      <h4 style="margin-top:0">${t('assignGroup')}</h4>
      <div class="form-row" style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
        <select id="assign-user" style="flex:1; min-width:140px">
          <option value="">${t('selectUser')}</option>
        </select>
        <select id="assign-group" style="flex:1; min-width:140px">
          <option value="">${t('selectGroup')}</option>
        </select>
        <button id="assign-btn" class="btn btn-primary">${t('assignGroup')}</button>
        <button id="remove-group-btn" class="btn btn-danger">${t('removeGroup')}</button>
      </div>
    </div>
  `;

  const result = container.querySelector('#groups-result');
  const tableContainer = container.querySelector('#groups-table-container');
  const createBtn = container.querySelector('#create-group-btn');
  const assignBtn = container.querySelector('#assign-btn');
  const removeBtn = container.querySelector('#remove-group-btn');
  const userSelect = container.querySelector('#assign-user');
  const groupSelect = container.querySelector('#assign-group');

  let groups = [];
  let users = [];

  // ---- Render groups table ----
  function renderGroupsTable() {
    if (groups.length === 0) {
      tableContainer.innerHTML = `<p>${t('noGroups')}</p>`;
      return;
    }

    tableContainer.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>${t('groupName')}</th>
            <th>${t('groupType')}</th>
            <th>${t('userCount')}</th>
          </tr>
        </thead>
        <tbody>
          ${groups.map(g => `
            <tr>
              <td>${g.name}</td>
              <td>${getTypeName(g.type)}</td>
              <td>${g.user_count}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // ---- Populate selects ----
  function populateSelects() {
    // Users
    userSelect.innerHTML = `<option value="">${t('selectUser')}</option>`;
    users.forEach(u => {
      const groupLabel = u.group ? ` [${u.group.name}]` : '';
      userSelect.innerHTML += `<option value="${u.id}">${u.display_name || u.login} (${u.login})${groupLabel}</option>`;
    });

    // Groups
    groupSelect.innerHTML = `<option value="">${t('selectGroup')}</option>`;
    groups.forEach(g => {
      groupSelect.innerHTML += `<option value="${g.id}">${g.name} (${getTypeName(g.type)})</option>`;
    });
  }

  // ---- Load data ----
  async function loadAll() {
    tableContainer.innerHTML = `<p>${t('loading')}</p>`;
    try {
      const [groupsData, usersData] = await Promise.all([
        adminGetGroups(),
        adminGetUsers()
      ]);
      groups = groupsData.groups || [];
      users = usersData.users || [];
      renderGroupsTable();
      populateSelects();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
    }
  }

  // ---- Create group ----
  createBtn.addEventListener('click', async () => {
    const name = container.querySelector('#new-group-name').value.trim();
    const type = container.querySelector('#new-group-type').value;

    if (!name) {
      result.innerHTML = `<p class="error">${t('error')}: ${t('groupName')} required</p>`;
      return;
    }

    try {
      await adminCreateGroup({ name, type });
      result.innerHTML = `<p class="success">${t('groupCreated')}</p>`;
      container.querySelector('#new-group-name').value = '';
      await loadAll();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
    }
  });

  // ---- Assign group ----
  assignBtn.addEventListener('click', async () => {
    const userId = userSelect.value;
    const groupId = groupSelect.value;

    if (!userId || !groupId) {
      result.innerHTML = `<p class="error">${t('selectUser')} / ${t('selectGroup')}</p>`;
      return;
    }

    try {
      await adminAssignGroup(userId, groupId);
      result.innerHTML = `<p class="success">${t('groupAssigned')}</p>`;
      await loadAll();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
    }
  });

  // ---- Remove group ----
  removeBtn.addEventListener('click', async () => {
    const userId = userSelect.value;
    if (!userId) {
      result.innerHTML = `<p class="error">${t('selectUser')}</p>`;
      return;
    }

    try {
      await adminAssignGroup(userId, null);
      result.innerHTML = `<p class="success">${t('groupRemoved')}</p>`;
      await loadAll();
    } catch (err) {
      result.innerHTML = `<p class="error">${t('error')}: ${err.message}</p>`;
    }
  });

  await loadAll();
}
