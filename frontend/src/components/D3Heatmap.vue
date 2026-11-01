<template>
  <div ref="containerRef" class="d3-heatmap">
    <div v-show="tip.show" class="hm-tip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }">
      <div class="tip-date">{{ tip.date }}</div>
      <div class="tip-text" v-html="tip.text"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  // [{ date: 'YYYY-MM-DD', rate: 0-100, total: n }]
  data: { type: Array, default: () => [] },
  weeks: { type: Number, default: 18 }
})

const containerRef = ref(null)
const tip = reactive({ show: false, x: 0, y: 0, date: '', text: '' })

const CELL = 14
const GAP = 3
const STEP = CELL + GAP
const LEFT = 30
const TOP = 22

const color = d3.scaleLinear()
  .domain([0, 50, 80, 100])
  .range(['#FFE9A8', '#FFD24A', '#FFAE5F', '#FF7FA0'])

const EMPTY = '#F6EDDD'
const fmt = d3.timeFormat('%Y-%m-%d')

const render = () => {
  if (!containerRef.value) return
  d3.select(containerRef.value).selectAll('svg').remove()

  const dataMap = new Map(props.data.map(d => [d.date, d]))

  // 结束于今天，往前推 weeks 周，周一对齐
  const end = new Date()
  const totalDays = props.weeks * 7 - 1
  const rawStart = d3.timeDay.offset(end, -totalDays)
  const start = d3.timeMonday.floor(rawStart)

  const days = d3.timeDay.range(start, d3.timeDay.offset(end, 1))
  const weekIndex = d3.timeMonday.count(start, end) + 1

  const w = LEFT + weekIndex * STEP + 6
  const h = TOP + 7 * STEP + 26

  const svg = d3.select(containerRef.value).append('svg')
    .attr('width', '100%')
    .attr('height', h)
    .attr('viewBox', `0 0 ${w} ${h}`)
    .attr('preserveAspectRatio', 'xMinYMid meet')

  // 月份标签
  const monthG = svg.append('g')
  let lastMonth = -1
  days.forEach(d => {
    const wi = d3.timeMonday.count(start, d)
    const m = d.getMonth()
    if (d.getDay() === 1 && m !== lastMonth) {
      lastMonth = m
      monthG.append('text')
        .attr('x', LEFT + wi * STEP)
        .attr('y', 12)
        .attr('fill', '#8A7466')
        .attr('font-size', 11)
        .attr('font-weight', 700)
        .text(`${m + 1}月`)
    }
  })

  // 星期标签（一三五）
  const wdLabels = { 1: '一', 3: '三', 5: '五' }
  Object.entries(wdLabels).forEach(([day, txt]) => {
    svg.append('text')
      .attr('x', LEFT - 8)
      .attr('y', TOP + (Number(day) - 1) * STEP + CELL / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'central')
      .attr('fill', '#B7A48F')
      .attr('font-size', 10)
      .text(txt)
  })

  // 格子
  const cellX = d => LEFT + d3.timeMonday.count(start, d) * STEP
  const cellY = d => TOP + ((d.getDay() + 6) % 7) * STEP
  const cell = svg.append('g').selectAll('rect')
    .data(days)
    .join('rect')
    .attr('x', cellX)
    .attr('y', cellY)
    .attr('width', CELL)
    .attr('height', CELL)
    .attr('rx', 4)
    .attr('fill', d => {
      const rec = dataMap.get(fmt(d))
      if (!rec || !rec.total) return EMPTY
      return color(Math.max(0, Math.min(100, rec.rate ?? 0)))
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 1)
    .style('cursor', 'pointer')
    .style('transition', 'transform .12s ease')

  cell
    .on('mouseenter', function (event, d) {
      // 以格子中心缩放，避免以 SVG 原点缩放导致格子移出光标、引发 enter/leave 闪烁
      const cx = cellX(d) + CELL / 2
      const cy = cellY(d) + CELL / 2
      d3.select(this)
        .attr('transform', `translate(${cx},${cy}) scale(1.3) translate(${-cx},${-cy})`)
        .attr('stroke', '#E8862B')
      const rec = dataMap.get(fmt(d))
      const rect = containerRef.value.getBoundingClientRect()
      const [mx, my] = d3.pointer(event, containerRef.value)
      tip.date = d3.timeFormat('%Y年%m月%d日')(d)
      tip.text = rec && rec.total
        ? `应服 <b>${rec.total}</b> 次 · 依从率 <b>${Number((rec.rate ?? 0).toFixed(0))}%</b>`
        : '这一天没有服药任务 🐾'
      tip.x = Math.min(mx + 14, rect.width - 170)
      tip.y = Math.max(my - 54, 4)
      tip.show = true
    })
    .on('mouseleave', function () {
      d3.select(this).attr('transform', null).attr('stroke', '#fff')
      tip.show = false
    })

  // 入场动画
  cell.attr('opacity', 0)
    .transition()
    .delay((d, i) => i * 2)
    .duration(220)
    .attr('opacity', 1)

  // 图例
  const legend = svg.append('g')
    .attr('transform', `translate(${w - 172}, ${h - 16})`)
  legend.append('text')
    .attr('x', -34).attr('y', 10)
    .attr('fill', '#B7A48F').attr('font-size', 10)
    .text('低')
  const legendColors = [EMPTY, '#FFE9A8', '#FFD24A', '#FFAE5F', '#FF7FA0']
  legend.selectAll('rect')
    .data(legendColors)
    .join('rect')
    .attr('x', (c, i) => i * 16)
    .attr('y', 0)
    .attr('width', 12).attr('height', 12).attr('rx', 3)
    .attr('fill', c => c)
    .attr('stroke', '#fff')
  legend.append('text')
    .attr('x', legendColors.length * 16 + 6).attr('y', 10)
    .attr('fill', '#B7A48F').attr('font-size', 10)
    .text('高')
}

onMounted(render)
watch(() => [props.data, props.weeks], render, { deep: true })
onBeforeUnmount(() => { d3.select(containerRef.value).selectAll('*').remove() })
</script>

<style scoped>
.d3-heatmap { position: relative; width: 100%; overflow-x: auto; }
.hm-tip {
  position: absolute;
  z-index: 10;
  pointer-events: none;
  background: #FFFDF7;
  border: 2px solid #FFE6A8;
  border-radius: 12px;
  padding: 8px 12px;
  box-shadow: 0 8px 18px rgba(201, 155, 92, .25);
  white-space: nowrap;
}
.tip-date { font-size: 11px; font-weight: 800; color: var(--ink); margin-bottom: 2px; }
.tip-text { font-size: 11px; color: var(--ink-soft); }
.tip-text :deep(b) { color: var(--pink-deep); }
</style>
