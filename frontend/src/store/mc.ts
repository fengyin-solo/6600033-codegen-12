import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ColumnStat {
  name: string
  count: number
  missing_count: number
  missing_percent: number
  mean: number | null
  median: number | null
  std: number | null
  min: number | null
  max: number | null
  outlier_count: number | null
  outlier_percent: number | null
}

export interface StatsSummary {
  columns: ColumnStat[]
  total_rows: number
  total_missing: number
  total_missing_percent: number
  total_outliers: number
  total_outlier_percent: number
}

export interface HistogramData {
  labels: string[]
  values: number[]
}

export interface BoxplotData {
  min: number
  q1: number
  median: number
  q3: number
  max: number
  lower_whisker: number
  upper_whisker: number
}

export interface MissingReportColumn {
  name: string
  missing_before: number
  missing_after: number
  missing_percent_before: number
  missing_percent_after: number
}

export interface MissingReport {
  total_missing_before: number
  total_missing_after: number
  missing_method: string
  columns: MissingReportColumn[]
}

export interface OutlierReportColumn {
  name: string
  outliers_before: number
  outliers_after: number
  outlier_percent_before: number
  outlier_percent_after: number
}

export interface OutlierReport {
  total_outliers_before: number
  total_outliers_after: number
  outlier_method: string
  outlier_threshold: number
  outlier_action: string
  columns: OutlierReportColumn[]
}

export interface DataCleaningResult {
  before: {
    stats: StatsSummary
    histograms: Record<string, HistogramData>
    boxplots: Record<string, BoxplotData>
    data_preview: any[][]
  }
  after: {
    stats: StatsSummary
    histograms: Record<string, HistogramData>
    boxplots: Record<string, BoxplotData>
    data_preview: any[][]
  }
  missing_report: MissingReport
  outlier_report: OutlierReport
  processed_data: any[][]
  columns: string[]
}

export interface MCScenario {
  id: string
  name: string
  description: string
  params: Record<string, number>
  category: string
}

export interface MCResult {
  scenario: string
  iterations: number
  estimate: number
  trueValue?: number
  error?: number
  samples: number[]
  convergence: number[]
}

export interface HypTestResult {
  testType: string
  statistic: number
  pValue: number
  significant: boolean
  alpha: number
  df?: number
}

function normalRandom(): number {
  let u = 0, v = 0
  while (u === 0) u = Math.random()
  while (v === 0) v = Math.random()
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v)
}

function runMC(scenario: MCScenario, n: number): MCResult {
  const samples: number[] = []
  const convergence: number[] = []

  if (scenario.id === 'pi') {
    let inside = 0
    for (let i = 0; i < n; i++) {
      const x = Math.random() * 2 - 1, y = Math.random() * 2 - 1
      if (x * x + y * y <= 1) inside++
      samples.push(x * x + y * y <= 1 ? 1 : 0)
      convergence.push((inside / (i + 1)) * 4)
    }
    const estimate = (inside / n) * 4
    return { scenario: 'pi', iterations: n, estimate, trueValue: Math.PI, error: Math.abs(estimate - Math.PI), samples, convergence }
  }
  if (scenario.id === 'brownian') {
    let pos = 0
    const dt = scenario.params.dt || 0.01
    for (let i = 0; i < n; i++) { pos += normalRandom() * Math.sqrt(dt); samples.push(pos) }
    convergence.push(...samples.slice(0, 200))
    return { scenario: 'brownian', iterations: n, estimate: pos, samples, convergence }
  }
  if (scenario.id === 'option') {
    const { S0 = 100, K = 105, r = 0.05, sigma = 0.2, T = 1 } = scenario.params
    let payoffSum = 0
    for (let i = 0; i < n; i++) {
      const ST = S0 * Math.exp((r - 0.5 * sigma * sigma) * T + sigma * Math.sqrt(T) * normalRandom())
      const p = Math.max(ST - K, 0); payoffSum += p; samples.push(p)
      if ((i + 1) % 50 === 0) convergence.push((payoffSum / (i + 1)) * Math.exp(-r * T))
    }
    return { scenario: 'option', iterations: n, estimate: (payoffSum / n) * Math.exp(-r * T), samples, convergence }
  }
  if (scenario.id === 'random_walk') {
    let pos = 0
    for (let i = 0; i < n; i++) { pos += Math.random() > 0.5 ? 1 : -1; samples.push(pos) }
    convergence.push(...samples.slice(0, 200))
    return { scenario: 'random_walk', iterations: n, estimate: pos, samples, convergence }
  }
  if (scenario.id === 'diffusion') {
    const { D = 1, dt = 0.01 } = scenario.params
    let x = 0, y = 0
    for (let i = 0; i < n; i++) {
      x += normalRandom() * Math.sqrt(2 * D * dt); y += normalRandom() * Math.sqrt(2 * D * dt)
      samples.push(Math.sqrt(x * x + y * y))
    }
    convergence.push(...samples.slice(0, 200))
    return { scenario: 'diffusion', iterations: n, estimate: Math.sqrt(x * x + y * y), samples, convergence }
  }
  // gambler
  const { p = 0.45, bankroll = 50, goal = 100 } = scenario.params
  let ruinCount = 0
  for (let i = 0; i < n; i++) {
    let money = bankroll
    let steps = 0
    while (money > 0 && money < goal && steps < 10000) { money += Math.random() < p ? 1 : -1; steps++ }
    if (money <= 0) ruinCount++
    samples.push(money <= 0 ? 0 : 1)
    convergence.push(ruinCount / (i + 1))
  }
  return { scenario: 'gambler', iterations: n, estimate: ruinCount / n, samples, convergence }
}

export const SCENARIOS: MCScenario[] = [
  { id: 'pi', name: '圆周率π估算', description: '随机投点估算π值，观察收敛过程', params: {}, category: '基础' },
  { id: 'brownian', name: '布朗运动模拟', description: '粒子热运动随机路径模拟', params: { dt: 0.01 }, category: '物理' },
  { id: 'option', name: '欧式期权定价', description: 'Black-Scholes期权价格蒙特卡洛估算', params: { S0: 100, K: 105, r: 0.05, sigma: 0.2, T: 1 }, category: '金融' },
  { id: 'random_walk', name: '随机游走', description: '一维离散随机游走轨迹模拟', params: {}, category: '基础' },
  { id: 'diffusion', name: '粒子扩散', description: '二维粒子随机扩散位移分析', params: { D: 1, dt: 0.01 }, category: '物理' },
  { id: 'gambler', name: '赌徒破产', description: '不利赌局下资金耗尽概率估算', params: { p: 0.45, bankroll: 50, goal: 100 }, category: '概率' }
]

export const useMCStore = defineStore('mc', () => {
  const currentScenario = ref<MCScenario>(SCENARIOS[0])
  const iterations = ref(1000)
  const result = ref<MCResult | null>(null)
  const testResult = ref<HypTestResult | null>(null)
  const isRunning = ref(false)

  const cleaningResult = ref<DataCleaningResult | null>(null)
  const isCleaning = ref(false)
  const selectedChartColumn = ref<string>('')
  const showDataCleaner = ref(false)

  const API_BASE = 'http://localhost:8000'

  async function loadSampleData() {
    try {
      const response = await fetch(`${API_BASE}/api/data-cleaning/sample-data`)
      return await response.json()
    } catch (error) {
      console.error('Failed to load sample data:', error)
      return null
    }
  }

  async function runDataCleaning(data: any[][], columns: string[], options: {
    missing_value_method: string
    outlier_method: string
    outlier_threshold: number
    outlier_action: string
  }) {
    isCleaning.value = true
    try {
      const response = await fetch(`${API_BASE}/api/data-cleaning/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data,
          columns,
          missing_value_method: options.missing_value_method,
          outlier_method: options.outlier_method,
          outlier_threshold: options.outlier_threshold,
          outlier_action: options.outlier_action
        })
      })
      cleaningResult.value = await response.json()
      if (cleaningResult.value && cleaningResult.value.columns.length > 0) {
        selectedChartColumn.value = cleaningResult.value.columns[0]
      }
      return cleaningResult.value
    } catch (error) {
      console.error('Data cleaning failed:', error)
      return null
    } finally {
      isCleaning.value = false
    }
  }

  function setShowDataCleaner(show: boolean) {
    showDataCleaner.value = show
  }

  function setSelectedChartColumn(column: string) {
    selectedChartColumn.value = column
  }

  function runSimulation() {
    isRunning.value = true
    setTimeout(() => { result.value = runMC(currentScenario.value, iterations.value); isRunning.value = false }, 10)
  }

  function runTest(g1: number[], g2: number[]) {
    const n1 = g1.length, n2 = g2.length
    const m1 = g1.reduce((a, b) => a + b, 0) / n1
    const m2 = g2.reduce((a, b) => a + b, 0) / n2
    const v1 = g1.reduce((s, x) => s + (x - m1) ** 2, 0) / (n1 - 1)
    const v2 = g2.reduce((s, x) => s + (x - m2) ** 2, 0) / (n2 - 1)
    const se = Math.sqrt(v1 / n1 + v2 / n2)
    const t = (m1 - m2) / se
    const df = Math.round((v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)))
    const pValue = 2 * (1 - Math.min(0.9999, Math.abs(t) / (Math.abs(t) + Math.sqrt(df))))
    testResult.value = { testType: 'Welch T检验', statistic: Math.round(t * 1000) / 1000, pValue: Math.round(pValue * 10000) / 10000, significant: pValue < 0.05, alpha: 0.05, df }
  }

  function setScenario(s: MCScenario) { currentScenario.value = s; result.value = null }

  const convergenceData = computed(() => {
    if (!result.value) return [] as [number, number][]
    return result.value.convergence.slice(0, 200).map((v, i): [number, number] => [i, Math.round(v * 100000) / 100000])
  })

  const histogramData = computed(() => {
    if (!result.value) return { xAxis: [] as number[], data: [] as number[] }
    const s = result.value.samples.slice(0, 1000)
    const mn = Math.min(...s), mx = Math.max(...s)
    const bins = 20, bs = (mx - mn) / bins || 1
    const counts = new Array(bins).fill(0)
    s.forEach(v => { counts[Math.min(bins - 1, Math.floor((v - mn) / bs))]++ })
    return { xAxis: Array.from({ length: bins }, (_, i) => Math.round((mn + i * bs) * 100) / 100), data: counts }
  })

  return {
    currentScenario, iterations, result, testResult, isRunning,
    cleaningResult, isCleaning, selectedChartColumn, showDataCleaner,
    convergenceData, histogramData,
    runSimulation, runTest, setScenario,
    loadSampleData, runDataCleaning, setShowDataCleaner, setSelectedChartColumn
  }
})
