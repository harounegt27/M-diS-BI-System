import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Home from './pages/Home'
import Dashboards from './pages/Dashboards'
import Predictions from './pages/Predictions'
import Clients from './pages/Clients'
import Produits from './pages/Produits'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main>
          <Routes>
            <Route path="/"            element={<Home />} />
            <Route path="/dashboards"  element={<Dashboards />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/clients"     element={<Clients />} />
            <Route path="/produits"    element={<Produits />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}