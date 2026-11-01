const api = require('../../utils/api.js');
const app = getApp();

Page({
  data: {
    sb: 20,
    username: '',
    password: '',
    loading: false,
    err: '',
  },

  onLoad() {
    this.setData({ sb: app.globalData.statusBarHeight });
    if (app.isLogin()) {
      wx.switchTab({ url: '/pages/index/index' });
    }
  },

  onUsername(e) {
    this.setData({ username: e.detail.value, err: '' });
  },

  onPassword(e) {
    this.setData({ password: e.detail.value, err: '' });
  },

  async submit() {
    const { username, password } = this.data;
    if (!username || !password) {
      this.setData({ err: '请填写用户名和密码' });
      return;
    }
    if (this.data.loading) return;
    this.setData({ loading: true, err: '' });

    try {
      const res = await api.login(username.trim(), password);
      wx.setStorageSync('token', res.access);
      wx.setStorageSync('refresh', res.refresh);
      const me = await api.get('/users/me/');
      wx.setStorageSync('user', me);
      app.globalData.user = me;
      api.reset();
      this.setData({ loading: false });
      wx.switchTab({ url: '/pages/index/index' });
    } catch (e) {
      let msg = '登录失败，请稍后重试';
      const raw = (e && e.message) || '';
      if (raw.indexOf('No active account') >= 0) msg = '用户名或密码不正确';
      else if (raw.indexOf('网络') >= 0) msg = '无法连接后端服务';
      this.setData({ loading: false, err: msg });
    }
  },
});
