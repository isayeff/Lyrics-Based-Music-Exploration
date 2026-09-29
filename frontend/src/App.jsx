import { useCallback, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Results from './pages/Results'
import SongDetail from './pages/SongDetail'
import { GenreList, GenreDetail } from './pages/Genres'
import Login from './pages/Login'
import Profile from './pages/Profile'
import About from './pages/About'
import Toaster from './components/Toaster'
import { AuthProvider } from './auth'

const MAX_RECENT = 8

export default function App() {
  // Recent searches live in React state (not localStorage) - they disappear on
  // reload, so no query history is persisted to disk.
  const [recent, setRecent] = useState([])

  const onSearch = useCallback((query) => {
    setRecent((prev) => [query, ...prev.filter((q) => q !== query)].slice(0, MAX_RECENT))
  }, [])

  return (
    <AuthProvider>
      <Toaster />
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home recent={recent} onSearch={onSearch} />} />
            <Route path="/results" element={<Results recent={recent} onSearch={onSearch} />} />
            <Route path="/song/:songId" element={<SongDetail />} />
            <Route path="/genres" element={<GenreList />} />
            <Route path="/genres/:genre" element={<GenreDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
