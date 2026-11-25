const csrf = document.querySelector('meta[name="csrf-token"]').content;
const $ = (selector) => document.querySelector(selector);
let profileBaseUrl = location.origin;
let expiryUser = '';

const words = {
  tr: {
    panelName:'ANYCONNECT PANELİ',overview:'Genel bakış',customers:'Müşteriler',settings:'Ayarlar',activity:'Hareketler',panelVersion:'Panel sürümü',logout:'Çıkış yap',controlCenter:'KONTROL MERKEZİ',language:'Dil',lightTheme:'Açık tema',darkTheme:'Koyu tema',serverStatus:'SUNUCU DURUMU',loading:'Yükleniyor',checkingService:'Servis kontrol ediliyor',customerAccounts:'MÜŞTERİ HESAPLARI',activeAndDisabled:'Aktif ve devre dışı hesaplar',vpnAddress:'VPN ADRESİ',connectionPort:'Bağlantı portu:',domainWarning:'VPN alan adı sertifika ayarlarından bulunamadı. Profil URL’leri çalışmayabilir; kurulum betiğini aynı VPN alan adıyla güncelle.',authWarning:'VPN kullanıcı dosyası',authWarningEnd:'bulunamadı. Panelde oluşturulan hesaplar bağlanamayabilir.',accessManagement:'ERİŞİM YÖNETİMİ',profilesDescription:'Her aktif müşteri için ayrı AnyConnect profil URL’si oluşturulur.',addCustomer:'＋ Müşteri ekle',username:'Kullanıcı adı',vpnPassword:'VPN şifresi',passwordPlaceholder:'İstediğin parolayı yaz veya üret',generatePassword:'Güvenli şifre üret',deviceLimit:'Eşzamanlı cihaz sınırı',deviceLimitShort:'CİHAZ SINIRI',device1:'1 cihaz',device2:'2 cihaz',device3:'3 cihaz',device4:'4 cihaz',subscriptionTerm:'Abonelik süresi',byDays:'Gün sayısı',specificDate:'Bitiş tarihi',unlimited:'Sınırsız',days:'Gün',expiryDate:'Bitiş tarihi',createCustomer:'Müşteri oluştur',cancel:'Vazgeç',status:'DURUM',expiry:'BİTİŞ TARİHİ',profile:'ANYCONNECT PROFİLİ',actions:'İŞLEMLER',customersLoading:'Müşteriler yükleniyor…',serverSettings:'SUNUCU YAPILANDIRMASI',dnsNote:'DNS kaydı VPN servisini yeniden başlatır',subscriptionAndServers:'Sabit abonelik ve VPN sunucuları',subscriptionNote:'Müşterinin profil URL’si sabit kalır. XML, burada seçtiğin aktif VPN sunucusunu önce, yedeği sonra gösterir. Değişiklikten sonra müşteri profili yeniden içe aktarılmalıdır.',subscriptionBase:'Sabit abonelik taban adresi',subscriptionExample:'Örnek: https://userrtm.sub.com:8443 — bu adres AnyConnect paneline yönlenmeli',primaryVpn:'Birincil VPN domain/IP',backupVpn:'Yedek VPN domain/IP',hostPlaceholder:'vpn.example.com veya IP',backupPlaceholder:'Yedek domain veya IP',port:'Port',backupPort:'Yedek port',activeServer:'Profilde ilk gösterilecek sunucu',primary:'Birincil',backup:'Yedek',saveServers:'Abonelik ve sunucuları kaydet',dnsServers:'DNS sunucuları',dnsHelp:'Her satıra bir IPv4 veya IPv6 adresi yaz',saveDns:'DNS ayarını kaydet',vpnService:'VPN servisi',serviceCheckNote:'Yeniden başlatmadan önce yapılandırmayı kontrol edebilirsin.',checkConfig:'Yapılandırmayı kontrol et',restartVpn:'VPN’i yeniden başlat',changePanelPassword:'Panel şifresini değiştir',currentPassword:'Mevcut panel şifresi',newPassword:'Yeni şifre',newPasswordPlaceholder:'İstediğin parolayı gir',updatePanelPassword:'Panel şifresini güncelle',adminActions:'YÖNETİCİ EYLEMLERİ',recentActivity:'Son hareketler',refresh:'Yenile',activityLoading:'Hareketler yükleniyor…',vpnLogs:'VPN servis günlükleri',chooseExpiry:'Süreyi nasıl belirlemek istiyorsun?',save:'Kaydet',unlimitedDate:'Sınırsız',unknown:'Bilinmiyor',serviceStartUnknown:'Başlangıç zamanı alınamadı',notConfigured:'Ayarlanmamış',noLogs:'Henüz kayıt yok.',noCustomers:'Henüz müşteri yok. İlk hesabı ekleyebilirsin.',noActivity:'Henüz yönetici hareketi yok.',done:'İşlem tamamlandı',active:'Aktif',expired:'Süresi doldu',disabled:'Devre dışı',stop:'Durdur',extend:'Süreyi uzat',enable:'Etkinleştir',copyUri:'URI’yi kopyala',unavailable:'Kullanılamıyor',term:'Süre',deviceLimitAction:'Cihaz sınırı',password:'Şifre',delete:'Sil',daysPrompt:'Aynı anda izin verilen cihaz sayısı (1-4):',limitInvalid:'Cihaz sınırı 1 ile 4 arasında olmalı.',confirmDelete:'“{user}” hesabı kalıcı olarak silinsin mi?',confirmDisable:'“{user}” hesabı devre dışı bırakılsın mı?',confirmRestart:'VPN servisi yeniden başlatılsın mı? Bağlı kullanıcıların bağlantısı kesilir.',passwordPrompt:'{user} için yeni VPN şifresi:',passwordInvalid:'Şifre boş olamaz; en fazla 128 karakter olabilir.',expiryInvalid:'Süre 1–3650 gün arasında olmalı.',dateRequired:'Bir bitiş tarihi seç.',createdCopied:'Müşteri eklendi. Giriş bilgileri ve profili panoya kopyalandı.',customerAdded:'Müşteri eklendi.',limitUpdated:'Eşzamanlı cihaz sınırı güncellendi.',profileCopied:'Müşterinin kişisel AnyConnect URL’si kopyalandı.',customerDeleted:'Müşteri silindi.',enabledToast:'Hesap etkinleştirildi.',disabledToast:'Hesap durduruldu.',expiryUpdated:'Abonelik süresi güncellendi.',passwordUpdated:'VPN şifresi güncellendi.',dnsSaved:'DNS ayarları kaydedildi.',serversSaved:'Abonelik ve sunucular kaydedildi.',configValid:'Yapılandırma geçerli.',vpnRestarted:'VPN servisi yeniden başlatıldı.',creating:'Oluşturuluyor…',unlimitedTerm:'Sınırsız',expiryTitle:'Abonelik süresi: {user}',unnamed:'Kullanıcı',copyCredentials:'Kullanıcı adı: {user}\nVPN şifresi: {password}\nEşzamanlı cihaz sınırı: {limit}\nAnyConnect profil URL: {url}',eventAdd:'Müşteri oluşturuldu',eventDelete:'Müşteri silindi',eventDisable:'Müşteri durduruldu',eventEnable:'Müşteri etkinleştirildi',eventExpiry:'Abonelik süresi güncellendi',eventPassword:'VPN parolası yenilendi',eventDns:'DNS ayarları değiştirildi',eventRestart:'VPN servisi yeniden başlatıldı',eventNetwork:'Abonelik ve VPN uçları güncellendi'
  },
  ru: {
    panelName:'ПАНЕЛЬ ANYCONNECT',overview:'Обзор',customers:'Клиенты',settings:'Настройки',activity:'События',panelVersion:'Версия панели',logout:'Выйти',controlCenter:'ЦЕНТР УПРАВЛЕНИЯ',language:'Язык',lightTheme:'Светлая тема',darkTheme:'Тёмная тема',serverStatus:'СОСТОЯНИЕ СЕРВЕРА',loading:'Загрузка',checkingService:'Проверяем службу',customerAccounts:'АККАУНТЫ КЛИЕНТОВ',activeAndDisabled:'Активные и отключённые аккаунты',vpnAddress:'АДРЕС VPN',connectionPort:'Порт подключения:',domainWarning:'Домен VPN не найден в настройках сертификата. Ссылки профилей могут не работать; обновите установщик с тем же доменом VPN.',authWarning:'Файл пользователей VPN',authWarningEnd:'не найден. Созданные в панели аккаунты могут не подключаться.',accessManagement:'УПРАВЛЕНИЕ ДОСТУПОМ',profilesDescription:'Для каждого активного клиента создаётся отдельная ссылка профиля AnyConnect.',addCustomer:'＋ Добавить клиента',username:'Имя пользователя',vpnPassword:'Пароль VPN',passwordPlaceholder:'Введите пароль или сгенерируйте его',generatePassword:'Создать надёжный пароль',deviceLimit:'Лимит одновременных устройств',deviceLimitShort:'ЛИМИТ УСТРОЙСТВ',device1:'1 устройство',device2:'2 устройства',device3:'3 устройства',device4:'4 устройства',subscriptionTerm:'Срок подписки',byDays:'Количество дней',specificDate:'Дата окончания',unlimited:'Без ограничений',days:'Дни',expiryDate:'Дата окончания',createCustomer:'Создать клиента',cancel:'Отмена',status:'СТАТУС',expiry:'ДАТА ОКОНЧАНИЯ',profile:'ПРОФИЛЬ ANYCONNECT',actions:'ДЕЙСТВИЯ',customersLoading:'Загрузка клиентов…',serverSettings:'НАСТРОЙКИ СЕРВЕРА',dnsNote:'Изменение DNS перезапустит службу VPN',subscriptionAndServers:'Постоянная подписка и серверы VPN',subscriptionNote:'Ссылка профиля клиента остаётся постоянной. XML сначала показывает выбранный активный VPN-сервер, затем резервный. После изменения клиенту нужно заново импортировать профиль.',subscriptionBase:'Базовый адрес постоянной подписки',subscriptionExample:'Пример: https://userrtm.sub.com:8443 — адрес должен вести на панель AnyConnect',primaryVpn:'Основной домен/IP VPN',backupVpn:'Резервный домен/IP VPN',hostPlaceholder:'vpn.example.com или IP',backupPlaceholder:'Резервный домен или IP',port:'Порт',backupPort:'Резервный порт',activeServer:'Первый сервер в профиле',primary:'Основной',backup:'Резервный',saveServers:'Сохранить подписку и серверы',dnsServers:'DNS-серверы',dnsHelp:'Укажите по одному IPv4 или IPv6 адресу в строке',saveDns:'Сохранить DNS',vpnService:'Служба VPN',serviceCheckNote:'Перед перезапуском можно проверить конфигурацию.',checkConfig:'Проверить конфигурацию',restartVpn:'Перезапустить VPN',changePanelPassword:'Изменить пароль панели',currentPassword:'Текущий пароль панели',newPassword:'Новый пароль',newPasswordPlaceholder:'Введите новый пароль',updatePanelPassword:'Обновить пароль панели',adminActions:'ДЕЙСТВИЯ АДМИНИСТРАТОРА',recentActivity:'Последние события',refresh:'Обновить',activityLoading:'Загрузка событий…',vpnLogs:'Журнал службы VPN',chooseExpiry:'Как задать срок?',save:'Сохранить',unlimitedDate:'Без ограничений',unknown:'Неизвестно',serviceStartUnknown:'Время запуска недоступно',notConfigured:'Не настроено',noLogs:'Записей пока нет.',noCustomers:'Клиентов пока нет. Создайте первый аккаунт.',noActivity:'Действий администратора пока нет.',done:'Выполнено',active:'Активен',expired:'Срок истёк',disabled:'Отключён',stop:'Отключить',extend:'Продлить',enable:'Включить',copyUri:'Копировать URI',unavailable:'Недоступно',term:'Срок',deviceLimitAction:'Лимит устройств',password:'Пароль',delete:'Удалить',daysPrompt:'Количество одновременных устройств (1–4):',limitInvalid:'Лимит устройств должен быть от 1 до 4.',confirmDelete:'Удалить аккаунт «{user}» без возможности восстановления?',confirmDisable:'Отключить аккаунт «{user}»?',confirmRestart:'Перезапустить VPN? Подключённые клиенты отключатся.',passwordPrompt:'Новый пароль VPN для {user}:',passwordInvalid:'Пароль не может быть пустым и должен содержать не более 128 символов.',expiryInvalid:'Срок должен быть от 1 до 3650 дней.',dateRequired:'Выберите дату окончания.',createdCopied:'Клиент создан. Данные для входа и профиль скопированы.',customerAdded:'Клиент добавлен.',limitUpdated:'Лимит одновременных устройств обновлён.',profileCopied:'Личная ссылка AnyConnect скопирована.',customerDeleted:'Клиент удалён.',enabledToast:'Аккаунт включён.',disabledToast:'Аккаунт отключён.',expiryUpdated:'Срок подписки обновлён.',passwordUpdated:'Пароль VPN обновлён.',dnsSaved:'Настройки DNS сохранены.',serversSaved:'Подписка и серверы сохранены.',configValid:'Конфигурация корректна.',vpnRestarted:'Служба VPN перезапущена.',creating:'Создание…',unlimitedTerm:'Без ограничений',expiryTitle:'Срок подписки: {user}',unnamed:'Пользователь',copyCredentials:'Имя пользователя: {user}\nПароль VPN: {password}\nЛимит одновременных устройств: {limit}\nСсылка профиля AnyConnect: {url}',eventAdd:'Создан клиент',eventDelete:'Клиент удалён',eventDisable:'Клиент отключён',eventEnable:'Клиент включён',eventExpiry:'Срок подписки обновлён',eventPassword:'Пароль VPN обновлён',eventDns:'Настройки DNS изменены',eventRestart:'Служба VPN перезапущена',eventNetwork:'Обновлены подписка и VPN-серверы'
  },
  en: {
    panelName:'ANYCONNECT PANEL',overview:'Overview',customers:'Customers',settings:'Settings',activity:'Activity',panelVersion:'Panel version',logout:'Sign out',controlCenter:'CONTROL CENTER',language:'Language',lightTheme:'Light theme',darkTheme:'Dark theme',serverStatus:'SERVER STATUS',loading:'Loading',checkingService:'Checking service',customerAccounts:'CUSTOMER ACCOUNTS',activeAndDisabled:'Active and disabled accounts',vpnAddress:'VPN ADDRESS',connectionPort:'Connection port:',domainWarning:'The VPN domain was not found in the certificate settings. Profile URLs may not work; update the installer with the same VPN domain.',authWarning:'VPN user file',authWarningEnd:'was not found. Accounts created in the panel may not connect.',accessManagement:'ACCESS MANAGEMENT',profilesDescription:'Each active customer gets a separate AnyConnect profile URL.',addCustomer:'＋ Add customer',username:'Username',vpnPassword:'VPN password',passwordPlaceholder:'Enter a password or generate one',generatePassword:'Generate secure password',deviceLimit:'Concurrent device limit',deviceLimitShort:'DEVICE LIMIT',device1:'1 device',device2:'2 devices',device3:'3 devices',device4:'4 devices',subscriptionTerm:'Subscription term',byDays:'Number of days',specificDate:'Expiry date',unlimited:'Unlimited',days:'Days',expiryDate:'Expiry date',createCustomer:'Create customer',cancel:'Cancel',status:'STATUS',expiry:'EXPIRY DATE',profile:'ANYCONNECT PROFILE',actions:'ACTIONS',customersLoading:'Loading customers…',serverSettings:'SERVER SETTINGS',dnsNote:'Changing DNS restarts the VPN service',subscriptionAndServers:'Stable subscription and VPN servers',subscriptionNote:'The customer profile URL stays the same. The XML lists the selected active VPN server first, then the backup. Customers must re-import the profile after a change.',subscriptionBase:'Stable subscription base URL',subscriptionExample:'Example: https://userrtm.sub.com:8443 — this address must point to the AnyConnect panel',primaryVpn:'Primary VPN domain/IP',backupVpn:'Backup VPN domain/IP',hostPlaceholder:'vpn.example.com or IP',backupPlaceholder:'Backup domain or IP',port:'Port',backupPort:'Backup port',activeServer:'Server listed first in profile',primary:'Primary',backup:'Backup',saveServers:'Save subscription and servers',dnsServers:'DNS servers',dnsHelp:'Enter one IPv4 or IPv6 address per line',saveDns:'Save DNS settings',vpnService:'VPN service',serviceCheckNote:'Check the configuration before restarting.',checkConfig:'Check configuration',restartVpn:'Restart VPN',changePanelPassword:'Change panel password',currentPassword:'Current panel password',newPassword:'New password',newPasswordPlaceholder:'Enter the new password',updatePanelPassword:'Update panel password',adminActions:'ADMIN ACTIONS',recentActivity:'Recent activity',refresh:'Refresh',activityLoading:'Loading activity…',vpnLogs:'VPN service logs',chooseExpiry:'How do you want to set the term?',save:'Save',unlimitedDate:'Unlimited',unknown:'Unknown',serviceStartUnknown:'Start time unavailable',notConfigured:'Not configured',noLogs:'No logs yet.',noCustomers:'No customers yet. Add the first account.',noActivity:'No administrator activity yet.',done:'Done',active:'Active',expired:'Expired',disabled:'Disabled',stop:'Disable',extend:'Extend term',enable:'Enable',copyUri:'Copy URI',unavailable:'Unavailable',term:'Term',deviceLimitAction:'Device limit',password:'Password',delete:'Delete',daysPrompt:'Concurrent device limit (1–4):',limitInvalid:'Device limit must be from 1 to 4.',confirmDelete:'Permanently delete account “{user}”?',confirmDisable:'Disable account “{user}”?',confirmRestart:'Restart the VPN service? Connected users will be disconnected.',passwordPrompt:'New VPN password for {user}:',passwordInvalid:'Password cannot be empty and must be 128 characters or fewer.',expiryInvalid:'Term must be from 1 to 3650 days.',dateRequired:'Choose an expiry date.',createdCopied:'Customer added. Login details and profile copied to clipboard.',customerAdded:'Customer added.',limitUpdated:'Concurrent device limit updated.',profileCopied:'Customer’s personal AnyConnect URL copied.',customerDeleted:'Customer deleted.',enabledToast:'Account enabled.',disabledToast:'Account disabled.',expiryUpdated:'Subscription term updated.',passwordUpdated:'VPN password updated.',dnsSaved:'DNS settings saved.',serversSaved:'Subscription and servers saved.',configValid:'Configuration is valid.',vpnRestarted:'VPN service restarted.',creating:'Creating…',unlimitedTerm:'Unlimited',expiryTitle:'Subscription term: {user}',unnamed:'User',copyCredentials:'Username: {user}\nVPN password: {password}\nConcurrent device limit: {limit}\nAnyConnect profile URL: {url}',eventAdd:'Customer created',eventDelete:'Customer deleted',eventDisable:'Customer disabled',eventEnable:'Customer enabled',eventExpiry:'Subscription term updated',eventPassword:'VPN password reset',eventDns:'DNS settings changed',eventRestart:'VPN service restarted',eventNetwork:'Subscription and VPN endpoints updated'
  }
};

let language = localStorage.getItem('oc-language') || 'tr';
const t = (key) => (words[language] && words[language][key]) || words.tr[key] || key;
const fill = (key, values = {}) => Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, value), t(key));
const locale = () => ({ tr:'tr-TR', ru:'ru-RU', en:'en-US' }[language] || 'tr-TR');

function applyLanguage() {
  document.documentElement.lang = language;
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  $('#language-select').value = language;
  $('#view-title').textContent = t(viewTitles[document.body.dataset.view] || 'overview');
  const theme = document.body.dataset.theme;
  $('#theme-toggle').querySelector('span').textContent = theme === 'dark' ? t('lightTheme') : t('darkTheme');
  if (cachedState) renderState(cachedState);
}

const toast = (message, error = false) => {
  const el = $('#toast');
  el.textContent = message;
  el.classList.toggle('error', error);
  el.classList.add('show');
  clearTimeout(el.hideTimer);
  el.hideTimer = setTimeout(() => el.classList.remove('show'), 3500);
};

async function api(path, method = 'GET', body) {
  const response = await fetch(path, {
    method, cache: 'no-store',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const data = await response.json().catch(() => ({ error: 'Unexpected server response.' }));
  if (response.status === 401) { location.href = '/login'; throw new Error(data.error || 'Session expired.'); }
  if (!response.ok) throw new Error(data.error || 'Request failed.');
  return data;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]));
}

function dateText(value, options = { dateStyle: 'medium' }) {
  if (!value) return t('unlimitedDate');
  const date = new Date(value * 1000);
  return Number.isNaN(date.getTime()) ? t('unknown') : date.toLocaleString(locale(), options);
}

const eventLabels = {
  'Müşteri oluşturuldu':'eventAdd','Müşteri silindi':'eventDelete','Müşteri durduruldu':'eventDisable',
  'Müşteri etkinleştirildi':'eventEnable','Abonelik süresi güncellendi':'eventExpiry',
  'VPN parolası yenilendi':'eventPassword','DNS ayarları değiştirildi':'eventDns',
  'VPN servisi yeniden başlatıldı':'eventRestart','Abonelik ve VPN uçları güncellendi':'eventNetwork'
};

function renderEvents(events = []) {
  const box = $('#activity-list');
  if (!events.length) { box.innerHTML = `<p class="muted">${escapeHtml(t('noActivity'))}</p>`; return; }
  box.innerHTML = events.map((event) => {
    const label = t(eventLabels[event.action] || '') || event.action;
    return `<article class="activity-item"><span class="activity-mark"></span><div><b>${escapeHtml(label)}</b><p>${escapeHtml(event.detail || t('done'))}</p></div><time>${escapeHtml(dateText(event.created_at, { dateStyle:'medium', timeStyle:'short' }))}</time></article>`;
  }).join('');
}

function renderUsers(users = []) {
  $('#user-count').textContent = users.length;
  const tbody = $('#users-body');
  if (!users.length) { tbody.innerHTML = `<tr class="row-enter"><td colspan="6" class="muted">${escapeHtml(t('noCustomers'))}</td></tr>`; return; }
  tbody.innerHTML = users.map((user) => {
    const name = escapeHtml(user.username);
    const status = user.status || 'active';
    const statusLabel = status === 'active' ? t('active') : status === 'expired' ? t('expired') : t('disabled');
    const toggle = status === 'active' ? 'disable' : status === 'expired' ? 'expiry' : 'enable';
    const toggleText = status === 'active' ? t('stop') : status === 'expired' ? t('extend') : t('enable');
    const uriReady = status === 'active' && user.profile_token;
    return `<tr class="row-enter" data-user="${name}"><td><span class="user-avatar">${escapeHtml(user.username.slice(0,1).toUpperCase())}</span><b>${name}</b></td><td><span class="pill ${status === 'active' ? '' : 'pill-off'}">${escapeHtml(statusLabel)}</span></td><td>${escapeHtml(dateText(user.expires_at))}</td><td>${Number(user.max_same_clients) || 1} ${escapeHtml(language === 'en' ? 'devices' : language === 'ru' ? 'устройства' : 'cihaz')}</td><td><button class="text-button" data-action="copy-profile" data-user="${name}" data-token="${escapeHtml(user.profile_token || '')}" ${uriReady ? '' : 'disabled'}>${escapeHtml(uriReady ? t('copyUri') : t('unavailable'))}</button></td><td class="align-right actions"><button class="text-button" data-action="${toggle}" data-user="${name}">${escapeHtml(toggleText)}</button><button class="text-button" data-action="expiry" data-user="${name}" data-expires="${Number(user.expires_at) || ''}">${escapeHtml(t('term'))}</button><button class="text-button" data-action="limit" data-user="${name}" data-limit="${Number(user.max_same_clients) || 1}">${escapeHtml(t('deviceLimitAction'))}</button><button class="text-button" data-action="password" data-user="${name}">${escapeHtml(t('password'))}</button><button class="text-button delete-user" data-action="delete" data-user="${name}">${escapeHtml(t('delete'))}</button></td></tr>`;
  }).join('');
}

let cachedState = null;
function renderState(data) {
  cachedState = data;
  const settings = data.settings || {};
  renderUsers(data.users || []);
  renderEvents(data.events || []);
  $('#service-status').textContent = data.service.active === 'active' ? t('active') : data.service.active;
  $('#service-dot').classList.toggle('online', data.service.active === 'active');
  $('#service-since').textContent = data.service.since || t('serviceStartUnknown');
  $('#vpn-domain').textContent = settings.primary_host || settings.domain || t('notConfigured');
  $('#vpn-port').textContent = settings.primary_port || settings.port || '443';
  $('#domain-warning').classList.toggle('hidden', Boolean(settings.domain));
  const authMissing = !settings.auth_file_exists;
  $('#auth-warning').classList.toggle('hidden', !authMissing);
  $('#auth-path').textContent = settings.auth_passwd || 'ocserv';
  $('#dns-input').value = (settings.dns || []).join('\n');
  profileBaseUrl = settings.subscription_base_url || location.origin;
  $('#subscription-base').value = settings.subscription_base_url || '';
  $('#primary-host').value = settings.primary_host || settings.domain || '';
  $('#primary-port').value = settings.primary_port || settings.port || 443;
  $('#backup-host').value = settings.backup_host || '';
  $('#backup-port').value = settings.backup_port || settings.port || 443;
  $('#active-endpoint').value = settings.active_endpoint || 'primary';
  $('#active-endpoint').disabled = !settings.backup_host;
  $('#logs-output').textContent = data.logs || t('noLogs');
}

async function load() {
  const refreshButton = $('#refresh');
  refreshButton?.classList.add('is-loading');
  try { renderState(await api('/api/state')); }
  catch (error) { toast(error.message, true); }
  finally { refreshButton?.classList.remove('is-loading'); }
}

function setExpiryInputs(modeSelect, daysWrap, dateWrap, daysInput, dateInput) {
  const mode = modeSelect.value;
  daysWrap.classList.toggle('hidden', mode !== 'days');
  dateWrap.classList.toggle('hidden', mode !== 'date');
  daysInput.required = mode === 'days';
  dateInput.required = mode === 'date';
}

function toLocalExpiryTimestamp(dateValue) {
  if (!dateValue) throw new Error(t('dateRequired'));
  const [year, month, day] = dateValue.split('-').map(Number);
  const timestamp = Math.floor(new Date(year, month - 1, day, 23, 59, 59).getTime() / 1000);
  if (!Number.isFinite(timestamp)) throw new Error(t('dateRequired'));
  return timestamp;
}

function expiryPayload(mode, days, dateValue) {
  if (mode === 'unlimited') return { expires_at: null };
  if (mode === 'date') return { expires_at: toLocalExpiryTimestamp(dateValue) };
  const value = Number(days);
  if (!Number.isInteger(value) || value < 1 || value > 3650) throw new Error(t('expiryInvalid'));
  return { days: value };
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.classList.toggle('is-loading', busy);
}

$('#language-select').onchange = (event) => {
  language = ['tr','ru','en'].includes(event.target.value) ? event.target.value : 'tr';
  localStorage.setItem('oc-language', language);
  applyLanguage();
};

const themeButton = $('#theme-toggle');
function setTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem('oc-theme', theme);
  themeButton.querySelector('span').textContent = theme === 'dark' ? t('lightTheme') : t('darkTheme');
  themeButton.firstChild.textContent = theme === 'dark' ? '☼ ' : '☾ ';
}
setTheme(localStorage.getItem('oc-theme') || 'dark');
themeButton.onclick = () => setTheme(document.body.dataset.theme === 'dark' ? 'light' : 'dark');

const viewTitles = { overview:'overview', customers:'customers', settings:'settings', logs:'activity' };
function showView(name, updateHash = true) {
  if (!Object.hasOwn(viewTitles, name)) name = 'overview';
  document.body.dataset.view = name;
  $('#view-title').textContent = t(viewTitles[name]);
  document.querySelectorAll('.nav-link').forEach((link) => link.classList.toggle('active', link.hash === `#${name}`));
  if (updateHash && location.hash !== `#${name}`) history.replaceState(null, '', `#${name}`);
}
document.querySelectorAll('.nav-link').forEach((link) => link.onclick = (event) => { event.preventDefault(); showView(link.hash.slice(1)); });
window.addEventListener('hashchange', () => showView(location.hash.slice(1), false));
showView(location.hash.slice(1) || 'overview');

$('#show-add').onclick = () => {
  $('#add-form-wrap').classList.toggle('hidden');
  if (!$('#add-form-wrap').classList.contains('hidden')) $('#add-form input[name="username"]').focus();
};
$('#cancel-add').onclick = () => $('#add-form-wrap').classList.add('hidden');
$('#new-expiry-mode').onchange = () => setExpiryInputs($('#new-expiry-mode'), $('#new-days-wrap'), $('#new-date-wrap'), $('#add-form [name="days"]'), $('#add-form [name="expiry_date"]'));
$('#generate-password').onclick = () => {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%';
  const values = crypto.getRandomValues(new Uint8Array(24));
  $('#add-form input[name="password"]').value = Array.from(values, (value) => alphabet[value % alphabet.length]).join('');
};

async function copyText(value) {
  try { await navigator.clipboard.writeText(value); }
  catch {
    const input = document.createElement('textarea'); input.value = value; input.style.position = 'fixed'; input.style.opacity = '0'; document.body.appendChild(input); input.select(); document.execCommand('copy'); input.remove();
  }
}

$('#add-form').onsubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('[type="submit"]');
  const formData = new FormData(form);
  const username = formData.get('username').trim();
  const password = formData.get('password');
  const mode = $('#new-expiry-mode').value;
  const max_same_clients = Number(formData.get('max_same_clients'));
  setBusy(submit, true);
  try {
    const expiry = expiryPayload(mode, formData.get('days'), formData.get('expiry_date'));
    const result = await api('/api/users', 'POST', { username, password, ...expiry, max_same_clients });
    const profileUrl = result.profile_url || `${profileBaseUrl}/customer-profile/${encodeURIComponent(result.profile_token)}.xml`;
    await copyText(fill('copyCredentials', { user:username, password, limit:max_same_clients, url:profileUrl }));
    form.reset();
    $('#new-expiry-mode').value = 'days';
    $('#add-form [name="days"]').value = '30';
    setExpiryInputs($('#new-expiry-mode'), $('#new-days-wrap'), $('#new-date-wrap'), $('#add-form [name="days"]'), $('#add-form [name="expiry_date"]'));
    $('#add-form-wrap').classList.add('hidden');
    await load();
    const row = [...$('#users-body').querySelectorAll('tr')].find((item) => item.dataset.user === username);
    if (row) { row.classList.add('row-new'); row.scrollIntoView({ behavior:'smooth', block:'nearest' }); }
    toast(t('createdCopied'));
  } catch (error) { toast(error.message, true); }
  finally { setBusy(submit, false); }
};

function openExpiryDialog(user, expiresAt) {
  expiryUser = user;
  $('#expiry-title').textContent = fill('expiryTitle', { user });
  $('#expiry-mode').value = expiresAt ? 'date' : 'unlimited';
  $('#expiry-days').value = '';
  if (expiresAt) {
    const d = new Date(expiresAt * 1000);
    const localDate = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0,10);
    $('#expiry-date').value = localDate;
  } else $('#expiry-date').value = '';
  setExpiryInputs($('#expiry-mode'), $('#expiry-days-wrap'), $('#expiry-date-wrap'), $('#expiry-days'), $('#expiry-date'));
  $('#expiry-dialog').showModal();
}
$('#expiry-mode').onchange = () => setExpiryInputs($('#expiry-mode'), $('#expiry-days-wrap'), $('#expiry-date-wrap'), $('#expiry-days'), $('#expiry-date'));
$('#close-expiry').onclick = $('#cancel-expiry').onclick = () => $('#expiry-dialog').close();
$('#expiry-form').onsubmit = async (event) => {
  event.preventDefault();
  const submit = $('#expiry-form [type="submit"]');
  setBusy(submit, true);
  try {
    const payload = expiryPayload($('#expiry-mode').value, $('#expiry-days').value, $('#expiry-date').value);
    await api(`/api/users/${encodeURIComponent(expiryUser)}/expiry`, 'POST', payload);
    $('#expiry-dialog').close();
    await load();
    toast(t('expiryUpdated'));
  } catch (error) { toast(error.message, true); }
  finally { setBusy(submit, false); }
};

$('#users-body').onclick = async (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) return;
  const user = button.dataset.user;
  const action = button.dataset.action;
  const path = `/api/users/${encodeURIComponent(user)}`;
  if (action === 'copy-profile') {
    await copyText(`${profileBaseUrl}/customer-profile/${encodeURIComponent(button.dataset.token)}.xml`);
    toast(t('profileCopied'));
    return;
  }
  if (action === 'expiry') { openExpiryDialog(user, Number(button.dataset.expires) || null); return; }
  try {
    if (action === 'limit') {
      const value = prompt(t('daysPrompt'), button.dataset.limit || '1');
      if (value === null) return;
      const limit = Number(value);
      if (!Number.isInteger(limit) || limit < 1 || limit > 4) throw new Error(t('limitInvalid'));
      await api(`${path}/limit`, 'POST', { max_same_clients:limit });
      toast(t('limitUpdated'));
    } else if (action === 'delete') {
      if (!confirm(fill('confirmDelete', { user }))) return;
      await api(path, 'DELETE');
      toast(t('customerDeleted'));
    } else if (action === 'disable' || action === 'enable') {
      if (action === 'disable' && !confirm(fill('confirmDisable', { user }))) return;
      await api(`${path}/status`, 'POST', { active:action === 'enable' });
      toast(action === 'enable' ? t('enabledToast') : t('disabledToast'));
    } else if (action === 'password') {
      const password = prompt(fill('passwordPrompt', { user }));
      if (password === null) return;
      if (!password || password.length > 128) throw new Error(t('passwordInvalid'));
      await api(`${path}/password`, 'POST', { password });
      toast(t('passwordUpdated'));
    }
    await load();
  } catch (error) { toast(error.message, true); }
};

$('#save-dns').onclick = async (event) => {
  const button = event.currentTarget;
  setBusy(button, true);
  const dns = $('#dns-input').value.split(/\s+/).filter(Boolean);
  try { await api('/api/dns', 'POST', { dns }); toast(t('dnsSaved')); await load(); }
  catch (error) { toast(error.message, true); }
  finally { setBusy(button, false); }
};

$('#save-profile-settings').onclick = async (event) => {
  const button = event.currentTarget;
  setBusy(button, true);
  const body = {
    subscription_base_url:$('#subscription-base').value.trim(),
    primary_host:$('#primary-host').value.trim(), primary_port:Number($('#primary-port').value),
    backup_host:$('#backup-host').value.trim(), backup_port:Number($('#backup-port').value),
    active_endpoint:$('#active-endpoint').value
  };
  try { await api('/api/profile-settings', 'POST', body); toast(t('serversSaved')); await load(); }
  catch (error) { toast(error.message, true); }
  finally { setBusy(button, false); }
};

$('#check-config').onclick = async (event) => {
  const button = event.currentTarget;
  setBusy(button, true);
  try { await api('/api/check', 'POST', {}); toast(t('configValid')); }
  catch (error) { toast(error.message, true); }
  finally { setBusy(button, false); }
};

$('#restart-service').onclick = async (event) => {
  if (!confirm(t('confirmRestart'))) return;
  const button = event.currentTarget;
  setBusy(button, true);
  try { await api('/api/restart', 'POST', {}); toast(t('vpnRestarted')); setTimeout(load, 1000); }
  catch (error) { toast(error.message, true); }
  finally { setTimeout(() => setBusy(button, false), 1200); }
};

$('#admin-password-form').onsubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('[type="submit"]');
  const formData = new FormData(form);
  setBusy(button, true);
  try {
    const result = await api('/api/admin/password', 'POST', { current:formData.get('current'), new:formData.get('new') });
    toast(result.message);
    setTimeout(() => { location.href = '/login'; }, 1400);
  } catch (error) { toast(error.message, true); setBusy(button, false); }
};

$('#refresh').onclick = load;

applyLanguage();
load();
