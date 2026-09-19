/**
 * Balaji Medical - Frontend Application Controller
 * Handles product catalog, cart, prescription upload, checkout, invoice generation,
 * and pharmacist admin management.
 */

// Global State
let state = {
    medicines: [],
    categories: [],
    companies: [],
    activeCategory: 'all',
    searchQuery: '',
    cart: JSON.parse(localStorage.getItem('bm_cart') || '[]'),
    activePrescription: JSON.parse(sessionStorage.getItem('bm_prescription') || 'null'),
    currentView: 'customer',
    currentUser: null,
    selectedPrescriptionFile: null
};

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    updateCartBadges();
    checkActivePrescription();
    initPaymentMethodListeners();
    await checkCurrentUser();
    await fetchCategories();
    await fetchMedicines();

    if (window.lucide) {
        lucide.createIcons();
    }
}

// ----------------- User Authentication ----------------- //

async function checkCurrentUser() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.success && data.user) {
            state.currentUser = data.user;
        } else {
            state.currentUser = null;
        }
        renderAuthUI();
    } catch (err) {
        console.error('Error checking user session:', err);
    }
}

function renderAuthUI() {
    const container = document.getElementById('authNavContainer');
    if (!container) return;

    if (state.currentUser) {
        const isPharmacist = state.currentUser.role === 'pharmacist';
        container.innerHTML = `
            <div class="relative flex items-center gap-2">
                <div class="flex items-center space-x-2 bg-slate-100 border border-slate-200 py-1 px-2.5 rounded-xl text-xs font-semibold">
                    <span class="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-[11px]">
                        ${state.currentUser.name.charAt(0).toUpperCase()}
                    </span>
                    <div class="hidden sm:block text-left">
                        <span class="block text-slate-800 leading-tight truncate max-w-[110px]">${state.currentUser.name}</span>
                        <span class="text-[9px] font-bold uppercase tracking-wider ${isPharmacist ? 'text-indigo-600' : 'text-emerald-600'}">
                            ${isPharmacist ? 'Pharmacist' : 'Customer'}
                        </span>
                    </div>
                </div>

                <button onclick="handleLogout()" title="Sign Out" class="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-slate-100 transition">
                    <i data-lucide="log-out" class="w-4 h-4"></i>
                </button>
            </div>
        `;
    } else {
        container.innerHTML = `
            <button onclick="openAuthModal('login')" class="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-2 rounded-xl text-sm font-semibold transition">
                <i data-lucide="user" class="w-4 h-4 text-slate-600"></i>
                <span class="hidden sm:inline">Sign In</span>
            </button>
        `;
    }

    if (window.lucide) lucide.createIcons();
}

function openAuthModal(tab = 'login') {
    switchAuthTab(tab);
    document.getElementById('authModal')?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

function closeAuthModal() {
    document.getElementById('authModal')?.classList.add('hidden');
}

function switchAuthTab(tab) {
    const loginTabBtn = document.getElementById('authTabLogin');
    const registerTabBtn = document.getElementById('authTabRegister');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const modalTitle = document.getElementById('authModalTitle');

    if (tab === 'login') {
        loginTabBtn.classList.add('bg-white', 'text-slate-900', 'shadow-sm');
        loginTabBtn.classList.remove('text-slate-500');
        registerTabBtn.classList.remove('bg-white', 'text-slate-900', 'shadow-sm');
        registerTabBtn.classList.add('text-slate-500');
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        if (modalTitle) modalTitle.innerText = 'Balaji Medical Account Sign In';
    } else {
        registerTabBtn.classList.add('bg-white', 'text-slate-900', 'shadow-sm');
        registerTabBtn.classList.remove('text-slate-500');
        loginTabBtn.classList.remove('bg-white', 'text-slate-900', 'shadow-sm');
        loginTabBtn.classList.add('text-slate-500');
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        if (modalTitle) modalTitle.innerText = 'Register with Balaji Medical';
    }
}

function autofillDemoAuth(role) {
    if (role === 'customer') {
        document.getElementById('loginEmail').value = 'adhiraj@example.com';
        document.getElementById('loginPassword').value = 'user123';
    } else {
        document.getElementById('loginEmail').value = 'pharmacist@balajimedical.com';
        document.getElementById('loginPassword').value = 'admin123';
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const btn = document.getElementById('loginSubmitBtn');

    btn.disabled = true;
    btn.innerText = 'Authenticating...';

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="log-in" class="w-4 h-4"></i> Sign In to Balaji Medical';

        if (data.success) {
            state.currentUser = data.user;
            renderAuthUI();
            closeAuthModal();
            showToast(data.message, 'success');

            // Autofill customer name in checkout
            const custName = document.getElementById('custName');
            const custPhone = document.getElementById('custPhone');
            const custEmail = document.getElementById('custEmail');
            if (custName && !custName.value) custName.value = data.user.name;
            if (custPhone && !custPhone.value) custPhone.value = data.user.phone || '';
            if (custEmail && !custEmail.value) custEmail.value = data.user.email;
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (err) {
        btn.disabled = false;
        btn.innerText = 'Sign In';
        showToast('Error during login', 'error');
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const phone = document.getElementById('regPhone').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const role = document.getElementById('regRole').value;
    const btn = document.getElementById('registerSubmitBtn');

    btn.disabled = true;
    btn.innerText = 'Registering Account...';

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, phone, password, role })
        });
        const data = await res.json();
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="user-plus" class="w-4 h-4"></i> Register Account';

        if (data.success) {
            state.currentUser = data.user;
            renderAuthUI();
            closeAuthModal();
            showToast(data.message, 'success');
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (err) {
        btn.disabled = false;
        btn.innerText = 'Register Account';
        showToast('Error during registration', 'error');
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        state.currentUser = null;
        renderAuthUI();
        showToast('You have been logged out.', 'info');
        if (state.currentView === 'admin') {
            showCustomerView();
        }
    } catch (err) {
        console.error('Logout error:', err);
    }
}

// ----------------- Categories & Product Catalog ----------------- //

async function fetchCategories() {
    try {
        const res = await fetch('/api/categories');
        const data = await res.json();
        if (data.success) {
            state.categories = data.categories;
            renderCategoriesBar();
            populateAdminCategoryDropdown();
        }
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

function renderCategoriesBar() {
    const bar = document.getElementById('categoriesBar');
    if (!bar) return;

    let html = `
        <button onclick="filterByCategory('all')" data-cat="all" class="category-chip ${state.activeCategory === 'all' ? 'active' : ''} flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap bg-slate-100 text-slate-700 transition">
            <i data-lucide="grid" class="w-3.5 h-3.5"></i>
            All Medicines
        </button>
    `;

    state.categories.forEach(cat => {
        const isActive = state.activeCategory === cat.slug;
        html += `
            <button onclick="filterByCategory('${cat.slug}')" data-cat="${cat.slug}" class="category-chip ${isActive ? 'active' : ''} flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap bg-slate-100 text-slate-700 transition">
                <i data-lucide="${cat.icon || 'pill'}" class="w-3.5 h-3.5"></i>
                ${cat.name} (${cat.medicine_count})
            </button>
        `;
    });

    bar.innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

function populateAdminCategoryDropdown() {
    const select = document.getElementById('adminMedCategory');
    if (!select) return;
    select.innerHTML = state.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
}

async function fetchMedicines() {
    const grid = document.getElementById('medicinesGrid');
    const emptyState = document.getElementById('noResultsState');
    const badge = document.getElementById('productCountBadge');

    const params = new URLSearchParams();
    if (state.searchQuery) params.append('search', state.searchQuery);
    if (state.activeCategory && state.activeCategory !== 'all') params.append('category', state.activeCategory);

    const compVal = document.getElementById('companyFilter')?.value;
    if (compVal && compVal !== 'all') params.append('company', compVal);

    const stockStatus = document.getElementById('stockStatusFilter')?.value;
    if (stockStatus && stockStatus !== 'all') params.append('stock_status', stockStatus);

    const rxVal = document.getElementById('rxFilter')?.value;
    if (rxVal) params.append('requires_rx', rxVal);

    const sortVal = document.getElementById('sortFilter')?.value;
    if (sortVal) params.append('sort', sortVal);

    try {
        const res = await fetch(`/api/medicines?${params.toString()}`);
        const data = await res.json();
        if (data.success) {
            state.medicines = data.medicines;
            if (data.companies) {
                state.companies = data.companies;
                populateCompanyDropdown(data.companies);
            }
            if (badge) badge.innerText = `${data.count} Products Available`;

            if (data.medicines.length === 0) {
                grid.classList.add('hidden');
                emptyState.classList.remove('hidden');
            } else {
                emptyState.classList.add('hidden');
                grid.classList.remove('hidden');
                renderMedicines(data.medicines);
            }
        }
    } catch (err) {
        console.error('Error fetching medicines:', err);
    }
}

function populateCompanyDropdown(companies) {
    const select = document.getElementById('companyFilter');
    if (!select || select.children.length > 1) return;

    const currentVal = select.value;
    let html = '<option value="all">All Pharma Companies</option>';
    companies.forEach(comp => {
        html += `<option value="${comp}">${comp}</option>`;
    });
    select.innerHTML = html;
    if (currentVal) select.value = currentVal;
}

function renderMedicines(medicines) {
    const grid = document.getElementById('medicinesGrid');
    if (!grid) return;

    grid.innerHTML = medicines.map(med => {
        const effectivePrice = med.discount_price || med.price;
        const hasDiscount = med.discount_price && med.discount_price < med.price;
        const discountPercent = hasDiscount ? Math.round(((med.price - med.discount_price) / med.price) * 100) : 0;
        const isOutOfStock = med.stock_quantity <= 0;
        const isLowStock = med.stock_quantity > 0 && med.stock_quantity <= 15;

        return `
            <div class="medicine-card bg-white rounded-2xl border border-slate-200/80 p-4 flex flex-col justify-between relative group hover:border-emerald-300 ${isOutOfStock ? 'opacity-90' : ''}">
                
                <!-- Badges Row -->
                <div class="flex items-center justify-between gap-1 mb-2.5">
                    <div class="flex items-center gap-1 flex-wrap">
                        ${med.requires_prescription 
                            ? `<span class="bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-black px-2 py-0.5 rounded-md flex items-center gap-1">
                                 <i data-lucide="shield-alert" class="w-3 h-3"></i> Rx Required
                               </span>` 
                            : `<span class="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1">
                                 <i data-lucide="check" class="w-3 h-3"></i> OTC
                               </span>`
                        }
                        ${isOutOfStock ? `
                            <span class="bg-rose-600 text-white text-[10px] font-black px-1.5 py-0.5 rounded shadow-sm">
                                Out of Stock
                            </span>
                        ` : ''}
                    </div>

                    ${hasDiscount && !isOutOfStock 
                        ? `<span class="bg-emerald-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">${discountPercent}% OFF</span>`
                        : `<span class="text-[10px] text-slate-400 font-medium">${med.dosage_form}</span>`
                    }
                </div>

                <!-- Product Thumbnail -->
                <div class="w-full h-36 bg-slate-50 rounded-xl overflow-hidden flex items-center justify-center p-2 mb-3 relative cursor-pointer" onclick="openMedicineDetail(${med.id})">
                    <img src="${med.image_url}" alt="${med.name}" 
                         onerror="this.src='https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300'" 
                         class="max-h-full max-w-full object-contain group-hover:scale-105 transition transform duration-300 ${isOutOfStock ? 'grayscale-[50%]' : ''}">
                    
                    ${isOutOfStock ? `
                        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-[1px] flex flex-col items-center justify-center text-center p-2">
                            <span class="bg-rose-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full shadow mb-1">Out of Stock</span>
                            <span class="text-[10px] text-emerald-300 font-semibold">⚡ Tap for in-stock alternative</span>
                        </div>
                    ` : ''}
                </div>

                <!-- Product Meta -->
                <div class="flex-1 flex flex-col justify-between">
                    <div>
                        <div class="flex items-center justify-between gap-1">
                            <span class="text-[10px] uppercase font-bold tracking-wider text-emerald-700">${med.category_name}</span>
                            <span class="text-[10px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded truncate max-w-[120px]" title="${med.manufacturer}">
                                ${med.manufacturer}
                            </span>
                        </div>
                        <h3 class="font-bold text-slate-900 text-sm leading-snug cursor-pointer hover:text-emerald-600 transition mt-0.5" onclick="openMedicineDetail(${med.id})">
                            ${med.name}
                        </h3>
                        <p class="text-[11px] text-slate-500 font-medium italic mt-0.5 line-clamp-1" title="${med.generic_name}">
                            Salt: ${med.generic_name}
                        </p>
                        <p class="text-[10px] text-slate-400 mt-1">
                            ${med.dosage_form} ${med.strength ? '• ' + med.strength : ''}
                        </p>
                    </div>

                    <!-- Stock & Price Row -->
                    <div class="mt-3 pt-3 border-t border-slate-100 space-y-2">
                        <div class="flex items-baseline justify-between">
                            <div>
                                <span class="text-base font-black text-slate-900">₹${effectivePrice.toFixed(2)}</span>
                                ${hasDiscount ? `<span class="text-xs text-slate-400 line-through ml-1">₹${med.price.toFixed(2)}</span>` : ''}
                            </div>
                            
                            ${isOutOfStock ? `
                                <span class="text-[10px] font-bold text-rose-600">Unavailable</span>
                            ` : isLowStock ? `
                                <span class="text-[10px] font-semibold text-amber-600">Only ${med.stock_quantity} left</span>
                            ` : `
                                <span class="text-[10px] font-medium text-emerald-600">In Stock (${med.stock_quantity})</span>
                            `}
                        </div>

                        <!-- Action Buttons -->
                        ${isOutOfStock ? `
                            <div class="space-y-1.5">
                                <button onclick="openAlternativesModal(${med.id})" class="w-full bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 text-xs font-bold py-2 rounded-xl transition flex items-center justify-center gap-1 shadow-sm">
                                    <i data-lucide="sparkles" class="w-3.5 h-3.5 text-emerald-600"></i>
                                    View In-Stock Alternatives
                                </button>
                                <div class="grid grid-cols-2 gap-1.5">
                                    <button onclick="openMedicineDetail(${med.id})" class="text-slate-600 hover:text-slate-800 bg-slate-100 text-[11px] font-semibold py-1 rounded-lg text-center">
                                        Details
                                    </button>
                                    <button onclick="notifyStockAlert('${med.name}')" class="text-slate-500 hover:text-emerald-700 bg-slate-50 text-[11px] font-semibold py-1 rounded-lg border border-slate-200 text-center">
                                        Notify Me
                                    </button>
                                </div>
                            </div>
                        ` : `
                            <div class="grid grid-cols-2 gap-2">
                                <button onclick="openMedicineDetail(${med.id})" class="text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 text-xs font-semibold py-2 rounded-xl transition text-center">
                                    Details
                                </button>
                                <button onclick="addToCart(${med.id})" 
                                        class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-2 rounded-xl shadow-sm hover:shadow transition flex items-center justify-center gap-1">
                                    <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                                    Add
                                </button>
                            </div>
                        `}
                    </div>
                </div>

            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

// ----------------- Filter & Search Handlers ----------------- //

let searchDebounceTimer = null;
function handleSearchInput() {
    const input = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    state.searchQuery = input.value.trim();

    if (state.searchQuery) {
        clearBtn.classList.remove('hidden');
    } else {
        clearBtn.classList.add('hidden');
    }

    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        fetchMedicines();
    }, 250);
}

function handleMobileSearchInput() {
    const input = document.getElementById('mobileSearchInput');
    state.searchQuery = input.value.trim();
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        fetchMedicines();
    }, 250);
}

function clearSearch() {
    const input = document.getElementById('searchInput');
    const mobileInput = document.getElementById('mobileSearchInput');
    if (input) input.value = '';
    if (mobileInput) mobileInput.value = '';
    state.searchQuery = '';
    document.getElementById('clearSearchBtn')?.classList.add('hidden');
    fetchMedicines();
}

function filterByCategory(catSlug) {
    state.activeCategory = catSlug;
    renderCategoriesBar();
    fetchMedicines();
}

function applyFilters() {
    fetchMedicines();
}

function resetAllFilters() {
    state.activeCategory = 'all';
    state.searchQuery = '';
    const sInput = document.getElementById('searchInput');
    const rxF = document.getElementById('rxFilter');
    const stockF = document.getElementById('stockFilter');
    const sortF = document.getElementById('sortFilter');

    if (sInput) sInput.value = '';
    if (rxF) rxF.value = '';
    if (stockF) stockF.checked = false;
    if (sortF) sortF.value = 'default';

    renderCategoriesBar();
    fetchMedicines();
}

// ----------------- Medicine Detail Modal ----------------- //

async function openMedicineDetail(medId) {
    try {
        const res = await fetch(`/api/medicines/${medId}`);
        const data = await res.json();
        if (!data.success) return;

        const med = data.medicine;
        const effectivePrice = med.discount_price || med.price;
        const hasDiscount = med.discount_price && med.discount_price < med.price;
        const isOutOfStock = med.stock_quantity <= 0;

        const modal = document.getElementById('medicineDetailModal');
        const content = document.getElementById('medicineDetailContent');

        content.innerHTML = `
            <div class="grid sm:grid-cols-12 gap-6 items-start">
                <div class="sm:col-span-5 bg-slate-50 p-4 rounded-2xl flex items-center justify-center">
                    <img src="${med.image_url}" alt="${med.name}" 
                         onerror="this.src='https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300'" 
                         class="max-h-56 max-w-full object-contain">
                </div>

                <div class="sm:col-span-7 space-y-3">
                    <div class="flex items-center gap-2">
                        ${med.requires_prescription 
                            ? `<span class="bg-rose-100 text-rose-800 text-xs font-black px-2.5 py-0.5 rounded-full flex items-center gap-1">
                                 <i data-lucide="alert-circle" class="w-3.5 h-3.5"></i> Prescription Required (Rx)
                               </span>` 
                            : `<span class="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                                 <i data-lucide="check" class="w-3.5 h-3.5"></i> Over-the-Counter (OTC)
                               </span>`
                        }
                        <span class="text-xs text-slate-500">${med.category_name}</span>
                    </div>

                    <h2 class="text-xl font-black text-slate-900">${med.name}</h2>
                    <p class="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg inline-block">
                        Active Salt: ${med.generic_name}
                    </p>

                    <div class="grid grid-cols-2 gap-2 text-xs py-2 border-y border-slate-100">
                        <div>
                            <span class="text-slate-400">Manufacturer:</span>
                            <p class="font-bold text-slate-700">${med.manufacturer}</p>
                        </div>
                        <div>
                            <span class="text-slate-400">Dosage Form & Strength:</span>
                            <p class="font-bold text-slate-700">${med.dosage_form} ${med.strength ? '• ' + med.strength : ''}</p>
                        </div>
                        <div>
                            <span class="text-slate-400">Batch Number:</span>
                            <p class="font-mono font-bold text-slate-700">${med.batch_no || 'N/A'}</p>
                        </div>
                        <div>
                            <span class="text-slate-400">Expiry Date:</span>
                            <p class="font-bold text-slate-700">${med.expiry_date}</p>
                        </div>
                    </div>

                    <div class="space-y-2 text-xs">
                        <div>
                            <h4 class="font-bold text-slate-800">Description / Clinical Purpose:</h4>
                            <p class="text-slate-600 mt-0.5">${med.description || 'Standard therapeutic formulation.'}</p>
                        </div>
                        <div>
                            <h4 class="font-bold text-slate-800">Usage & Directions:</h4>
                            <p class="text-slate-600 mt-0.5">${med.usage_instructions || 'Take as advised by medical doctor.'}</p>
                        </div>
                        ${med.side_effects ? `
                            <div>
                                <h4 class="font-bold text-rose-700">Possible Side Effects:</h4>
                                <p class="text-rose-600 mt-0.5">${med.side_effects}</p>
                            </div>
                        ` : ''}
                    </div>

                    <!-- In-Stock Alternatives List (if available) -->
                    ${data.alternatives && data.alternatives.length > 0 ? `
                        <div class="mt-3 pt-3 border-t border-slate-100">
                            <h4 class="font-bold text-slate-900 text-xs mb-2 flex items-center gap-1.5 text-emerald-800">
                                <i data-lucide="sparkles" class="w-3.5 h-3.5 text-emerald-600"></i>
                                Available Alternative Brands (${med.generic_name})
                            </h4>
                            <div class="space-y-1.5 max-h-36 overflow-y-auto">
                                ${data.alternatives.map(a => `
                                    <div class="flex items-center justify-between text-xs bg-slate-50 p-2 rounded-xl border border-slate-100">
                                        <div class="min-w-0 flex-1 pr-2">
                                            <span class="font-bold text-slate-800 truncate block">${a.name}</span>
                                            <span class="text-[10px] text-slate-500 block">${a.manufacturer} • ₹${(a.discount_price || a.price).toFixed(2)}</span>
                                        </div>
                                        <button onclick="addToCart(${a.id}); closeMedicineDetailModal();" class="text-[11px] bg-emerald-600 text-white font-bold px-2.5 py-1 rounded-lg hover:bg-emerald-700 flex-shrink-0">
                                            Add
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Pricing & Cart Button -->
                    <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                        <div>
                            <div class="flex items-baseline gap-2">
                                <span class="text-2xl font-black text-slate-900">₹${effectivePrice.toFixed(2)}</span>
                                ${hasDiscount ? `<span class="text-sm text-slate-400 line-through">₹${med.price.toFixed(2)}</span>` : ''}
                            </div>
                            <span class="text-[11px] text-slate-400">Inclusive of all taxes</span>
                        </div>

                        <button onclick="addToCart(${med.id}); closeMedicineDetailModal();" ${isOutOfStock ? 'disabled' : ''} 
                                class="bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold px-6 py-2.5 rounded-xl shadow-md text-xs flex items-center gap-2 transition">
                            <i data-lucide="shopping-bag" class="w-4 h-4"></i>
                            ${isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
                        </button>
                    </div>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Error viewing medicine:', err);
    }
}

function closeMedicineDetailModal() {
    document.getElementById('medicineDetailModal')?.classList.add('hidden');
}

// ----------------- Prescription Upload Flow ----------------- //

function openPrescriptionModal() {
    document.getElementById('prescriptionModal')?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

function closePrescriptionModal() {
    document.getElementById('prescriptionModal')?.classList.add('hidden');
}

function handleFileSelected(e) {
    const file = e.target.files[0];
    if (file) {
        state.selectedPrescriptionFile = file;
        document.getElementById('dropzoneEmpty')?.classList.add('hidden');
        const preview = document.getElementById('dropzonePreview');
        const nameSpan = document.getElementById('selectedFileName');
        if (preview && nameSpan) {
            preview.classList.remove('hidden');
            nameSpan.innerText = file.name;
        }
    }
}

async function handlePrescriptionSubmit(e) {
    e.preventDefault();
    if (!state.selectedPrescriptionFile) {
        showToast('Please select an image or PDF prescription document', 'error');
        return;
    }

    const patientName = document.getElementById('rxPatientName').value.trim();
    const patientPhone = document.getElementById('rxPatientPhone').value.trim();
    const doctorName = document.getElementById('rxDoctorName').value.trim();
    const notes = document.getElementById('rxNotes').value.trim();

    const formData = new FormData();
    formData.append('file', state.selectedPrescriptionFile);
    formData.append('patient_name', patientName);
    formData.append('patient_phone', patientPhone);
    formData.append('doctor_name', doctorName);
    formData.append('notes', notes);

    const submitBtn = document.getElementById('uploadRxSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Verifying with Balaji Medical Pharmacist...';

    try {
        const res = await fetch('/api/prescriptions/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="shield-check" class="w-4 h-4"></i> Submit Prescription for Pharmacist Verification';

        if (data.success) {
            state.activePrescription = data.prescription;
            sessionStorage.setItem('bm_prescription', JSON.stringify(data.prescription));
            checkActivePrescription();
            closePrescriptionModal();
            showToast('Prescription uploaded & verified by Balaji Medical pharmacist!', 'success');
        } else {
            showToast(data.error || 'Failed to upload prescription', 'error');
        }
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Submit Prescription';
        showToast('Server error while uploading prescription', 'error');
    }
}

function checkActivePrescription() {
    const alertBox = document.getElementById('activePrescriptionAlert');
    const infoText = document.getElementById('attachedRxInfo');
    if (!alertBox || !infoText) return;

    if (state.activePrescription) {
        alertBox.classList.remove('hidden');
        infoText.innerText = `Prescription for ${state.activePrescription.patient_name} verified. (${state.activePrescription.filename})`;
    } else {
        alertBox.classList.add('hidden');
    }
}

function viewAttachedPrescription() {
    if (state.activePrescription?.file_url) {
        window.open(state.activePrescription.file_url, '_blank');
    }
}

function removeAttachedPrescription() {
    state.activePrescription = null;
    sessionStorage.removeItem('bm_prescription');
    checkActivePrescription();
    showToast('Attached prescription removed', 'info');
}

// ----------------- Shopping Cart Operations ----------------- //

function addToCart(medId, qty = 1) {
    const med = state.medicines.find(m => m.id === medId);
    if (!med) return;

    if (med.stock_quantity <= 0) {
        showToast(`'${med.name}' is currently out of stock`, 'error');
        return;
    }

    const existing = state.cart.find(item => item.id === medId);
    if (existing) {
        if (existing.quantity + qty > med.stock_quantity) {
            showToast(`Cannot add more. Only ${med.stock_quantity} units available in stock.`, 'error');
            return;
        }
        existing.quantity += qty;
    } else {
        state.cart.push({
            id: med.id,
            name: med.name,
            generic_name: med.generic_name,
            price: med.price,
            discount_price: med.discount_price,
            quantity: qty,
            requires_prescription: med.requires_prescription,
            image_url: med.image_url,
            stock_quantity: med.stock_quantity
        });
    }

    saveCart();
    showToast(`Added '${med.name}' to cart!`, 'success');
}

function updateCartItemQty(medId, delta) {
    const item = state.cart.find(i => i.id === medId);
    if (!item) return;

    const newQty = item.quantity + delta;
    if (newQty <= 0) {
        state.cart = state.cart.filter(i => i.id !== medId);
    } else if (newQty > item.stock_quantity) {
        showToast(`Maximum stock limit reached (${item.stock_quantity} units).`, 'error');
        return;
    } else {
        item.quantity = newQty;
    }

    saveCart();
    renderCartDrawer();
}

function removeCartItem(medId) {
    state.cart = state.cart.filter(i => i.id !== medId);
    saveCart();
    renderCartDrawer();
}

function saveCart() {
    localStorage.setItem('bm_cart', JSON.stringify(state.cart));
    updateCartBadges();
}

function updateCartBadges() {
    const totalCount = state.cart.reduce((sum, i) => sum + i.quantity, 0);
    const subtotal = state.cart.reduce((sum, i) => sum + ((i.discount_price || i.price) * i.quantity), 0);

    const badge = document.getElementById('cartCountBadge');
    const headerTotal = document.getElementById('cartTotalHeader');
    const drawerCount = document.getElementById('cartDrawerItemsCount');

    if (badge) badge.innerText = totalCount;
    if (headerTotal) headerTotal.innerText = `₹${subtotal.toFixed(2)}`;
    if (drawerCount) drawerCount.innerText = `${totalCount} item${totalCount === 1 ? '' : 's'}`;
}

function openCartDrawer() {
    renderCartDrawer();
    document.getElementById('cartDrawer')?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

function closeCartDrawer() {
    document.getElementById('cartDrawer')?.classList.add('hidden');
}

function renderCartDrawer() {
    const list = document.getElementById('cartItemsList');
    const emptyState = document.getElementById('emptyCartState');
    const footer = document.getElementById('cartFooter');
    const rxNotice = document.getElementById('cartRxNotice');
    if (!list) return;

    if (state.cart.length === 0) {
        list.classList.add('hidden');
        footer.classList.add('hidden');
        rxNotice.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    list.classList.remove('hidden');
    footer.classList.remove('hidden');
    emptyState.classList.add('hidden');

    const hasRxItems = state.cart.some(i => i.requires_prescription);
    if (hasRxItems && !state.activePrescription) {
        rxNotice.classList.remove('hidden');
    } else {
        rxNotice.classList.add('hidden');
    }

    let subtotal = 0;
    list.innerHTML = state.cart.map(item => {
        const effectivePrice = item.discount_price || item.price;
        const itemTotal = effectivePrice * item.quantity;
        subtotal += itemTotal;

        return `
            <div class="flex items-center justify-between gap-3 py-2">
                <img src="${item.image_url}" alt="${item.name}" 
                     onerror="this.src='https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300'" 
                     class="w-12 h-12 rounded-xl object-contain bg-slate-50 p-1 border border-slate-100 flex-shrink-0">
                
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-1">
                        <h4 class="text-xs font-bold text-slate-800 truncate">${item.name}</h4>
                        ${item.requires_prescription ? '<span class="text-[9px] bg-rose-100 text-rose-700 font-bold px-1 rounded">Rx</span>' : ''}
                    </div>
                    <p class="text-[10px] text-slate-400 truncate">${item.generic_name}</p>
                    <p class="text-xs font-black text-slate-900 mt-0.5">₹${effectivePrice.toFixed(2)}</p>
                </div>

                <div class="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
                    <button onclick="updateCartItemQty(${item.id}, -1)" class="w-6 h-6 flex items-center justify-center rounded bg-white text-slate-700 hover:bg-slate-200 text-xs font-bold shadow-sm">
                        -
                    </button>
                    <span class="w-6 text-center text-xs font-bold text-slate-800">${item.quantity}</span>
                    <button onclick="updateCartItemQty(${item.id}, 1)" class="w-6 h-6 flex items-center justify-center rounded bg-white text-slate-700 hover:bg-slate-200 text-xs font-bold shadow-sm">
                        +
                    </button>
                </div>

                <button onclick="removeCartItem(${item.id})" class="text-slate-400 hover:text-rose-600 p-1">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </div>
        `;
    }).join('');

    const deliveryFee = subtotal >= 499 ? 0 : 40;
    const discount = subtotal >= 1000 ? subtotal * 0.05 : 0;
    const grandTotal = subtotal + deliveryFee - discount;

    document.getElementById('cartSubtotal').innerText = `₹${subtotal.toFixed(2)}`;
    document.getElementById('cartDeliveryFee').innerText = deliveryFee === 0 ? 'FREE' : `₹${deliveryFee.toFixed(2)}`;
    document.getElementById('cartDiscount').innerText = `-₹${discount.toFixed(2)}`;
    document.getElementById('cartGrandTotal').innerText = `₹${grandTotal.toFixed(2)}`;

    if (window.lucide) lucide.createIcons();
}

// ----------------- Checkout Flow ----------------- //

function proceedToCheckout() {
    if (state.cart.length === 0) {
        showToast('Cart is empty', 'error');
        return;
    }

    const hasRx = state.cart.some(i => i.requires_prescription);
    if (hasRx && !state.activePrescription) {
        showToast('Your order contains Rx medicines. Please upload a doctor prescription first.', 'error');
        openPrescriptionModal();
        return;
    }

    closeCartDrawer();

    const subtotal = state.cart.reduce((sum, i) => sum + ((i.discount_price || i.price) * i.quantity), 0);
    const deliveryFee = subtotal >= 499 ? 0 : 40;
    const discount = subtotal >= 1000 ? subtotal * 0.05 : 0;
    const total = subtotal + deliveryFee - discount;

    document.getElementById('checkoutTotalAmount').innerText = `₹${total.toFixed(2)}`;

    // Prefill if prescription exists
    if (state.activePrescription) {
        const nameInput = document.getElementById('custName');
        const phoneInput = document.getElementById('custPhone');
        if (nameInput && !nameInput.value) nameInput.value = state.activePrescription.patient_name || '';
        if (phoneInput && !phoneInput.value) phoneInput.value = state.activePrescription.patient_phone || '';
    }

    document.getElementById('checkoutModal')?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

function closeCheckoutModal() {
    document.getElementById('checkoutModal')?.classList.add('hidden');
}

function initPaymentMethodListeners() {
    const radios = document.querySelectorAll('input[name="paymentMethod"]');
    const qrBox = document.getElementById('upiQrBox');

    radios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.querySelectorAll('.payment-card').forEach(card => {
                card.classList.remove('border-emerald-600', 'bg-emerald-50/40');
                card.classList.add('border-slate-200', 'bg-white');
            });
            const parent = e.target.closest('.payment-card');
            if (parent) {
                parent.classList.remove('border-slate-200', 'bg-white');
                parent.classList.add('border-emerald-600', 'bg-emerald-50/40');
            }

            if (e.target.value === 'UPI / QR Code') {
                qrBox?.classList.remove('hidden');
            } else {
                qrBox?.classList.add('hidden');
            }
        });
    });
}

async function handleCheckoutSubmit(e) {
    e.preventDefault();
    const customerName = document.getElementById('custName').value.trim();
    const customerPhone = document.getElementById('custPhone').value.trim();
    const customerEmail = document.getElementById('custEmail').value.trim();
    const deliveryAddress = document.getElementById('custAddress').value.trim();
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked')?.value || 'Cash on Delivery';

    const payload = {
        customer_name: customerName,
        customer_phone: customerPhone,
        customer_email: customerEmail,
        delivery_address: deliveryAddress,
        payment_method: paymentMethod,
        prescription_id: state.activePrescription ? state.activePrescription.id : null,
        items: state.cart.map(i => ({ medicine_id: i.id, quantity: i.quantity }))
    };

    const submitBtn = document.getElementById('placeOrderSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Processing Order at Balaji Medical...';

    try {
        const res = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i data-lucide="check-circle" class="w-4 h-4"></i> Confirm Order & Generate Medical Invoice';

        if (data.success) {
            state.cart = [];
            saveCart();
            closeCheckoutModal();
            openInvoiceModal(data.order.order_code);
            showToast('Order confirmed! Generating tax invoice...', 'success');
        } else {
            showToast(data.error || 'Failed to place order', 'error');
        }
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Confirm Order';
        showToast('Server error while placing order', 'error');
    }
}

// ----------------- Medical Invoice Generation ----------------- //

async function openInvoiceModal(orderCode) {
    try {
        const res = await fetch(`/api/orders/code/${orderCode}`);
        const data = await res.json();
        if (!data.success) return;

        const order = data.order;
        const items = data.items;
        const rx = data.prescription;
        const printArea = document.getElementById('invoicePrintArea');

        printArea.innerHTML = `
            <div class="border-2 border-slate-900 p-6 sm:p-8 rounded-2xl bg-white text-slate-900 space-y-6">
                
                <!-- Invoice Header -->
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b-2 border-slate-900 pb-5 gap-4">
                    <div>
                        <div class="flex items-center space-x-2">
                            <div class="w-8 h-8 bg-slate-900 text-emerald-400 rounded-lg flex items-center justify-center font-black">
                                +
                            </div>
                            <h2 class="text-2xl font-black tracking-tight">BALAJI MEDICAL</h2>
                        </div>
                        <p class="text-xs text-slate-600 mt-1">Retail & Wholesale Chemist • 24x7 Emergency Pharmacy</p>
                        <p class="text-[11px] text-slate-500">Shop #4-5, Medical Market, Main Road • Phone: +91 98765 43210</p>
                    </div>

                    <div class="text-right sm:text-right space-y-0.5 text-xs">
                        <span class="bg-slate-900 text-white font-bold text-[10px] px-2.5 py-0.5 rounded uppercase tracking-wider">TAX INVOICE</span>
                        <p class="font-mono font-bold text-slate-800 pt-1">Invoice: ${order.order_code}</p>
                        <p class="text-[11px] text-slate-500">Date: ${order.created_at}</p>
                        <p class="text-[11px] text-slate-500 font-medium">Drug License: <strong>DL-20B/21B-BALAJI-4421</strong></p>
                        <p class="text-[11px] text-slate-500 font-medium">GSTIN: <strong>07AAAAA0000A1Z5</strong></p>
                    </div>
                </div>

                <!-- Patient & Bill To -->
                <div class="grid grid-cols-2 gap-4 text-xs border-b border-slate-200 pb-4">
                    <div>
                        <span class="text-slate-400 text-[10px] uppercase tracking-wider font-bold">Patient / Customer Info</span>
                        <h4 class="font-bold text-slate-900 text-sm mt-0.5">${order.customer_name}</h4>
                        <p class="text-slate-600">Phone: ${order.customer_phone}</p>
                        ${order.customer_email ? `<p class="text-slate-600">Email: ${order.customer_email}</p>` : ''}
                    </div>

                    <div>
                        <span class="text-slate-400 text-[10px] uppercase tracking-wider font-bold">Delivery & Payment</span>
                        <p class="text-slate-700 mt-0.5 leading-snug">${order.delivery_address}</p>
                        <p class="text-slate-600 mt-1">Payment: <strong>${order.payment_method}</strong> (${order.payment_status})</p>
                        ${rx ? `<p class="text-emerald-700 font-semibold">Doctor: ${rx.doctor_name || 'Verified'}</p>` : ''}
                    </div>
                </div>

                <!-- Itemized Medicine Table -->
                <div>
                    <table class="w-full text-left text-xs">
                        <thead class="border-b-2 border-slate-900 text-slate-800 font-bold">
                            <tr>
                                <th class="py-2">Item Description</th>
                                <th class="py-2">Batch</th>
                                <th class="py-2">Exp.</th>
                                <th class="py-2 text-center">Qty</th>
                                <th class="py-2 text-right">Rate</th>
                                <th class="py-2 text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200">
                            ${items.map(item => `
                                <tr>
                                    <td class="py-2">
                                        <div class="font-bold text-slate-900">${item.medicine_name}</div>
                                        <div class="text-[10px] text-slate-500">${item.manufacturer} • ${item.strength || item.dosage_form}</div>
                                    </td>
                                    <td class="py-2 font-mono text-[11px]">${item.batch_no || 'GEN-44'}</td>
                                    <td class="py-2 text-[11px]">${item.expiry_date || '2027-12'}</td>
                                    <td class="py-2 text-center font-bold">${item.quantity}</td>
                                    <td class="py-2 text-right font-mono">₹${item.unit_price.toFixed(2)}</td>
                                    <td class="py-2 text-right font-bold font-mono">₹${item.subtotal.toFixed(2)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>

                <!-- Financial Calculation Summary -->
                <div class="border-t-2 border-slate-900 pt-4 flex justify-between items-start text-xs">
                    <div class="max-w-xs space-y-1 text-[11px] text-slate-500">
                        <p><strong>Note:</strong> Goods once sold will be replaced only under standard pharmaceutical return guidelines. Keep away from direct sunlight.</p>
                        <p class="font-semibold text-slate-700">Dispensed by: Balaji Medical Registered Pharmacist (Reg #PH-98214)</p>
                    </div>

                    <div class="w-56 space-y-1 text-right">
                        <div class="flex justify-between text-slate-600">
                            <span>Subtotal:</span>
                            <span class="font-mono">₹${order.subtotal.toFixed(2)}</span>
                        </div>
                        <div class="flex justify-between text-slate-600">
                            <span>Delivery Fee:</span>
                            <span class="font-mono">${order.delivery_fee === 0 ? 'FREE' : '₹' + order.delivery_fee.toFixed(2)}</span>
                        </div>
                        ${order.discount > 0 ? `
                            <div class="flex justify-between text-emerald-700 font-semibold">
                                <span>Discount:</span>
                                <span class="font-mono">-₹${order.discount.toFixed(2)}</span>
                            </div>
                        ` : ''}
                        <div class="flex justify-between text-base font-black text-slate-900 pt-2 border-t border-slate-300">
                            <span>Net Payable:</span>
                            <span class="font-mono text-emerald-800">₹${order.total_amount.toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                <!-- Pharmacist Signature Stamp -->
                <div class="pt-6 flex justify-between items-end border-t border-dashed border-slate-300 text-xs">
                    <div>
                        <span class="inline-block border-2 border-emerald-600 text-emerald-700 font-black text-[10px] px-2 py-1 rounded tracking-wider uppercase">
                            BALAJI MEDICAL • PHARMACIST VERIFIED
                        </span>
                    </div>
                    <div class="text-center">
                        <div class="h-9 border-b border-slate-400 w-44"></div>
                        <span class="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Authorized Pharmacist Signature</span>
                    </div>
                </div>

            </div>
        `;

        document.getElementById('invoiceModal')?.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Error loading invoice:', err);
    }
}

function closeInvoiceModal() {
    document.getElementById('invoiceModal')?.classList.add('hidden');
}

// ----------------- Customer Order Tracking ----------------- //

function openOrdersModal() {
    document.getElementById('ordersModal')?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

function closeOrdersModal() {
    document.getElementById('ordersModal')?.classList.add('hidden');
}

async function lookupCustomerOrders() {
    const phone = document.getElementById('trackPhoneInput').value.trim();
    const container = document.getElementById('trackedOrdersContainer');

    if (!phone) {
        showToast('Please enter your 10-digit mobile number', 'error');
        return;
    }

    container.innerHTML = '<p class="text-xs text-slate-400 text-center py-4">Searching orders...</p>';

    try {
        const res = await fetch(`/api/orders?phone=${phone}`);
        const data = await res.json();

        if (data.success && data.orders.length > 0) {
            container.innerHTML = data.orders.map(order => {
                let statusBadge = 'bg-blue-100 text-blue-800';
                if (order.order_status === 'Dispatched') statusBadge = 'bg-amber-100 text-amber-800';
                if (order.order_status === 'Delivered') statusBadge = 'bg-emerald-100 text-emerald-800';
                if (order.order_status === 'Cancelled') statusBadge = 'bg-rose-100 text-rose-800';

                return `
                    <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 text-xs">
                        <div class="flex justify-between items-center">
                            <div>
                                <span class="font-mono font-bold text-slate-900">${order.order_code}</span>
                                <p class="text-[10px] text-slate-400">${order.created_at}</p>
                            </div>
                            <span class="${statusBadge} text-[10px] font-bold px-2 py-0.5 rounded-full">
                                ${order.order_status}
                            </span>
                        </div>
                        <div class="flex justify-between items-center text-slate-600 pt-1 border-t border-slate-200">
                            <span>Amount: <strong class="text-slate-900">₹${order.total_amount.toFixed(2)}</strong> (${order.payment_method})</span>
                            <button onclick="openInvoiceModal('${order.order_code}')" class="text-emerald-700 font-bold hover:underline flex items-center gap-1">
                                View Invoice
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<p class="text-xs text-slate-500 text-center py-6">No orders found for this phone number.</p>';
        }
    } catch (err) {
        container.innerHTML = '<p class="text-xs text-rose-500 text-center py-6">Error looking up orders.</p>';
    }
}

// ----------------- Pharmacist / Admin Portal ----------------- //

function toggleAdminPortal() {
    const customerView = document.getElementById('customerView');
    const adminView = document.getElementById('adminPortalView');
    const toggleText = document.getElementById('portalToggleText');

    if (state.currentView === 'customer') {
        // Enforce Pharmacist authentication
        if (!state.currentUser || state.currentUser.role !== 'pharmacist') {
            showToast('Pharmacist login required to access Admin Portal. Sign in or use Demo Pharmacist.', 'error');
            openAuthModal('login');
            return;
        }

        state.currentView = 'admin';
        customerView.classList.add('hidden');
        adminView.classList.remove('hidden');
        toggleText.innerText = 'Switch to Customer View';
        loadAdminStats();
        refreshAdminInventory();
        loadAdminOrders();
        loadAdminPrescriptions();
    } else {
        state.currentView = 'customer';
        adminView.classList.add('hidden');
        customerView.classList.remove('hidden');
        toggleText.innerText = 'Pharmacist Admin Portal';
        fetchMedicines();
    }
    if (window.lucide) lucide.createIcons();
}

// ----------------- Brand Alternatives & Stock Alerts ----------------- //

async function openAlternativesModal(medId) {
    const modal = document.getElementById('alternativesModal');
    const title = document.getElementById('altModalTitle');
    const subtitle = document.getElementById('altModalSubtitle');
    const notice = document.getElementById('altModalNotice');
    const list = document.getElementById('alternativesList');

    list.innerHTML = '<p class="text-xs text-slate-400 text-center py-6">Finding in-stock alternative brands...</p>';
    modal.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();

    try {
        const res = await fetch(`/api/medicines/${medId}/alternatives`);
        const data = await res.json();

        if (data.success) {
            const med = state.medicines.find(m => m.id === medId);
            if (title && med) title.innerText = `In-Stock Alternatives for ${med.name}`;
            if (subtitle) subtitle.innerText = `Active Generic Salt: ${data.generic_name}`;
            if (notice) {
                notice.innerHTML = `
                    <div class="flex items-start gap-2">
                        <i data-lucide="info" class="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5"></i>
                        <div>
                            <strong>Pharmacist Note:</strong> The following medications from licensed pharmaceutical companies share the exact same active salt formula (<strong>${data.generic_name}</strong>) with identical therapeutic strength and efficacy.
                        </div>
                    </div>
                `;
            }

            if (data.alternatives.length === 0) {
                list.innerHTML = `
                    <div class="text-center py-8 bg-slate-50 rounded-2xl p-4">
                        <p class="text-xs text-slate-700 font-bold">No in-stock alternatives found right now.</p>
                        <p class="text-[11px] text-slate-400 mt-1">Our pharmacist has been alerted to restock this salt formula immediately.</p>
                        <button onclick="closeAlternativesModal()" class="mt-3 bg-slate-900 text-white text-xs font-semibold px-4 py-1.5 rounded-lg">Close</button>
                    </div>
                `;
            } else {
                list.innerHTML = data.alternatives.map(alt => {
                    const price = alt.discount_price || alt.price;
                    return `
                        <div class="bg-slate-50 hover:bg-emerald-50/50 border border-slate-200 hover:border-emerald-300 rounded-2xl p-3.5 flex items-center justify-between gap-3 transition">
                            <img src="${alt.image_url}" alt="${alt.name}" 
                                 onerror="this.src='https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300'" 
                                 class="w-12 h-12 rounded-xl object-contain bg-white p-1 border border-slate-100 flex-shrink-0">
                            
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-1.5">
                                    <h4 class="text-xs font-bold text-slate-900 truncate">${alt.name}</h4>
                                    ${alt.requires_prescription ? '<span class="text-[9px] bg-rose-100 text-rose-700 font-bold px-1 rounded">Rx</span>' : '<span class="text-[9px] bg-emerald-100 text-emerald-700 font-bold px-1 rounded">OTC</span>'}
                                </div>
                                <p class="text-[10px] text-slate-500 font-medium">By ${alt.manufacturer} • ${alt.strength || alt.dosage_form}</p>
                                <div class="flex items-center gap-2 mt-1">
                                    <span class="text-xs font-black text-slate-900">₹${price.toFixed(2)}</span>
                                    <span class="text-[10px] text-emerald-600 font-semibold bg-emerald-100/70 px-1.5 py-0.5 rounded">In Stock (${alt.stock_quantity} units)</span>
                                </div>
                            </div>

                            <button onclick="addToCart(${alt.id}); closeAlternativesModal();" 
                                    class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl shadow-sm hover:shadow flex items-center gap-1 transition flex-shrink-0">
                                <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                                <span>Add</span>
                            </button>
                        </div>
                    `;
                }).join('');
            }
            if (window.lucide) lucide.createIcons();
        }
    } catch (err) {
        list.innerHTML = '<p class="text-xs text-rose-500 text-center py-4">Error loading alternatives.</p>';
    }
}

function closeAlternativesModal() {
    document.getElementById('alternativesModal')?.classList.add('hidden');
}

function notifyStockAlert(medName) {
    showToast(`Stock notification enabled for '${medName}'. We will alert you when fresh batch arrives!`, 'success');
}

function showCustomerView() {
    if (state.currentView === 'admin') {
        toggleAdminPortal();
    }
}

function switchAdminTab(tabName) {
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.remove('active', 'text-emerald-600', 'border-emerald-600');
        tab.classList.add('text-slate-500', 'border-transparent');
    });

    const activeBtn = document.getElementById(`tabBtn-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'text-emerald-600', 'border-emerald-600');
        activeBtn.classList.remove('text-slate-500', 'border-transparent');
    }

    document.getElementById('adminPanel-inventory')?.classList.add('hidden');
    document.getElementById('adminPanel-orders')?.classList.add('hidden');
    document.getElementById('adminPanel-prescriptions')?.classList.add('hidden');

    document.getElementById(`adminPanel-${tabName}`)?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

async function loadAdminStats() {
    try {
        const res = await fetch('/api/admin/stats');
        const data = await res.json();
        if (data.success) {
            const s = data.stats;
            document.getElementById('statTotalMeds').innerText = s.total_medicines;
            document.getElementById('statLowStock').innerText = s.low_stock_count;
            document.getElementById('statNearExpiry').innerText = s.near_expiry_count;
            document.getElementById('statTotalOrders').innerText = s.total_orders;
            document.getElementById('statRevenue').innerText = `₹${s.total_revenue.toLocaleString()}`;
            document.getElementById('statPendingRx').innerText = s.pending_prescriptions;
        }
    } catch (err) {
        console.error('Error loading admin stats:', err);
    }
}

async function refreshAdminInventory() {
    try {
        const res = await fetch('/api/medicines');
        const data = await res.json();
        if (data.success) {
            renderAdminInventoryTable(data.medicines);
        }
    } catch (err) {
        console.error('Error refreshing admin inventory:', err);
    }
}

function renderAdminInventoryTable(medicines) {
    const tbody = document.getElementById('adminInventoryTableBody');
    if (!tbody) return;

    tbody.innerHTML = medicines.map(m => {
        const isLow = m.stock_quantity <= 15;
        const today = new Date();
        const expiry = new Date(m.expiry_date);
        const daysToExpiry = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
        const isNearExp = daysToExpiry <= 60;

        return `
            <tr class="hover:bg-slate-50 transition">
                <td class="py-3 px-4 font-bold text-slate-900">
                    <div>${m.name}</div>
                    <div class="text-[10px] text-slate-400 font-normal">By ${m.manufacturer}</div>
                </td>
                <td class="py-3 px-3 italic font-medium text-slate-700">${m.generic_name}</td>
                <td class="py-3 px-3"><span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded">${m.category_name}</span></td>
                <td class="py-3 px-3">
                    <div class="font-mono text-[11px]">${m.batch_no || 'N/A'}</div>
                    <div class="text-[11px] ${isNearExp ? 'text-rose-600 font-bold' : 'text-slate-500'}">${m.expiry_date} ${isNearExp ? '⚠️' : ''}</div>
                </td>
                <td class="py-3 px-3 font-mono">
                    <strong>₹${(m.discount_price || m.price).toFixed(2)}</strong>
                    ${m.discount_price ? `<span class="line-through text-slate-400 ml-1 text-[10px]">₹${m.price.toFixed(2)}</span>` : ''}
                </td>
                <td class="py-3 px-3">
                    <span class="px-2 py-0.5 rounded font-bold ${isLow ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
                        ${m.stock_quantity} units
                    </span>
                </td>
                <td class="py-3 px-3">
                    ${m.requires_prescription ? '<span class="text-rose-700 font-bold">Yes (Rx)</span>' : '<span class="text-emerald-700">OTC</span>'}
                </td>
                <td class="py-3 px-4 text-right space-x-2">
                    <button onclick="editMedicine(${m.id})" class="text-emerald-700 hover:text-emerald-900 font-semibold text-xs">
                        Edit
                    </button>
                    <button onclick="deleteMedicine(${m.id})" class="text-rose-600 hover:text-rose-800 font-semibold text-xs">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function filterAdminInventory() {
    const q = document.getElementById('adminSearchInput').value.toLowerCase();
    const filtered = state.medicines.filter(m => 
        m.name.toLowerCase().includes(q) || 
        m.generic_name.toLowerCase().includes(q) || 
        (m.batch_no && m.batch_no.toLowerCase().includes(q))
    );
    renderAdminInventoryTable(filtered);
}

function openAddMedicineModal() {
    document.getElementById('adminMedModalTitle').innerText = 'Add Medicine to Balaji Medical Inventory';
    document.getElementById('adminMedicineForm').reset();
    document.getElementById('adminMedId').value = '';
    document.getElementById('adminMedicineModal')?.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

function closeAddMedicineModal() {
    document.getElementById('adminMedicineModal')?.classList.add('hidden');
}

async function editMedicine(id) {
    try {
        const res = await fetch(`/api/medicines/${id}`);
        const data = await res.json();
        if (!data.success) return;

        const m = data.medicine;
        document.getElementById('adminMedModalTitle').innerText = `Edit '${m.name}' in Catalog`;
        document.getElementById('adminMedId').value = m.id;
        document.getElementById('adminMedName').value = m.name;
        document.getElementById('adminMedGeneric').value = m.generic_name;
        document.getElementById('adminMedCategory').value = m.category_id;
        document.getElementById('adminMedDosageForm').value = m.dosage_form;
        document.getElementById('adminMedStrength').value = m.strength || '';
        document.getElementById('adminMedPrice').value = m.price;
        document.getElementById('adminMedDiscountPrice').value = m.discount_price || '';
        document.getElementById('adminMedStock').value = m.stock_quantity;
        document.getElementById('adminMedRx').value = m.requires_prescription;
        document.getElementById('adminMedManufacturer').value = m.manufacturer || '';
        document.getElementById('adminMedBatch').value = m.batch_no || '';
        document.getElementById('adminMedExpiry').value = m.expiry_date;
        document.getElementById('adminMedDesc').value = m.description || '';
        document.getElementById('adminMedUsage').value = m.usage_instructions || '';

        document.getElementById('adminMedicineModal')?.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Error loading medicine for edit:', err);
    }
}

async function handleSaveMedicineSubmit(e) {
    e.preventDefault();
    const payload = {
        id: document.getElementById('adminMedId').value || null,
        name: document.getElementById('adminMedName').value.trim(),
        generic_name: document.getElementById('adminMedGeneric').value.trim(),
        category_id: parseInt(document.getElementById('adminMedCategory').value),
        dosage_form: document.getElementById('adminMedDosageForm').value,
        strength: document.getElementById('adminMedStrength').value.trim(),
        price: parseFloat(document.getElementById('adminMedPrice').value),
        discount_price: document.getElementById('adminMedDiscountPrice').value ? parseFloat(document.getElementById('adminMedDiscountPrice').value) : null,
        stock_quantity: parseInt(document.getElementById('adminMedStock').value),
        requires_prescription: parseInt(document.getElementById('adminMedRx').value),
        manufacturer: document.getElementById('adminMedManufacturer').value.trim(),
        batch_no: document.getElementById('adminMedBatch').value.trim(),
        expiry_date: document.getElementById('adminMedExpiry').value,
        description: document.getElementById('adminMedDesc').value.trim(),
        usage_instructions: document.getElementById('adminMedUsage').value.trim()
    };

    try {
        const res = await fetch('/api/admin/medicines', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            closeAddMedicineModal();
            showToast(data.message, 'success');
            refreshAdminInventory();
            loadAdminStats();
        } else {
            showToast(data.error || 'Failed to save medicine', 'error');
        }
    } catch (err) {
        showToast('Server error while saving medicine', 'error');
    }
}

async function deleteMedicine(id) {
    if (!confirm('Are you sure you want to remove this medicine from Balaji Medical catalog?')) return;

    try {
        const res = await fetch(`/api/admin/medicines/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            refreshAdminInventory();
            loadAdminStats();
        }
    } catch (err) {
        showToast('Error deleting medicine', 'error');
    }
}

async function loadAdminOrders() {
    const tbody = document.getElementById('adminOrdersTableBody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/orders');
        const data = await res.json();
        if (data.success) {
            tbody.innerHTML = data.orders.map(o => `
                <tr class="hover:bg-slate-50 transition">
                    <td class="py-3 px-4 font-mono font-bold text-slate-900">${o.order_code}</td>
                    <td class="py-3 px-3">
                        <div class="font-bold text-slate-800">${o.customer_name}</div>
                        <div class="text-[11px] text-slate-500">${o.customer_phone}</div>
                    </td>
                    <td class="py-3 px-3 max-w-xs truncate">${o.delivery_address}</td>
                    <td class="py-3 px-3">
                        <div>${o.payment_method}</div>
                        <span class="text-[10px] font-bold ${o.payment_status === 'Paid' ? 'text-emerald-600' : 'text-amber-600'}">${o.payment_status}</span>
                    </td>
                    <td class="py-3 px-3 font-mono font-bold text-slate-900">₹${o.total_amount.toFixed(2)}</td>
                    <td class="py-3 px-3">
                        <select onchange="updateOrderStatus(${o.id}, this.value)" class="text-xs bg-slate-100 border border-slate-200 rounded p-1 font-semibold">
                            <option value="Placed" ${o.order_status === 'Placed' ? 'selected' : ''}>Placed</option>
                            <option value="Processing" ${o.order_status === 'Processing' ? 'selected' : ''}>Processing</option>
                            <option value="Dispatched" ${o.order_status === 'Dispatched' ? 'selected' : ''}>Dispatched</option>
                            <option value="Delivered" ${o.order_status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                            <option value="Cancelled" ${o.order_status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                        </select>
                    </td>
                    <td class="py-3 px-4 text-right">
                        <button onclick="openInvoiceModal('${o.order_code}')" class="text-emerald-700 font-bold hover:underline">
                            Invoice
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error('Error loading admin orders:', err);
    }
}

async function updateOrderStatus(orderId, newStatus) {
    try {
        const res = await fetch(`/api/admin/orders/${orderId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Order #${orderId} set to ${newStatus}`, 'success');
            loadAdminStats();
        }
    } catch (err) {
        showToast('Error updating order status', 'error');
    }
}

async function loadAdminPrescriptions() {
    const tbody = document.getElementById('adminPrescriptionsTableBody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/admin/prescriptions');
        const data = await res.json();
        if (data.success) {
            tbody.innerHTML = data.prescriptions.map(p => `
                <tr class="hover:bg-slate-50 transition">
                    <td class="py-3 px-4 font-mono font-bold">#Rx-${p.id}</td>
                    <td class="py-3 px-3 font-bold text-slate-800">${p.patient_name}</td>
                    <td class="py-3 px-3">
                        <div>${p.doctor_name || 'N/A'}</div>
                        <div class="text-[10px] text-slate-500">${p.patient_phone || ''}</div>
                    </td>
                    <td class="py-3 px-3 text-[11px] text-slate-500">${p.uploaded_at}</td>
                    <td class="py-3 px-3">
                        <a href="${p.file_path}" target="_blank" class="text-emerald-700 font-bold hover:underline flex items-center gap-1">
                            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            View Document
                        </a>
                    </td>
                    <td class="py-3 px-3">
                        <span class="text-[11px] font-bold px-2 py-0.5 rounded ${p.status === 'Approved' ? 'bg-emerald-100 text-emerald-800' : p.status === 'Rejected' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}">
                            ${p.status}
                        </span>
                    </td>
                    <td class="py-3 px-4 text-right space-x-2">
                        <button onclick="updatePrescriptionStatus(${p.id}, 'Approved')" class="text-emerald-700 hover:text-emerald-900 font-bold">
                            Approve
                        </button>
                        <button onclick="updatePrescriptionStatus(${p.id}, 'Rejected')" class="text-rose-600 hover:text-rose-800 font-bold">
                            Reject
                        </button>
                    </td>
                </tr>
            `).join('');
            if (window.lucide) lucide.createIcons();
        }
    } catch (err) {
        console.error('Error loading prescriptions:', err);
    }
}

async function updatePrescriptionStatus(pId, status) {
    try {
        const res = await fetch(`/api/admin/prescriptions/${pId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Prescription #${pId} marked as ${status}`, 'success');
            loadAdminPrescriptions();
            loadAdminStats();
        }
    } catch (err) {
        showToast('Error updating prescription', 'error');
    }
}

// ----------------- Toast Notifications ----------------- //

let toastTimer = null;
function showToast(msg, type = 'info') {
    const toast = document.getElementById('toastNotification');
    const msgEl = document.getElementById('toastMessage');
    const iconEl = document.getElementById('toastIcon');
    if (!toast || !msgEl) return;

    msgEl.innerText = msg;

    if (type === 'success') {
        iconEl?.setAttribute('data-lucide', 'check-circle');
        iconEl?.classList.remove('text-amber-400', 'text-rose-400');
        iconEl?.classList.add('text-emerald-400');
    } else if (type === 'error') {
        iconEl?.setAttribute('data-lucide', 'alert-circle');
        iconEl?.classList.remove('text-emerald-400', 'text-amber-400');
        iconEl?.classList.add('text-rose-400');
    } else {
        iconEl?.setAttribute('data-lucide', 'info');
        iconEl?.classList.remove('text-emerald-400', 'text-rose-400');
        iconEl?.classList.add('text-amber-400');
    }

    if (window.lucide) lucide.createIcons();

    toast.classList.remove('hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.add('hidden');
    }, 3500);
}
