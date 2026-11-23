import { useState } from "react"
import { MoreHorizontal, Play, Plus } from "lucide-react"
import { toast } from "sonner"

import { MockNotice, PageHeading, Panel, toneClass } from "@/components/shared/common"
import { activityLog, adminUsers, etlSources } from "@/services/mock-data"

const TABS = ["Người dùng", "Nguồn dữ liệu & ETL", "Nhật ký"] as const
type Tab = (typeof TABS)[number]

type EtlStatus = "Thành công" | "Đang chạy" | "Cảnh báo"
const statusTone: Record<string, string> = {
  "Thành công": toneClass.positive,
  "Đang chạy": toneClass.info,
  "Cảnh báo": toneClass.neutral,
}

export default function QuanTriPage() {
  const [tab, setTab] = useState<Tab>("Người dùng")
  const [users, setUsers] = useState(adminUsers)
  const [etl, setEtl] = useState<{ name: string; status: string; time: string; count: string }[]>(etlSources)
  const [form, setForm] = useState({ name: "", email: "", role: "Viewer" })
  const [adding, setAdding] = useState(false)

  const addUser = () => {
    const name = form.name.trim()
    const email = form.email.trim()
    if (!name || !/^\S+@\S+\.\S+$/.test(email)) {
      toast.error("Vui lòng nhập họ tên và email hợp lệ.")
      return
    }
    if (users.some((user) => user.email.toLowerCase() === email.toLowerCase())) {
      toast.error("Email này đã tồn tại.")
      return
    }
    setUsers((current) => [...current, { name, email, role: form.role, active: true, last: "Chưa đăng nhập" }])
    setForm({ name: "", email: "", role: "Viewer" })
    setAdding(false)
    toast.success(`Đã thêm người dùng ${name} (minh họa).`)
  }

  const rerun = (name: string) => {
    setEtl((current) => current.map((row) => (row.name === name ? { ...row, status: "Đang chạy" satisfies EtlStatus } : row)))
    toast.success(`Đã xếp lịch chạy lại: ${name} (minh họa).`)
  }

  return (
    <>
      <PageHeading eyebrow="QUẢN LÝ HỆ THỐNG" title="Quản trị" description="Quản lý người dùng, nguồn dữ liệu và hoạt động hệ thống. Chỉ vai trò Admin truy cập được." />

      <div className="mb-4 flex items-center justify-between border-b border-border">
        <div className="flex gap-1">
          {TABS.map((item) => (
            <button
              key={item}
              onClick={() => setTab(item)}
              className={`border-b-2 px-4 py-3 text-xs font-medium ${tab === item ? "border-indigo-600 text-indigo-600" : "border-transparent text-muted-foreground"}`}
            >
              {item}
            </button>
          ))}
        </div>
        <MockNotice />
      </div>

      {tab === "Người dùng" && (
        <Panel
          title="Người dùng hệ thống"
          subtitle="Quản lý quyền truy cập và trạng thái tài khoản"
          action={
            <button onClick={() => setAdding((v) => !v)} className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700">
              <Plus size={14} />Thêm người dùng
            </button>
          }
        >
          {adding && (
            <div className="mb-5 grid grid-cols-1 gap-3 rounded-xl border border-border bg-muted/40 p-4 sm:grid-cols-[1fr_1.2fr_auto_auto]">
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Họ và tên" className="rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none focus:border-indigo-400" />
              <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="email@congty.vn" type="email" className="rounded-lg border border-border bg-background px-3 py-2 text-xs outline-none focus:border-indigo-400" />
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="rounded-lg border border-border bg-background px-3 py-2 text-xs">
                <option>Viewer</option>
                <option>Admin</option>
              </select>
              <button onClick={addUser} className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700">Lưu</button>
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-3 font-medium">Người dùng</th>
                  <th className="pb-3 font-medium">Vai trò</th>
                  <th className="pb-3 font-medium">Trạng thái</th>
                  <th className="pb-3 font-medium">Hoạt động gần nhất</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.email} className="border-t border-border">
                    <td className="py-3">
                      <div className="flex items-center gap-2.5">
                        <div className={`grid size-8 place-items-center rounded-full text-[10px] font-semibold ${toneClass.brand}`}>
                          {user.name.split(" ").map((part) => part[0]).slice(-2).join("").toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-foreground">{user.name}</div>
                          <div className="mt-0.5 text-[10px] text-muted-foreground">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <select
                        value={user.role}
                        onChange={(e) => setUsers((current) => current.map((u) => (u.email === user.email ? { ...u, role: e.target.value } : u)))}
                        className="rounded-md border border-border bg-background px-2 py-1 text-[10px]"
                      >
                        <option>Admin</option>
                        <option>Viewer</option>
                      </select>
                    </td>
                    <td>
                      <button
                        onClick={() => setUsers((current) => current.map((u) => (u.email === user.email ? { ...u, active: !u.active } : u)))}
                        title="Bấm để đổi trạng thái"
                        className={`rounded-full px-2 py-1 text-[9px] ${user.active ? toneClass.positive : toneClass.muted}`}
                      >
                        {user.active ? "Hoạt động" : "Vô hiệu hóa"}
                      </button>
                    </td>
                    <td className="text-muted-foreground">{user.last}</td>
                    <td><MoreHorizontal size={16} className="text-muted-foreground" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {tab === "Nguồn dữ liệu & ETL" && (
        <Panel title="Bộ thu thập dữ liệu" subtitle="Trạng thái các collector và lịch đồng bộ (n8n)">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] text-left text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-3 font-medium">Nguồn</th>
                  <th className="pb-3 font-medium">Trạng thái</th>
                  <th className="pb-3 font-medium">Lần chạy gần nhất</th>
                  <th className="pb-3 font-medium">Bản ghi</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {etl.map((row) => (
                  <tr key={row.name} className="border-t border-border">
                    <td className="py-4 font-semibold text-foreground">{row.name}</td>
                    <td><span className={`rounded-full px-2 py-1 text-[9px] ${statusTone[row.status] ?? toneClass.muted}`}>{row.status}</span></td>
                    <td className="text-muted-foreground">{row.time}</td>
                    <td>{row.count}</td>
                    <td>
                      <button
                        onClick={() => rerun(row.name)}
                        disabled={row.status === "Đang chạy"}
                        className="flex items-center gap-1 text-[10px] font-semibold text-indigo-600 disabled:opacity-40"
                      >
                        <Play size={12} />Chạy lại
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {tab === "Nhật ký" && (
        <Panel title="Nhật ký hoạt động" subtitle="Lịch sử thao tác và sự kiện hệ thống gần đây">
          <div className="flex flex-col">
            {activityLog.map((entry, index) => (
              <div key={entry.text} className="flex gap-3 border-t border-border py-4 first:border-0">
                <span className={`mt-1 size-2 rounded-full ${index === 0 ? "bg-indigo-500" : index === 1 ? "bg-emerald-500" : "bg-slate-300"}`} />
                <div className="flex-1 text-xs text-foreground/80">
                  {entry.text}
                  <div className="mt-1 text-[10px] text-muted-foreground">{entry.time}</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </>
  )
}
