<template>
  <div class="records-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">📁 健康档案</span>
        <h1>把每一次<em>看病记录</em>收好</h1>
        <p>病例资料 + 用药反馈，一张卡片就够</p>
      </div>
      <el-select
        v-if="auth.isAdmin"
        v-model="patient"
        filterable
        clearable
        placeholder="选择患者"
        style="width:200px"
        @change="onFilter"
      />
    </div>

    <div class="candy-card tilt-mint">
      <el-tabs v-model="tab">
        <el-tab-pane name="cases">
          <template #label><span class="tab-label">🗂️ 病例资料</span></template>
          <div class="toolbar">
            <span class="toolbar-hint">就诊单、检查报告都可以放在这里</span>
            <el-button type="primary" @click="openCaseDialog">＋ 新增病例</el-button>
          </div>
          <el-table :data="caseList" v-loading="caseLoading" class="record-table">
            <el-table-column label="标题" min-width="180">
              <template #default="{ row }">
                <div class="title-cell"><span>📄</span><b>{{ row.title }}</b></div>
              </template>
            </el-table-column>
            <el-table-column label="就诊日期" width="120">
              <template #default="{ row }">{{ row.visit_date || '-' }}</template>
            </el-table-column>
            <el-table-column label="医院" min-width="150">
              <template #default="{ row }">{{ row.hospital || '-' }}</template>
            </el-table-column>
            <el-table-column label="诊断" min-width="150">
              <template #default="{ row }">
                <span v-if="row.diagnosis" class="pill sky">{{ row.diagnosis }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="附件" width="110">
              <template #default="{ row }">
                <a v-if="row.attachment" :href="row.attachment_url || row.attachment" target="_blank" rel="noopener" class="file-link">下载附件</a>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="casePage"
            v-model:page-size="casePageSize"
            :total="caseTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pager"
            @size-change="loadCases" @current-change="loadCases"
          />
        </el-tab-pane>

        <el-tab-pane name="feedback">
          <template #label><span class="tab-label">💬 用药反馈</span></template>

          <div class="feedback-stats">
            <div class="fb-tile pink">
              <div class="fb-num">{{ summary.adverse_count }}</div>
              <div class="fb-label">近 30 天不良反应</div>
            </div>
            <div class="fb-tile mint">
              <div class="fb-num">{{ summary.avg_efficacy ?? '-' }}</div>
              <div class="fb-label">平均疗效评分</div>
            </div>
          </div>

          <div class="toolbar">
            <span class="toolbar-hint">吃完药感觉如何？记录下来才好调整方案</span>
            <el-button type="primary" @click="openFeedbackDialog">＋ 新增反馈</el-button>
          </div>

          <el-table :data="feedbackList" v-loading="feedbackLoading" class="record-table">
            <el-table-column label="药品" min-width="150">
              <template #default="{ row }">
                <div class="title-cell"><span>💊</span><b>{{ row.medication_name || '-' }}</b></div>
              </template>
            </el-table-column>
            <el-table-column label="类型" width="110">
              <template #default="{ row }">
                <span class="pill" :class="row.kind === 'adverse' ? 'pink' : 'mint'">
                  {{ row.kind === 'adverse' ? '不良反应' : '疗效自评' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="严重程度 / 疗效" width="140">
              <template #default="{ row }">
                {{ row.kind === 'adverse' ? (row.severity ?? '-') : (row.efficacy_score ?? '-') }}
              </template>
            </el-table-column>
            <el-table-column label="描述" min-width="220">
              <template #default="{ row }">{{ row.description || '-' }}</template>
            </el-table-column>
            <el-table-column label="提交时间" width="170">
              <template #default="{ row }">{{ format(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="feedbackPage"
            v-model:page-size="feedbackPageSize"
            :total="feedbackTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            class="pager"
            @size-change="loadFeedback" @current-change="loadFeedback"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 新增病例 -->
    <el-dialog v-model="caseDialogVisible" title="新增病例" width="560px">
      <el-form :model="caseForm" :rules="caseRules" ref="caseFormRef" label-width="90px">
        <el-form-item v-if="auth.isAdmin" label="患者">
          <el-select v-model="casePatient" filterable placeholder="选择患者" style="width:100%">
            <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="caseForm.title" placeholder="如 2026 年体检报告" />
        </el-form-item>
        <el-form-item label="就诊日期">
          <el-date-picker v-model="caseForm.visit_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="医院">
          <el-input v-model="caseForm.hospital" />
        </el-form-item>
        <el-form-item label="诊断">
          <el-input v-model="caseForm.diagnosis" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="caseForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            v-model:file-list="fileList"
            :auto-upload="false"
            :limit="1"
            :on-exceed="onExceed"
          >
            <el-button :icon="Upload">选择文件</el-button>
            <template #tip>
              <div class="upload-tip">可选，支持图片或 PDF，单个文件不超过 10MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="caseSubmitting" @click="onSubmitCase">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增反馈 -->
    <el-dialog v-model="feedbackDialogVisible" title="新增用药反馈" width="520px">
      <el-form :model="feedbackForm" label-width="110px">
        <el-form-item v-if="auth.isAdmin" label="患者">
          <el-select v-model="feedbackPatient" filterable placeholder="选择患者" style="width:100%">
            <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="反馈类型">
          <el-radio-group v-model="feedbackForm.kind">
            <el-radio label="adverse">不良反应</el-radio>
            <el-radio label="efficacy">疗效自评</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="feedbackForm.kind === 'adverse'" label="严重程度">
          <el-rate v-model="feedbackForm.severity" :max="5" :texts="severityTexts" show-text />
        </el-form-item>
        <el-form-item v-else label="疗效评分">
          <el-rate v-model="feedbackForm.efficacy_score" :max="5" :texts="efficacyTexts" show-text />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="feedbackForm.description" type="textarea" :rows="4" placeholder="描述具体反应或感受" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="feedbackSubmitting" @click="onSubmitFeedback">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { clinicApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const tab = ref('cases')
const patient = ref(null)
const patients = ref([])

// 病例资料
const caseLoading = ref(false)
const caseSubmitting = ref(false)
const caseList = ref([])
const caseTotal = ref(0)
const casePage = ref(1)
const casePageSize = ref(10)
const caseDialogVisible = ref(false)
const caseFormRef = ref()
const fileList = ref([])
const casePatient = ref(null)

const caseForm = reactive({ title: '', hospital: '', visit_date: '', diagnosis: '', description: '' })
const caseRules = { title: [{ required: true, message: '请填写标题', trigger: 'blur' }] }

// 用药反馈
const feedbackLoading = ref(false)
const feedbackSubmitting = ref(false)
const feedbackList = ref([])
const feedbackTotal = ref(0)
const feedbackPage = ref(1)
const feedbackPageSize = ref(10)
const feedbackDialogVisible = ref(false)
const feedbackPatient = ref(null)
const summary = reactive({ adverse_count: 0, avg_efficacy: null })

const feedbackForm = reactive({ kind: 'adverse', severity: 0, efficacy_score: 0, description: '' })
const severityTexts = ['很轻', '较轻', '中等', '较重', '严重']
const efficacyTexts = ['很差', '较差', '一般', '较好', '很好']

const format = (v) => v ? String(v).replace('T', ' ').slice(0, 16) : '-'
const patientParams = () => (patient.value ? { patient_id: patient.value } : {})

const loadCases = async () => {
  caseLoading.value = true
  try {
    const params = { page: casePage.value, page_size: casePageSize.value, ...patientParams() }
    const data = await clinicApi.casesList(params)
    caseList.value = data.results || data || []
    caseTotal.value = data.count ?? caseList.value.length
  } finally {
    caseLoading.value = false
  }
}

const loadSummary = async () => {
  try {
    const data = await clinicApi.feedbackSummary({ days: 30, ...patientParams() })
    summary.adverse_count = data.adverse_count || 0
    summary.avg_efficacy = data.avg_efficacy ?? null
  } catch (e) {
    summary.adverse_count = 0
    summary.avg_efficacy = null
  }
}

const loadFeedback = async () => {
  feedbackLoading.value = true
  try {
    const params = { page: feedbackPage.value, page_size: feedbackPageSize.value, ...patientParams() }
    const data = await clinicApi.feedbackList(params)
    feedbackList.value = data.results || data || []
    feedbackTotal.value = data.count ?? feedbackList.value.length
  } finally {
    feedbackLoading.value = false
  }
}

const onFilter = () => {
  casePage.value = 1
  feedbackPage.value = 1
  loadCases()
  loadFeedback()
  loadSummary()
}

onMounted(async () => {
  if (auth.isAdmin) {
    const data = await userApi.list({ role: 'patient', page_size: 200 })
    patients.value = data.results || data || []
  }
  loadCases()
  loadFeedback()
  loadSummary()
})

const openCaseDialog = () => {
  Object.assign(caseForm, { title: '', hospital: '', visit_date: '', diagnosis: '', description: '' })
  casePatient.value = patient.value || null
  fileList.value = []
  caseDialogVisible.value = true
}

const onExceed = () => {
  ElMessage.warning('只能上传一个附件，请先移除已选文件')
}

const onSubmitCase = async () => {
  if (auth.isAdmin && !casePatient.value) {
    ElMessage.warning('请先选择患者')
    return
  }
  await caseFormRef.value.validate()
  caseSubmitting.value = true
  try {
    const fd = new FormData()
    fd.append('title', caseForm.title)
    if (caseForm.hospital) fd.append('hospital', caseForm.hospital)
    if (caseForm.visit_date) fd.append('visit_date', caseForm.visit_date)
    if (caseForm.diagnosis) fd.append('diagnosis', caseForm.diagnosis)
    if (caseForm.description) fd.append('description', caseForm.description)
    if (casePatient.value) fd.append('patient_id', casePatient.value)
    const file = fileList.value[0]?.raw
    if (file) fd.append('attachment', file)
    await clinicApi.casesCreate(fd)
    ElMessage.success('新增成功')
    caseDialogVisible.value = false
    loadCases()
  } finally {
    caseSubmitting.value = false
  }
}

const openFeedbackDialog = () => {
  Object.assign(feedbackForm, { kind: 'adverse', severity: 0, efficacy_score: 0, description: '' })
  feedbackPatient.value = patient.value || null
  feedbackDialogVisible.value = true
}

const onSubmitFeedback = async () => {
  if (auth.isAdmin && !feedbackPatient.value) {
    ElMessage.warning('请先选择患者')
    return
  }
  feedbackSubmitting.value = true
  try {
    const payload = { kind: feedbackForm.kind, description: feedbackForm.description }
    if (feedbackForm.kind === 'adverse') {
      payload.severity = feedbackForm.severity || null
    } else {
      payload.efficacy_score = feedbackForm.efficacy_score || null
    }
    if (feedbackPatient.value) payload.patient_id = feedbackPatient.value
    await clinicApi.feedbackCreate(payload)
    ElMessage.success('新增成功')
    feedbackDialogVisible.value = false
    loadFeedback()
    loadSummary()
  } finally {
    feedbackSubmitting.value = false
  }
}
</script>

<style scoped>
.records-page { max-width: 1400px; }
.tab-label { font-weight: 800; font-size: 14px; }

.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.toolbar-hint { font-size: 12px; color: var(--ink-faint); }

.title-cell { display: flex; align-items: center; gap: 8px; }
.title-cell span { font-size: 15px; }
.title-cell b { color: var(--ink); font-weight: 700; }

.file-link { color: var(--sky-deep); font-weight: 700; font-size: 12.5px; text-decoration: none; border-bottom: 1px dashed var(--sky); }

.feedback-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; }
.fb-tile {
  border-radius: 18px; padding: 16px 20px; color: #fff;
  box-shadow: inset 0 -7px 0 rgba(0, 0, 0, .10), 0 8px 18px rgba(0, 0, 0, .06);
  display: flex; align-items: baseline; gap: 10px;
}
.fb-tile.pink { background: linear-gradient(150deg, #FF9CB4, #F0698C); }
.fb-tile.mint { background: linear-gradient(150deg, #83DFC0, #43B08D); }
.fb-num { font-size: 28px; font-weight: 800; }
.fb-label { font-size: 12px; font-weight: 600; opacity: .92; }

.pager { margin-top: 16px; justify-content: flex-end; display: flex; }
.upload-tip { font-size: 12px; color: var(--ink-faint); margin-top: 4px; }

@media (max-width: 700px) {
  .feedback-stats { grid-template-columns: 1fr; }
}
</style>
