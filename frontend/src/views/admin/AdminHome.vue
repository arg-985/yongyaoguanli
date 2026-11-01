<template>
  <div class="ah-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">📊 管理总览</span>
        <h1>医院<em>运行概况</em></h1>
        <p>账号 · 基础数据 · 系统安全 · 业务开关 都由管理员统一管理</p>
      </div>
      <span class="pill mint">🛡️ 管理员</span>
    </div>

    <div class="kpi-row">
      <div class="kpi-tile pink">
        <div class="kpi-num">{{ data.today_visits }}</div>
        <div class="kpi-label">今日接诊量</div>
      </div>
      <div class="kpi-tile yellow">
        <div class="kpi-num">{{ data.waiting }}</div>
        <div class="kpi-label">全院候诊</div>
      </div>
      <div class="kpi-tile sky">
        <div class="kpi-num">{{ data.unpaid }}</div>
        <div class="kpi-label">待缴费单据</div>
      </div>
      <div class="kpi-tile mint">
        <div class="kpi-num">{{ data.users }}</div>
        <div class="kpi-label">系统账号总数</div>
      </div>
    </div>

    <div class="module-grid">
      <div class="candy-card tilt-pink module" @click="$router.push('/admin/accounts')">
        <div class="m-icon">👥</div>
        <div class="m-title">账号与角色</div>
        <div class="m-desc">开号 / 注销 / 重置密码 / 分配角色，体现 RBAC 最小权限</div>
        <span class="m-go">进入 →</span>
      </div>
      <div class="candy-card tilt-sky module" @click="$router.push('/admin/catalog')">
        <div class="m-icon">🏥</div>
        <div class="m-title">基础数据</div>
        <div class="m-desc">科室、药品库（药名 / 价格 / 库存）、医生排班与号源</div>
        <span class="m-go">进入 →</span>
      </div>
      <div class="candy-card tilt-mint module" @click="$router.push('/admin/system')">
        <div class="m-icon">🔐</div>
        <div class="m-title">系统安全</div>
        <div class="m-desc">操作审计日志、数据库备份、发热门诊快速通道等业务开关</div>
        <span class="m-go">进入 →</span>
      </div>
    </div>

    <div class="candy-card tilt-yellow">
      <div class="rbac-head">🧩 三角色权限边界（RBAC）</div>
      <el-table :data="rbacRows" size="small" border>
        <el-table-column prop="item" label="能力" width="200" />
        <el-table-column prop="patient" label="患者" min-width="180" />
        <el-table-column prop="doctor" label="医生" min-width="220" />
        <el-table-column prop="admin" label="管理员" min-width="220" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { workflowApi } from '../../api/modules'

const data = ref({ today_visits: 0, waiting: 0, unpaid: 0, users: 0 })

const rbacRows = [
  { item: '就诊档案', patient: '只看自己的（只读）', doctor: '只看自己接诊过的', admin: '全量查询（不含修改病历）' },
  { item: '预约挂号', patient: '预约 / 取消自己的', doctor: '查看本人号源', admin: '配置排班与号源' },
  { item: '电子病历', patient: '不可见 / 不可改', doctor: '只能写自己的，归档后需申请修改', admin: '不可直接修改' },
  { item: '开处方', patient: '不可', doctor: '可以（不能改药库与定价）', admin: '不可开处方' },
  { item: '药品库 / 价格 / 库存', patient: '不可', doctor: '只读', admin: '增删改' },
  { item: '账号与角色', patient: '仅自己资料', doctor: '仅自己资料', admin: '开户 / 注销 / 重置 / 分配角色' },
  { item: '经营数据（收入 / 科室利润）', patient: '不可见', doctor: '不可见', admin: '可见' },
]

onMounted(async () => {
  data.value = await workflowApi.workbench()
})
</script>

<style scoped>
.ah-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.kpi-tile {
  border-radius: 22px; padding: 18px 20px; border: 2px solid #FFE2B8;
  background: #FFFDF7; box-shadow: var(--shadow-soft);
}
.kpi-tile.pink { border-color: #FFD3DF; background: linear-gradient(160deg, #FFF6F9, #FFE4EB); }
.kpi-tile.yellow { border-color: #FFE6A8; background: linear-gradient(160deg, #FFFDF2, #FFF3CC); }
.kpi-tile.sky { border-color: #CDE9F7; background: linear-gradient(160deg, #F6FCFF, #E1F2FC); }
.kpi-tile.mint { border-color: #C9EDDF; background: linear-gradient(160deg, #F7FFFB, #DFF6EC); }
.kpi-num { font-size: 30px; font-weight: 900; color: var(--ink); }
.kpi-label { font-size: 12px; font-weight: 700; color: var(--ink-soft); margin-top: 4px; }

.module-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.module { cursor: pointer; transition: transform .18s, box-shadow .18s; }
.module:hover { transform: translateY(-3px); box-shadow: 0 16px 32px rgba(201, 155, 92, .24); }
.m-icon { font-size: 30px; }
.m-title { font-size: 16px; font-weight: 900; color: var(--ink); margin-top: 8px; }
.m-desc { font-size: 12px; color: var(--ink-soft); line-height: 1.7; margin: 8px 0 12px; min-height: 42px; }
.m-go { font-size: 12.5px; font-weight: 800; color: var(--pink-deep); }

.rbac-head { font-size: 14px; font-weight: 800; color: var(--ink); margin-bottom: 10px; }
@media (max-width: 1000px) { .kpi-row { grid-template-columns: repeat(2, 1fr); } .module-grid { grid-template-columns: 1fr; } }
</style>
