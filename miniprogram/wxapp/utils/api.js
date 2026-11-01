const app = () => getApp();

function pickError(data) {
  if (!data) return '';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const key = Object.keys(data)[0];
  const val = data[key];
  if (Array.isArray(val)) return val[0];
  return val ? String(val) : '';
}

function request(path, options) {
  const opts = options || {};
  const method = opts.method || 'GET';
  const data = opts.data || {};
  const auth = opts.auth !== false;

  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' };
    const token = wx.getStorageSync('token');
    if (auth && token) header.Authorization = 'Bearer ' + token;

    wx.request({
      url: app().globalData.baseUrl + path,
      method,
      data,
      header,
      success(res) {
        if (res.statusCode === 401) {
          wx.removeStorageSync('token');
          wx.navigateTo({ url: '/pages/login/login' });
          reject(new Error('登录已过期'));
          return;
        }
        if (res.statusCode >= 400) {
          const msg = pickError(res.data) || '请求失败 ' + res.statusCode;
          wx.showToast({ title: msg, icon: 'none' });
          reject(new Error(msg));
          return;
        }
        resolve(res.data);
      },
      fail(err) {
        wx.showToast({ title: '网络异常，请确认后端已启动', icon: 'none' });
        reject(err);
      },
    });
  });
}

function list(data) {
  if (Array.isArray(data)) return data;
  return (data && data.results) || [];
}

/** 后端开启分页，这里自动翻页拉全量数据 */
async function getAll(path, params) {
  const query = params || {};
  let out = [];
  let page = 1;
  for (let i = 0; i < 10; i += 1) {
    const data = await request(path, { data: Object.assign({}, query, { page }) });
    if (Array.isArray(data)) return out.concat(data);
    out = out.concat(data.results || []);
    if (!data.next) break;
    page += 1;
  }
  return out;
}

let cachedPatientId = null;

/**
 * 解析当前要查看的患者 ID。
 * 患者看自己；家属看已绑定的患者；管理员取第一个患者账号。
 */
async function patientId() {
  if (cachedPatientId) return cachedPatientId;
  const user = wx.getStorageSync('user') || {};
  let id = null;

  if (user.role === 'patient') {
    id = user.id;
  } else if (user.role === 'family') {
    const rows = await getAll('/family/bindings/');
    const bind = rows.filter((r) => r.is_authorized !== false)[0];
    id = bind ? bind.patient : null;
  } else if (user.role === 'admin') {
    const users = await getAll('/users/');
    const p = users.filter((u) => u.role === 'patient')[0];
    id = p ? p.id : null;
  }

  cachedPatientId = id || null;
  return cachedPatientId;
}

/** 切换账号后清空缓存 */
function reset() {
  cachedPatientId = null;
}

module.exports = {
  request,
  list,
  getAll,
  patientId,
  reset,
  get: (path, params) => request(path, { data: params }),
  post: (path, data) => request(path, { method: 'POST', data }),
  login: (username, password) =>
    request('/token/', { method: 'POST', data: { username, password }, auth: false }),
};
