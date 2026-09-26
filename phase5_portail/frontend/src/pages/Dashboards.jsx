import { useState } from 'react'
import { BarChart2, Users, Package, Maximize2 } from 'lucide-react'

const TABS = [
  {
    key: 'vente',
    label: 'Ventes',
    icon: BarChart2,
    color: '#2B7CC2',
    url: 'https://app.fabric.microsoft.com/reportEmbed?reportId=296848f1-0347-4bc1-9aec-a99e6810dc0d&autoAuth=true&ctid=dbd6664d-4eb9-46eb-99d8-5c43ba153c61&pageName=2939f93ae7b3b91b2d31',
    description: 'Analyse des ventes par période, produit et marché'
  },
  {
    key: 'produit',
    label: 'Produits',
    icon: Package,
    color: '#8B5CF6',
    url: 'https://app.fabric.microsoft.com/reportEmbed?reportId=296848f1-0347-4bc1-9aec-a99e6810dc0d&autoAuth=true&ctid=dbd6664d-4eb9-46eb-99d8-5c43ba153c61&pageName=41074227b7a83ab87452',
    description: 'Performance par famille, forme galénique et activité'
  },
  {
    key: 'client',
    label: 'Clients',
    icon: Users,
    color: '#10B981',
    url: 'https://app.fabric.microsoft.com/reportEmbed?reportId=296848f1-0347-4bc1-9aec-a99e6810dc0d&autoAuth=true&ctid=dbd6664d-4eb9-46eb-99d8-5c43ba153c61&pageName=3cd65d5c2bd97ea6ce25',
    description: 'Segmentation clients par région, pays et chiffre d\'affaires'
  },
]

export default function Dashboards() {
  const [active, setActive]       = useState('vente')
  const [loading, setLoading]     = useState(true)
  const [fullscreen, setFullscreen] = useState(false)

  const current = TABS.find(t => t.key === active)

  const handleTabChange = (key) => {
    if (key === active) return
    setLoading(true)
    setActive(key)
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 24px' }}>

      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{
          fontSize: '24px', fontWeight: 700,
          color: '#1E2A6E', marginBottom: '6px', letterSpacing: '-0.3px'
        }}>
          Dashboards Power BI
        </h1>
        <p style={{ color: '#64748B', fontSize: '14px' }}>
          Rapports interactifs connectés en temps réel au Data Warehouse DW_Medis
        </p>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: '12px',
        marginBottom: '20px',
        borderBottom: '2px solid #E2E8F0',
        paddingBottom: '0',
      }}>
        {TABS.map(({ key, label, icon: Icon, color }) => (
          <button
            key={key}
            onClick={() => handleTabChange(key)}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '10px 20px',
              background: 'none', border: 'none',
              borderBottom: active === key ? `3px solid ${color}` : '3px solid transparent',
              marginBottom: '-2px',
              color: active === key ? color : '#64748B',
              fontWeight: active === key ? 600 : 400,
              fontSize: '14px', cursor: 'pointer',
              transition: 'all 0.2s ease',
              borderRadius: '0',
            }}
            onMouseEnter={e => {
              if (active !== key) e.currentTarget.style.color = '#1E2A6E'
            }}
            onMouseLeave={e => {
              if (active !== key) e.currentTarget.style.color = '#64748B'
            }}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}

        {/* Fullscreen button */}
        <button
          onClick={() => setFullscreen(!fullscreen)}
          title={fullscreen ? 'Quitter plein écran' : 'Plein écran'}
          style={{
            marginLeft: 'auto',
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 14px',
            background: '#F0F4FA', border: '1px solid #E2E8F0',
            borderRadius: '8px', color: '#64748B',
            fontSize: '13px', cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = '#1E2A6E'
            e.currentTarget.style.color = '#fff'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = '#F0F4FA'
            e.currentTarget.style.color = '#64748B'
          }}
        >
          <Maximize2 size={14} />
          {fullscreen ? 'Réduire' : 'Plein écran'}
        </button>
      </div>

      {/* Description */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        marginBottom: '16px',
      }}>
        <div style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: current.color,
        }} />
        <span style={{ fontSize: '13px', color: '#64748B' }}>
          {current.description}
        </span>
      </div>

      {/* iFrame Container */}
      <div style={{
        position: fullscreen ? 'fixed' : 'relative',
        inset: fullscreen ? '0' : 'auto',
        zIndex: fullscreen ? 100 : 'auto',
        background: '#fff',
        borderRadius: fullscreen ? '0' : '16px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
        overflow: 'hidden',
        border: '1px solid #E2E8F0',
      }}>

        {/* Loading overlay */}
        {loading && (
          <div style={{
            position: 'absolute', inset: 0,
            background: '#F8FAFC',
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            zIndex: 10, gap: '16px',
          }}>
            <div style={{
              width: '40px', height: '40px',
              border: '3px solid #E2E8F0',
              borderTop: '3px solid #2B7CC2',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
            }} />
            <span style={{ color: '#64748B', fontSize: '14px' }}>
              Chargement du rapport {current.label}...
            </span>
          </div>
        )}

        <iframe
          key={active}
          src={current.url}
          title={`Dashboard ${current.label}`}
          style={{
            width: '100%',
            height: fullscreen ? '100vh' : '700px',
            border: 'none',
            display: 'block',
          }}
          onLoad={() => setLoading(false)}
          allowFullScreen
        />
      </div>

      {/* Fullscreen close hint */}
      {fullscreen && (
        <button
          onClick={() => setFullscreen(false)}
          style={{
            position: 'fixed', top: '16px', right: '16px',
            zIndex: 200,
            background: 'rgba(30,42,110,0.9)',
            color: '#fff', border: 'none',
            borderRadius: '10px', padding: '10px 18px',
            fontSize: '13px', fontWeight: 500,
            cursor: 'pointer', backdropFilter: 'blur(8px)',
          }}
        >
          ✕ Quitter le plein écran
        </button>
      )}

      {/* CSS for spinner */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}