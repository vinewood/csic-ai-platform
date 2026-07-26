/**
 * 全站共享的模型元数据（标签 + 主题色）
 * 供 ModelCompareGrid 宫格组件与各页面的模型选择 chips 统一使用
 */
export const MODEL_META = {
  deepseek:          { label: 'DeepSeek V4 Pro', color: '#4D6BFE' },
  qwen:              { label: '通义千问',        color: '#615CED' },
  'qwen-plus':       { label: 'Qwen Plus',       color: '#615CED' },
  'qwen-max':        { label: 'Qwen Max',        color: '#4338CA' },
  'qwen-turbo':      { label: 'Qwen Turbo',      color: '#818CF8' },
  'qwen-coder-plus': { label: 'Qwen Coder',      color: '#3730A3' },
  'glm-4':           { label: '智谱 GLM',        color: '#3B9CFF' },
  zhipu:             { label: '智谱 GLM',        color: '#3B9CFF' },
  kimi:              { label: 'Kimi',            color: '#111827' },
  minimax:           { label: 'MiniMax',         color: '#F59E0B' },
  doubao:            { label: '豆包',            color: '#22C55E' },
}

export const modelLabel = m => MODEL_META[m]?.label || m
export const modelColor = m => MODEL_META[m]?.color || '#1677ff'

/** 可选模型列表（工具栏 chips 用，按推荐顺序） */
export const MODEL_OPTIONS = [
  'deepseek', 'qwen-plus', 'qwen-max', 'glm-4', 'kimi', 'minimax',
]

/** 最多同时对比的模型数 */
export const MAX_COMPARE = 6
