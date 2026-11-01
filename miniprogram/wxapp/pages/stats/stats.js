const api = require('../../utils/api.js');
const app = getApp();

const WEEK_CN = ['日', '一', '二', '三', '四', '五', '六'];

function rateOf(stats) {
  if (!stats || !stats.daily || !stats.daily.length) return 0;
  let taken = 0;
  let total = 0;
  stats.daily.forEach((d) => {
    taken += (d.adherence_rate * d.total) / 100;
    total += d.total;
  });
  return total ? (taken / total) * 100 : 0;
}

Page({
  data: {
    sb: 20,
    loading: true,
    empty: false,
    rate: '0',
    deltaText: '',
    deltaCls: 'flat',
    bars: [],
    dist: [],
    onTime: 0,
    late: 0,
    missed: 0,
    tip: '',
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
      const pid = await api.patientId();
      const scope = pid ? { patient_id: pid } : {};
      const [s7, s14] = await Promise.all([
        api.get('/records/adherence-stats/', Object.assign({ days: 7 }, scope)),
        api.get('/records/adherence-stats/', Object.assign({ days: 14 }, scope)),
      ]);

      if (!s7 || !s7.total) {
        this.setData({ loading: false, empty: true, rate: '0' });
        return;
      }

      // 近 7 天加权依从率
      const cur = rateOf(s7);
      // 对比上一周
      const prevStats = Object.assign({}, s14, {
        daily: (s14.daily || []).slice(0, 7),
      });
      const prev = rateOf(prevStats);
      let deltaText = '与上周持平';
      let deltaCls = 'flat';
      if (s14 && s14.daily && s14.daily.length > 7) {
        const diff = Math.round((cur - prev) * 10) / 10;
        if (diff > 0) {
          deltaText = '↑ ' + diff + '% 较上周';
          deltaCls = 'up';
        } else if (diff < 0) {
          deltaText = '↓ ' + Math.abs(diff) + '% 较上周';
          deltaCls = 'down';
        }
      }

      const daily = s7.daily || [];
      const maxRate = Math.max.apply(null, daily.map((d) => d.adherence_rate).concat([0]));
      const bars = daily.map((d, i) => {
        const w = WEEK_CN[new Date(d.date.replace(/-/g, '/')).getDay()];
        return {
          k: d.date,
          label: w,
          h: Math.max(10, Math.round(d.adherence_rate)),
          hi: maxRate > 0 && d.adherence_rate === maxRate,
        };
      });

      const raw = s14.by_weekday || [];
      const sum = raw.reduce((acc, r) => acc + r.count, 0);
      const dist = raw
        .filter((r) => r.count > 0)
        .sort((a, b) => b.count - a.count)
        .slice(0, 4)
        .map((r) => ({
          k: r.weekday,
          label: '周' + ['一', '二', '三', '四', '五', '六', '日'][r.weekday - 1],
          pct: Math.round((r.count / sum) * 100),
        }));

      let tip = '';
      if (dist.length) {
        tip = `${dist[0].label} 是最容易漏服的一天，建议把药盒放在显眼处，或让家属在固定时间提醒。`;
      } else {
        tip = '近 14 天没有漏服记录，目前的服药节奏保持得很好。';
      }

      this.setData({
        loading: false,
        empty: false,
        rate: Math.round(cur),
        deltaText,
        deltaCls,
        bars,
        dist,
        onTime: s7.on_time,
        late: s7.late,
        missed: s7.missed,
        tip,
      });
    } catch (err) {
      this.setData({ loading: false });
    }
  },
});
