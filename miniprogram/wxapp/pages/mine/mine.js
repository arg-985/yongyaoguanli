const api = require('../../utils/api.js');
const app = getApp();

const ROLE = {
  patient: '患者账号',
  family: '家属账号',
  admin: '管理员',
};

Page({
  data: {
    sb: 20,
    loading: true,
    name: '',
    roleLabel: '',
    avatarText: '',
    planCount: 0,
    recordCount: 0,
    rate: 0,
  },

  onLoad() {
    this.setData({ sb: app.globalData.statusBarHeight });
  },

  onShow() {
    if (!app.isLogin()) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    this.load();
  },

  async load() {
    this.setData({ loading: true });
    try {
      const me = await api.get('/users/me/');
      wx.setStorageSync('user', me);
      app.globalData.user = me;

      const plans = await api.getAll('/plans/plans/', { status: 'active' });

      let recordCount = 0;
      let rate = 0;
      try {
        const pid = await api.patientId();
        const scope = pid ? { patient_id: pid } : {};
        const stats = await api.get('/records/adherence-stats/', Object.assign({ days: 30 }, scope));
        recordCount = (stats.on_time || 0) + (stats.late || 0) + (stats.missed || 0) + (stats.skipped || 0);
        rate = Math.round(stats.adherence_rate || 0);
      } catch (e) {
        rate = 0;
      }

      const name = me.real_name || me.username || '未命名';
      this.setData({
        loading: false,
        name,
        roleLabel: ROLE[me.role] || '用户',
        avatarText: name.slice(0, 1),
        planCount: plans.length,
        recordCount,
        rate,
      });
    } catch (err) {
      this.setData({ loading: false });
    }
  },

  onFamily() {
    wx.showToast({ title: '家属绑定请到 Web 端操作', icon: 'none' });
  },

  onPlans() {
    wx.showToast({ title: '计划管理请到 Web 端操作', icon: 'none' });
  },

  onRemind() {
    wx.showToast({ title: '提醒设置开发中', icon: 'none' });
  },

  onAbout() {
    wx.showModal({
      title: '慢性病用药提醒与依从性追踪系统',
      content: '小程序端基于原生 WXML / WXSS 编写，通过 JWT 调用 Django REST Framework 接口，与 Web 端共用同一套数据。',
      showCancel: false,
      confirmText: '知道了',
    });
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      confirmColor: '#C4695F',
      success: (res) => {
        if (!res.confirm) return;
        wx.removeStorageSync('token');
        wx.removeStorageSync('refresh');
        wx.removeStorageSync('user');
        app.globalData.user = null;
        api.reset();
        wx.navigateTo({ url: '/pages/login/login' });
      },
    });
  },
});
