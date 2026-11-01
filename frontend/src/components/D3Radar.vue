<template>
  <div ref="containerRef" class="d3-radar"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] },
  size: { type: Number, default: 300 }
})

const containerRef = ref(null)
let svg, g, axesGroup, area, dotsGroup, labelsGroup

const render = () => {
  if (!containerRef.value) return
  const w = props.size
  const h = props.size
  const cx = w / 2
  const cy = h / 2
  const radius = Math.min(w, h) / 2 - 48

  const data = props.data.length ? props.data : [
    { axis: '按时', value: 0 },
    { axis: '迟服', value: 0 },
    { axis: '漏服', value: 0 },
    { axis: '跳过', value: 0 },
    { axis: '连续', value: 0 },
    { axis: '规律', value: 0 },
  ]

  d3.select(containerRef.value).selectAll('*').remove()
  svg = d3.select(containerRef.value).append('svg').attr('width', w).attr('height', h)
  g = svg.append('g').attr('transform', `translate(${cx},${cy})`)

  const angleSlice = (Math.PI * 2) / data.length
  const rScale = d3.scaleLinear().domain([0, 100]).range([0, radius])

  // 网格背景（多层多边形）
  const levels = 5
  const axesGroup = g.append('g').attr('class', 'grid')
  for (let lvl = 0; lvl < levels; lvl++) {
    const r = (radius / levels) * (lvl + 1)
    axesGroup.append('polygon')
      .attr('points', data.map((_, i) => {
        const a = angleSlice * i - Math.PI / 2
        return [Math.cos(a) * r, Math.sin(a) * r].join(',')
      }).join(' '))
      .attr('fill', '#FFF8EC')
      .attr('fill-opacity', lvl % 2 ? 0.4 : 0.9)
      .attr('stroke', '#FFE6A8')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', lvl === levels - 1 ? '' : '3,3')
  }

  // 轴线
  data.forEach((_, i) => {
    const a = angleSlice * i - Math.PI / 2
    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', Math.cos(a) * radius)
      .attr('y2', Math.sin(a) * radius)
      .attr('stroke', '#FFD9A8')
      .attr('stroke-width', 1)
  })

  // 数据多边形
  const lineGen = d3.lineRadial().radius(d => rScale(d.value)).angle((_, i) => angleSlice * i - Math.PI / 2).curve(d3.curveLinearClosed)
  g.append('path')
    .datum(data)
    .attr('d', lineGen)
    .attr('fill', 'url(#radarGrad)')
    .attr('stroke', '#FF7FA0')
    .attr('stroke-width', 2.5)
    .attr('stroke-linejoin', 'round')

  const grad = svg.append('defs').append('radialGradient').attr('id', 'radarGrad')
  grad.append('stop').attr('offset', '0%').attr('stop-color', '#FFB7C8').attr('stop-opacity', 0.9)
  grad.append('stop').attr('offset', '100%').attr('stop-color', '#FFE6EE').attr('stop-opacity', 0.4)

  // 数据点
  dotsGroup = g.append('g')
  data.forEach((d, i) => {
    const a = angleSlice * i - Math.PI / 2
    dotsGroup.append('circle')
      .attr('cx', Math.cos(a) * rScale(d.value))
      .attr('cy', Math.sin(a) * rScale(d.value))
      .attr('r', 4)
      .attr('fill', '#FF7FA0')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
  })

  // 轴标签
  labelsGroup = g.append('g')
  data.forEach((d, i) => {
    const a = angleSlice * i - Math.PI / 2
    const lx = Math.cos(a) * (radius + 26)
    const ly = Math.sin(a) * (radius + 26)
    labelsGroup.append('text')
      .attr('x', lx)
      .attr('y', ly)
      .attr('text-anchor', Math.cos(a) > 0.2 ? 'start' : Math.cos(a) < -0.2 ? 'end' : 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', '#8A7466')
      .attr('font-size', 12)
      .attr('font-weight', 700)
      .text(`${d.axis} ${d.value}`)
  })
}

onMounted(render)
watch(() => props.data, render, { deep: true })

onBeforeUnmount(() => { if (svg) svg.remove() })
</script>

<style scoped>
.d3-radar { width: 100%; display: flex; justify-content: center; }
</style>
