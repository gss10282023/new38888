import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import Inspect from 'vite-plugin-inspect'

const projectRoot = fileURLToPath(new URL('../', import.meta.url))
const frontendNodeModules = fileURLToPath(new URL('./node_modules', import.meta.url))

const resolveAlias = {
  '@': fileURLToPath(new URL('./src', import.meta.url)),
  vue: fileURLToPath(new URL('./node_modules/vue/dist/vue.runtime.esm-bundler.js', import.meta.url)),
  pinia: fileURLToPath(new URL('./node_modules/pinia/dist/pinia.mjs', import.meta.url)),
  'vue-router': fileURLToPath(new URL('./node_modules/vue-router/dist/vue-router.mjs', import.meta.url)),
  gsap: fileURLToPath(new URL('./node_modules/gsap/index.js', import.meta.url)),
  '@testing-library/jest-dom': fileURLToPath(
    new URL('./node_modules/@testing-library/jest-dom/dist/index.mjs', import.meta.url)
  ),
  '@vue/test-utils': fileURLToPath(
    new URL('./node_modules/@vue/test-utils/dist/vue-test-utils.esm-bundler.mjs', import.meta.url)
  ),
  'msw/node': fileURLToPath(new URL('./node_modules/msw/lib/node/index.mjs', import.meta.url)),
  'msw/browser': fileURLToPath(new URL('./node_modules/msw/lib/browser/index.mjs', import.meta.url)),
  msw: fileURLToPath(new URL('./node_modules/msw/lib/core/index.mjs', import.meta.url)),
}

export default defineConfig(({ mode }) => {
  const plugins = [vue()]
  if (mode !== 'test') {
    plugins.push(vueDevTools(), Inspect())
  }

  return {
    plugins,
    resolve: {
      alias: resolveAlias,
    },
    server: {
      fs: {
        allow: [projectRoot],
      },
    },
    test: {
      root: projectRoot,
      include: ['tests/frontend/**/*.{test,spec}.{js,ts,tsx}'],
      globals: true,
      environment: 'jsdom',
      setupFiles: ['tests/frontend/vitest.setup.js'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'lcov'],
        reportsDirectory: 'tests/frontend/coverage',
      },
      alias: resolveAlias,
      deps: {
        moduleDirectories: ['node_modules', frontendNodeModules],
      },
    },
  }
})
