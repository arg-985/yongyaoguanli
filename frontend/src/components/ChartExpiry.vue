<template>
  <div class="chartjs-expiry">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'
import ChartDataLabels from 'chartjs-plugin-datalabels'

const props = defineProps({
  // [{ label: '正常', value: n }, { label: '30天内到期', value: n }, { label: '已过期', value: n }]
  data: { type: Array, default: () => [] },
  centerText: { type: String, default: '' }
})

Chart.register(ChartDataLabels)

const canvasRef = ref(null)
let chart = null

// 与语义对应：正常=薄荷绿 / 临期=奶油黄 / 过期=樱花粉
const COLORS = ['#5FC7A1', '#FFD24A', '#FF7FA0']

const render = () => {
  if (!canvasRef.value) return
  const ctx = canvasRef.value.getContext('2d')
  if (chart) chart.destroy()

  const data = props.data.length ? props.data : [
    { label: '正常', value: 0 },
    { label: '30天内到期', value: 0 },
    { label: '已过期', value: 0 },
  ]

  const centerText = {
    id: 'centerText',
    afterDatasetsDraw(chart) {
      const { ctx, chartArea: { top, bottom, left, right } } = chart
      const cx = (left + right) / 2
      const cy = (top + bottom) / 2
      ctx.save()
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.font = 'bold 24px sans-serif'
      ctx.fillStyle = '#4A3B32'
      ctx.fillText(props.centerText, cx, cy - 8)
      ctx.font = '11px sans-serif'
      ctx.fillStyle = '#8A7466'
      ctx.fillText('箱内药品', cx, cy + 14)
      ctx.restore()
    }
  }

  chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.label),
      datasets: [{
        data: data.map(d => d.value),
        backgroundColor: COLORS,
        borderColor: '#FFFDF7',
        borderWidth: 4,
        hoverOffset: 8,
        borderRadius: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '64%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#5A4739', font: { size: 12, weight: '700' }, padding: 10, usePointStyle: true, pointStyle: 'circle' }
        },
        tooltip: {
          backgroundColor: 'rgba(255,253,247,0.98)',
          titleColor: '#4A3B32',
          bodyColor: '#5A4739',
          borderColor: '#FFE6A8',
          borderWidth: 1,
          cornerRadius: 10,
          padding: 10,
          callbacks: {
            label: (item) => ` ${item.parsed} 件`
          }
        },
        datalabels: {
          color: '#fff',
          font: { weight: '800', size: 13 },
          formatter: (v) => (v > 0 ? v : '')
        }
      },
      animation: { animateRotate: true, animateScale: true, duration: 800 }
    },
    plugins: [centerText]
  })
}

onMounted(render)
watch(() => [props.data, props.centerText], render, { deep: true })
onBeforeUnmount(() => { if (chart) chart.destroy() })
</script>

<style scoped>
.chartjs-expiry { width: 100%; height: 230px; position: relative; }
.chartjs-expiry canvas { width: 100% !important; height: 100% !important; }
</style>
