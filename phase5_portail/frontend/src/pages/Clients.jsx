import { useEffect, useState, useCallback } from 'react'
import { getClients, getClientDetail } from '../services/api'
import { Search, X, Users, ArrowLeft, ChevronRight } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts'

const fmt = (n) =>
  n >= 1_000_000 ? (n / 1_000_000).toFixed(2) + ' M DT'
  : n >= 1_000   ? (n / 1_000).toFixed(1) + ' K DT'
  : (n ?? 0).toLocaleString('fr-FR') + ' DT'

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

function TypeBadge({ type }) {
  if (!type) return null
  const colors = {
    'PUBLIC':  { bg: '#F0FDF4', color: '#10B981' },
    'PRIVE':   { bg: '#EFF6FF', color: '#2B7CC2' },
    'default': { bg: '#F8FAFC', color: '#64748B' },
  }
  const c = colors[type?.toUpperCase()] || colors.default
  return (
    <span style={{
      background: c.bg, color: c.color,
      fontSize: '11px', fontWeight: 500,
      padding: '2px 8px', borderRadius: '999px',
    }}>
      {type}
    </span>
  )
}

function DetailPanel({ client, onClose }) {
  const [historique, setHistorique] = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    setLoading(true)
    getClientDetail(client.code_client)
      .then(r => setHistorique(r.data.map(d => ({
        name: `${d.nom_mois.slice(0,3)} ${String(d.annee).slice(2)}`,
        ca: d.ca, quantite: d.quantite,
      }))))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [client.code_client])

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end',
    }}>
      <div onClick={onClose} style={{
        position: 'absolute', inset: 0,
        background: 'rgba(15,23,42,0.4)',
        backdropFilter: 'blur(3px)',
      }} />
      <div style={{
        position: 'relative', zIndex: 1,
        width: '480px', height: '100vh',
        background: '#fff',
        boxShadow: '-8px 0 40px rgba(0,0,0,0.12)',
        display: 'flex', flexDirection: 'column',
        animation: 'slideIn 0.3s ease',
      }}>
        {/* Header */}
        <div style={{
          padding: '24px', borderBottom: '1px solid #F1F5F9',
          background: 'linear-gradient(135deg, #064E3B, #10B981)',
        }}>
          <button onClick={onClose} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(255,255,255,0.15)', border: 'none',
            color: '#fff', borderRadius: '8px',
            padding: '6px 12px', fontSize: '13px',
            cursor: 'pointer', marginBottom: '16px',
          }}>
            <ArrowLeft size={13} /> Retour
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: 42, height: 42, borderRadius: '10px',
              background: 'rgba(255,255,255,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Users size={20} color="#fff" />
            </div>
            <div>
              <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '11px', marginBottom: 4 }}>
                {client.code_client}
              </div>
              <div style={{ color: '#fff', fontWeight: 600, fontSize: '15px' }}>
                {client.client}
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: '16px', padding: '20px',
          borderBottom: '1px solid #F1F5F9',
        }}>
          {[
            { label: 'CA Total',     value: fmt(client.ca_total),                          color: '#10B981' },
            { label: 'Commandes',    value: (client.nb_commandes ?? 0).toLocaleString(),    color: '#2B7CC2' },
            { label: 'Pays',         value: client.pays ?? '—',                             color: '#F59E0B' },
            { label: 'Région',       value: client.region ?? '—',                           color: '#8B5CF6' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              background: '#F8FAFC', borderRadius: '10px',
              padding: '14px', borderLeft: `3px solid ${color}`,
            }}>
              <div style={{ fontSize: '11px', color: '#94A3B8', marginBottom: 6 }}>{label}</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#1E293B' }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Chart */}
        <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#1E2A6E', marginBottom: '16px' }}>
            Historique des achats mensuels
          </h3>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[...Array(4)].map((_, i) => <Skeleton key={i} h="20px" />)}
            </div>
          ) : historique.length === 0 ? (
            <div style={{ color: '#94A3B8', fontSize: '13px', textAlign: 'center', padding: '40px 0' }}>
              Aucun historique disponible
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={historique} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="clientGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#10B981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}   />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} width={55}
                  tickFormatter={v => v >= 1000 ? (v/1000).toFixed(0)+'K' : v} />
                <Tooltip
                  contentStyle={{
                    background: '#064E3B', border: 'none',
                    borderRadius: '8px', fontSize: '12px', color: '#fff'
                  }}
                  formatter={v => [v.toLocaleString('fr-FR') + ' DT', 'CA']}
                />
                <Area type="monotone" dataKey="ca"
                  stroke="#10B981" strokeWidth={2}
                  fill="url(#clientGrad)" dot={false}
                  activeDot={{ r: 4, fill: '#10B981' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Clients() {
  const [clients, setClients]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState('')
  const [selected, setSelected] = useState(null)
  const [page, setPage]         = useState(1)
  const PER_PAGE = 15

  const fetchClients = useCallback((q) => {
    setLoading(true)
    getClients(q)
      .then(r => { setClients(r.data); setPage(1) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { fetchClients('') }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    fetchClients(search)
  }

  const paginated  = clients.slice((page - 1) * PER_PAGE, page * PER_PAGE)
  const totalPages = Math.ceil(clients.length / PER_PAGE)

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 24px' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#1E2A6E', marginBottom: 6 }}>
            Portefeuille Clients
          </h1>
          <p style={{ color: '#64748B', fontSize: '14px' }}>
            {loading ? '...' : `${clients.length} clients trouvés`}
          </p>
        </div>

        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{
              position: 'absolute', left: 12, top: '50%',
              transform: 'translateY(-50%)', color: '#94A3B8',
              pointerEvents: 'none',
            }} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher un client..."
              style={{
                paddingLeft: '36px', paddingRight: search ? '36px' : '14px',
                paddingTop: '10px', paddingBottom: '10px',
                border: '1.5px solid #E2E8F0', borderRadius: '10px',
                fontSize: '14px', width: '280px', outline: 'none',
                color: '#1E293B', background: '#fff',
                transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = '#10B981'}
              onBlur={e => e.target.style.borderColor = '#E2E8F0'}
            />
            {search && (
              <button type="button" onClick={() => { setSearch(''); fetchClients('') }}
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
          </div>
          <button type="submit" style={{
            background: '#10B981', color: '#fff',
            border: 'none', borderRadius: '10px',
            padding: '10px 20px', fontSize: '14px',
            fontWeight: 500, cursor: 'pointer',
            transition: 'background 0.2s',
          }}
            onMouseEnter={e => e.currentTarget.style.background = '#059669'}
            onMouseLeave={e => e.currentTarget.style.background = '#10B981'}
          >
            Rechercher
          </button>
        </form>
      </div>

      {/* Table */}
      <div style={{
        background: '#fff', borderRadius: '16px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
        overflow: 'hidden', border: '1px solid #F1F5F9',
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '140px 1fr 100px 120px 130px 120px 40px',
          padding: '12px 20px',
          background: '#F8FAFC',
          borderBottom: '1px solid #E2E8F0',
          fontSize: '12px', fontWeight: 600,
          color: '#64748B', letterSpacing: '0.3px',
        }}>
          <span>CODE</span>
          <span>CLIENT</span>
          <span>TYPE</span>
          <span>PAYS</span>
          <span style={{ textAlign: 'right' }}>CA TOTAL</span>
          <span style={{ textAlign: 'right' }}>COMMANDES</span>
          <span />
        </div>

        {loading ? (
          [...Array(8)].map((_, i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '140px 1fr 100px 120px 130px 120px 40px',
              padding: '16px 20px', gap: '12px',
              borderBottom: '1px solid #F8FAFC',
            }}>
              {[...Array(6)].map((_, j) => <Skeleton key={j} h="14px" />)}
            </div>
          ))
        ) : paginated.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#94A3B8' }}>
            <Users size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
            <div>Aucun client trouvé</div>
          </div>
        ) : (
          paginated.map((c, i) => (
            <div
              key={c.code_client}
              onClick={() => setSelected(c)}
              style={{
                display: 'grid',
                gridTemplateColumns: '140px 1fr 100px 120px 130px 120px 40px',
                padding: '14px 20px',
                borderBottom: i < paginated.length - 1 ? '1px solid #F8FAFC' : 'none',
                cursor: 'pointer', alignItems: 'center',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#F8FAFC'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{ fontSize: '12px', color: '#64748B', fontFamily: 'monospace' }}>
                {c.code_client}
              </span>
              <span style={{
                fontSize: '13px', fontWeight: 500, color: '#1E293B',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                paddingRight: '16px',
              }}>
                {c.client}
              </span>
              <div><TypeBadge type={c.type} /></div>
              <span style={{ fontSize: '13px', color: '#64748B' }}>{c.pays ?? '—'}</span>
              <span style={{ fontSize: '13px', color: '#1E2A6E', fontWeight: 600, textAlign: 'right' }}>
                {fmt(c.ca_total)}
              </span>
              <span style={{ fontSize: '13px', color: '#64748B', textAlign: 'right' }}>
                {(c.nb_commandes ?? 0).toLocaleString()}
              </span>
              <ChevronRight size={15} color="#CBD5E1" />
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: '8px', marginTop: '24px',
        }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            style={{
              padding: '8px 16px', borderRadius: '8px',
              border: '1px solid #E2E8F0', background: '#fff',
              color: page === 1 ? '#CBD5E1' : '#1E2A6E',
              cursor: page === 1 ? 'default' : 'pointer',
              fontSize: '13px', fontWeight: 500,
            }}
          >← Précédent</button>
          {[...Array(Math.min(totalPages, 7))].map((_, i) => (
            <button key={i} onClick={() => setPage(i + 1)}
              style={{
                width: '36px', height: '36px', borderRadius: '8px',
                border: '1px solid',
                borderColor: page === i + 1 ? '#10B981' : '#E2E8F0',
                background: page === i + 1 ? '#10B981' : '#fff',
                color: page === i + 1 ? '#fff' : '#64748B',
                cursor: 'pointer', fontSize: '13px', fontWeight: 500,
              }}
            >{i + 1}</button>
          ))}
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
            style={{
              padding: '8px 16px', borderRadius: '8px',
              border: '1px solid #E2E8F0', background: '#fff',
              color: page === totalPages ? '#CBD5E1' : '#1E2A6E',
              cursor: page === totalPages ? 'default' : 'pointer',
              fontSize: '13px', fontWeight: 500,
            }}
          >Suivant →</button>
        </div>
      )}

      {selected && <DetailPanel client={selected} onClose={() => setSelected(null)} />}

      <style>{`
        @keyframes shimmer {
          0%   { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);   opacity: 1; }
        }
      `}</style>
    </div>
  )
}