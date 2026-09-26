import { useEffect, useState, useCallback } from 'react'
import { getProduits, getPredictions, getPredictionsAll } from '../services/api'
import { Brain, TrendingUp, Calendar, Search, X, ChevronRight, Zap } from 'lucide-react'
import {
  ComposedChart, Bar, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

// ── Helpers ───────────────────────────────────────────────
const now = new Date()
const defaultPeriode = `${now.getFullYear()}-${String(now.getMonth() + 2).padStart(2, '0')}`

const badgeStyle = (c) => ({
  'Haute':   { bg: '#F0FDF4', color: '#10B981', dot: '#10B981' },
  'Moyenne': { bg: '#FFFBEB', color: '#F59E0B', dot: '#F59E0B' },
  'Faible':  { bg: '#FEF2F2', color: '#EF4444', dot: '#EF4444' },
}[c] || { bg: '#F8FAFC', color: '#64748B', dot: '#64748B' })

function ConfidenceBadge({ confiance }) {
  const s = badgeStyle(confiance)
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: s.bg, color: s.color,
      fontSize: '12px', fontWeight: 500,
      padding: '3px 10px', borderRadius: '999px',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.dot }} />
      {confiance}
    </span>
  )
}

function Skeleton({ w = '100%', h = '16px', r = '6px' }) {
  return (
    <div style={{
      width: w, height: h, borderRadius: r,
      background: 'linear-gradient(90deg, #E2E8F0 25%, #F1F5F9 50%, #E2E8F0 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.4s infinite',
    }} />
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1E2A6E', borderRadius: '10px',
      padding: '10px 16px', color: '#fff', fontSize: '12px',
    }}>
      <div style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name} : {Number(p.value).toLocaleString('fr-FR')} unités
        </div>
      ))}
    </div>
  )
}

// ── Prediction Result Panel ───────────────────────────────
function PredictionResult({ result }) {
  if (!result) return null
  const chartData = result.predictions.map(p => ({
    name: p.mois,
    prediction: Math.round(p.quantite_predite),
  }))

  return (
    <div style={{ animation: 'fadeIn 0.35s ease' }}>
      {/* Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${result.predictions.length}, 1fr)`,
        gap: 12, marginBottom: 20,
      }}>
        {result.predictions.map((p, i) => (
          <div key={i} style={{
            background: '#F8FAFC', borderRadius: '12px',
            padding: '16px', borderTop: '3px solid #2B7CC2',
            animation: `fadeIn 0.3s ease ${i * 0.08}s both`,
          }}>
            <div style={{ fontSize: '12px', color: '#64748B', marginBottom: 6 }}>{p.mois}</div>
            <div style={{
              fontSize: '24px', fontWeight: 700, color: '#1E2A6E',
              marginBottom: 6, fontVariantNumeric: 'tabular-nums',
            }}>
              {Math.round(p.quantite_predite).toLocaleString('fr-FR')}
            </div>
            <div style={{ fontSize: '11px', color: '#94A3B8', marginBottom: 8 }}>unités prévues</div>
            <ConfidenceBadge confiance={p.confiance} />
          </div>
        ))}
      </div>

      {/* Chart */}
      <div style={{ background: '#F8FAFC', borderRadius: '12px', padding: '20px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#1E2A6E', marginBottom: 16 }}>
          Visualisation des prévisions
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false}
              tickFormatter={v => v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="prediction" name="Quantité prévue"
              fill="#2B7CC2" radius={[6, 6, 0, 0]} fillOpacity={0.85} />
            <Line dataKey="prediction" name="Tendance"
              stroke="#1E2A6E" strokeWidth={2}
              dot={{ r: 4, fill: '#1E2A6E' }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── Section 1 : Prédiction par produit ───────────────────
function PredictionProduit({ produits }) {
  const [search, setSearch]     = useState('')
  const [filtered, setFiltered] = useState([])
  const [showDrop, setShowDrop] = useState(false)
  const [selected, setSelected] = useState(null)
  const [horizon, setHorizon]   = useState(3)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)

  useEffect(() => {
    if (!search.trim()) { setFiltered([]); return }
    setFiltered(
      produits.filter(p =>
        p.designation.toLowerCase().includes(search.toLowerCase()) ||
        p.reference_produit.toLowerCase().includes(search.toLowerCase())
      ).slice(0, 8)
    )
    setShowDrop(true)
  }, [search, produits])

  const handleSelect = (p) => {
    setSelected(p)
    setSearch(p.designation)
    setShowDrop(false)
    setResult(null)
  }

  const handlePredict = useCallback(() => {
    if (!selected) return
    setLoading(true)
    setResult(null)
    getPredictions(selected.reference_produit, horizon)
      .then(r => setResult(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selected, horizon])

  return (
    <div style={{
      background: '#fff', borderRadius: '16px', padding: '28px',
      boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
      border: '1px solid #F1F5F9', marginBottom: '24px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '10px',
          background: 'linear-gradient(135deg, #1E2A6E, #2B7CC2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Brain size={18} color="#fff" />
        </div>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#1E2A6E' }}>
            Prédiction par Produit
          </h2>
          <p style={{ fontSize: '12px', color: '#64748B' }}>
            Sélectionne un produit → choisis l'horizon → lance la prédiction
          </p>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>

        {/* Search dropdown */}
        <div style={{ position: 'relative', flex: 1, minWidth: '280px' }}>
          <Search size={14} style={{
            position: 'absolute', left: 12, top: '50%',
            transform: 'translateY(-50%)', color: '#94A3B8',
            pointerEvents: 'none', zIndex: 1,
          }} />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setSelected(null) }}
            placeholder="Rechercher un produit..."
            style={{
              width: '100%', paddingLeft: 36,
              paddingRight: search ? 36 : 14,
              paddingTop: 11, paddingBottom: 11,
              border: '1.5px solid #E2E8F0', borderRadius: '10px',
              fontSize: '14px', outline: 'none', color: '#1E293B',
              transition: 'border-color 0.2s', background: '#fff',
            }}
            onFocus={e => { e.target.style.borderColor = '#2B7CC2'; search && setShowDrop(true) }}
            onBlur={e => { e.target.style.borderColor = '#E2E8F0'; setTimeout(() => setShowDrop(false), 200) }}
          />
          {search && (
            <button onClick={() => { setSearch(''); setSelected(null); setResult(null) }}
              style={{
                position: 'absolute', right: 10, top: '50%',
                transform: 'translateY(-50%)',
                background: 'none', border: 'none',
                cursor: 'pointer', color: '#94A3B8', padding: 0,
              }}
            >
              <X size={14} />
            </button>
          )}

          {showDrop && filtered.length > 0 && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, right: 0,
              background: '#fff', border: '1px solid #E2E8F0',
              borderRadius: '10px', boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
              zIndex: 50, overflow: 'hidden', marginTop: 4,
            }}>
              {filtered.map(p => (
                <div key={p.reference_produit} onMouseDown={() => handleSelect(p)}
                  style={{
                    padding: '10px 14px', cursor: 'pointer',
                    borderBottom: '1px solid #F8FAFC',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#F0F4FA'}
                  onMouseLeave={e => e.currentTarget.style.background = '#fff'}
                >
                  <div style={{ fontSize: '13px', fontWeight: 500, color: '#1E293B' }}>
                    {p.designation}
                  </div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: 2 }}>
                    {p.reference_produit} — {p.famille || ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Horizon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '13px', color: '#64748B', whiteSpace: 'nowrap' }}>Horizon :</span>
          <div style={{ display: 'flex', gap: 4 }}>
            {[1, 2, 3, 4, 5, 6].map(h => (
              <button key={h} onClick={() => setHorizon(h)} style={{
                width: 34, height: 34, borderRadius: '8px',
                border: '1.5px solid',
                borderColor: horizon === h ? '#2B7CC2' : '#E2E8F0',
                background: horizon === h ? '#2B7CC2' : '#fff',
                color: horizon === h ? '#fff' : '#64748B',
                fontSize: '13px', fontWeight: 500,
                cursor: 'pointer', transition: 'all 0.15s',
              }}>
                {h}
              </button>
            ))}
          </div>
          <span style={{ fontSize: '12px', color: '#94A3B8' }}>mois</span>
        </div>

        {/* Predict button */}
        <button
          onClick={handlePredict}
          disabled={!selected || loading}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: selected && !loading
              ? 'linear-gradient(135deg, #1E2A6E, #2B7CC2)'
              : '#E2E8F0',
            color: selected && !loading ? '#fff' : '#94A3B8',
            border: 'none', borderRadius: '10px',
            padding: '11px 24px', fontSize: '14px', fontWeight: 600,
            cursor: selected && !loading ? 'pointer' : 'default',
            transition: 'all 0.2s', whiteSpace: 'nowrap',
          }}
        >
          <Brain size={15} />
          {loading ? 'Calcul...' : 'Prédire'}
        </button>
      </div>

      {/* Empty state */}
      {!selected && !result && !loading && (
        <div style={{
          textAlign: 'center', padding: '48px 0',
          color: '#94A3B8', borderTop: '1px solid #F1F5F9',
        }}>
          <Brain size={40} style={{ marginBottom: 12, opacity: 0.3 }} />
          <div style={{ fontSize: '14px', marginBottom: 4 }}>
            Recherche un produit pour lancer une prédiction
          </div>
          <div style={{ fontSize: '12px' }}>
            {produits.length} produits disponibles
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, borderTop: '1px solid #F1F5F9', paddingTop: 20 }}>
          <div style={{ display: 'flex', gap: 12 }}>
            {[...Array(horizon)].map((_, i) => <Skeleton key={i} h="100px" r="12px" />)}
          </div>
          <Skeleton h="200px" r="12px" />
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div style={{ borderTop: '1px solid #F1F5F9', paddingTop: 20 }}>
          <div style={{ fontSize: '13px', color: '#64748B', marginBottom: 16 }}>
            Résultats pour <strong style={{ color: '#1E2A6E' }}>{selected.designation}</strong>
          </div>
          <PredictionResult result={result} />
        </div>
      )}
    </div>
  )
}

// ── Section 2 : Prédictions Globales ─────────────────────
function PredictionsGlobales() {
  const [periode, setPeriode] = useState(defaultPeriode)
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter]   = useState('Tous')
  const [page, setPage]       = useState(1)
  const PER_PAGE = 10

  const handlePredict = useCallback(() => {
    setLoading(true)
    setResult(null)
    getPredictionsAll(periode)
      .then(r => { setResult(r.data); setPage(1) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [periode])

  const filtered   = result?.predictions?.filter(p => filter === 'Tous' || p.confiance === filter) || []
  const paginated  = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)
  const totalPages = Math.ceil(filtered.length / PER_PAGE)

  return (
    <div style={{
      background: '#fff', borderRadius: '16px', padding: '28px',
      boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
      border: '1px solid #F1F5F9',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '10px',
          background: 'linear-gradient(135deg, #7C3AED, #A78BFA)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Zap size={18} color="#fff" />
        </div>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#1E2A6E' }}>
            Prédictions Globales
          </h2>
          <p style={{ fontSize: '12px', color: '#64748B' }}>
            Classement de tous les produits pour une période — lancé à la demande
          </p>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Calendar size={14} color="#64748B" />
          <input
            type="month"
            value={periode}
            onChange={e => { setPeriode(e.target.value); setResult(null) }}
            style={{
              border: '1.5px solid #E2E8F0', borderRadius: '10px',
              padding: '9px 14px', fontSize: '14px',
              outline: 'none', color: '#1E293B',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = '#7C3AED'}
            onBlur={e => e.target.style.borderColor = '#E2E8F0'}
          />
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: loading ? '#E2E8F0' : 'linear-gradient(135deg, #7C3AED, #A78BFA)',
            color: loading ? '#94A3B8' : '#fff',
            border: 'none', borderRadius: '10px',
            padding: '11px 24px', fontSize: '14px', fontWeight: 600,
            cursor: loading ? 'default' : 'pointer',
            transition: 'all 0.2s', whiteSpace: 'nowrap',
          }}
        >
          <Zap size={15} />
          {loading ? 'Calcul en cours...' : 'Lancer pour tous les produits'}
        </button>

        {loading && (
          <span style={{ fontSize: '13px', color: '#64748B' }}>
            ⏳ ~30 secondes pour 487 produits...
          </span>
        )}
      </div>

      {/* Empty state */}
      {!result && !loading && (
        <div style={{
          textAlign: 'center', padding: '48px 0',
          color: '#94A3B8', borderTop: '1px solid #F1F5F9',
        }}>
          <Zap size={40} style={{ marginBottom: 12, opacity: 0.3 }} />
          <div style={{ fontSize: '14px', marginBottom: 4 }}>
            Clique sur "Lancer" pour calculer les prédictions de tous les produits
          </div>
          <div style={{ fontSize: '12px' }}>
            Le calcul prend environ 30 secondes
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, borderTop: '1px solid #F1F5F9', paddingTop: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
            {[...Array(4)].map((_, i) => <Skeleton key={i} h="70px" r="10px" />)}
          </div>
          <Skeleton h="40px" r="8px" />
          {[...Array(6)].map((_, i) => <Skeleton key={i} h="44px" r="8px" />)}
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div style={{ animation: 'fadeIn 0.35s ease', borderTop: '1px solid #F1F5F9', paddingTop: 20 }}>

          {/* Summary cards */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(4,1fr)',
            gap: 12, marginBottom: 20,
          }}>
            {[
              { label: 'Produits prédits', value: result.nb_produits,                                                  color: '#7C3AED' },
              { label: 'Confiance Haute',  value: result.predictions.filter(p => p.confiance === 'Haute').length,   color: '#10B981' },
              { label: 'Confiance Moy.',   value: result.predictions.filter(p => p.confiance === 'Moyenne').length, color: '#F59E0B' },
              { label: 'Confiance Faible', value: result.predictions.filter(p => p.confiance === 'Faible').length,  color: '#EF4444' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{
                background: '#F8FAFC', borderRadius: '10px',
                padding: '14px', borderLeft: `3px solid ${color}`,
              }}>
                <div style={{ fontSize: '11px', color: '#94A3B8', marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: '22px', fontWeight: 700, color: '#1E2A6E' }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Filter tabs */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
            {['Tous', 'Haute', 'Moyenne', 'Faible'].map(f => (
              <button key={f} onClick={() => { setFilter(f); setPage(1) }} style={{
                padding: '6px 16px', borderRadius: '999px',
                border: '1.5px solid',
                borderColor: filter === f ? '#7C3AED' : '#E2E8F0',
                background: filter === f ? '#7C3AED' : '#fff',
                color: filter === f ? '#fff' : '#64748B',
                fontSize: '13px', fontWeight: 500,
                cursor: 'pointer', transition: 'all 0.15s',
              }}>
                {f}
              </button>
            ))}
            <span style={{ marginLeft: 'auto', fontSize: '13px', color: '#64748B' }}>
              {filtered.length} produits
            </span>
          </div>

          {/* Table */}
          <div style={{ border: '1px solid #F1F5F9', borderRadius: '12px', overflow: 'hidden' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '40px 150px 1fr 120px 130px 110px',
              padding: '10px 16px', background: '#F8FAFC',
              borderBottom: '1px solid #E2E8F0',
              fontSize: '11px', fontWeight: 600, color: '#64748B',
            }}>
              <span>#</span>
              <span>RÉFÉRENCE</span>
              <span>DÉSIGNATION</span>
              <span>FAMILLE</span>
              <span style={{ textAlign: 'right' }}>QTÉ PRÉVUE</span>
              <span style={{ textAlign: 'center' }}>CONFIANCE</span>
            </div>

            {paginated.map((p, i) => (
              <div key={p.reference_produit} style={{
                display: 'grid',
                gridTemplateColumns: '40px 150px 1fr 120px 130px 110px',
                padding: '12px 16px', alignItems: 'center',
                borderBottom: i < paginated.length - 1 ? '1px solid #F8FAFC' : 'none',
                transition: 'background 0.15s',
              }}
                onMouseEnter={e => e.currentTarget.style.background = '#F8FAFC'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>
                  {(page - 1) * PER_PAGE + i + 1}
                </span>
                <span style={{ fontSize: '11px', color: '#64748B', fontFamily: 'monospace' }}>
                  {p.reference_produit}
                </span>
                <span style={{
                  fontSize: '13px', fontWeight: 500, color: '#1E293B',
                  overflow: 'hidden', textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap', paddingRight: 12,
                }}>
                  {p.designation}
                </span>
                <span style={{
                  fontSize: '11px', color: '#2B7CC2',
                  background: '#EFF6FF', padding: '2px 8px',
                  borderRadius: '999px', whiteSpace: 'nowrap',
                  overflow: 'hidden', textOverflow: 'ellipsis',
                  maxWidth: '110px', display: 'inline-block',
                }}>
                  {p.famille || '—'}
                </span>
                <span style={{
                  fontSize: '14px', fontWeight: 700, color: '#1E2A6E',
                  textAlign: 'right', fontVariantNumeric: 'tabular-nums',
                }}>
                  {Math.round(p.quantite_predite).toLocaleString('fr-FR')}
                </span>
                <div style={{ textAlign: 'center' }}>
                  <ConfidenceBadge confiance={p.confiance} />
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{
              display: 'flex', alignItems: 'center',
              justifyContent: 'center', gap: 8, marginTop: 20,
            }}>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                style={{
                  padding: '7px 14px', borderRadius: '8px',
                  border: '1px solid #E2E8F0', background: '#fff',
                  color: page === 1 ? '#CBD5E1' : '#1E2A6E',
                  cursor: page === 1 ? 'default' : 'pointer', fontSize: '13px',
                }}
              >← Préc.</button>
              {[...Array(Math.min(totalPages, 8))].map((_, i) => (
                <button key={i} onClick={() => setPage(i + 1)} style={{
                  width: 34, height: 34, borderRadius: '8px',
                  border: '1px solid',
                  borderColor: page === i + 1 ? '#7C3AED' : '#E2E8F0',
                  background: page === i + 1 ? '#7C3AED' : '#fff',
                  color: page === i + 1 ? '#fff' : '#64748B',
                  cursor: 'pointer', fontSize: '13px',
                }}>
                  {i + 1}
                </button>
              ))}
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                style={{
                  padding: '7px 14px', borderRadius: '8px',
                  border: '1px solid #E2E8F0', background: '#fff',
                  color: page === totalPages ? '#CBD5E1' : '#1E2A6E',
                  cursor: page === totalPages ? 'default' : 'pointer', fontSize: '13px',
                }}
              >Suiv. →</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────
export default function Predictions() {
  const [produits, setProduits] = useState([])
  const [loadingProduits, setLoadingProduits] = useState(true)

  useEffect(() => {
    getProduits('')
      .then(r => setProduits(r.data))
      .catch(console.error)
      .finally(() => setLoadingProduits(false))
  }, [])

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{
          fontSize: '24px', fontWeight: 700,
          color: '#1E2A6E', marginBottom: 6, letterSpacing: '-0.3px',
        }}>
          Prédictions de Demande
        </h1>
        <p style={{ color: '#64748B', fontSize: '14px' }}>
          Modèle XGBoost — 633 produits — 40 mois d'historique
        </p>
      </div>

      {loadingProduits ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Skeleton h="300px" r="16px" />
          <Skeleton h="200px" r="16px" />
        </div>
      ) : (
        <>
          <PredictionProduit produits={produits} />
          <PredictionsGlobales />
        </>
      )}

      <style>{`
        @keyframes shimmer {
          0%   { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}