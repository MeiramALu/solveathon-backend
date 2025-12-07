'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Activity, AlertTriangle, CheckCircle, Thermometer, Zap, X } from 'lucide-react'

// --- 1. Типы данных ---
type MachineStatus = 'running' | 'warning' | 'error'

interface Machine {
    id: string
    name: string
    status: MachineStatus
    location: string
    lastMaintenance: string
}

// --- 2. Генерация данных (Mock Backend) ---
const MACHINES: Machine[] = Array.from({ length: 10 }).map((_, i) => ({
    id: `M-${100 + i}`,
    name: `Weaving Unit #${i + 1}`,
    status: i === 3 ? 'warning' : i === 7 ? 'error' : 'running', // Симуляция проблемных машин
    location: `Zone ${String.fromCharCode(65 + (i % 3))}`, // Zone A, B, C
    lastMaintenance: '2025-10-12'
}))

// --- 3. Компонент "Живого Графика" ---
function LiveMonitor({ machine, onClose }: { machine: Machine; onClose: () => void }) {
    // Состояние для хранения истории данных графика
    const [data, setData] = useState<{ time: string; temp: number; vibration: number }[]>([])

    // Эмуляция живых данных (WebSocket simulation)
    useEffect(() => {
        // Заполняем начальными данными
        const initialData = Array.from({ length: 20 }).map((_, i) => ({
            time: new Date(Date.now() - (20 - i) * 1000).toLocaleTimeString(),
            temp: 60 + Math.random() * 10,
            vibration: 2 + Math.random()
        }))
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setData(initialData)

        // Запускаем интервал обновления (каждую секунду)
        const interval = setInterval(() => {
            setData(prev => {
                const now = new Date()
                const newPoint = {
                    time: now.toLocaleTimeString(),
                    // Генерируем случайные скачки
                    temp: 60 + Math.random() * 15 + (machine.status === 'warning' ? 20 : 0),
                    vibration: 2 + Math.random() * 2 + (machine.status === 'error' ? 5 : 0)
                }
                // Оставляем только последние 20 точек
                return [...prev.slice(1), newPoint]
            })
        }, 1000)

        return () => clearInterval(interval)
    }, [machine])

    // Получаем текущие показатели (последняя точка)
    const current = data[data.length - 1] || { temp: 0, vibration: 0 }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white w-full max-w-4xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">

                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-slate-100 bg-slate-50">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                            {machine.name}
                            <span className={`px-2 py-0.5 rounded-full text-xs uppercase font-bold border ${machine.status === 'running' ? 'bg-green-100 text-green-700 border-green-200' :
                                    machine.status === 'warning' ? 'bg-orange-100 text-orange-700 border-orange-200' :
                                        'bg-red-100 text-red-700 border-red-200'
                                }`}>
                                {machine.status}
                            </span>
                        </h2>
                        <p className="text-slate-500 text-sm">ID: {machine.id} • Location: {machine.location}</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition">
                        <X className="w-6 h-6 text-slate-500" />
                    </button>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-2 gap-4 p-6 bg-white">
                    <div className="p-4 rounded-xl bg-red-50 border border-red-100">
                        <div className="flex items-center gap-2 text-red-600 mb-2">
                            <Thermometer className="w-5 h-5" />
                            <span className="font-semibold">Temperature</span>
                        </div>
                        <div className="text-3xl font-bold text-slate-800">
                            {current.temp.toFixed(1)}°C
                        </div>
                        <div className="text-xs text-slate-500 mt-1">Normal range: 50-80°C</div>
                    </div>

                    <div className="p-4 rounded-xl bg-blue-50 border border-blue-100">
                        <div className="flex items-center gap-2 text-blue-600 mb-2">
                            <Activity className="w-5 h-5" />
                            <span className="font-semibold">Vibration (Shake)</span>
                        </div>
                        <div className="text-3xl font-bold text-slate-800">
                            {current.vibration.toFixed(2)} G
                        </div>
                        <div className="text-xs text-slate-500 mt-1">Normal range: 0-4 G</div>
                    </div>
                </div>

                {/* Charts Area */}
                <div className="p-6 pt-0 h-[300px] w-full">
                    <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase tracking-wider">Real-time Telemetry</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                            <XAxis dataKey="time" hide />
                            <YAxis yAxisId="left" domain={[0, 120]} orientation="left" stroke="#ef4444" label={{ value: 'Temp (°C)', angle: -90, position: 'insideLeft' }} />
                            <YAxis yAxisId="right" domain={[0, 10]} orientation="right" stroke="#3b82f6" label={{ value: 'Vibration (G)', angle: 90, position: 'insideRight' }} />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            />
                            <Legend />
                            <Line yAxisId="left" type="monotone" dataKey="temp" name="Temperature" stroke="#ef4444" strokeWidth={3} dot={false} isAnimationActive={false} />
                            <Line yAxisId="right" type="monotone" dataKey="vibration" name="Vibration" stroke="#3b82f6" strokeWidth={3} dot={false} isAnimationActive={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

// --- 4. Основной компонент Таблицы ---
export default function FactoryModule() {
    const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null)

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                <h2 className="font-semibold text-slate-800 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-600" />
                    Production Line Status
                </h2>
                <div className="text-sm text-slate-500">Total Machines: {MACHINES.length}</div>
            </div>

            {/* Table */}
            <div className="overflow-auto flex-1">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
                        <tr>
                            <th className="p-4">Machine Name</th>
                            <th className="p-4">Status</th>
                            <th className="p-4 hidden md:table-cell">Location</th>
                            <th className="p-4 hidden md:table-cell">Last Maintenance</th>
                            <th className="p-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {MACHINES.map((machine) => (
                            <tr
                                key={machine.id}
                                onClick={() => setSelectedMachine(machine)}
                                className="hover:bg-slate-50 cursor-pointer transition-colors group"
                            >
                                <td className="p-4 font-medium text-slate-800">
                                    {machine.name}
                                    <div className="text-xs text-slate-400 font-normal">{machine.id}</div>
                                </td>
                                <td className="p-4">
                                    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${machine.status === 'running' ? 'bg-green-50 text-green-700 border-green-200' :
                                            machine.status === 'warning' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                                                'bg-red-50 text-red-700 border-red-200'
                                        }`}>
                                        {machine.status === 'running' && <CheckCircle className="w-3 h-3" />}
                                        {machine.status === 'warning' && <AlertTriangle className="w-3 h-3" />}
                                        {machine.status === 'error' && <Activity className="w-3 h-3" />}
                                        {machine.status.toUpperCase()}
                                    </div>
                                </td>
                                <td className="p-4 text-slate-500 hidden md:table-cell">{machine.location}</td>
                                <td className="p-4 text-slate-500 hidden md:table-cell">{machine.lastMaintenance}</td>
                                <td className="p-4 text-right">
                                    <button className="text-blue-600 font-medium text-xs bg-blue-50 px-3 py-1.5 rounded-md hover:bg-blue-100 transition">
                                        View Live
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal for Chart */}
            {selectedMachine && (
                <LiveMonitor
                    machine={selectedMachine}
                    onClose={() => setSelectedMachine(null)}
                />
            )}
        </div>
    )
}