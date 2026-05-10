import { useState } from "react"

const API = "http://localhost:8000"

const DAYS_TR = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
const MONTHS_TR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return {}
  }
}

function getMondayOfWeek(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function getWeekDays(monday) {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    return d
  })
}

function formatDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
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

// ── TAKVİM SEKMESİ ──────────────────────────────────────────────────

function CalendarTab({ token, username, role }) {
  const [slots, setSlots] = useState([])
  const [appointments, setAppointments] = useState([])
  const [weekStart, setWeekStart] = useState(getMondayOfWeek(new Date()))
  const [message, setMessage] = useState("")
  const [messageType, setMessageType] = useState("success")
  const [newSlot, setNewSlot] = useState({ date: "", start_time: "", end_time: "", note: "" })
  const [requestNote, setRequestNote] = useState("")
  const [requestingSlot, setRequestingSlot] = useState(null)
  const [loaded, setLoaded] = useState(false)
  const [statusFilter, setStatusFilter] = useState("all")

  const headers = { Authorization: `Bearer ${token}` }

  const showMsg = (msg, type = "success") => {
    setMessage(msg)
    setMessageType(type)
    setTimeout(() => setMessage(""), 3000)
  }

  const load = async () => {
    const [sRes, aRes] = await Promise.all([
      fetch(`${API}/booking/slots`, { headers }),
      fetch(`${API}/booking/appointments${role === "student" ? `?student_username=${username}` : ""}`, { headers })
    ])
    const sData = await sRes.json()
    const aData = await aRes.json()
    setSlots(Array.isArray(sData) ? sData : [])
    setAppointments(Array.isArray(aData) ? aData : [])
    setLoaded(true)
  }

  const createSlot = async () => {
    const res = await fetch(`${API}/booking/slots`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify(newSlot)
    })
    const data = await res.json()
    if (res.ok) {
      showMsg("Slot oluşturuldu")
      setNewSlot({ date: "", start_time: "", end_time: "", note: "" })
      load()
    } else {
      showMsg(data.detail || "Hata oluştu", "error")
    }
  }

  const deleteSlot = async (slotId) => {
    const res = await fetch(`${API}/booking/slots/${slotId}`, { method: "DELETE", headers })
    if (res.ok || res.status === 204) {
      showMsg("Slot silindi")
      load()
    } else {
      const data = await res.json()
      showMsg(data.detail || "Silinemedi", "error")
    }
  }

  const requestAppointment = async (slotId) => {
    const res = await fetch(`${API}/booking/appointments`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ slot_id: slotId, student_username: username, student_note: requestNote })
    })
    const data = await res.json()
    if (res.ok) {
      showMsg("Randevu talebiniz gönderildi")
      setRequestingSlot(null)
      setRequestNote("")
      load()
    } else {
      showMsg(data.detail || "Hata oluştu", "error")
    }
  }

  const updateAppointment = async (apptId, status, teacherNote = "") => {
    const res = await fetch(`${API}/booking/appointments/${apptId}`, {
      method: "PUT",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ status, teacher_note: teacherNote })
    })
    if (res.ok) {
      showMsg(status === "approved" ? "Randevu onaylandı" : "Randevu reddedildi")
      load()
    }
  }

  const cancelAppointment = async (apptId) => {
    const res = await fetch(`${API}/booking/appointments/${apptId}`, {
      method: "PUT",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ status: "cancelled" })
    })
    if (res.ok) {
      showMsg("Randevu iptal edildi")
      load()
    }
  }

  const deleteAppointment = async (apptId) => {
    const res = await fetch(`${API}/booking/appointments/${apptId}`, { method: "DELETE", headers })
    if (res.ok || res.status === 204) {
      showMsg("Randevu silindi")
      load()
    }
  }

  const weekDays = getWeekDays(weekStart)
  const prevWeek = () => { const d = new Date(weekStart); d.setDate(d.getDate() - 7); setWeekStart(d) }
  const nextWeek = () => { const d = new Date(weekStart); d.setDate(d.getDate() + 7); setWeekStart(d) }

  const slotsForDay = (dateStr) => slots.filter(s => s.date === dateStr)
  const appointmentForSlot = (slotId) => appointments.find(a => a.slot_id === slotId && ["pending","approved"].includes(a.status))
  const historyForSlot = (slotId) => appointments.filter(a => a.slot_id === slotId && ["rejected","cancelled"].includes(a.status))

  const filteredAppointments = statusFilter === "all" ? appointments : appointments.filter(a => a.status === statusFilter)

  const counts = {
    total: appointments.length,
    pending: appointments.filter(a => a.status === "pending").length,
    approved: appointments.filter(a => a.status === "approved").length,
    rejected: appointments.filter(a => a.status === "rejected").length,
    cancelled: appointments.filter(a => a.status === "cancelled").length,
  }

  const statusBadge = {
    pending:  "bg-yellow-800 text-yellow-300",
    approved: "bg-green-800 text-green-300",
    rejected: "bg-red-800 text-red-300",
    cancelled: "bg-gray-700 text-gray-400"
  }
  const statusLabel = {
    pending: "Bekliyor", approved: "Onaylandı", rejected: "Reddedildi", cancelled: "İptal"
  }

  const weekLabel = `${weekDays[0].getDate()} ${MONTHS_TR[weekDays[0].getMonth()]} – ${weekDays[6].getDate()} ${MONTHS_TR[weekDays[6].getMonth()]} ${weekDays[6].getFullYear()}`

  if (!loaded) {
    return (
      <div className="text-center py-20">
        <button onClick={load} className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition">
          Takvimi Yükle
        </button>
      </div>
    )
  }

  return (
    <div>
      {message && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${messageType === "success" ? "bg-green-800 text-green-200" : "bg-red-800 text-red-200"}`}>
          {message}
        </div>
      )}

      {/* Teacher: slot oluşturma formu */}
      {(role === "teacher" || role === "admin") && (
        <div className="bg-gray-800 rounded-xl p-5 mb-6">
          <h3 className="font-semibold mb-4 text-gray-300">Yeni Slot Ekle</h3>
          <div className="flex gap-3 flex-wrap items-end">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Tarih</label>
              <input
                type="date"
                className="bg-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newSlot.date}
                onChange={e => setNewSlot({ ...newSlot, date: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Başlangıç</label>
              <input
                type="time"
                className="bg-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newSlot.start_time}
                onChange={e => setNewSlot({ ...newSlot, start_time: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">Bitiş</label>
              <input
                type="time"
                className="bg-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newSlot.end_time}
                onChange={e => setNewSlot({ ...newSlot, end_time: e.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1 flex-1 min-w-36">
              <label className="text-xs text-gray-400">Not (isteğe bağlı)</label>
              <input
                className="bg-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Örn: Online ders"
                value={newSlot.note}
                onChange={e => setNewSlot({ ...newSlot, note: e.target.value })}
              />
            </div>
            <button onClick={createSlot} className="bg-green-600 hover:bg-green-700 text-white px-5 py-2 rounded-lg transition">
              Ekle
            </button>
          </div>
        </div>
      )}

      {/* Hafta navigasyonu */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={prevWeek} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition">
          ← Önceki
        </button>
        <span className="text-gray-300 font-medium">{weekLabel}</span>
        <button onClick={nextWeek} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition">
          Sonraki →
        </button>
      </div>

      {/* Haftalık grid */}
      <div className="grid grid-cols-7 gap-2">
        {weekDays.map((day, i) => {
          const dateStr = formatDate(day)
          const daySlots = slotsForDay(dateStr)
          const isToday = formatDate(new Date()) === dateStr

          return (
            <div key={dateStr} className={`bg-gray-800 rounded-xl p-3 min-h-32 ${isToday ? "ring-2 ring-blue-500" : ""}`}>
              <div className="text-center mb-2">
                <div className="text-xs text-gray-400">{DAYS_TR[i]}</div>
                <div className={`text-sm font-bold ${isToday ? "text-blue-400" : "text-white"}`}>{day.getDate()}</div>
              </div>

              <div className="flex flex-col gap-1">
                {daySlots.map(slot => {
                  const appt = appointmentForSlot(slot.id)

                  const history = historyForSlot(slot.id)
                  return (
                    <div key={slot.id} className={`rounded-lg p-2 text-xs ${slot.is_available ? "bg-blue-900 border border-blue-700" : "bg-gray-700 border border-gray-600"}`}>
                      <div className="font-semibold text-white">{slot.start_time}–{slot.end_time}</div>
                      {slot.note && <div className="text-gray-400 truncate">{slot.note}</div>}

                      {/* Teacher/Admin: aktif randevu detayı + onayla/reddet */}
                      {(role === "teacher" || role === "admin") && appt && (
                        <div className="mt-1">
                          <span className={`text-xs px-1.5 py-0.5 rounded-full ${statusBadge[appt.status]}`}>
                            {statusLabel[appt.status]}
                          </span>
                          <div className="text-gray-300 mt-0.5 truncate">{appt.student_username}</div>
                          {appt.student_note && <div className="text-gray-400 truncate italic">"{appt.student_note}"</div>}
                          {appt.status === "pending" && (
                            <div className="flex gap-1 mt-1">
                              <button onClick={() => updateAppointment(appt.id, "approved")} className="flex-1 bg-green-700 hover:bg-green-600 text-white rounded px-1 py-0.5">✓</button>
                              <button onClick={() => updateAppointment(appt.id, "rejected")} className="flex-1 bg-red-700 hover:bg-red-600 text-white rounded px-1 py-0.5">✗</button>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Admin: geçmiş randevular (iptal/reddedilen) */}
                      {role === "admin" && history.length > 0 && (
                        <div className="mt-1 border-t border-gray-600 pt-1">
                          <div className="text-gray-500 text-xs mb-0.5">Geçmiş ({history.length})</div>
                          {history.map(h => (
                            <div key={h.id} className="flex items-center justify-between gap-1">
                              <span className="text-gray-500 truncate">{h.student_username}</span>
                              <span className={`text-xs px-1 rounded-full ${statusBadge[h.status]}`}>{statusLabel[h.status]}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Teacher: boş slot sil */}
                      {(role === "teacher" || role === "admin") && !appt && (
                        <button onClick={() => deleteSlot(slot.id)} className="mt-1 w-full text-red-400 hover:text-red-300 text-xs">
                          Sil
                        </button>
                      )}

                      {/* Student: müsait slot talep et */}
                      {role === "student" && slot.is_available && (
                        requestingSlot === slot.id ? (
                          <div className="mt-1">
                            <input
                              className="w-full bg-gray-600 text-white rounded px-1 py-0.5 text-xs mb-1 focus:outline-none"
                              placeholder="Not (isteğe bağlı)"
                              value={requestNote}
                              onChange={e => setRequestNote(e.target.value)}
                            />
                            <div className="flex gap-1">
                              <button onClick={() => requestAppointment(slot.id)} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded px-1 py-0.5">Gönder</button>
                              <button onClick={() => setRequestingSlot(null)} className="flex-1 bg-gray-600 hover:bg-gray-500 text-white rounded px-1 py-0.5">İptal</button>
                            </div>
                          </div>
                        ) : (
                          <button onClick={() => setRequestingSlot(slot.id)} className="mt-1 w-full bg-blue-600 hover:bg-blue-700 text-white rounded px-1 py-0.5 text-xs">
                            Talep Et
                          </button>
                        )
                      )}

                      {/* Student: kendi randevusu */}
                      {role === "student" && appt && (
                        <div className="mt-1">
                          <span className={`text-xs px-1.5 py-0.5 rounded-full ${statusBadge[appt.status]}`}>
                            {statusLabel[appt.status]}
                          </span>
                          {appt.teacher_note && <div className="text-gray-400 mt-0.5 truncate italic">"{appt.teacher_note}"</div>}
                          {appt.status === "pending" && (
                            <button onClick={() => cancelAppointment(appt.id)} className="mt-1 w-full text-red-400 hover:text-red-300 text-xs">
                              İptal Et
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Admin: özet istatistikler */}
      {role === "admin" && appointments.length > 0 && (
        <div className="mt-8 grid grid-cols-5 gap-3">
          {[
            { label: "Toplam", value: counts.total, color: "bg-gray-700" },
            { label: "Bekliyor", value: counts.pending, color: "bg-yellow-900" },
            { label: "Onaylandı", value: counts.approved, color: "bg-green-900" },
            { label: "Reddedildi", value: counts.rejected, color: "bg-red-900" },
            { label: "İptal", value: counts.cancelled, color: "bg-gray-800 border border-gray-600" },
          ].map(stat => (
            <div key={stat.label} className={`${stat.color} rounded-xl p-4 text-center`}>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-gray-400 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Randevu listesi (teacher + admin) */}
      {(role === "teacher" || role === "admin") && appointments.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h3 className="text-gray-300 font-semibold">
              {role === "admin" ? "Tüm Randevular" : "Randevular"}
            </h3>
            {role === "admin" && (
              <div className="flex gap-1">
                {["all","pending","approved","rejected","cancelled"].map(s => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition ${statusFilter === s ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-300 hover:bg-gray-600"}`}
                  >
                    {s === "all" ? "Tümü" : statusLabel[s]}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="bg-gray-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-700 text-gray-300">
                  <th className="text-left px-4 py-3">Öğrenci</th>
                  <th className="text-left px-4 py-3">Tarih / Saat</th>
                  <th className="text-left px-4 py-3">Öğrenci Notu</th>
                  <th className="text-left px-4 py-3">Durum</th>
                  <th className="text-right px-4 py-3">İşlem</th>
                </tr>
              </thead>
              <tbody>
                {filteredAppointments.map(appt => {
                  const slot = slots.find(s => s.id === appt.slot_id)
                  const isInactive = ["rejected","cancelled"].includes(appt.status)
                  return (
                    <tr key={appt.id} className={`border-t border-gray-700 ${isInactive ? "opacity-50" : ""}`}>
                      <td className="px-4 py-3 text-white">{appt.student_username}</td>
                      <td className="px-4 py-3 text-gray-300">{slot ? `${slot.date} ${slot.start_time}–${slot.end_time}` : "—"}</td>
                      <td className="px-4 py-3 text-gray-400 italic max-w-xs truncate">{appt.student_note || "—"}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-1 rounded-full ${statusBadge[appt.status]}`}>
                          {statusLabel[appt.status]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex gap-2 justify-end">
                          {appt.status === "pending" && (
                            <>
                              <button onClick={() => updateAppointment(appt.id, "approved")} className="text-green-400 hover:text-green-300">Onayla</button>
                              <button onClick={() => updateAppointment(appt.id, "rejected")} className="text-red-400 hover:text-red-300">Reddet</button>
                            </>
                          )}
                          {role === "admin" && (
                            <button onClick={() => deleteAppointment(appt.id)} className="text-gray-500 hover:text-red-400">Sil</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {filteredAppointments.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-500">Bu durumda randevu yok.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ── DASHBOARD ───────────────────────────────────────────────────────

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
        <button onClick={() => setActiveTab("calendar")} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "calendar" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
          Takvim
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

        {/* Calendar */}
        {activeTab === "calendar" && (
          <CalendarTab token={token} username={username} role={role} />
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
