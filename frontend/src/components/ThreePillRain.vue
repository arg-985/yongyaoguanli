<template>
  <div ref="containerRef" class="three-pill-rain"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const containerRef = ref(null)
let scene, camera, renderer, group
let rafId
const floaters = []

const PALETTE = [0xff8fae, 0xffd24a, 0x8fe3c4, 0x6fc3e8, 0xff9f6b, 0xc7a6f0]

const makeCapsule = (colorA, colorB) => {
  const g = new THREE.Group()
  const r = 0.16 + Math.random() * 0.06
  const len = 0.34 + Math.random() * 0.12
  const matA = new THREE.MeshPhysicalMaterial({ color: colorA, roughness: 0.2, clearcoat: 1, clearcoatRoughness: 0.15 })
  const matB = new THREE.MeshPhysicalMaterial({ color: colorB, roughness: 0.2, clearcoat: 1, clearcoatRoughness: 0.15 })
  const top = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 24, 0, Math.PI * 2, 0, Math.PI / 2), matA)
  top.position.y = len / 2
  const bottom = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 24, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), matB)
  bottom.position.y = -len / 2
  const mid = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 24, 1, true), matA)
  g.add(top, bottom, mid)
  return g
}

const makeTablet = (color) => {
  const mat = new THREE.MeshPhysicalMaterial({ color, roughness: 0.35, clearcoat: 0.6 })
  const t = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.07, 28), mat)
  // 药片刻痕
  const groove = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 0.012, 0.02),
    new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6 })
  )
  groove.position.y = 0.036
  t.add(groove)
  return t
}

onMounted(() => {
  const el = containerRef.value
  if (!el) return
  const w = el.clientWidth || 400
  const h = el.clientHeight || 480

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 60)
  camera.position.set(0, 0, 7)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  el.appendChild(renderer.domElement)

  scene.add(new THREE.AmbientLight(0xfff1d6, 0.9))
  const key = new THREE.DirectionalLight(0xffffff, 1.1)
  key.position.set(3, 5, 6)
  scene.add(key)
  const rim = new THREE.DirectionalLight(0xff8fae, 0.5)
  rim.position.set(-4, -2, 3)
  scene.add(rim)

  group = new THREE.Group()
  scene.add(group)

  // 视野边界（在 z=0 平面上估算）
  const halfH = Math.tan(THREE.MathUtils.degToRad(25)) * 7
  const halfW = halfH * (w / h)

  for (let i = 0; i < 16; i++) {
    const isCapsule = i % 3 !== 0
    const c1 = PALETTE[i % PALETTE.length]
    const c2 = PALETTE[(i + 2) % PALETTE.length]
    const obj = isCapsule ? makeCapsule(c1, c2) : makeTablet(c1)
    obj.position.set(
      (Math.random() * 2 - 1) * halfW,
      (Math.random() * 2 - 1) * halfH,
      -1.5 - Math.random() * 2.5
    )
    obj.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI)
    const s = 0.8 + Math.random() * 0.5
    obj.scale.setScalar(s)
    obj.userData = {
      vy: 0.004 + Math.random() * 0.008,          // 上浮速度
      rx: (Math.random() - 0.5) * 0.01,
      ry: (Math.random() - 0.5) * 0.012,
      sway: Math.random() * Math.PI * 2,           // 左右摇摆相位
      swayAmp: 0.15 + Math.random() * 0.25,
      x0: obj.position.x,
      top: halfH + 0.8,
      bottom: -halfH - 0.8
    }
    group.add(obj)
    floaters.push(obj)
  }

  const animate = () => {
    rafId = requestAnimationFrame(animate)
    const t = performance.now() * 0.001
    floaters.forEach(o => {
      const u = o.userData
      o.position.y += u.vy
      if (o.position.y > u.top) o.position.y = u.bottom
      o.position.x = u.x0 + Math.sin(t * 0.6 + u.sway) * u.swayAmp
      o.rotation.x += u.rx
      o.rotation.y += u.ry
    })
    renderer.render(scene, camera)
  }
  animate()

  const ro = new ResizeObserver(() => {
    const nw = el.clientWidth
    const nh = el.clientHeight
    if (!nw || !nh) return
    camera.aspect = nw / nh
    camera.updateProjectionMatrix()
    renderer.setSize(nw, nh)
  })
  ro.observe(el)
  el._ro = ro
})

onBeforeUnmount(() => {
  const el = containerRef.value
  if (el?._ro) el._ro.disconnect()
  cancelAnimationFrame(rafId)
  floaters.length = 0
  if (group) {
    group.traverse(o => {
      o.geometry?.dispose()
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach(m => m.dispose())
        else o.material.dispose()
      }
    })
  }
  if (renderer) {
    renderer.dispose()
    renderer.domElement?.parentNode?.removeChild(renderer.domElement)
  }
})
</script>

<style scoped>
.three-pill-rain {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.three-pill-rain canvas { display: block; width: 100% !important; height: 100% !important; }
</style>
