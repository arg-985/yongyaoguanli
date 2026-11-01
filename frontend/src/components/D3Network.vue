<template>
  <div ref="containerRef" class="d3-network">
    <div v-show="tip.show" class="net-tip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }">
      <div class="tip-name">{{ tip.name }}</div>
      <div class="tip-text">{{ tip.text }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import * as d3 from 'd3'

// findings: [{ level: 'high'|'medium'|'info', title, medications: [{id, name}] }]
const props = defineProps({
  findings: { type: Array, default: () => [] },
  height: { type: Number, default: 380 }
})

const containerRef = ref(null)
const tip = reactive({ show: false, x: 0, y: 0, name: '', text: '' })

const LEVEL_COLOR = { high: '#FF7FA0', medium: '#FFD24A', info: '#6FC3E8' }
const LEVEL_RANK = { info: 1, medium: 2, high: 3 }
const LEVEL_LABEL = { high: '高风险', medium: '需关注', info: '提示' }

let simulation = null

const buildGraph = () => {
  const nodeMap = new Map()
  const linkMap = new Map()

  props.findings.forEach(f => {
    const meds = (f.medications || []).filter(m => m && m.name)
    meds.forEach(m => {
      if (!nodeMap.has(m.id)) {
        nodeMap.set(m.id, { id: m.id, name: m.name, count: 0, level: 'info', findings: [] })
      }
      const n = nodeMap.get(m.id)
      n.count += 1
      n.findings.push(f.title)
      if ((LEVEL_RANK[f.level] || 1) > LEVEL_RANK[n.level]) n.level = f.level
    })
    // 同一风险项里的药两两连线
    for (let i = 0; i < meds.length; i++) {
      for (let j = i + 1; j < meds.length; j++) {
        const key = [meds[i].id, meds[j].id].sort().join('|')
        if (!linkMap.has(key)) {
          linkMap.set(key, { source: meds[i].id, target: meds[j].id, titles: [], level: 'info' })
        }
        const l = linkMap.get(key)
        l.titles.push(f.title)
        if ((LEVEL_RANK[f.level] || 1) > LEVEL_RANK[l.level]) l.level = f.level
      }
    }
  })
  return { nodes: [...nodeMap.values()], links: [...linkMap.values()] }
}

const render = () => {
  if (!containerRef.value) return
  if (simulation) { simulation.stop(); simulation = null }
  d3.select(containerRef.value).selectAll('svg').remove()

  const { nodes, links } = buildGraph()
  if (!nodes.length) return

  const w = containerRef.value.clientWidth || 640
  const h = props.height

  const svg = d3.select(containerRef.value).append('svg')
    .attr('width', '100%')
    .attr('height', h)
    .attr('viewBox', `0 0 ${w} ${h}`)

  // 箭头定义
  const defs = svg.append('defs')
  Object.entries(LEVEL_COLOR).forEach(([lv, c]) => {
    defs.append('marker')
      .attr('id', `arrow-${lv}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 26).attr('refY', 0)
      .attr('markerWidth', 7).attr('markerHeight', 7)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4L8,0L0,4')
      .attr('fill', c)
  })

  const link = svg.append('g').selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', d => LEVEL_COLOR[d.level])
    .attr('stroke-width', d => 1.5 + d.titles.length)
    .attr('stroke-opacity', 0.65)
    .attr('stroke-dasharray', d => d.level === 'high' ? '' : '6,4')
    .attr('marker-end', d => `url(#arrow-${d.level})`)

  const node = svg.append('g').selectAll('g')
    .data(nodes)
    .join('g')
    .style('cursor', 'grab')

  node.append('circle')
    .attr('r', 0)
    .attr('fill', d => LEVEL_COLOR[d.level])
    .attr('fill-opacity', 0.92)
    .attr('stroke', '#fff')
    .attr('stroke-width', 3)
    .style('filter', 'drop-shadow(0 4px 6px rgba(201,155,92,.3))')
    .transition()
    .duration(500)
    .attr('r', d => 15 + Math.min(d.count, 4) * 4)

  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 4)
    .attr('font-size', 13)
    .text('💊')

  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('y', d => 15 + Math.min(d.count, 4) * 4 + 15)
    .attr('font-size', 11)
    .attr('font-weight', 700)
    .attr('fill', '#5A4739')
    .text(d => d.name.length > 7 ? d.name.slice(0, 7) + '…' : d.name)

  node
    .on('mouseenter', function (event, d) {
      d3.select(this).select('circle').attr('stroke', '#E8862B').attr('stroke-width', 3.5)
      const [mx, my] = d3.pointer(event, containerRef.value)
      tip.name = `${d.name} · ${LEVEL_LABEL[d.level]}`
      tip.text = d.findings.length > 2
        ? `涉及 ${d.findings.length} 项风险：${d.findings.slice(0, 2).join('；')} 等`
        : `涉及：${d.findings.join('；')}`
      tip.x = Math.min(mx + 14, w - 200)
      tip.y = Math.max(my - 60, 6)
      tip.show = true
    })
    .on('mouseleave', function () {
      d3.select(this).select('circle').attr('stroke', '#fff').attr('stroke-width', 3)
      tip.show = false
    })

  node.call(
    d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.25).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null; d.fy = null
      })
  )

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-320))
    .force('center', d3.forceCenter(w / 2, h / 2 - 10))
    .force('x', d3.forceX(w / 2).strength(0.06))
    .force('y', d3.forceY(h / 2).strength(0.1))
    .force('collide', d3.forceCollide(d => 15 + Math.min(d.count, 4) * 4 + 22))
    .on('tick', () => {
      nodes.forEach(d => {
        const r = 15 + Math.min(d.count, 4) * 4
        d.x = Math.max(r + 4, Math.min(w - r - 4, d.x))
        d.y = Math.max(r + 4, Math.min(h - r - 24, d.y))
      })
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)
      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })
}

onMounted(render)
watch(() => props.findings, render, { deep: true })
onBeforeUnmount(() => {
  if (simulation) simulation.stop()
  d3.select(containerRef.value).selectAll('*').remove()
})
</script>

<style scoped>
.d3-network { position: relative; width: 100%; }
.net-tip {
  position: absolute;
  z-index: 10;
  pointer-events: none;
  max-width: 220px;
  background: #FFFDF7;
  border: 2px solid #FFD3DF;
  border-radius: 12px;
  padding: 8px 12px;
  box-shadow: 0 8px 18px rgba(201, 155, 92, .25);
}
.tip-name { font-size: 12px; font-weight: 800; color: var(--pink-deep); margin-bottom: 2px; }
.tip-text { font-size: 11px; color: var(--ink-soft); line-height: 1.6; }
</style>
