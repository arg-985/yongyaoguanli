const api = require('../../utils/api.js');
const app = getApp();

const pad2 = (n) => (n < 10 ? '0' + n : '' + n);
const ymd = (y, m, d) => `${y}-${pad2(m)}-${pad2(d)}`;
const daysIn = (y, m) => new Date(y, m, 0).getDate();

const COLOR = { TAKEN: '#3C8D6B', LATE: '#DFA24E', MISSED: '#C4695F', SKIPPED: '#B8B3A6' };

const WEEK = ['一', '二', '三', '四', '五', '六', '日'];

Page({
  data: {
    sb: 20,
    loading: true,
    weekDays: WEEK,
    year: 0,
    month: 0,
    monthLabel: '',
    cells: [],
    summary: { total: 0, onTime: 0, late: 0, missed: 0 },
    selected: '',
    selectedLabel: '',
    dayRecords: [],
  },

  onLoad() {
    const now = new Date();
    this.setData(
      {
        sb: app.globalData.statusBarHeight,
        year: now.getFullYear(),
        month: now.getMonth() + 1,
        selected: ymd(now.getFullYear(), now.getMonth() + 1, now.getDate()),
      },
      () => {
        this._booted = true;
        if (app.isLogin()) this.load();
      }
    );
  },

  onShow() {
    if (!app.isLogin()) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    if (this._booted) this.load();
  },

  async load() {
    const { year, month } = this.data;
    this.setData({ loading: true });

    try {
      const records = await api.getAll('/records/', {
        start_date: ymd(year, month, 1),
        end_date: ymd(year, month, daysIn(year, month)),
        ordering: 'scheduled_time',
      });

      const byDay = {};
      records.forEach((r) => {
        const key = r.scheduled_time.slice(0, 10);
        if (!byDay[key]) byDay[key] = [];
        byDay[key].push(r);
      });

      const now = new Date();
      const todayStr = ymd(now.getFullYear(), now.getMonth() + 1, now.getDate());
      const offset = (new Date(year, month - 1, 1).getDay() + 6) % 7;
      const total = daysIn(year, month);
      const prevTotal = daysIn(year, month === 1 ? 12 : month - 1);

      const cells = [];
      for (let i = offset; i > 0; i -= 1) {
        cells.push({
          key: 'p' + i,
          day: prevTotal - i + 1,
          date: '',
          cls: 'muted',
          marks: [],
        });
      }
      for (let d = 1; d <= total; d += 1) {
        const date = ymd(year, month, d);
        const list = byDay[date] || [];
        const order = ['MISSED', 'LATE', 'TAKEN'];
        const marks = [];
        order.forEach((st) => {
          const hit = list.find((r) => r.status === st);
          if (hit && marks.length < 3) marks.push({ k: st, c: COLOR[st] });
        });
        let cls = '';
        if (date === this.data.selected) cls = 'on';
        else if (date === todayStr) cls = 'today';
        cells.push({ key: date, day: d, date, cls, marks });
      }
      while (cells.length % 7 !== 0) {
        cells.push({ key: 'n' + cells.length, day: '', date: '', cls: 'muted', marks: [] });
      }

      const summary = { total: records.length, onTime: 0, late: 0, missed: 0 };
      records.forEach((r) => {
        if (r.status === 'TAKEN') summary.onTime += 1;
        else if (r.status === 'LATE') summary.late += 1;
        else if (r.status === 'MISSED') summary.missed += 1;
      });

      this.setData(
        {
          cells,
          summary,
          monthLabel: `${year} 年 ${month} 月`,
          loading: false,
        },
        () => this.paintSelected(byDay)
      );
    } catch (err) {
      this.setData({ loading: false });
    }
  },

  paintSelected(byDay) {
    const selected = this.data.selected;
    const list = (byDay || {})[selected] || [];
    const dayRecords = list
      .slice()
      .sort((a, b) => (a.scheduled_time > b.scheduled_time ? 1 : -1))
      .map((r) => {
        let cls = '';
        let text = '';
        if (r.status === 'TAKEN') { cls = 'ok'; text = '已服'; }
        else if (r.status === 'LATE') { cls = 'late'; text = '迟服 ' + (r.delay_minutes || 0) + ' 分'; }
        else if (r.status === 'MISSED') { cls = 'miss'; text = '漏服'; }
        else if (r.status === 'SKIPPED') { cls = 'skip'; text = '已跳过'; }
        else { text = '待服用'; }
        return {
          id: r.id,
          time: r.scheduled_time.slice(11, 16),
          name: r.medication_name || '未命名药品',
          meta: r.taken_time ? r.taken_time.slice(11, 16) + ' 服用' : '无服药记录',
          cls,
          text,
        };
      });

    const d = selected.slice(8, 10).replace(/^0/, '');
    const m = selected.slice(5, 7).replace(/^0/, '');
    this.setData({
      dayRecords,
      selectedLabel: `${m} 月 ${d} 日`,
    });
  },

  onPick(e) {
    const date = e.currentTarget.dataset.date;
    if (!date) return;
    const cells = this.data.cells.map((c) => {
      let cls = '';
      if (c.date === date) cls = 'on';
      else if (c.cls === 'today') cls = 'today';
      return Object.assign({}, c, { cls });
    });
    this.setData({ cells, selected: date });
    this.load();
  },

  prevMonth() {
    let { year, month } = this.data;
    month -= 1;
    if (month < 1) { month = 12; year -= 1; }
    this.setData({ year, month, selected: ymd(year, month, 1) }, () => this.load());
  },

  nextMonth() {
    let { year, month } = this.data;
    month += 1;
    if (month > 12) { month = 1; year += 1; }
    this.setData({ year, month, selected: ymd(year, month, 1) }, () => this.load());
  },
});
