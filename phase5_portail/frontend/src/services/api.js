import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
})

const apiSlow = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
})

export const getKPIs             = () => api.get('/api/ventes/kpis')
export const getVentesMensuelles = () => api.get('/api/ventes/mensuelles')
export const getTopProduits      = (limit = 10) => api.get(`/api/ventes/top-produits?limit=${limit}`)
export const getTopClients       = (limit = 10) => api.get(`/api/ventes/top-clients?limit=${limit}`)
export const getProduits         = (search = '') => api.get(`/api/produits/?search=${search}`)
export const getProduitDetail    = (ref) => apiSlow.get(`/api/produits/${ref}`)
export const getClients          = (search = '') => api.get(`/api/clients/?search=${search}`)
export const getClientDetail     = (code) => apiSlow.get(`/api/clients/${code.trim()}`)
export const getPredictions      = (ref, horizon) => apiSlow.get(`/api/predictions/${ref}?horizon=${horizon}`)
export const getPredictionsAll   = (periode) => apiSlow.get(`/api/predictions/all?periode=${periode}`)