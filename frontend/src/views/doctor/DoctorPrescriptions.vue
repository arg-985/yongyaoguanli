<template>
  <div class="drx-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">💊 我的处方</span>
        <h1>我开出的<em>每一张处方</em></h1>
        <p>可开药与调整剂量，但不能改动药库库存与药品定价</p>
      </div>
      <el-select v-model="range" style="width:160px" @change="load">
        <el-option label="全部处方" value="all" />
        <el-option label="本月处方" value="month" />
      </el-select>
    </div>

    <div class="kpi-row">
      <div class="kpi-tile mint">
        <div class="kpi-num">{{ stats.count }}</div>
        <div class="kpi-label">处方数量</div>
      </div>
      <div class="kpi-tile sky">
        <div class="kpi-num">{{ stats.patients }}</div>
        <div class="kpi-label">覆盖患者</div>
      </div>
      <div class="kpi-tile pink">
        <div class="kpi-num">¥{{ stats.amount }}</div>
        <div class="kpi-label">处方金额合计</div>
      </div>
    </div>

    <div class="candy-card tilt-mint">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-box">
              <div v-for="it in row.items" :key="it.id" class="rx-line">
                <b>{{ it.medication_name }}</b>
                <span>{{ it.specification }}</span>
                <span>{{ it.dosage }} · {{ it.frequency }} · {{ it.days }} 天</span>
                <span>×{{ it.quantity }}</span>
                <span>单价 ¥{{ it.unit_price }}</span>
              </div>
              <div v-if="!row.items.length" class="empty-items">暂无明细</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="处方号" width="90">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column prop="patient_name" label="患者" width="130" />
        <el-table-column prop="diagnosis" label="临床诊断" min-width="180">
          <template #default="{ row }">{{ row.diagnosis || '—' }}</template>
        </el-table-column>
        <el-table-column label="药品数" width="90">
          <template #default="{ row }">{{ row.items.length }} 种</template>
        </el-table-column>
        <el-table-column label="金额" width="110">
          <template #default="{ row }"><span class="amount">¥{{ row.total_amount }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ISSUED' ? 'success' : 'info'" size="small">
              {{ row.status === 'ISSUED' ? '已开具' : '已作废' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开方时间" width="160">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="还没有开具的处方" :image-size="80" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { workflowApi } from '../../api/modules'

const list = ref([])
const loading = ref(false)
const range = ref('all')

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')

const stats = computed(() => {
  const count = list.value.length
  const patients = new Set(list.value.map((r) => r.patient)).size
  const amount = list.value.reduce((s, r) => s + Number(r.total_amount || 0), 0).toFixed(2)
  return { count, patients, amount }
})

const load = async () => {
  loading.value = true
  try {
    const res = await workflowApi.prescriptions({ page_size: 300 })
    let rows = listOf(res)
    if (range.value === 'month') {
      const now = new Date()
      const prefix = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
      rows = rows.filter((r) => String(r.created_at || '').startsWith(prefix))
    }
    list.value = rows
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.drx-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.kpi-tile {
  border-radius: 22px; padding: 18px 20px; border: 2px solid #FFE2B8;
  background: #FFFDF7; box-shadow: var(--shadow-soft);
}
.kpi-tile.mint { border-color: #C9EDDF; background: linear-gradient(160deg, #F7FFFB, #DFF6EC); }
.kpi-tile.sky { border-color: #CDE9F7; background: linear-gradient(160deg, #F6FCFF, #E1F2FC); }
.kpi-tile.pink { border-color: #FFD3DF; background: linear-gradient(160deg, #FFF6F9, #FFE4EB); }
.kpi-num { font-size: 28px; font-weight: 900; color: var(--ink); }
.kpi-label { font-size: 12px; font-weight: 700; color: var(--ink-soft); margin-top: 4px; }
.amount { font-weight: 900; color: var(--orange-deep); }
.expand-box { padding: 10px 24px; display: flex; flex-direction: column; gap: 6px; }
.rx-line { display: flex; gap: 14px; font-size: 12.5px; color: var(--ink-soft); flex-wrap: wrap; }
.empty-items { font-size: 12px; color: var(--ink-faint); }
</style>
