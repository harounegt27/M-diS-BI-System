import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getKPIs, getVentesMensuelles } from '../services/api'
import {
  TrendingUp, Users, Package, ShoppingCart,
  BarChart2, Brain, ArrowRight
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts'

// ── Helpers ──────────────────────────────────────────────
const fmt = (n) =>
  n >= 1_000_000
    ? (n / 1_000_000).toFixed(2) + ' M'
    : n >= 1_000
    ? (n / 1_000).toFixed(1) + ' K'
    : n?.toLocaleString('fr-FR') ?? '—'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1E2A6E', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px', padding: '10px 16px', color: '#fff', fontSize: '13px'
    }}>
      <div style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontWeight: 600, color: '#4FA3E0' }}>
        {Number(payload[0].value).toLocaleString('fr-FR')} DT
      </div>
    </div>
  )
}

// ── KPI Card ─────────────────────────────────────────────
function KPICard({ icon: Icon, label, value, color, delay }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  return (
    <div style={{
      background: '#fff',
      borderRadius: '14px',
      padding: '24px',
      borderLeft: `4px solid ${color}`,
      boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(16px)',
      transition: 'opacity 0.4s ease, transform 0.4s ease',
      cursor: 'default',
    }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-4px)'
        e.currentTarget.style.boxShadow = `0 8px 24px rgba(0,0,0,0.1)`
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.06)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <span style={{ fontSize: '13px', color: '#64748B', fontWeight: 500 }}>{label}</span>
        <div style={{
          width: 38, height: 38, borderRadius: '10px',
          background: color + '18',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <Icon size={18} color={color} />
        </div>
      </div>
      <div style={{
        fontSize: '28px', fontWeight: 700, color: '#1E2A6E',
        fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.5px'
      }}>
        {value}
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────
export default function Home() {
  const [kpis, setKpis]     = useState(null)
  const [data, setData]     = useState([])
  const [loading, setLoading] = useState(true)
  const navigate            = useNavigate()

  useEffect(() => {
    Promise.all([getKPIs(), getVentesMensuelles()])
      .then(([kRes, mRes]) => {
        setKpis(kRes.data)
        const last12 = mRes.data.slice(-12).map(d => ({
          name: `${d.nom_mois.slice(0, 3)} ${String(d.annee).slice(2)}`,
          ca: d.ca,
        }))
        setData(last12)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const cards = kpis ? [
    { icon: TrendingUp, label: 'Chiffre d\'Affaires Total',  value: fmt(kpis.ca_total) + ' DT', color: '#2B7CC2', delay: 0   },
    { icon: ShoppingCart,label: 'Nombre de Commandes',       value: fmt(kpis.nb_commandes),      color: '#10B981', delay: 100 },
    { icon: Users,       label: 'Clients Actifs',            value: fmt(kpis.nb_clients_actifs), color: '#F59E0B', delay: 200 },
    { icon: Package,     label: 'Quantité Totale Vendue',    value: fmt(kpis.quantite_totale),   color: '#8B5CF6', delay: 300 },
  ] : []

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '40px 24px' }}>

      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, #1E2A6E 0%, #2B7CC2 100%)',
        borderRadius: '20px',
        padding: '48px 48px',
        marginBottom: '36px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Cercles décoratifs */}
        <div style={{
          position: 'absolute', top: -60, right: -60,
          width: 240, height: 240,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.05)',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', bottom: -40, right: 120,
          width: 160, height: 160,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.04)',
          pointerEvents: 'none',
        }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(255,255,255,0.12)',
            borderRadius: '999px', padding: '4px 14px',
            marginBottom: '20px',
          }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#10B981' }} />
            <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: '12px', fontWeight: 500 }}>
              Système connecté — DW_Medis en ligne
            </span>
          </div>

          <h1 style={{
            color: '#fff', fontSize: '36px', fontWeight: 700,
            lineHeight: 1.2, marginBottom: '12px', letterSpacing: '-0.5px'
          }}>
            Portail BI — Laboratoires MédiS
          </h1>
          <p style={{
            color: 'rgba(255,255,255,0.65)', fontSize: '15px',
            maxWidth: '520px', lineHeight: 1.7, marginBottom: '28px'
          }}>
            Tableau de bord analytique centralisant les ventes, clients et prédictions
            de demande pour une prise de décision éclairée.
          </p>

          <div style={{ display: 'flex', gap: 12 }}>
            <button
              onClick={() => navigate('/dashboards')}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: '#fff', color: '#1E2A6E',
                border: 'none', borderRadius: '10px',
                padding: '11px 22px', fontSize: '14px', fontWeight: 600,
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.15)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              <BarChart2 size={15} /> Voir les Dashboards
            </button>
            <button
              onClick={() => navigate('/predictions')}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: 'rgba(255,255,255,0.12)', color: '#fff',
                border: '1.5px solid rgba(255,255,255,0.2)',
                borderRadius: '10px', padding: '11px 22px',
                fontSize: '14px', fontWeight: 500,
                cursor: 'pointer',
                transition: 'background 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.18)'}
              onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.12)'}
            >
              <Brain size={15} /> Prédictions XGBoost <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {loading ? (
        <div style={{ textAlign: 'center', color: '#64748B', padding: '40px' }}>
          Chargement des données...
        </div>
      ) : (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '20px',
            marginBottom: '32px',
          }}>
            {cards.map((c, i) => <KPICard key={i} {...c} />)}
          </div>

          {/* Chart */}
          <div style={{
            background: '#fff',
            borderRadius: '16px',
            padding: '28px',
            boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#1E2A6E', marginBottom: 4 }}>
                  Évolution du Chiffre d'Affaires
                </h2>
                <p style={{ fontSize: '13px', color: '#64748B' }}>12 derniers mois disponibles</p>
              </div>
              <button
                onClick={() => navigate('/dashboards')}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: '#F0F4FA', color: '#2B7CC2',
                  border: 'none', borderRadius: '8px',
                  padding: '8px 14px', fontSize: '13px',
                  fontWeight: 500, cursor: 'pointer',
                }}
              >
                Détail complet <ArrowRight size={13} />
              </button>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="caGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#2B7CC2" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#2B7CC2" stopOpacity={0}   />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={v => fmt(v)} tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} width={70} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone" dataKey="ca"
                  stroke="#2B7CC2" strokeWidth={2.5}
                  fill="url(#caGrad)" dot={false}
                  activeDot={{ r: 5, fill: '#2B7CC2', stroke: '#fff', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}