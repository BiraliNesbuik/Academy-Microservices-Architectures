import { useState } from "react"

const API = "http://localhost:8000"

function Login({ onLogin }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  const handleLogin = async () => {
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      if (res.ok) {
        onLogin(data.access_token, username)
      } else {
        setError("Hatalı kullanıcı adı veya şifre")
      }
    } catch {
      setError("Sunucuya bağlanılamadı")
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-gray-800 p-8 rounded-2xl shadow-xl w-96">
        <h1 className="text-3xl font-bold text-white mb-2">Dil Akademisi</h1>
        <p className="text-gray-400 mb-6">Hesabınıza giriş yapın</p>
        {error && <p className="text-red-400 mb-4 text-sm">{error}</p>}
        <input
          className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Kullanıcı adı"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />
        <input
          className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 mb-6 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Şifre"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        <button
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
          onClick={handleLogin}
        >
          Giriş Yap
        </button>
      </div>
    </div>
  )
}

function Dashboard({ token, username, onLogout }) {
  const [courses, setCourses] = useState([])
  const [exams, setExams] = useState([])
  const [cart, setCart] = useState([])
  const [activeTab, setActiveTab] = useState("courses")
  const [message, setMessage] = useState("")

  const headers = { Authorization: `Bearer ${token}` }

  const loadCourses = async () => {
    const res = await fetch(`${API}/course/courses`, { headers })
    const data = await res.json()
    setCourses(data)
    setActiveTab("courses")
  }

  const loadExams = async () => {
    const res = await fetch(`${API}/exam/exams`, { headers })
    const data = await res.json()
    setExams(data)
    setActiveTab("exams")
  }

  const loadCart = async () => {
    const res = await fetch(`${API}/course/courses/cart?username=${username}`, { headers })
    const data = await res.json()
    setCart(data.items || [])
    setActiveTab("cart")
  }

  const addToCart = async (courseId) => {
    const res = await fetch(`${API}/course/courses/cart/add`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ username, course_id: courseId })
    })
    const data = await res.json()
    setMessage(data.message || data.detail)
    setTimeout(() => setMessage(""), 3000)
  }

  const checkout = async () => {
    const res = await fetch(`${API}/course/courses/cart/checkout`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ username, course_id: "" })
    })
    const data = await res.json()
    setMessage(data.message || data.detail)
    setCart([])
    setTimeout(() => setMessage(""), 3000)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 flex justify-between items-center shadow">
        <h1 className="text-xl font-bold text-blue-400">Dil Akademisi</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">Hoş geldin, <span className="text-white font-medium">{username}</span></span>
          <button onClick={onLogout} className="text-sm text-red-400 hover:text-red-300">Çıkış</button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className="mx-6 mt-4 bg-green-800 text-green-200 px-4 py-3 rounded-lg text-sm">
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 px-6 mt-6">
        <button
          onClick={loadCourses}
          className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "courses" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
        >
          Kurslar
        </button>
        <button
          onClick={loadExams}
          className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "exams" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
        >
          Sınavlar
        </button>
        <button
          onClick={loadCart}
          className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "cart" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}
        >
          Sepet {cart.length > 0 && <span className="ml-1 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{cart.length}</span>}
        </button>
      </div>

      {/* Content */}
      <div className="px-6 mt-6">

        {/* Courses */}
        {activeTab === "courses" && (
          <div>
            <h2 className="text-lg font-semibold mb-4 text-gray-300">Mevcut Kurslar</h2>
            {courses.length === 0 && <p className="text-gray-500">Kursları görmek için "Kurslar" butonuna tıklayın.</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {courses.map(course => (
                <div key={course.id} className="bg-gray-800 rounded-xl p-5 flex flex-col gap-3">
                  <div>
                    <h3 className="font-semibold text-white">{course.title}</h3>
                    <p className="text-gray-400 text-sm mt-1">Seviye: {course.level}</p>
                  </div>
                  <div className="flex justify-between items-center mt-auto">
                    <span className="text-blue-400 font-bold">₺{course.price}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${course.is_active ? "bg-green-800 text-green-300" : "bg-red-900 text-red-300"}`}>
                      {course.is_active ? "Aktif" : "Pasif"}
                    </span>
                  </div>
                  {course.is_active && (
                    <button
                      onClick={() => addToCart(course.id)}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm transition"
                    >
                      Sepete Ekle
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Exams */}
        {activeTab === "exams" && (
          <div>
            <h2 className="text-lg font-semibold mb-4 text-gray-300">Mevcut Sınavlar</h2>
            {exams.length === 0 && <p className="text-gray-500">Sınavları görmek için "Sınavlar" butonuna tıklayın.</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {exams.map(exam => (
                <div key={exam.id} className="bg-gray-800 rounded-xl p-5">
                  <h3 className="font-semibold text-white">{exam.title}</h3>
                  <p className="text-gray-400 text-sm mt-1">Süre: {exam.duration_minutes} dakika</p>
                  <p className="text-gray-400 text-sm">Soru sayısı: {exam.questions?.length || 0}</p>
                  <span className={`inline-block mt-3 text-xs px-2 py-1 rounded-full ${exam.is_active ? "bg-green-800 text-green-300" : "bg-red-900 text-red-300"}`}>
                    {exam.is_active ? "Aktif" : "Pasif"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cart */}
        {activeTab === "cart" && (
          <div>
            <h2 className="text-lg font-semibold mb-4 text-gray-300">Sepetim</h2>
            {cart.length === 0 ? (
              <p className="text-gray-500">Sepetiniz boş.</p>
            ) : (
              <div>
                <div className="bg-gray-800 rounded-xl p-5 mb-4">
                  {cart.map((courseId, i) => (
                    <div key={i} className="text-gray-300 py-2 border-b border-gray-700 last:border-0 text-sm">
                      Kurs ID: {courseId}
                    </div>
                  ))}
                </div>
                <button
                  onClick={checkout}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition"
                >
                  Tümünü Satın Al
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState("")

  const handleLogin = (token, username) => {
    setToken(token)
    setUsername(username)
  }

  const handleLogout = () => {
    setToken(null)
    setUsername("")
  }

  if (!token) return <Login onLogin={handleLogin} />
  return <Dashboard token={token} username={username} onLogout={handleLogout} />
}