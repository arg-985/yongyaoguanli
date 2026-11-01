<template>
  <main class="app-main">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </main>
</template>

<script setup>
</script>

<style scoped>
.app-main {
  padding: 22px 24px 90px;
  min-height: calc(100vh - 64px);
  overflow-y: auto;
  background: transparent;
}
.fade-enter-active, .fade-leave-active { transition: opacity .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
