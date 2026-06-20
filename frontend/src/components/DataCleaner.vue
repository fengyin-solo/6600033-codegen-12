<template>
  <div class="bg-slate-900 text-slate-200 min-h-screen">
    <header class="border-b border-slate-700 px-6 py-4 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-emerald-400">样本数据清洗助手</h1>
        <p class="text-sm text-slate-500 mt-1">缺失值检测 · 异常值识别 · 处理前后对比</p>
      </div>
      <button @click="$emit('close')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm">
        ← 返回
      </button>
    </header>

    <div class="p-4">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-1 space-y-4">
          <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 class="text-sm font-bold text-slate-400 mb-3">数据输入</h3>
            <div class="space-y-3">
              <div>
                <label class="text-xs text-slate-500">列名 (逗号分隔)</label>
                <input v-model="columnsInput" type="text" placeholder="年龄,收入,分数" 
                  class="w-full mt-1 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm focus:outline-none focus:border-emerald-500" />
              </div>
              <div>
                <label class="text-xs text-slate-500">数据 (每行一条记录，逗号分隔)</label>
                <textarea v-model="dataInput" rows="8" placeholder="35,50000,75&#10;42,65000,82&#10;None,45000,68" 
                  class="w-full mt-1 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-emerald-500 resize-none"></textarea>
              </div>
              <button @click="loadSample" class="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm">
                📊 加载示例数据
              </button>
            </div>
          </div>

          <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 class="text-sm font-bold text-slate-400 mb-3">缺失值处理</h3>
            <div class="space-y-2">
              <label class="text-xs text-slate-500">处理方法</label>
              <select v-model="missingMethod" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm focus:outline-none focus:border-emerald-500">
                <option value="mean">均值填充</option>
                <option value="median">中位数填充</option>
                <option value="mode">众数填充</option>
                <option value="forward">前向填充</option>
                <option value="backward">后向填充</option>
                <option value="zero">零值填充</option>
                <option value="drop">删除缺失行</option>
              </select>
            </div>
          </div>

          <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 class="text-sm font-bold text-slate-400 mb-3">异常值处理</h3>
            <div class="space-y-3">
              <div>
                <label class="text-xs text-slate-500">检测方法</label>
                <select v-model="outlierMethod" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm focus:outline-none focus:border-emerald-500">
                  <option value="iqr">IQR 四分位法</option>
                  <option value="zscore">Z-score 标准化</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-slate-500">阈值: {{ outlierThreshold }}</label>
                <input v-model.number="outlierThreshold" type="range" min="1" max="3" step="0.1" 
                  class="w-full mt-1 accent-emerald-500" />
              </div>
              <div>
                <label class="text-xs text-slate-500">处理方式</label>
                <select v-model="outlierAction" class="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm focus:outline-none focus:border-emerald-500">
                  <option value="cap">盖帽法 (限制在边界)</option>
                  <option value="mean">均值替换</option>
                  <option value="median">中位数替换</option>
                  <option value="remove">删除异常行</option>
                </select>
              </div>
            </div>
          </div>

          <button @click="runCleaning" :disabled="store.isCleaning || !columnsInput || !dataInput" 
            class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-sm font-bold">
            {{ store.isCleaning ? '处理中...' : '🔧 开始数据清洗' }}
          </button>
        </div>

        <div class="lg:col-span-2 space-y-4">
          <div v-if="store.cleaningResult" class="grid grid-cols-2 gap-4">
            <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 class="text-sm font-bold text-slate-400 mb-2">📊 处理前概览</h3>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">总行数</div>
                  <div class="text-lg font-bold text-slate-300">{{ store.cleaningResult.before.stats.total_rows }}</div>
                </div>
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">总列数</div>
                  <div class="text-lg font-bold text-slate-300">{{ store.cleaningResult.before.stats.columns.length }}</div>
                </div>
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">缺失值</div>
                  <div class="text-lg font-bold text-orange-400">{{ store.cleaningResult.missing_report.total_missing_before }}</div>
                  <div class="text-xs text-slate-500">({{ store.cleaningResult.before.stats.total_missing_percent }}%)</div>
                </div>
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">异常值</div>
                  <div class="text-lg font-bold text-red-400">{{ store.cleaningResult.outlier_report.total_outliers_before }}</div>
                  <div class="text-xs text-slate-500">({{ store.cleaningResult.before.stats.total_outlier_percent }}%)</div>
                </div>
              </div>
            </div>

            <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 class="text-sm font-bold text-slate-400 mb-2">✅ 处理后概览</h3>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">总行数</div>
                  <div class="text-lg font-bold text-slate-300">{{ store.cleaningResult.after.stats.total_rows }}</div>
                </div>
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">总列数</div>
                  <div class="text-lg font-bold text-slate-300">{{ store.cleaningResult.after.stats.columns.length }}</div>
                </div>
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">缺失值</div>
                  <div class="text-lg font-bold text-emerald-400">{{ store.cleaningResult.missing_report.total_missing_after }}</div>
                  <div class="text-xs text-slate-500">({{ store.cleaningResult.after.stats.total_missing_percent }}%)</div>
                </div>
                <div class="bg-slate-900 rounded p-2 text-center">
                  <div class="text-xs text-slate-500">异常值</div>
                  <div class="text-lg font-bold text-emerald-400">{{ store.cleaningResult.outlier_report.total_outliers_after }}</div>
                  <div class="text-xs text-slate-500">({{ store.cleaningResult.after.stats.total_outlier_percent }}%)</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="store.cleaningResult" class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div class="flex justify-between items-center mb-3">
              <h3 class="text-sm font-bold text-slate-400">📈 处理对比 - 列选择</h3>
              <select v-model="store.selectedChartColumn" class="bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm focus:outline-none focus:border-emerald-500">
                <option v-for="col in store.cleaningResult.columns" :key="col" :value="col">{{ col }}</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <h4 class="text-xs text-slate-500 mb-2">处理前 - 直方图</h4>
                <div ref="histBeforeRef" class="w-full rounded" style="height:200px;background:#0f172a;"></div>
              </div>
              <div>
                <h4 class="text-xs text-slate-500 mb-2">处理后 - 直方图</h4>
                <div ref="histAfterRef" class="w-full rounded" style="height:200px;background:#0f172a;"></div>
              </div>
            </div>
            <div class="mt-4">
              <h4 class="text-xs text-slate-500 mb-2">箱线图对比</h4>
              <div ref="boxplotRef" class="w-full rounded" style="height:180px;background:#0f172a;"></div>
            </div>
          </div>

          <div v-if="store.cleaningResult" class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 class="text-sm font-bold text-slate-400 mb-3">📋 列统计详情</h3>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-slate-500 border-b border-slate-700">
                    <th class="text-left py-2 px-2">列名</th>
                    <th class="text-right py-2 px-2">状态</th>
                    <th class="text-right py-2 px-2">缺失值(前→后)</th>
                    <th class="text-right py-2 px-2">异常值(前→后)</th>
                    <th class="text-right py-2 px-2">均值(前→后)</th>
                    <th class="text-right py-2 px-2">标准差(前→后)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(col, idx) in store.cleaningResult.before.stats.columns" :key="col.name" class="border-b border-slate-700/50">
                    <td class="py-2 px-2 font-medium">{{ col.name }}</td>
                    <td class="py-2 px-2 text-right">
                      <span v-if="getColStatus(idx) === 'clean'" class="text-emerald-400">✓ 正常</span>
                      <span v-else-if="getColStatus(idx) === 'fixed'" class="text-yellow-400">🔧 已修复</span>
                      <span v-else class="text-red-400">⚠️ 有问题</span>
                    </td>
                    <td class="py-2 px-2 text-right font-mono">
                      <span :class="col.missing_count > 0 ? 'text-orange-400' : 'text-slate-400'">{{ col.missing_count }}</span>
                      →
                      <span :class="getAfterCol(idx)?.missing_count === 0 ? 'text-emerald-400' : 'text-slate-400'">
                        {{ getAfterCol(idx)?.missing_count || 0 }}
                      </span>
                    </td>
                    <td class="py-2 px-2 text-right font-mono">
                      <span :class="(col.outlier_count || 0) > 0 ? 'text-red-400' : 'text-slate-400'">{{ col.outlier_count || 0 }}</span>
                      →
                      <span :class="(getAfterCol(idx)?.outlier_count || 0) === 0 ? 'text-emerald-400' : 'text-slate-400'">
                        {{ getAfterCol(idx)?.outlier_count || 0 }}
                      </span>
                    </td>
                    <td class="py-2 px-2 text-right font-mono">
                      {{ col.mean?.toFixed(2) || '-' }}
                      →
                      {{ getAfterCol(idx)?.mean?.toFixed(2) || '-' }}
                    </td>
                    <td class="py-2 px-2 text-right font-mono">
                      {{ col.std?.toFixed(2) || '-' }}
                      →
                      {{ getAfterCol(idx)?.std?.toFixed(2) || '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="store.cleaningResult" class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 class="text-sm font-bold text-slate-400 mb-3">📝 处理报告</h3>
            <div class="space-y-4 text-sm">
              <div class="bg-slate-900 rounded p-3">
                <h4 class="font-bold text-orange-400 mb-2">缺失值处理 (方法: {{ getMethodName(store.cleaningResult.missing_report.missing_method) }})</h4>
                <div class="space-y-1 text-xs">
                  <div v-for="mr in store.cleaningResult.missing_report.columns" :key="mr.name" class="flex justify-between">
                    <span class="text-slate-400">{{ mr.name }}:</span>
                    <span>
                      <span :class="mr.missing_before > 0 ? 'text-orange-400' : 'text-slate-500'">{{ mr.missing_before }} 个缺失</span>
                      →
                      <span :class="mr.missing_after === 0 ? 'text-emerald-400' : 'text-orange-400'">{{ mr.missing_after }} 个缺失</span>
                    </span>
                  </div>
                </div>
              </div>
              <div class="bg-slate-900 rounded p-3">
                <h4 class="font-bold text-red-400 mb-2">异常值处理 (方法: {{ getOutlierMethodName(store.cleaningResult.outlier_report.outlier_method) }}, 阈值: {{ store.cleaningResult.outlier_report.outlier_threshold }})</h4>
                <div class="space-y-1 text-xs">
                  <div v-for="or in store.cleaningResult.outlier_report.columns" :key="or.name" class="flex justify-between">
                    <span class="text-slate-400">{{ or.name }}:</span>
                    <span>
                      <span :class="or.outliers_before > 0 ? 'text-red-400' : 'text-slate-500'">{{ or.outliers_before }} 个异常</span>
                      →
                      <span :class="or.outliers_after === 0 ? 'text-emerald-400' : 'text-red-400'">{{ or.outliers_after }} 个异常</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="store.cleaningResult" class="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 class="text-sm font-bold text-slate-400 mb-3">📄 数据预览 - 处理后 (前10行)</h3>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-slate-500 border-b border-slate-700">
                    <th class="text-left py-2 px-2">#</th>
                    <th v-for="col in store.cleaningResult.columns" :key="col" class="text-right py-2 px-2">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ridx) in store.cleaningResult.after.data_preview" :key="ridx" class="border-b border-slate-700/50">
                    <td class="py-2 px-2 text-slate-500">{{ Number(ridx) + 1 }}</td>
                    <td v-for="(val, cidx) in row" :key="cidx" class="py-2 px-2 text-right font-mono"
                      :class="val === null || val === '' ? 'text-orange-400' : 'text-slate-300'">
                      {{ val !== null ? val : 'NULL' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="!store.cleaningResult && !store.isCleaning" class="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center">
            <div class="text-6xl mb-4">🧹</div>
            <h3 class="text-xl font-bold text-slate-300 mb-2">准备好清洗您的数据了吗？</h3>
            <p class="text-slate-500 mb-4">输入数据并选择处理方法，点击"开始数据清洗"查看结果</p>
            <p class="text-xs text-slate-600">支持：缺失值填充、异常值检测、统计对比、可视化分析</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useMCStore } from '../store/mc'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useMCStore()
const columnsInput = ref('')
const dataInput = ref('')
const missingMethod = ref('mean')
const outlierMethod = ref('iqr')
const outlierThreshold = ref(1.5)
const outlierAction = ref('cap')

const histBeforeRef = ref<HTMLDivElement | null>(null)
const histAfterRef = ref<HTMLDivElement | null>(null)
const boxplotRef = ref<HTMLDivElement | null>(null)

let histBeforeChart: echarts.ECharts | null = null
let histAfterChart: echarts.ECharts | null = null
let boxplotChart: echarts.ECharts | null = null

function getAfterCol(idx: number) {
  if (!store.cleaningResult) return null
  return store.cleaningResult.after.stats.columns[idx]
}

function getColStatus(idx: number) {
  const before = store.cleaningResult?.before.stats.columns[idx]
  const after = getAfterCol(idx)
  if (!before || !after) return 'normal'
  
  const hadIssues = before.missing_count > 0 || (before.outlier_count || 0) > 0
  const hasIssues = after.missing_count > 0 || (after.outlier_count || 0) > 0
  
  if (!hadIssues) return 'clean'
  if (hadIssues && !hasIssues) return 'fixed'
  return 'warning'
}

function getMethodName(method: string) {
  const names: Record<string, string> = {
    mean: '均值填充',
    median: '中位数填充',
    mode: '众数填充',
    forward: '前向填充',
    backward: '后向填充',
    zero: '零值填充',
    drop: '删除缺失行'
  }
  return names[method] || method
}

function getOutlierMethodName(method: string) {
  return method === 'iqr' ? 'IQR 四分位法' : 'Z-score 标准化'
}

async function loadSample() {
  const sample = await store.loadSampleData()
  if (sample) {
    columnsInput.value = sample.columns.join(',')
    dataInput.value = sample.data.map((row: any[]) => 
      row.map(v => v === null ? 'None' : String(v)).join(',')
    ).join('\n')
  }
}

function parseData() {
  const columns = columnsInput.value.split(',').map((s: string) => s.trim()).filter(Boolean)
  const rows = dataInput.value.split('\n').filter((line: string) => line.trim())
  const data = rows.map((line: string) => {
    return line.split(',').map((s: string) => {
      const trimmed = s.trim()
      if (trimmed === '' || trimmed.toLowerCase() === 'none' || trimmed.toLowerCase() === 'null') {
        return null
      }
      const num = parseFloat(trimmed)
      return isNaN(num) ? trimmed : num
    })
  })
  return { columns, data }
}

async function runCleaning() {
  const { columns, data } = parseData()
  if (columns.length === 0 || data.length === 0) {
    alert('请输入有效的数据')
    return
  }
  
  await store.runDataCleaning(data, columns, {
    missing_value_method: missingMethod.value,
    outlier_method: outlierMethod.value,
    outlier_threshold: outlierThreshold.value,
    outlier_action: outlierAction.value
  })
  
  await nextTick()
  initCharts()
  updateCharts()
}

function initCharts() {
  if (histBeforeRef.value) histBeforeChart = echarts.init(histBeforeRef.value, 'dark')
  if (histAfterRef.value) histAfterChart = echarts.init(histAfterRef.value, 'dark')
  if (boxplotRef.value) boxplotChart = echarts.init(boxplotRef.value, 'dark')
}

function updateCharts() {
  if (!store.cleaningResult || !store.selectedChartColumn) return
  
  const col = store.selectedChartColumn
  const histBefore = store.cleaningResult.before.histograms[col]
  const histAfter = store.cleaningResult.after.histograms[col]
  const boxBefore = store.cleaningResult.before.boxplots[col]
  const boxAfter = store.cleaningResult.after.boxplots[col]
  
  if (histBeforeChart && histBefore) {
    histBeforeChart.setOption({
      backgroundColor: '#0f172a',
      grid: { top: 20, bottom: 40, left: 45, right: 15 },
      xAxis: { 
        type: 'category', 
        data: histBefore.labels, 
        axisLabel: { color: '#94a3b8', fontSize: 9, rotate: 30 } 
      },
      yAxis: { type: 'value', axisLabel: { color: '#94a3b8', fontSize: 10 } },
      series: [{ type: 'bar', data: histBefore.values, itemStyle: { color: '#f97316' } }],
      tooltip: { trigger: 'axis', backgroundColor: '#1e293b', borderColor: '#475569' }
    })
  }
  
  if (histAfterChart && histAfter) {
    histAfterChart.setOption({
      backgroundColor: '#0f172a',
      grid: { top: 20, bottom: 40, left: 45, right: 15 },
      xAxis: { 
        type: 'category', 
        data: histAfter.labels, 
        axisLabel: { color: '#94a3b8', fontSize: 9, rotate: 30 } 
      },
      yAxis: { type: 'value', axisLabel: { color: '#94a3b8', fontSize: 10 } },
      series: [{ type: 'bar', data: histAfter.values, itemStyle: { color: '#10b981' } }],
      tooltip: { trigger: 'axis', backgroundColor: '#1e293b', borderColor: '#475569' }
    })
  }
  
  if (boxplotChart && boxBefore && boxAfter) {
    boxplotChart.setOption({
      backgroundColor: '#0f172a',
      grid: { top: 30, bottom: 30, left: 50, right: 20 },
      xAxis: { 
        type: 'category', 
        data: ['处理前', '处理后'], 
        axisLabel: { color: '#94a3b8', fontSize: 11 } 
      },
      yAxis: { type: 'value', axisLabel: { color: '#94a3b8', fontSize: 10 } },
      series: [
        {
          type: 'boxplot',
          data: [
            [boxBefore.lower_whisker, boxBefore.q1, boxBefore.median, boxBefore.q3, boxBefore.upper_whisker],
            [boxAfter.lower_whisker, boxAfter.q1, boxAfter.median, boxAfter.q3, boxAfter.upper_whisker]
          ],
          itemStyle: { color: '#8b5cf6', borderColor: '#a78bfa' }
        }
      ],
      tooltip: { trigger: 'item', backgroundColor: '#1e293b', borderColor: '#475569' }
    })
  }
}

watch(() => store.selectedChartColumn, () => {
  updateCharts()
})

watch(() => store.cleaningResult, () => {
  nextTick(() => {
    if (histBeforeRef.value && !histBeforeChart) {
      initCharts()
    }
    updateCharts()
  })
}, { deep: true })

onMounted(() => {
  loadSample()
})
</script>
