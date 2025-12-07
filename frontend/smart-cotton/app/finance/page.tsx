'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import {
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import { TrendingUp, AlertCircle, Loader2 } from 'lucide-react'

interface ChartPoint {
    date: string
    price: number
    type: 'history' | 'forecast'
    historyPrice?: number
    forecastPrice?: number
}

interface AIAnalysis {
    signal: 'BUY' | 'SELL' | 'HOLD' | 'WAIT'
    confidence: string
    reason: string
    forecast_trend: 'UP' | 'DOWN'
}

interface MarketData {
    asset: string
    current_price: number
    chart_data: ChartPoint[]
    ai_analysis: AIAnalysis
}

interface AIBotRecommendation {
    success: boolean
    decision: 'sell' | 'wait'
    confidence: string
    reason: string
    forecast: number[]
    current_price: number
    predicted_peak: number
    peak_day: number
    change_percent: number
}

export default function FinancePage() {
    // Состояние
    const [error, setError] = useState<string | null>(null)
    const [marketData, setMarketData] = useState<MarketData | null>(null)
    const [aiBotRecommendation, setAiBotRecommendation] = useState<AIBotRecommendation | null>(null)
    const [botLoading, setBotLoading] = useState(true)

    // --- Загрузка данных ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Запрос данных по Хлопку (Cotton)
                const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/market/?asset=cotton`)
                // Трансформация данных для графика (чтобы сделать линию прогноза пунктирной)
                const rawData = response.data.chart_data
                const processedData = rawData.map((item: ChartPoint, index: number) => {
                    // Трюк: чтобы линии соединялись, последняя точка истории должна быть и началом прогноза
                    const isLastHistory = item.type === 'history' && rawData[index + 1]?.type === 'forecast'

                    return {
                        ...item,
                        // Если это история -> пишем в historyPrice
                        historyPrice: item.type === 'history' ? item.price : (isLastHistory ? item.price : null),
                        // Если это прогноз (или стык) -> пишем в forecastPrice
                        forecastPrice: item.type === 'forecast' || isLastHistory ? item.price : null
                    }
                })

                setMarketData({
                    ...response.data,
                    chart_data: processedData
                })

            } catch (err) {
                console.error("API Error:", err)
                setError("Failed to connect to Finance AI Service. Make sure Django is running.")
            }
        }

        const fetchAIBotRecommendations = async () => {
            try {
                setBotLoading(true)
                const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/finance/ai-recommendations/`)
                setAiBotRecommendation(response.data)
            } catch (err) {
                console.error("AI Bot API Error:", err)
            } finally {
                setBotLoading(false)
            }
        }

        fetchData()
        fetchAIBotRecommendations()
    }, [])


    if (error || !marketData) {
        return (
            <div className="h-full w-full flex items-center justify-center bg-white rounded-xl border border-slate-200">
                <div className="text-center p-6 bg-red-50 rounded-xl border border-red-100">
                    <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-2" />
                    <h3 className="text-red-800 font-bold">Service Unavailable</h3>
                    <p className="text-red-600 text-sm mt-1">{error}</p>
                </div>
            </div>
        )
    }

    return (
        <div className="bg-white h-full w-full rounded-xl p-6 border border-slate-200 shadow-sm overflow-y-auto">
            {/* Header */}

            <div className="gap-6">
                {/* --- 4. AI BOT RECOMMENDATION SECTION (Task 3 Integration) --- */}
                <div className="mt-6 w-full">
                    <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                        <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
                        AI Trading Bot Recommendation (LSTM/BiLSTM)
                    </h2>

                    {botLoading ? (
                        <div className="bg-white rounded-xl border border-slate-200 p-8 flex items-center justify-center">
                            <div className="flex flex-col items-center gap-3">
                                <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
                                <p className="text-slate-500 text-sm">AI Bot analyzing market data...</p>
                            </div>
                        </div>
                    ) : aiBotRecommendation && aiBotRecommendation.success ? (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                            {/* Main Recommendation Card */}
                            <div className={`lg:col-span-2 p-6 rounded-xl text-white shadow-xl ${aiBotRecommendation.decision === 'sell'
                                ? 'bg-linear-to-br from-red-500 to-rose-600'
                                : 'bg-linear-to-br from-blue-500 to-indigo-600'
                                }`}>
                                <div className="flex items-center justify-between mb-4">
                                        <div>
                                            <div className="flex items-center gap-2 opacity-80 mb-2">
                                                <TrendingUp className="w-5 h-5" />
                                                <span className="text-sm font-bold uppercase tracking-wider">AI Bot Decision</span>
                                            </div>
                                            <div className="text-5xl font-black tracking-tight mb-2">
                                                {aiBotRecommendation.decision.toUpperCase()}
                                            </div>
                                            <div className="flex items-center gap-2 bg-white/20 w-fit px-3 py-1 rounded-full text-sm backdrop-blur-sm">
                                                <span>Confidence:</span>
                                                <span className="font-bold">{aiBotRecommendation.confidence}</span>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-xs opacity-80 mb-1">Current Price</div>
                                            <div className="text-3xl font-bold">KZT {aiBotRecommendation.current_price.toFixed(2)}</div>
                                            <div className="text-xs opacity-80 mt-2">Peak Price</div>
                                            <div className="text-2xl font-bold">KZT {aiBotRecommendation.predicted_peak.toFixed(2)}</div>
                                            <div className="text-xs opacity-80 mt-1">in {aiBotRecommendation.peak_day} days</div>
                                        </div>
                                    </div>
                                    <div className="border-t border-white/20 pt-4">
                                        <p className="text-sm opacity-90 leading-relaxed">
                                            {aiBotRecommendation.reason}
                                        </p>
                                    </div>
                                </div>

                                {/* Stats Panel */}
                                <div className="space-y-4">
                                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                                        <div className="text-xs text-slate-500 uppercase font-bold mb-2">Price Change</div>
                                        <div className={`text-3xl font-bold ${aiBotRecommendation.change_percent > 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {aiBotRecommendation.change_percent > 0 ? '+' : ''}
                                            {aiBotRecommendation.change_percent.toFixed(2)}%
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">7-day forecast</div>
                                    </div>

                                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                                        <div className="text-xs text-slate-500 uppercase font-bold mb-2">Model Type</div>
                                        <div className="text-sm font-semibold text-slate-800">LSTM + BiLSTM Ensemble</div>
                                        <div className="text-xs text-slate-500 mt-1">Deep learning hybrid model</div>
                                    </div>

                                    <div className="bg-linear-to-br from-purple-50 to-indigo-50 p-4 rounded-xl border border-purple-200">
                                        <div className="text-xs text-purple-600 uppercase font-bold mb-1">Next Update</div>
                                        <div className="text-sm font-semibold text-purple-800">24 hours</div>
                                    </div>
                                </div>

                                {/* Forecast Chart */}
                                <div className="lg:col-span-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm h-80">
                                    <h4 className="text-sm font-bold text-slate-700 mb-3">30-Day Price Forecast</h4>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={aiBotRecommendation.forecast.map((price, idx) => ({
                                            day: `Day ${idx}`,
                                            dayNum: idx,
                                            price: price,
                                            isPeak: idx === aiBotRecommendation.peak_day
                                        }))}>
                                            <defs>
                                                <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                                                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                            <XAxis
                                                dataKey="day"
                                                tick={{ fontSize: 11, fill: '#94a3b8' }}
                                                tickMargin={8}
                                            />
                                            <YAxis
                                                domain={['auto', 'auto']}
                                                tick={{ fontSize: 11, fill: '#94a3b8' }}
                                                tickFormatter={(val) => `${val.toFixed(2)}`}
                                                width={50}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                                                    fontSize: '12px'
                                                }}
                                                formatter={(value: number) => [`KZT ${value.toFixed(2)}`, 'Price']}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="price"
                                                stroke="#8b5cf6"
                                                strokeWidth={3}
                                                fill="url(#forecastGradient)"
                                                name="Forecast"
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-white rounded-xl border border-slate-200 p-8">
                                <div className="text-center">
                                    <AlertCircle className="w-10 h-10 text-orange-500 mx-auto mb-2" />
                                    <h3 className="text-slate-800 font-bold">AI Bot Unavailable</h3>
                                    <p className="text-slate-600 text-sm mt-1">
                                        Unable to fetch AI recommendations. Please check the backend service.
                                    </p>
                                </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}