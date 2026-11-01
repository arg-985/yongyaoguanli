<template>
  <div class="chartjs-donut">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'
import ChartDataLabels from 'chartjs-plugin-datalabels'

const props = defineProps({
  data: { type: Array, default: () => [] },
  centerText: { type: String, default: '' }
})

Chart.register(ChartDataLabels)

const canvasRef = ref(null)
let chart = null

const COLORS = ['#FF7FA0', '#FFD24A', '#5FC7A1', '#6FC3E8', '#B794F4', '#FF9F6B']

const render = () => {
  if (!canvasRef.value) return
  const ctx = canvasRef.value.getContext('2d')

  if (chart) chart.destroy()

  const data = props.data.length ? props.data : [
    { label: '按时', value: 0 },
    { label: '迟服', value: 0 },
    { label: '漏服', value: 0 },
    { label: '跳过', value: 0 },
  ]

  // 画中心文字
  const centerText = {
    id: 'centerText',
    afterDatasetsDraw(chart) {
      const { ctx, chartArea: { top, bottom, left, right } } = chart
      const cx = (left + right) / 2
      const cy = (top + bottom) / 2
      ctx.save()
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.font = 'bold 26px sans-serif'
      ctx.fillStyle = '#4A3B32'
      ctx.fillText(props.centerText, cx, cy - 6)
      ctx.font = '12px sans-serif'
      ctx.fillStyle = '#8A7466'
      ctx.fillText('总完成', cx, cy + 18)
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
      cutout: '62%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#5A4739', font: { size: 12, weight: '700' }, padding: 12, usePointStyle: true, pointStyle: 'circle' }
        },
        tooltip: {
          backgroundColor: 'rgba(255,253,247,0.98)',
          titleColor: '#4A3B32',
          bodyColor: '#5A4739',
          borderColor: '#FFE6A8',
          borderWidth: 1,
          cornerRadius: 10,
          padding: 10,
          titleFont: { weight: '800' }
        },
        datalabels: {
          color: '#fff',
          font: { weight: '800', size: 12 },
          formatter: (v, ctx) => {
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
            if (!total) return ''
            const pct = ((v / total) * 100).toFixed(0)
            return pct >= 5 ? pct + '%' : ''
          }
        }
      },
      animation: { animateRotate: true, animateScale: true, duration: 900 }
    },
    plugins: [centerText]
  })
}

onMounted(render)
watch(() => [props.data, props.centerText], render, { deep: true })

onBeforeUnmount(() => { if (chart) chart.destroy() })
</script>

<style scoped>
.chartjs-donut { width: 100%; height: 320px; position: relative; }
.chartjs-donut canvas { width: 100% !important; height: 100% !important; }
</style>
