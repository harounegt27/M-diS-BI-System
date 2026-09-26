import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useRef, useLayoutEffect } from 'react'
import { Search, BarChart2, Brain, Users, Package, Home, X, Menu } from 'lucide-react'
import styles from './Navbar.module.css'

const navItems = [
  { to: '/',            label: 'Accueil',      icon: Home },
  { to: '/dashboards',  label: 'Dashboards',   icon: BarChart2 },
  { to: '/predictions', label: 'Prédictions',  icon: Brain },
  { to: '/clients',     label: 'Clients',      icon: Users },
  { to: '/produits',    label: 'Produits',     icon: Package },
]

export default function Navbar() {
  const [query, setQuery]       = useState('')
  const [focused, setFocused]   = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const navLinksRef = useRef(null)
  const linkRefs = useRef([])
  const underlineRef = useRef(null)
  const [underlineStyle, setUnderlineStyle] = useState({ left: 0, width: 0, opacity: 0 })
  const [logoPulse, setLogoPulse] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // One-time logo pulse removal
  useEffect(() => {
    const t = setTimeout(() => setLogoPulse(false), 900)
    return () => clearTimeout(t)
  }, [])

  // Update underline position when location changes or on resize
  useLayoutEffect(() => {
    const update = () => {
      const container = navLinksRef.current
      if (!container) return setUnderlineStyle(s => ({ ...s, opacity: 0 }))

      const path = location.pathname || '/'
      const activeIndex = navItems.findIndex(item => item.to === path)
      const activeEl = linkRefs.current[activeIndex]
      if (activeEl) {
        const containerRect = container.getBoundingClientRect()
        const r = activeEl.getBoundingClientRect()
        setUnderlineStyle({ left: r.left - containerRect.left + container.scrollLeft, width: r.width, opacity: 1 })
      } else {
        setUnderlineStyle(s => ({ ...s, opacity: 0 }))
      }
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [location.pathname])

  const handleSearch = (e) => {
    e.preventDefault()
    if (!query.trim()) return
    navigate(`/produits?search=${encodeURIComponent(query.trim())}`)
    setQuery('')
    setFocused(false)
  }

  return (
    <nav
      className={styles.nav}
      style={{
        background: scrolled ? 'rgba(18,22,50,0.65)' : '#1E2A6E',
        backdropFilter: scrolled ? 'blur(10px)' : 'none',
        boxShadow: scrolled ? '0 2px 20px rgba(0,0,0,0.25)' : '0 1px 0 rgba(255,255,255,0.04)'
      }}
    >
      <div className={styles.container}>

        {/* Logo */}
        <div className={styles.logoWrap}>
          <div className={`${styles.logoIcon} ${logoPulse ? styles.logoPulse : ''}`}>
            <BarChart2 size={16} color="white" />
          </div>
          <div>
            <span className={styles.brandText}>MédiSPerform</span>
          </div>
        </div>

        {/* Nav Links */}
        <div className={styles.navLinks} ref={navLinksRef}>
          {navItems.map(({ to, label, icon: Icon }, idx) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              ref={el => (linkRefs.current[idx] = el?.closest('a') ?? el)}
              className={styles.navLink}
              style={({ isActive }) => ({
                color: isActive ? '#fff' : 'rgba(255,255,255,0.75)',
                fontWeight: isActive ? 600 : 400,
                textDecoration: 'none'
              })}
            >
              <Icon size={14} />
              {label}
            </NavLink>
          ))}

          <div
            ref={underlineRef}
            className={styles.underline}
            style={{ left: underlineStyle.left, width: underlineStyle.width, opacity: underlineStyle.opacity }}
          />
        </div>

        {/* Search + Mobile Hamburger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <form onSubmit={handleSearch} className={styles.searchForm}>
            <div style={{ position: 'relative' }}>
              <Search
                size={14}
                style={{
                  position: 'absolute', left: '10px',
                  top: '50%', transform: 'translateY(-50%)',
                  color: focused ? '#2B7CC2' : 'rgba(255,255,255,0.45)',
                  transition: 'color 0.2s',
                  pointerEvents: 'none',
                }}
              />
              <input
                className={styles.searchInput}
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder="Rechercher..."
                aria-label="Rechercher"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  className={styles.clearBtn}
                >
                  <X size={13} />
                </button>
              )}
            </div>
          </form>

          <button
            className={styles.hamburger}
            aria-label="Menu"
            onClick={() => setMobileOpen(true)}
          >
            <Menu size={18} />
          </button>
        </div>

      </div>

      {/* Bottom accent line */}
      <div className={styles.bottomAccent} />

      {/* Mobile drawer */}
      <div className={`${styles.overlay} ${mobileOpen ? styles.overlayOpen : ''}`} onClick={() => setMobileOpen(false)} />
      <aside className={`${styles.drawer} ${mobileOpen ? styles.drawerOpen : ''}`} aria-hidden={!mobileOpen}>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className={styles.hamburger} onClick={() => setMobileOpen(false)} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>
        <nav className={styles.mobileNavLinks}>
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setMobileOpen(false)} className={styles.navLink} style={({ isActive }) => ({ color: isActive ? '#fff' : 'rgba(255,255,255,0.9)', fontWeight: isActive ? 600 : 500 })}>
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </nav>
  )
}