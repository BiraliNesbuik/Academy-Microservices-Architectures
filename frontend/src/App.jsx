import { useState, useEffect } from "react"

const API = "http://localhost:8000"

const DAYS_TR = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
const MONTHS_TR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

// Geçerli dakika değerleri: 10'un katları + çeyrek saatler
const VALID_MINUTES = [0, 10, 15, 20, 30, 40, 45, 50]

function generateTimeOptions() {
  const options = []
  for (let h = 0; h < 24; h++) {
    for (const m of VALID_MINUTES) {
      const hh = String(h).padStart(2, "0")
      const mm = String(m).padStart(2, "0")
      options.push(`${hh}:${mm}`)
    }
  }
  return options
}

const TIME_OPTIONS = generateTimeOptions()

function addOneHour(timeStr) {
  if (!timeStr) return ""
  const [h, m] = timeStr.split(":").map(Number)
  const newH = (h + 1) % 24
  return `${String(newH).padStart(2, "0")}:${String(m).padStart(2, "0")}`
}

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return {}
  }
}

function formatDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}

function getMonthGrid(year, month) {
  // month: 0-indexed
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  // Pazartesi başlangıç: 0=Pzt,...,6=Paz
  const startOffset = (firstDay.getDay() + 6) % 7
  const days = []
  for (let i = 0; i < startOffset; i++) days.push(null)
  for (let d = 1; d <= lastDay.getDate(); d++) days.push(new Date(year, month, d))
  while (days.length % 7 !== 0) days.push(null)
  return days
}

// ── LANDING PAGE ────────────────────────────────────────────────────

function LandingPage({ onGoLogin }) {
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">

      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5">
        <span className="text-2xl font-bold text-blue-400">Dil Akademisi</span>
        <button
          onClick={onGoLogin}
          className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg font-medium transition text-sm"
        >
          Giriş Yap
        </button>
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center text-center px-6 py-20">
        <div className="inline-block bg-blue-900 border border-blue-700 text-blue-300 text-xs font-semibold px-4 py-1.5 rounded-full mb-6 tracking-wide uppercase">
          Özel Dil Eğitimi
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold text-white mb-6 leading-tight">
          Senin hızında,<br />
          <span className="text-blue-400">senin zamanında</span> öğren.
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mb-10">
          Birebir dersler, esnek saatler ve kişiselleştirilmiş içeriklerle
          hedefine en hızlı şekilde ulaş.
        </p>
        <button
          onClick={onGoLogin}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-semibold text-lg transition shadow-lg shadow-blue-900/40"
        >
          Hemen Başla →
        </button>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto w-full px-8 pb-20">
        {[
          { icon: "📅", title: "Kolay Randevu", desc: "İstediğin tarih ve saatte ders talebi oluştur, gerisi bize kalsın." },
          { icon: "📚", title: "Kişisel Müfredat", desc: "Seviyene ve hedeflerine göre hazırlanmış ders planı." },
          { icon: "🎯", title: "Hedef Odaklı", desc: "A1'den C2'ye, sınav hazırlığından günlük konuşmaya kadar." },
        ].map(f => (
          <div key={f.title} className="bg-gray-800 border border-gray-700 rounded-2xl p-6">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="text-white font-semibold mb-2">{f.title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="text-center text-gray-600 text-xs pb-6">
        © 2026 Dil Akademisi
      </div>
    </div>
  )
}

function Login({ onLogin, onBack }) {
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
        {onBack && (
          <button onClick={onBack} className="text-gray-500 hover:text-gray-300 text-sm mb-4 flex items-center gap-1 transition">
            ← Ana sayfaya dön
          </button>
        )}
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
  const today = new Date()
  const todayStr = formatDate(today)

  const [appointments, setAppointments] = useState([])
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())
  const [selectedDate, setSelectedDate] = useState(todayStr)
  const [message, setMessage] = useState("")
  const [messageType, setMessageType] = useState("success")
  const [statusFilter, setStatusFilter] = useState("all")

  // Öğrenci talep formu
  const [reqTime, setReqTime] = useState("")
  const [reqNote, setReqNote] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => { load() }, [])

  const showMsg = (msg, type = "success") => {
    setMessage(msg); setMessageType(type)
    setTimeout(() => setMessage(""), 3500)
  }

  const load = async () => {
    const res = await fetch(
      `${API}/booking/appointments${role === "student" ? `?student_username=${username}` : ""}`,
      { headers }
    )
    const data = await res.json()
    setAppointments(Array.isArray(data) ? data : [])
  }

  const submitRequest = async () => {
    if (!selectedDate || !reqTime) { showMsg("Tarih ve saat seçmelisiniz.", "error"); return }
    setSubmitting(true)
    const res = await fetch(`${API}/booking/appointments`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ date: selectedDate, start_time: reqTime, student_username: username, student_note: reqNote })
    })
    const data = await res.json()
    setSubmitting(false)
    if (res.ok) {
      showMsg("Randevu talebiniz gönderildi! En kısa sürede ulaşacağız.")
      setReqTime(""); setReqNote("")
      load()
    } else {
      showMsg(data.detail || "Bir hata oluştu.", "error")
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

  const deleteAppointment = async (apptId) => {
    const res = await fetch(`${API}/booking/appointments/${apptId}`, { method: "DELETE", headers })
    if (res.ok || res.status === 204) { showMsg("Randevu silindi"); load() }
  }

  const prevMonth = () => { if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1) } else setViewMonth(m => m - 1) }
  const nextMonth = () => { if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1) } else setViewMonth(m => m + 1) }

  const filteredAppointments = statusFilter === "all" ? appointments : appointments.filter(a => a.status === statusFilter)
  const apptsForDay = (dateStr) => appointments.filter(a => a.date === dateStr)

  const counts = {
    total:     appointments.length,
    pending:   appointments.filter(a => a.status === "pending").length,
    approved:  appointments.filter(a => a.status === "approved").length,
    rejected:  appointments.filter(a => a.status === "rejected").length,
    cancelled: appointments.filter(a => a.status === "cancelled").length,
  }

  const statusBadge = {
    pending:   "bg-yellow-800 text-yellow-300",
    approved:  "bg-green-800 text-green-300",
    rejected:  "bg-red-800 text-red-300",
    cancelled: "bg-gray-700 text-gray-400"
  }
  const statusLabel = { pending: "Bekliyor", approved: "Onaylandı", rejected: "Reddedildi", cancelled: "İptal" }

  const monthGrid = getMonthGrid(viewYear, viewMonth)

  // Öğrenci: yaklaşan onaylı dersler (bugün ve sonrası)
  const upcomingApproved = appointments
    .filter(a => a.status === "approved" && a.date >= todayStr)
    .sort((a, b) => a.date.localeCompare(b.date) || a.start_time.localeCompare(b.start_time))

  // Öğretmen/Admin: önümüzdeki 2 saat içindeki onaylı dersler
  const now = new Date()
  const in2h = new Date(now.getTime() + 2 * 60 * 60 * 1000)
  const upcomingTeacher = appointments
    .filter(a => {
      if (a.status !== "approved") return false
      const lessonTime = new Date(`${a.date}T${a.start_time}:00`)
      return lessonTime >= now && lessonTime <= in2h
    })
    .sort((a, b) => a.date.localeCompare(b.date) || a.start_time.localeCompare(b.start_time))

  return (
    <div className="flex flex-col gap-6">

      {message && (
        <div className={`px-4 py-3 rounded-lg text-sm font-medium ${messageType === "success" ? "bg-green-900 border border-green-700 text-green-200" : "bg-red-900 border border-red-700 text-red-200"}`}>
          {message}
        </div>
      )}

      {/* ── ÖĞRETMEN / ADMİN: 2 saat içindeki dersler ── */}
      {(role === "teacher" || role === "admin") && upcomingTeacher.length > 0 && (
        <div className="bg-orange-950 border border-orange-800 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🔔</span>
            <h3 className="text-orange-300 font-semibold">Yaklaşan Dersler</h3>
            <span className="text-xs bg-orange-900 border border-orange-700 text-orange-300 px-2 py-0.5 rounded-full ml-1">
              2 saat içinde
            </span>
          </div>
          <div className="flex flex-wrap gap-3">
            {upcomingTeacher.map(a => {
              const d = new Date(a.date + "T00:00:00")
              const lessonTime = new Date(`${a.date}T${a.start_time}:00`)
              const diffMins = Math.round((lessonTime - now) / 60000)
              return (
                <div key={a.id} className="bg-orange-900 border border-orange-700 rounded-xl px-4 py-3 flex flex-col gap-1 min-w-44">
                  <div className="text-orange-200 text-xs">{DAYS_TR[(d.getDay() + 6) % 7]}, {d.getDate()} {MONTHS_TR[d.getMonth()]}</div>
                  <div className="text-white font-bold tabular-nums text-lg">{a.start_time}</div>
                  <div className="text-orange-300 font-medium text-sm">{a.student_username}</div>
                  <div className="text-orange-400 text-xs">
                    {diffMins < 60 ? `${diffMins} dakika sonra` : `${Math.floor(diffMins / 60)} saat ${diffMins % 60} dk sonra`}
                  </div>
                  {a.student_note && <div className="text-orange-300 text-xs italic mt-1">"{a.student_note}"</div>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── ÖĞRENCİ: Yaklaşan onaylı dersler ── */}
      {role === "student" && upcomingApproved.length > 0 && (
        <div className="bg-green-950 border border-green-800 rounded-2xl p-5">
          <h3 className="text-green-300 font-semibold mb-3">Yaklaşan Derslerim</h3>
          <div className="flex flex-wrap gap-3">
            {upcomingApproved.map(a => {
              const d = new Date(a.date + "T00:00:00")
              return (
                <div key={a.id} className="bg-green-900 border border-green-700 rounded-xl px-4 py-3 flex flex-col gap-1">
                  <div className="text-green-200 text-xs">{DAYS_TR[(d.getDay() + 6) % 7]}, {d.getDate()} {MONTHS_TR[d.getMonth()]}</div>
                  <div className="text-white font-bold tabular-nums">{a.start_time}</div>
                  {a.teacher_note && <div className="text-green-300 text-xs italic">"{a.teacher_note}"</div>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="flex gap-6 items-start flex-wrap lg:flex-nowrap">

        {/* ── AYLIK TAKVİM ── */}
        <div className="bg-gray-800 border border-gray-700 rounded-2xl p-5 w-full lg:w-80 shrink-0">
          <div className="flex items-center justify-between mb-4">
            <button onClick={prevMonth} className="text-gray-400 hover:text-white w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-700 transition text-lg">‹</button>
            <span className="text-white font-semibold">{MONTHS_TR[viewMonth]} {viewYear}</span>
            <button onClick={nextMonth} className="text-gray-400 hover:text-white w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-700 transition text-lg">›</button>
          </div>

          <div className="grid grid-cols-7 mb-1">
            {DAYS_TR.map(d => <div key={d} className="text-center text-xs font-medium text-gray-500 py-1">{d}</div>)}
          </div>

          <div className="grid grid-cols-7 gap-y-1">
            {monthGrid.map((day, idx) => {
              if (!day) return <div key={idx} />
              const dateStr = formatDate(day)
              const dayAppts = apptsForDay(dateStr)
              const isToday    = dateStr === todayStr
              const isSelected = dateStr === selectedDate
              const hasPending  = dayAppts.some(a => a.status === "pending")
              const hasApproved = dayAppts.some(a => a.status === "approved")
              return (
                <button key={dateStr}
                  onClick={() => { setSelectedDate(dateStr); setReqTime("") }}
                  className={`relative flex flex-col items-center justify-center h-9 w-full rounded-lg text-sm font-medium transition
                    ${isSelected ? "bg-blue-600 text-white" : isToday ? "border border-blue-500 text-blue-400" : "text-gray-300 hover:bg-gray-700"}`}>
                  {day.getDate()}
                  {dayAppts.length > 0 && !isSelected && (
                    <div className="flex gap-0.5 absolute bottom-1">
                      {hasPending  && <span className="w-1 h-1 rounded-full bg-yellow-400" />}
                      {hasApproved && <span className="w-1 h-1 rounded-full bg-green-400" />}
                    </div>
                  )}
                </button>
              )
            })}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-700 flex flex-col gap-1.5">
            {[
              { color: "bg-yellow-400", label: "Bekleyen talep" },
              { color: "bg-green-400",  label: "Onaylanan randevu" },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2 text-xs text-gray-400">
                <span className={`w-2 h-2 rounded-full ${item.color}`} />
                {item.label}
              </div>
            ))}
          </div>
        </div>

        {/* ── SAĞ PANEL ── */}
        <div className="flex-1 flex flex-col gap-4">

          {/* ÖĞRENCİ: Randevu talep formu */}
          {role === "student" && (
            <div className="bg-gray-800 border border-gray-700 rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-1">Ders Talebi Oluştur</h3>
              <p className="text-gray-400 text-sm mb-5">Uygun olduğun tarihi ve saati seç, talebini gönder. Sana en kısa sürede ulaşacağız.</p>
              <div className="flex gap-3 flex-wrap items-end">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-500">Seçili Tarih</label>
                  <div className="bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 text-sm tabular-nums min-w-32 text-center font-medium">
                    {selectedDate}
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-500">Saat</label>
                  <select
                    className="bg-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                    value={reqTime}
                    onChange={e => setReqTime(e.target.value)}
                  >
                    <option value="">Saat seçin</option>
                    {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1 flex-1 min-w-40">
                  <label className="text-xs text-gray-500">Not</label>
                  <input
                    className="bg-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                    placeholder="Konu, seviye... (isteğe bağlı)"
                    value={reqNote}
                    onChange={e => setReqNote(e.target.value)}
                  />
                </div>
                <button
                  onClick={submitRequest}
                  disabled={submitting}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg text-sm font-medium transition"
                >
                  {submitting ? "Gönderiliyor..." : "Talep Gönder"}
                </button>
              </div>
              <p className="text-gray-600 text-xs mt-4">← Soldan tarih seçebilirsin</p>
            </div>
          )}

          {/* ÖĞRENCİ: Kendi talepleri */}
          {role === "student" && (
            <div>
              <h3 className="text-white font-semibold mb-3">Taleplerim</h3>
              {appointments.length === 0 ? (
                <div className="text-center py-10 text-gray-500 bg-gray-800 border border-gray-700 rounded-2xl text-sm">
                  Henüz bir ders talebi göndermediniz.
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {[...appointments].sort((a, b) => b.date.localeCompare(a.date)).map(appt => (
                    <div key={appt.id} className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center justify-between gap-4 flex-wrap">
                      <div>
                        <div className="text-white font-semibold tabular-nums">{appt.date} — {appt.start_time}</div>
                        {appt.student_note && <div className="text-gray-400 text-xs mt-0.5 italic">"{appt.student_note}"</div>}
                        {appt.teacher_note && <div className="text-blue-300 text-xs mt-1">Öğretmen: "{appt.teacher_note}"</div>}
                      </div>
                      <span className={`text-xs px-2.5 py-1 rounded-full shrink-0 ${statusBadge[appt.status]}`}>
                        {statusLabel[appt.status]}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ÖĞRETMEN / ADMİN: Talep listesi */}
          {(role === "teacher" || role === "admin") && (
            <>
              {role === "admin" && (
                <div className="grid grid-cols-5 gap-3">
                  {[
                    { label: "Toplam",     value: counts.total,     color: "bg-gray-700 border-gray-600" },
                    { label: "Bekliyor",   value: counts.pending,   color: "bg-yellow-950 border-yellow-800" },
                    { label: "Onaylandı",  value: counts.approved,  color: "bg-green-950 border-green-800" },
                    { label: "Reddedildi", value: counts.rejected,  color: "bg-red-950 border-red-900" },
                    { label: "İptal",      value: counts.cancelled, color: "bg-gray-800 border-gray-700" },
                  ].map(stat => (
                    <div key={stat.label} className={`${stat.color} border rounded-xl p-4 text-center`}>
                      <div className="text-3xl font-bold text-white">{stat.value}</div>
                      <div className="text-xs text-gray-400 mt-1">{stat.label}</div>
                    </div>
                  ))}
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                  <h3 className="text-white font-semibold text-lg">Ders Talepleri</h3>
                  <div className="flex gap-1 flex-wrap">
                    {["all","pending","approved","rejected","cancelled"].map(s => (
                      <button key={s} onClick={() => setStatusFilter(s)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border
                          ${statusFilter === s ? "bg-blue-600 border-blue-500 text-white" : "bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700"}`}>
                        {s === "all" ? "Tümü" : statusLabel[s]}
                        {s !== "all" && <span className="ml-1 opacity-60">({counts[s]})</span>}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="bg-gray-800 border border-gray-700 rounded-2xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700 text-gray-400 text-xs uppercase tracking-wide">
                        <th className="text-left px-5 py-3">Öğrenci</th>
                        <th className="text-left px-5 py-3">Tarih / Saat</th>
                        <th className="text-left px-5 py-3">Not</th>
                        <th className="text-left px-5 py-3">Durum</th>
                        <th className="text-right px-5 py-3">İşlem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAppointments.map(appt => {
                        const isInactive = ["rejected","cancelled"].includes(appt.status)
                        return (
                          <tr key={appt.id} className={`border-t border-gray-700 ${isInactive ? "opacity-40" : ""}`}>
                            <td className="px-5 py-4 text-white font-medium">{appt.student_username}</td>
                            <td className="px-5 py-4 text-gray-300 tabular-nums">{appt.date} {appt.start_time}</td>
                            <td className="px-5 py-4 text-gray-400 italic max-w-xs truncate">{appt.student_note || "—"}</td>
                            <td className="px-5 py-4">
                              <span className={`text-xs px-2.5 py-1 rounded-full ${statusBadge[appt.status]}`}>{statusLabel[appt.status]}</span>
                            </td>
                            <td className="px-5 py-4 text-right">
                              <div className="flex gap-2 justify-end">
                                {appt.status === "pending" && (
                                  <>
                                    <button onClick={() => updateAppointment(appt.id, "approved")} className="text-green-400 hover:text-green-300 text-sm">Onayla</button>
                                    <button onClick={() => updateAppointment(appt.id, "rejected")} className="text-red-400 hover:text-red-300 text-sm">Reddet</button>
                                  </>
                                )}
                                {role === "admin" && (
                                  <button onClick={() => deleteAppointment(appt.id)} className="text-gray-500 hover:text-red-400 text-sm">Sil</button>
                                )}
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                      {filteredAppointments.length === 0 && (
                        <tr><td colSpan={5} className="px-5 py-10 text-center text-gray-500">Bu durumda talep yok.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
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
  }

  const loadExams = async () => {
    const res = await fetch(`${API}/exam/exams`, { headers })
    const data = await res.json()
    setExams(Array.isArray(data) ? data : [])
  }

  const loadUsers = async () => {
    const res = await fetch(`${API}/auth/users`, { headers })
    const data = await res.json()
    setUsers(Array.isArray(data) ? data : [])
  }

  const loadCart = async () => {
    const res = await fetch(`${API}/course/courses/cart?username=${username}`, { headers })
    const data = await res.json()
    setCart(data.items || [])
  }

  const loadPurchases = async () => {
    const res = await fetch(`${API}/course/courses/my-purchases?username=${username}`, { headers })
    const data = await res.json()
    setPurchases(Array.isArray(data) ? data : [])
  }

  useEffect(() => {
    if (activeTab === "courses") loadCourses()
    else if (activeTab === "exams") loadExams()
    else if (activeTab === "users") loadUsers()
    else if (activeTab === "cart") loadCart()
    else if (activeTab === "purchases") loadPurchases()
  }, [activeTab])

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
        <button onClick={() => setActiveTab("courses")} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "courses" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
          Kurslar
        </button>
        <button onClick={() => setActiveTab("exams")} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "exams" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
          Sınavlar
        </button>
        <button onClick={() => setActiveTab("calendar")} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "calendar" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
          Takvim
        </button>
        {role === "student" && (
          <>
            <button onClick={() => setActiveTab("cart")} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "cart" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
              Sepet {cart.length > 0 && <span className="ml-1 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{cart.length}</span>}
            </button>
            <button onClick={() => setActiveTab("purchases")} className={`px-5 py-2 rounded-lg font-medium transition ${activeTab === "purchases" ? "bg-blue-600" : "bg-gray-700 hover:bg-gray-600"}`}>
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
            {courses.length === 0 && <p className="text-gray-500">Henüz kurs bulunmuyor.</p>}
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
            {exams.length === 0 && <p className="text-gray-500">Henüz sınav bulunmuyor.</p>}
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
  const [page, setPage] = useState("landing") // "landing" | "login"

  const handleLogin = (token, username, role) => {
    setToken(token)
    setUsername(username)
    setRole(role)
    setPage("dashboard")
  }

  const handleLogout = () => {
    setToken(null)
    setUsername("")
    setRole("")
    setPage("landing")
  }

  if (token) return <Dashboard token={token} username={username} role={role} onLogout={handleLogout} />
  if (page === "login") return <Login onLogin={handleLogin} onBack={() => setPage("landing")} />
  return <LandingPage onGoLogin={() => setPage("login")} />
}
