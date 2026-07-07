/**
 * 中船党校 AI 平台 - 前端 API 帮助模块
 * 所有页面统一通过此模块调用后端 API
 */

// API_BASE: 生产环境同域名（Nginx 反代），开发环境用 localhost:8000
const API_BASE = window.location.port === '5173' ? 'http://localhost:8000' : ''

function getToken() {
  return localStorage.getItem('csic_token') || ''
}

function authHeaders() {
  const t = getToken()
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = 'Bearer ' + t
  return h
}

export async function apiGet(path) {
  try {
    const resp = await fetch(API_BASE + path, { headers: authHeaders() })
    if (resp.status === 401) { localStorage.removeItem('csic_token'); window.location.href = '/'; return null }
    return resp.ok ? await resp.json() : []
  } catch { return null }
}

export async function apiPost(path, data) {
  try {
    const resp = await fetch(API_BASE + path, { method: 'POST', headers: authHeaders(), body: JSON.stringify(data) })
    if (resp.status === 401) { localStorage.removeItem('csic_token'); window.location.href = '/'; return null }
    return resp.ok ? await resp.json() : null
  } catch { return null }
}

export async function apiPut(path, data) {
  try {
    const resp = await fetch(API_BASE + path, { method: 'PUT', headers: authHeaders(), body: JSON.stringify(data) })
    if (resp.status === 401) { localStorage.removeItem('csic_token'); window.location.href = '/'; return null }
    return resp.ok ? await resp.json() : null
  } catch { return null }
}

export async function apiDelete(path) {
  try {
    const resp = await fetch(API_BASE + path, { method: 'DELETE', headers: authHeaders() })
    if (resp.status === 401) { localStorage.removeItem('csic_token'); window.location.href = '/'; return null }
    return resp.ok ? await resp.json() : null
  } catch { return null }
}

export async function apiUpload(path, formData) {
  try {
    const resp = await fetch(API_BASE + path, { method: 'POST', headers: { 'Authorization': 'Bearer ' + getToken() }, body: formData })
    return resp.ok ? await resp.json() : null
  } catch { return null }
}

export default { apiGet, apiPost, apiPut, apiDelete, apiUpload }
