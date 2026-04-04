import { useState } from "react"

const API = "http://localhost:8000"

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return {}
  }
}

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
        const payload = parseJwt(data.access_token)
        onLogin(data.access_token, username, payload.role)
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

function Dashboard({ token, username, role, onLogout }) {
  const [courses, setCourses] = useState([])
  const [exams, setExams] = useState([])
  const [users, setUsers] = useState([])
  const [cart, setCart] = useState([])
  const [purchases, setPurchases] = useState([])
  const [activeTab, setActiveTab] = useState("courses")
  const [message, setMessage] = useState("")
  const [messageType, setMessageType] = useState("success")
  const [newCourse, setNewCourse] = useState({ title: "", level: "A1", price: "" })
  const [newExam, setNewExam] = useState({ title: "", duration_minutes: 30 })

  const headers = { Authorization: `Bearer ${token}` }

  const showMessage = (msg, type = "success") => {
    setMessage(msg)
    setMessageType(type)
    setTimeout(() => setMessage(""), 3000)
  }

  const loadCourses = async () => {
    const res = await fetch(`${API}/course/courses`, { headers })
    const data = await res.json()
    setCourses(Array.isArray(data) ? data : [])
    setActiveTab("courses")
  }

  const loadExams = async () => {
    const res = await fetch(`${API}/exam/exams`, { headers })
    const data = await res.json()
    setExams(Array.isArray(data) ? data : [])
    setActiveTab("exams")
  }

  const loadUsers = async () => {
    const res = await fetch(`${API}/auth/users`, { headers })
    const data = await res.json()
    setUsers(Array.isArray(data) ? data : [])
    setActiveTab("users")
  }

  const loadCart = async () => {
    const res = await fetch(`${API}/course/courses/cart?username=${username}`, { headers })
    const data = await res.json()
    setCart(data.items || [])
    setActiveTab("cart")
  }

  const loadPurchases = async () => {
    const res = await fetch(`${API}/course/courses/my-purchases?username=${username}`, { headers })
    const data = await res.json()
    setPurchases(Array.isArray(data) ? data : [])
    setActiveTab("purchases")
  }

  const addToCart = async (courseId) => {
    const res = await fetch(`${API}/course/courses/cart/add`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ username, course_id: courseId })
    })
    const data = await res.json()
    showMessage(data.message || data.detail, res.ok ? "success" : "error")
  }

  const checkout = async () => {
    const res = await fetch(`${API}/course/courses/cart/checkout`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ username, course_id: "" })
    })
    const data = await res.json()
    showMessage(data.message || data.detail, res.ok ? "success" : "error")
    setCart([])
  }

  const createCourse = async () => {
    const res = await fetch(`${API}/course/courses`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ ...newCourse, price: parseFloat(newCourse.price), is_active: true })
    })
    const data = await res.json()
    showMessage(data.message || data.detail, res.ok ? "success" : "error")
    if (res.ok) {
      setNewCourse({ title: "", level: "A1", price: "" })
      loadCourses()
    }
  }

  const createExam = async () => {
    const res = await fetch(`${API}/exam/exams`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ ...newExam, questions: [], is_active: true })
    })
    const data = await res.json()
    showMessage(data.message || data.detail, res.ok ? "success" : "error")
    if (res.ok) {
      setNewExam({ title: "", duration_minutes: 30 })
      loadExams()
    }
  }

  const deleteUser = async (uname) => {
    const res = await fetch(`${API}/auth/user/${uname}`, { method: "DELETE", headers })
    const data = await res.json()
    showMessage(data.message || data.detail, res.ok ? "success" : "error")
    if (res.ok) loadUsers()
  }

  const roleColor = {
    admin: "bg-red-800 text-red-300",
    teacher: "bg-yellow-800 text-yellow-300",
    student: "bg-blue-800 text-blue-300"
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 flex justify-between items-center shadow">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-blue-400">Dil Akademisi</h1>
          <span className={`text-xs px-2 py-1 rounded-full ${roleColor[role] || "bg-gray-700 text-gray-300"}`}>
            {role}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">Hoş geldin, <span className="text-white font-medium">{username}</span></span>
          <button onClick={onLogout} className="text-sm text-red-400 hover:text-red-300">Çıkış</button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`mx-6 mt-4 px-4 py-3 rounded-lg text-sm ${messageType === "success" ? "bg-green-800 text-green-200" : "bg-red-800 text-red-200"}`}>
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 px-6 mt-6 flex-wrap">
        <button onClick={loadCourses} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "courses" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
          Kurslar
        </button>
        <button onClick={loadExams} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "exams" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
          Sınavlar
        </button>
        {role === "student" && (
          <>
            <button onClick={loadCart} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "cart" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
              Sepet {cart.length > 0 && <span className="ml-1 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{cart.length}</span>}
            </button>
            <button onClick={loadPurchases} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "purchases" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
              Satın Aldıklarım
            </button>
          </>
        )}
        {role === "admin" && (
          <button onClick={loadUsers} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "users" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
            Kullanıcılar
          </button>
        )}
      </div>

      {/* Content */}
      <div className="px-6 mt-6 pb-10">

        {/* Courses */}
        {activeTab === "courses" && (
          <div>
            {(role === "teacher" || role === "admin") && (
              <div className="bg-gray-800 rounded-xl p-5 mb-6">
                <h3 className="font-semibold mb-4 text-gray-300">Yeni Kurs Ekle</h3>
                <div className="flex gap-3 flex-wrap">
                  <input
                    className="bg-gray-700 text-white rounded-lg px-4 py-2 flex-1 min-w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Kurs adı"
                    value={newCourse.title}
                    onChange={e => setNewCourse({ ...newCourse, title: e.target.value })}
                  />
                  <select
                    className="bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none"
                    value={newCourse.level}
                    onChange={e => setNewCourse({ ...newCourse, level: e.target.value })}
                  >
                    {["A1","A2","B1","B2","C1","C2"].map(l => <option key={l}>{l}</option>)}
                  </select>
                  <input
                    className="bg-gray-700 text-white rounded-lg px-4 py-2 w-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Fiyat"
                    type="number"
                    value={newCourse.price}
                    onChange={e => setNewCourse({ ...newCourse, price: e.target.value })}
                  />
                  <button onClick={createCourse} className="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-lg transition">
                    Ekle
                  </button>
                </div>
              </div>
            )}
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
                  {role === "student" && course.is_active && (
                    <button onClick={() => addToCart(course.id)} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm transition">
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
            {(role === "teacher" || role === "admin") && (
              <div className="bg-gray-800 rounded-xl p-5 mb-6">
                <h3 className="font-semibold mb-4 text-gray-300">Yeni Sınav Ekle</h3>
                <div className="flex gap-3 flex-wrap">
                  <input
                    className="bg-gray-700 text-white rounded-lg px-4 py-2 flex-1 min-w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Sınav adı"
                    value={newExam.title}
                    onChange={e => setNewExam({ ...newExam, title: e.target.value })}
                  />
                  <input
                    className="bg-gray-700 text-white rounded-lg px-4 py-2 w-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Süre (dakika)"
                    type="number"
                    value={newExam.duration_minutes}
                    onChange={e => setNewExam({ ...newExam, duration_minutes: parseInt(e.target.value) })}
                  />
                  <button onClick={createExam} className="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-lg transition">
                    Ekle
                  </button>
                </div>
              </div>
            )}
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
        {activeTab === "cart" && role === "student" && (
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
                <button onClick={checkout} className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition">
                  Tümünü Satın Al
                </button>
              </div>
            )}
          </div>
        )}

        {/* Purchases */}
        {activeTab === "purchases" && role === "student" && (
          <div>
            <h2 className="text-lg font-semibold mb-4 text-gray-300">Satın Aldıklarım</h2>
            {purchases.length === 0 ? (
              <p className="text-gray-500">Henüz kurs satın almadınız.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {purchases.map((purchase, i) => (
                  <div key={i} className="bg-gray-800 rounded-xl p-5">
                    <p className="text-gray-300 text-sm font-medium">Kurs ID:</p>
                    <p className="text-blue-400 text-sm mt-1">{purchase.course_id}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Users */}
        {activeTab === "users" && role === "admin" && (
          <div>
            <h2 className="text-lg font-semibold mb-4 text-gray-300">Kullanıcı Yönetimi</h2>
            <div className="bg-gray-800 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-700 text-gray-300 text-sm">
                    <th className="text-left px-5 py-3">Kullanıcı Adı</th>
                    <th className="text-left px-5 py-3">Rol</th>
                    <th className="text-right px-5 py-3">İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.username} className="border-t border-gray-700">
                      <td className="px-5 py-3 text-white">{user.username}</td>
                      <td className="px-5 py-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${roleColor[user.role] || "bg-gray-700 text-gray-300"}`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right">
                        {user.username !== username && (
                          <button onClick={() => deleteUser(user.username)} className="text-red-400 hover:text-red-300 text-sm">
                            Sil
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState("")
  const [role, setRole] = useState("")

  const handleLogin = (token, username, role) => {
    setToken(token)
    setUsername(username)
    setRole(role)
  }

  const handleLogout = () => {
    setToken(null)
    setUsername("")
    setRole("")
  }

  if (!token) return <Login onLogin={handleLogin} />
  return <Dashboard token={token} username={username} role={role} onLogout={handleLogout} />
}