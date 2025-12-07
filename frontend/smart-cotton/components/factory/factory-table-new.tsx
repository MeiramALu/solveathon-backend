'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Activity, Thermometer, X, TrendingUp, Gauge } from 'lucide-react'

// API Base URL
const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/factory`

interface Machine {
    id: number
    name: string
    machine_type: string
    status: string
    last_temp: number
    last_vibration: number
    last_motor_load: number
    last_humidity: number
    timestamp: string
}

interface MaintenanceLog {
    id: number
    machine: number
    machine_name?: string
    timestamp: string
    description: string
    is_prediction: boolean
    probability_failure: number
}

// Live Chart Modal Component
function LiveChartModal({ machine, onClose, isSimulating }: { machine: Machine; onClose: () => void; isSimulating: boolean }) {
    const [chartData, setChartData] = useState<Array<{
        time: string
        temp: number
        vibration: number
        motorLoad: number
        humidity: number
    }>>(() => {
        // Use machine data if available, otherwise generate random starting values
        const initialTemp = machine.last_temp || 70 + Math.random() * 10
        const initialVib = machine.last_vibration || 0.15 + Math.random() * 0.1
        const initialLoad = machine.last_motor_load || 45 + Math.random() * 15
        const initialHumidity = machine.last_humidity || 55 + Math.random() * 10

        return [{
            time: new Date().toLocaleTimeString(),
            temp: initialTemp,
            vibration: initialVib,
            motorLoad: initialLoad,
            humidity: initialHumidity
        }]
    })

    useEffect(() => {
        // Always run simulation for the modal charts
        const interval = setInterval(() => {
            setChartData(prev => {
                const tempVariation = (Math.random() - 0.5) * 8
                const vibVariation = (Math.random() - 0.5) * 0.08
                const loadVariation = (Math.random() - 0.5) * 12
                const humidityVariation = (Math.random() - 0.5) * 8

                const lastData = prev[prev.length - 1]
                const newData = {
                    time: new Date().toLocaleTimeString(),
                    temp: Math.max(50, Math.min(100, lastData.temp + tempVariation)),
                    vibration: Math.max(0.05, Math.min(0.5, lastData.vibration + vibVariation)),
                    motorLoad: Math.max(20, Math.min(80, lastData.motorLoad + loadVariation)),
                    humidity: Math.max(40, Math.min(80, lastData.humidity + humidityVariation))
                }

                return [...prev.slice(-19), newData] // Keep last 20 points
            })
        }, 1500) // Update every 1.5 seconds

        return () => clearInterval(interval)
    }, [machine])

    const latestData = chartData[chartData.length - 1] || {
        time: new Date().toLocaleTimeString(),
        temp: machine.last_temp,
        vibration: machine.last_vibration,
        motorLoad: machine.last_motor_load,
        humidity: machine.last_humidity
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white w-full max-w-6xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200 max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-slate-100 bg-slate-50 sticky top-0 z-10">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                            {machine.name}
                            {isSimulating && (
                                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 border border-green-200 flex items-center gap-1.5">
                                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                    Live
                                </span>
                            )}
                        </h2>
                        <p className="text-slate-500 text-sm">Type: {machine.machine_type} • ID: {machine.id}</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition">
                        <X className="w-6 h-6 text-slate-500" />
                    </button>
                </div>

                {/* Current Metrics */}
                <div className="grid grid-cols-4 gap-4 p-6 bg-white">
                    <div className={`p-4 rounded-xl border transition-all ${(latestData?.temp ?? 0) > 85
                        ? 'bg-red-100 border-red-300 animate-pulse'
                        : 'bg-red-50 border-red-100'
                        }`}>
                        <div className="flex items-center gap-2 text-red-600 mb-2">
                            <Thermometer className="w-5 h-5" />
                            <span className="font-semibold text-sm">Temperature</span>
                            {(latestData?.temp ?? 0) > 85 && <span className="text-xs">🔥</span>}
                        </div>
                        <div className={`text-2xl font-bold ${(latestData?.temp ?? 0) > 85 ? 'text-red-700' : 'text-slate-800'
                            }`}>
                            {latestData?.temp?.toFixed(1) ?? '0.0'}°C
                        </div>
                        {(latestData?.temp ?? 0) > 85 && (
                            <div className="text-xs text-red-600 font-medium mt-1">⚠️ DANGER ZONE</div>
                        )}
                    </div>

                    <div className={`p-4 rounded-xl border transition-all ${(latestData?.vibration ?? 0) > 0.35
                        ? 'bg-blue-100 border-blue-300 animate-pulse'
                        : 'bg-blue-50 border-blue-100'
                        }`}>
                        <div className="flex items-center gap-2 text-blue-600 mb-2">
                            <Activity className="w-5 h-5" />
                            <span className="font-semibold text-sm">Vibration</span>
                            {(latestData?.vibration ?? 0) > 0.35 && <span className="text-xs">⚡</span>}
                        </div>
                        <div className={`text-2xl font-bold ${(latestData?.vibration ?? 0) > 0.35 ? 'text-blue-700' : 'text-slate-800'
                            }`}>
                            {latestData?.vibration?.toFixed(3) ?? '0.000'} G
                        </div>
                        {(latestData?.vibration ?? 0) > 0.35 && (
                            <div className="text-xs text-blue-600 font-medium mt-1">⚠️ HIGH VIBRATION</div>
                        )}
                    </div>

                    <div className={`p-4 rounded-xl border transition-all ${(latestData?.motorLoad ?? 0) > 75
                        ? 'bg-purple-100 border-purple-300 animate-pulse'
                        : 'bg-purple-50 border-purple-100'
                        }`}>
                        <div className="flex items-center gap-2 text-purple-600 mb-2">
                            <Gauge className="w-5 h-5" />
                            <span className="font-semibold text-sm">Motor Load</span>
                            {(latestData?.motorLoad ?? 0) > 75 && <span className="text-xs">⚙️</span>}
                        </div>
                        <div className={`text-2xl font-bold ${(latestData?.motorLoad ?? 0) > 75 ? 'text-purple-700' : 'text-slate-800'
                            }`}>
                            {latestData?.motorLoad?.toFixed(1) ?? '0.0'}%
                        </div>
                        {(latestData?.motorLoad ?? 0) > 75 && (
                            <div className="text-xs text-purple-600 font-medium mt-1">⚠️ OVERLOAD</div>
                        )}
                    </div>

                    <div className="p-4 rounded-xl bg-cyan-50 border border-cyan-100">
                        <div className="flex items-center gap-2 text-cyan-600 mb-2">
                            <TrendingUp className="w-5 h-5" />
                            <span className="font-semibold text-sm">Humidity</span>
                        </div>
                        <div className="text-2xl font-bold text-slate-800">
                            {latestData?.humidity?.toFixed(1) ?? '0.0'}%
                        </div>
                        <div className="text-xs text-cyan-600 mt-1">✓ Normal Range</div>
                    </div>
                </div>

                {/* Live Charts */}
                {chartData.length > 0 ? (
                    <div className="p-6 space-y-6">
                        {!isSimulating && chartData.length === 1 && (
                            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
                                💡 <strong>Tip:</strong> Click &quot;Start Simulation&quot; above to see real-time data updates
                            </div>
                        )}

                        <div className="h-72">
                            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                                <span>Temperature & Vibration</span>
                                <span className="text-xs text-green-600 flex items-center gap-1">
                                    <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                                    Live
                                </span>
                            </h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="left" stroke="#ef4444" label={{ value: 'Temp (°C)', angle: -90, position: 'insideLeft' }} domain={[50, 100]} />
                                    <YAxis yAxisId="right" orientation="right" stroke="#3b82f6" label={{ value: 'Vibration (G)', angle: 90, position: 'insideRight' }} domain={[0, 0.5]} />
                                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                    <Legend />
                                    <Line yAxisId="left" type="monotone" dataKey="temp" name="Temperature" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
                                    <Line yAxisId="right" type="monotone" dataKey="vibration" name="Vibration" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                                </LineChart>
                            </ResponsiveContainer>
                            <div className="mt-2 flex gap-4 text-xs">
                                <div className="flex items-center gap-1">
                                    <div className="w-3 h-0.5 bg-red-500"></div>
                                    <span className="text-slate-600">🔥 Temp Danger: &gt;85°C</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <div className="w-3 h-0.5 bg-blue-500"></div>
                                    <span className="text-slate-600">⚡ Vib Danger: &gt;0.35G</span>
                                </div>
                            </div>
                        </div>

                        <div className="h-72">
                            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                                <span>Motor Load & Humidity</span>
                                <span className="text-xs text-green-600 flex items-center gap-1">
                                    <span className="inline-block w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                                    Live
                                </span>
                            </h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="left" stroke="#8b5cf6" label={{ value: 'Load (%)', angle: -90, position: 'insideLeft' }} domain={[20, 80]} />
                                    <YAxis yAxisId="right" orientation="right" stroke="#06b6d4" label={{ value: 'Humidity (%)', angle: 90, position: 'insideRight' }} domain={[40, 80]} />
                                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                    <Legend />
                                    <Line yAxisId="left" type="monotone" dataKey="motorLoad" name="Motor Load" stroke="#8b5cf6" strokeWidth={2} dot={false} isAnimationActive={false} />
                                    <Line yAxisId="right" type="monotone" dataKey="humidity" name="Humidity" stroke="#06b6d4" strokeWidth={2} dot={false} isAnimationActive={false} />
                                </LineChart>
                            </ResponsiveContainer>
                            <div className="mt-2 flex gap-4 text-xs">
                                <div className="flex items-center gap-1">
                                    <div className="w-3 h-0.5 bg-purple-500"></div>
                                    <span className="text-slate-600">⚙️ Load Danger: &gt;75%</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <div className="w-3 h-0.5 bg-cyan-500"></div>
                                    <span className="text-slate-600">💧 Humidity OK: 40-80%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="p-12 text-center text-slate-500">
                        <Activity className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                        <p>No telemetry data available</p>
                        <p className="text-sm mt-1">Start simulation to generate data</p>
                    </div>
                )}
            </div>
        </div>
    )
}

// Main Component
export default function FactoryModule() {
    const [machines, setMachines] = useState<Machine[]>([])
    const [logs, setLogs] = useState<MaintenanceLog[]>([])
    const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null)
    const [loading, setLoading] = useState(true)
    const [currentPage, setCurrentPage] = useState(1)
    const [isSimulating, setIsSimulating] = useState(false)
    const logsPerPage = 50

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 5000) // Refresh every 5 seconds
        return () => clearInterval(interval)
    }, [])

    // Simulation effect
    useEffect(() => {
        if (!isSimulating) return

        const simulationInterval = setInterval(() => {
            // Simulate new sensor readings for machines
            setMachines(prevMachines =>
                prevMachines.map(machine => {
                    const tempVariation = (Math.random() - 0.5) * 10
                    const vibVariation = (Math.random() - 0.5) * 0.1
                    const loadVariation = (Math.random() - 0.5) * 15
                    const humidityVariation = (Math.random() - 0.5) * 10

                    const newTemp = Math.max(50, Math.min(100, machine.last_temp + tempVariation))
                    const newVib = Math.max(0.05, Math.min(0.5, machine.last_vibration + vibVariation))
                    const newLoad = Math.max(20, Math.min(80, machine.last_motor_load + loadVariation))
                    const newHumidity = Math.max(40, Math.min(80, machine.last_humidity + humidityVariation))

                    // Determine status based on thresholds
                    let newStatus = 'ONLINE'
                    if (newTemp > 85 || newVib > 0.35 || newLoad > 75) {
                        newStatus = 'ERROR'
                    } else if (newTemp > 78 || newVib > 0.25 || newLoad > 65) {
                        newStatus = 'WARNING'
                    }

                    return {
                        ...machine,
                        last_temp: newTemp,
                        last_vibration: newVib,
                        last_motor_load: newLoad,
                        last_humidity: newHumidity,
                        status: newStatus,
                        timestamp: new Date().toISOString()
                    }
                })
            )

            // Simulate new maintenance log (10% chance)
            if (Math.random() < 0.1 && machines.length > 0) {
                const randomMachine = machines[Math.floor(Math.random() * machines.length)]
                const riskLevel = Math.random() * 100
                const statusText = riskLevel > 70 ? 'Требуется техобслуживание' :
                    riskLevel > 40 ? 'Повышенный износ' :
                        'Показатели в норме'

                const newLog: MaintenanceLog = {
                    id: Date.now(),
                    machine: randomMachine.id,
                    machine_name: randomMachine.name,
                    timestamp: new Date().toISOString(),
                    description: `Simulated: ${statusText} (T=${randomMachine.last_temp.toFixed(2)}°C, Vib=${randomMachine.last_vibration.toFixed(3)}, Load=${randomMachine.last_motor_load.toFixed(1)}%)`,
                    is_prediction: true,
                    probability_failure: riskLevel
                }

                setLogs(prevLogs => [newLog, ...prevLogs].slice(0, 500)) // Keep last 500 logs
            }
        }, 3000) // Update every 3 seconds

        return () => clearInterval(simulationInterval)
    }, [isSimulating, machines])

    const fetchData = async () => {
        try {
            const [machinesRes, logsRes] = await Promise.all([
                fetch(`${API_URL}/machines/`, {
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' }
                }),
                fetch(`${API_URL}/maintenance/?limit=500`, {
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' }
                })
            ])

            if (!machinesRes.ok || !logsRes.ok) {
                console.error('API Error:', machinesRes.status, logsRes.status)
                setLoading(false)
                return
            }

            const machinesData = await machinesRes.json()
            const logsData = await logsRes.json()

            // Enrich logs with machine names
            const enrichedLogs = logsData.map((log: MaintenanceLog) => ({
                ...log,
                machine_name: machinesData.find((m: Machine) => m.id === log.machine)?.name || `Machine ${log.machine}`
            }))

            setMachines(machinesData)
            setLogs(enrichedLogs)
        } catch (error) {
            console.error('Error fetching data:', error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return <div className="flex items-center justify-center h-full"><div className="text-slate-500">Loading factory data...</div></div>
    }

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
            {/* Header with Tabs */}
            <div className="p-4 border-b border-slate-200 bg-slate-50">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="font-semibold text-slate-800 text-lg">Smart Factory Monitor</h2>
                        <div className="text-sm text-slate-500 mt-1">
                            {machines.length} Machines • {logs.length} Logs
                        </div>
                    </div>
                </div>

                <div className="text-sm text-slate-600 font-medium">
                    Click on any machine to view live telemetry charts
                </div>
            </div>

            {/* Content */}
            <div className="overflow-auto flex-1">
                {/* Grouped by Machine Table */}
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-700 font-medium border-b border-slate-200 sticky top-0">
                        <tr>
                            <th className="p-4">Machine</th>
                            <th className="p-4">Status</th>
                            <th className="p-4 text-center">Total Logs</th>
                            <th className="p-4 text-center">Avg Risk</th>
                            <th className="p-4">Latest Metrics</th>
                            <th className="p-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {Object.entries(
                            logs.reduce((acc, log) => {
                                if (!acc[log.machine]) {
                                    acc[log.machine] = []
                                }
                                acc[log.machine].push(log)
                                return acc
                            }, {} as Record<number, MaintenanceLog[]>)
                        ).map(([machineId, machineLogs]) => {
                            const machine = machines.find(m => m.id === Number(machineId)) || {
                                id: Number(machineId),
                                name: machineLogs[0]?.machine_name || `Machine ${machineId}`,
                                machine_type: 'Unknown',
                                status: 'OFFLINE',
                                last_temp: 0,
                                last_vibration: 0,
                                last_motor_load: 0,
                                last_humidity: 0,
                                timestamp: ''
                            }

                            const avgRisk = machineLogs.reduce((sum, log) => sum + log.probability_failure, 0) / machineLogs.length

                            return (
                                <tr
                                    key={machineId}
                                    className="hover:bg-blue-50 cursor-pointer transition-colors group"
                                    onClick={() => setSelectedMachine(machine)}
                                >
                                    <td className="p-4">
                                        <div className="font-semibold text-slate-800">{machine.name}</div>
                                        <div className="text-xs text-slate-500">{machine.machine_type} • ID: {machineId}</div>
                                    </td>
                                    <td className="p-4">
                                        {machine.last_temp > 0 ? (
                                            <div className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold border ${machine.status === 'ONLINE' ? 'bg-green-50 text-green-700 border-green-200' :
                                                machine.status === 'WARNING' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                                                    machine.status === 'ERROR' ? 'bg-red-50 text-red-700 border-red-200' :
                                                        'bg-gray-50 text-gray-700 border-gray-200'
                                                }`}>
                                                {machine.status}
                                            </div>
                                        ) : (
                                            <span className="text-xs text-slate-400">No data</span>
                                        )}
                                    </td>
                                    <td className="p-4 text-center">
                                        <div className="font-bold text-slate-700">{machineLogs.length}</div>
                                    </td>
                                    <td className="p-4 text-center">
                                        <div className={`font-bold text-base ${avgRisk > 70 ? 'text-red-600' :
                                            avgRisk > 40 ? 'text-orange-600' :
                                                'text-green-600'
                                            }`}>
                                            {avgRisk.toFixed(0)}%
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        {machine.last_temp > 0 ? (
                                            <div className="flex gap-4 text-xs">
                                                <div className="flex items-center gap-1">
                                                    <Thermometer className="w-3.5 h-3.5 text-red-500" />
                                                    <span className="text-slate-700 font-medium">{machine.last_temp.toFixed(1)}°C</span>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Activity className="w-3.5 h-3.5 text-blue-500" />
                                                    <span className="text-slate-700 font-medium">{machine.last_vibration.toFixed(3)}G</span>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Gauge className="w-3.5 h-3.5 text-purple-500" />
                                                    <span className="text-slate-700 font-medium">{machine.last_motor_load.toFixed(1)}%</span>
                                                </div>
                                            </div>
                                        ) : (
                                            <span className="text-xs text-slate-400">No sensor data</span>
                                        )}
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="text-blue-600 font-medium text-xs bg-blue-50 px-4 py-2 rounded-md hover:bg-blue-100 transition group-hover:bg-blue-600 group-hover:text-white">
                                            📊 View Live Charts
                                        </button>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>

                {/* Pagination for Logs */}
                {logs.length > logsPerPage && (
                    <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50">
                        <div className="text-sm text-slate-600">
                            Showing {((currentPage - 1) * logsPerPage) + 1} to {Math.min(currentPage * logsPerPage, logs.length)} of {logs.length} logs
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="px-3 py-1.5 text-sm font-medium rounded-md border border-slate-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100 transition"
                            >
                                Previous
                            </button>
                            <div className="px-3 py-1.5 text-sm font-medium text-slate-700">
                                Page {currentPage} of {Math.ceil(logs.length / logsPerPage)}
                            </div>
                            <button
                                onClick={() => setCurrentPage(p => Math.min(Math.ceil(logs.length / logsPerPage), p + 1))}
                                disabled={currentPage >= Math.ceil(logs.length / logsPerPage)}
                                className="px-3 py-1.5 text-sm font-medium rounded-md border border-slate-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100 transition"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal */}
            {selectedMachine && (
                <LiveChartModal machine={selectedMachine} onClose={() => setSelectedMachine(null)} isSimulating={isSimulating} />
            )}
        </div>
    )
}
