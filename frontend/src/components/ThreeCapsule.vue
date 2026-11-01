<template>
  <div ref="containerRef" class="three-capsule"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const containerRef = ref(null)
let scene, camera, renderer, capsule, group
let rafId
let pointer = { x: 0, y: 0 }

const onMount = () => {
  const el = containerRef.value
  if (!el) return
  // 兜底：若布局还没算好，用默认尺寸
  const w = el.clientWidth || 300
  const h = el.clientHeight || 260

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100)
  camera.position.set(0, 0, 6)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  el.appendChild(renderer.domElement)

  // 灯光：主光 + 补光 + 环境光
  scene.add(new THREE.AmbientLight(0xfff1d6, 0.7))
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.2)
  keyLight.position.set(3, 4, 5)
  scene.add(keyLight)
  const rimLight = new THREE.DirectionalLight(0xff7fa0, 0.6)
  rimLight.position.set(-4, -2, 2)
  scene.add(rimLight)
  const fillLight = new THREE.PointLight(0x6fc3e8, 0.8, 20)
  fillLight.position.set(0, 3, -3)
  scene.add(fillLight)

  group = new THREE.Group()
  scene.add(group)

  // 胶囊：两个半球 + 中间圆柱
  const r = 0.8
  const seg = 64
  const matTop = new THREE.MeshPhysicalMaterial({
    color: 0xff8fae,
    roughness: 0.15,
    metalness: 0.1,
    clearcoat: 1,
    clearcoatRoughness: 0.1,
    transmission: 0.2,
    thickness: 1.2,
    ior: 1.4,
    transparent: true,
    opacity: 0.98
  })
  const matBottom = new THREE.MeshPhysicalMaterial({
    color: 0xffe7a6,
    roughness: 0.15,
    metalness: 0.1,
    clearcoat: 1,
    clearcoatRoughness: 0.1,
    transmission: 0.2,
    thickness: 1.2,
    transparent: true,
    opacity: 0.98
  })

  // 粉色半球
  const top = new THREE.Mesh(new THREE.SphereGeometry(r, seg, seg, 0, Math.PI * 2, 0, Math.PI / 2), matTop)
  top.position.y = 0.6
  // 黄色半球
  const bottom = new THREE.Mesh(new THREE.SphereGeometry(r, seg, seg, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), matBottom)
  bottom.position.y = -0.6
  // 中间圆柱
  const middle = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1.2, seg, 1, true), matTop)
  middle.position.y = 0
  group.add(top, bottom, middle)

  // 围绕的小球粒子
  for (let i = 0; i < 14; i++) {
    const angle = (i / 14) * Math.PI * 2
    const rad = 2.4 + Math.random() * 0.4
    const s = new THREE.Mesh(
      new THREE.SphereGeometry(0.06 + Math.random() * 0.05, 16, 16),
      new THREE.MeshBasicMaterial({ color: [0xffd24a, 0xff8fae, 0x8fe3c4, 0x6fc3e8][i % 4] })
    )
    s.position.set(Math.cos(angle) * rad, (Math.random() - 0.5) * 2.5, Math.sin(angle) * rad)
    s.userData = { angle, rad, speed: 0.3 + Math.random() * 0.5, yBase: s.position.y }
    group.add(s)
  }

  group.rotation.x = 0.3
  group.rotation.z = -0.6

  const onPointerMove = (e) => {
    const rect = el.getBoundingClientRect()
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
  }
  el.addEventListener('mousemove', onPointerMove)

  const animate = () => {
    rafId = requestAnimationFrame(animate)
    group.rotation.y += 0.008
    // 鼠标微动跟随
    group.rotation.x += ((pointer.y * 0.4 + 0.3) - group.rotation.x) * 0.05
    group.rotation.z += ((-pointer.x * 0.5 - 0.6) - group.rotation.z) * 0.05

    group.children.forEach(c => {
      if (c.userData.angle != null) {
        c.userData.angle += 0.006 * c.userData.speed
        c.position.x = Math.cos(c.userData.angle) * c.userData.rad
        c.position.z = Math.sin(c.userData.angle) * c.userData.rad
        c.position.y = c.userData.yBase + Math.sin(Date.now() * 0.001 + c.userData.angle) * 0.3
      }
    })
    renderer.render(scene, camera)
  }
  animate()

  const onResize = () => {
    if (!renderer) return
    const nw = el.clientWidth
    const nh = el.clientHeight
    camera.aspect = nw / nh
    camera.updateProjectionMatrix()
    renderer.setSize(nw, nh)
  }
  window.addEventListener('resize', onResize)
  el._onResize = onResize
  el._onMove = onPointerMove
}

onMounted(() => {
  // 立即初始化（尺寸用兜底），然后用 ResizeObserver 跟随真实尺寸
  onMount()
  const ro = new ResizeObserver(() => {
    if (renderer && containerRef.value) {
      const nw = containerRef.value.clientWidth
      const nh = containerRef.value.clientHeight
      if (nw > 0 && nh > 0) {
        camera.aspect = nw / nh
        camera.updateProjectionMatrix()
        renderer.setSize(nw, nh)
      }
    }
  })
  if (containerRef.value) ro.observe(containerRef.value)
})

onBeforeUnmount(() => {
  const el = containerRef.value
  if (el) {
    el.removeEventListener('mousemove', el._onMove)
    window.removeEventListener('resize', el._onResize)
  }
  cancelAnimationFrame(rafId)
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
    if (renderer.domElement?.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement)
  }
})
</script>

<style scoped>
.three-capsule {
  width: 100%;
  height: 260px;
}
.three-capsule canvas { display: block; width: 100% !important; height: 100% !important; }
</style>
