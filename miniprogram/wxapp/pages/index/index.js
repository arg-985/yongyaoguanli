const api = require('../../utils/api.js');
const app = getApp();

const pad2 = (n) => (n < 10 ? '0' + n : '' + n);

const FREQ = {
  DAILY: '每日一次',
  BID: '每日两次',
  TID: '每日三次',
  QID: '每日四次',
  ONCE_WEEKLY: '每周一次',
  CUSTOM: '自定义',
};

function parseLocal(iso) {
  return new Date(
    Number(iso.slice(0, 4)),
    Number(iso.slice(5, 7)) - 1,
    Number(iso.slice(8, 10)),
    Number(iso.slice(11, 13)),
    Number(iso.slice(14, 16))
  );
}

function periodOf(iso) {
  const h = Number(iso.slice(11, 13));
  if (h < 11) return '早';
  if (h < 14) return '午';
  if (h < 19) return '晚';
  return '睡前';
}

function greetOf(h) {
  if (h < 6) return '夜深了';
  if (h < 11) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
}

Page({
  data: {
    sb: 20,
    loading: true,
    greet: '',
    userName: '',
    avatarText: '',
    dateLabel: '',
    items: [],
    total: 0,
    done: 0,
    percent: 0,
    next: null,
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
    const now = new Date();
    const dateStr = `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())}`;

    try {
      const pid = await api.patientId();
      const scope = pid ? { patient_id: pid } : {};
      const results = await Promise.all([
        api.getAll('/plans/reminders/', Object.assign({ date: dateStr }, scope)),
        api.getAll('/records/', Object.assign({ start_date: dateStr, end_date: dateStr }, scope)),
        api.getAll('/plans/plans/'),
        api.getAll('/medications/'),
      ]);

      const reminders = results[0];
      const records = results[1];
      const plans = results[2];
      const meds = results[3];

      const planMap = {};
      plans.forEach((p) => { planMap[p.id] = p; });
      const medMap = {};
      meds.forEach((m) => { medMap[m.id] = m; });
      const recMap = {};
      records.forEach((r) => { if (r.reminder) recMap[r.reminder] = r; });

      const user = wx.getStorageSync('user') || {};
      const name = user.real_name || user.username || '朋友';

      const items = reminders
        .slice()
        .sort((a, b) => (a.scheduled_time > b.scheduled_time ? 1 : -1))
        .map((r) => {
          const plan = planMap[r.plan] || {};
          const med = medMap[plan.medication] || {};
          const dosage = plan.dosage_per_time ? String(Number(plan.dosage_per_time)) : '';
          const metaParts = [
            med.specification,
            dosage ? dosage + (med.unit || '片') : '',
            FREQ[plan.frequency] || '',
          ].filter(Boolean);

          const rec = recMap[r.id];
          let state = 'wait';
          let cls = '';
          let text = '';
          if (r.status === 'TAKEN') {
            if (rec && rec.delay_minutes > 0) {
              state = 'late';
              cls = 'late';
              text = '迟服 ' + rec.delay_minutes + ' 分';
            } else {
              state = 'done';
              cls = 'ok';
              text = '已服';
            }
          } else if (r.status === 'MISSED') {
            state = 'miss';
            cls = 'miss';
            text = '漏服';
          } else if (r.status === 'SKIPPED') {
            state = 'skip';
            text = '已跳过';
          }

          return {
            id: r.id,
            time: r.scheduled_time.slice(11, 16),
            period: periodOf(r.scheduled_time),
            name: r.medication_name || med.name || '未命名药品',
            meta: metaParts.join(' · '),
            tag: plan.notes ? String(plan.notes).slice(0, 6) : '',
            state,
            cls,
            text,
            raw: r.scheduled_time,
          };
        });

      const total = items.length;
      const done = items.filter((i) => i.state === 'done' || i.state === 'late').length;
      const percent = total ? Math.round((done / total) * 100) : 0;

      let next = null;
      const pending = items.filter((i) => i.state === 'wait');
      if (pending.length) {
        const target = pending[0];
        const diff = Math.round((parseLocal(target.raw) - now) / 60000);
        let left = '';
        if (diff <= 0) left = '已到时间';
        else if (diff < 60) left = diff + ' 分钟';
        else left = Math.floor(diff / 60) + ' 小时' + (diff % 60 ? ' ' + (diff % 60) + ' 分' : '');
        next = { time: target.time, name: target.name, left };
      }

      let tip = '';
      if (pending.length) {
        tip = `还有 ${pending.length} 次待服用，下一次在 ${next.time}，服完记得回来打卡。`;
      } else if (total) {
        tip = `今天的 ${total} 次用药已全部完成，继续保持，依从率会越来越好看。`;
      } else {
        tip = '今天没有待服提醒，可以到「用药计划」里新建一条。';
      }

      this.setData({
        items,
        total,
        done,
        percent,
        next,
        tip,
        greet: greetOf(now.getHours()),
        userName: name,
        avatarText: name.slice(0, 1),
        dateLabel: `${now.getMonth() + 1} 月 ${now.getDate()} 日`,
        loading: false,
      });
    } catch (err) {
      this.setData({ loading: false });
    }
  },

  async onTake(e) {
    const id = e.currentTarget.dataset.id;
    if (this.data.busy) return;
    this.setData({ busy: true });
    try {
      await api.post('/records/mark-taken/', { reminder_id: id });
      wx.showToast({ title: '打卡成功', icon: 'success' });
      await this.load();
    } catch (err) {
      // 错误提示已在请求层统一处理
    } finally {
      this.setData({ busy: false });
    }
  },
});
