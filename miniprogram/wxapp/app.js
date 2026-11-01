App({
  globalData: {
    // 后端根地址：开发者工具中需勾选「不校验合法域名」
    baseUrl: 'http://127.0.0.1:8001/api',
    statusBarHeight: 20,
    user: null,
  },

  onLaunch() {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    this.globalData.statusBarHeight = (info && info.statusBarHeight) || 20;
    this.globalData.user = wx.getStorageSync('user') || null;
  },

  isLogin() {
    return !!wx.getStorageSync('token');
  },
});
