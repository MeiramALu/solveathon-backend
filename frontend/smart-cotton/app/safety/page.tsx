'use client'

import { useState } from 'react'
import axios from 'axios'
import { Upload, AlertTriangle, Shield, Flame, HardHat, Loader2 } from 'lucide-react'
import Image from 'next/image'

type DetectionResult = {
    predictions: Array<{
        x: number
        y: number
        width: number
        height: number
        confidence: number
        class: string
        class_id: number
    }>
    image: {
        width: number
        height: number
    }
}

type TabType = 'fire' | 'safety-gear'

export default function SafetyPage() {
    const [activeTab, setActiveTab] = useState<TabType>('fire')
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<DetectionResult | null>(null)
    const [error, setError] = useState<string | null>(null)

    const loadImageBase64 = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.readAsDataURL(file)
            reader.onload = () => resolve(reader.result as string)
            reader.onerror = (error) => reject(error)
        })
    }

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            setSelectedFile(file)
            setPreviewUrl(URL.createObjectURL(file))
            setResult(null)
            setError(null)
        }
    }

    const handleAnalyze = async () => {
        if (!selectedFile) return

        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const image = await loadImageBase64(selectedFile)

            const apiConfig = activeTab === 'fire'
                ? {
                    url: 'https://serverless.roboflow.com/fire-smoke-spark-jb5ug/7',
                    api_key: '9bGAFNpKD7bUZ01jTKUb'
                }
                : {
                    url: 'https://serverless.roboflow.com/safety-helmet-and-reflection-vest-detection/4',
                    api_key: '9bGAFNpKD7bUZ01jTKUb'
                }

            const response = await axios({
                method: 'POST',
                url: apiConfig.url,
                params: {
                    api_key: apiConfig.api_key
                },
                data: image,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })

            setResult(response.data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to analyze image')
        } finally {
            setLoading(false)
        }
    }

    const getDetectionStats = () => {
        if (!result?.predictions) return null

        const counts: Record<string, number> = {}
        result.predictions.forEach(pred => {
            counts[pred.class] = (counts[pred.class] || 0) + 1
        })

        return counts
    }

    const stats = getDetectionStats()

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
                        <Shield className="w-8 h-8 text-blue-600" />
                        Safety Detection System
                    </h1>
                    <p className="text-slate-600 mt-2">AI-powered safety monitoring for fire detection and PPE compliance</p>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => {
                            setActiveTab('fire')
                            setSelectedFile(null)
                            setPreviewUrl(null)
                            setResult(null)
                            setError(null)
                        }}
                        className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition ${activeTab === 'fire'
                            ? 'bg-orange-500 text-white shadow-lg'
                            : 'bg-white text-slate-700 hover:bg-slate-100'
                            }`}
                    >
                        <Flame className="w-5 h-5" />
                        Fire & Smoke Detection
                    </button>
                    <button
                        onClick={() => {
                            setActiveTab('safety-gear')
                            setSelectedFile(null)
                            setPreviewUrl(null)
                            setResult(null)
                            setError(null)
                        }}
                        className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition ${activeTab === 'safety-gear'
                            ? 'bg-blue-500 text-white shadow-lg'
                            : 'bg-white text-slate-700 hover:bg-slate-100'
                            }`}
                    >
                        <HardHat className="w-5 h-5" />
                        Safety Gear Detection
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Upload Section */}
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h2 className="text-xl font-semibold text-slate-800 mb-4">Upload Image</h2>

                        <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-blue-400 transition">
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="file-upload"
                            />
                            <label htmlFor="file-upload" className="cursor-pointer">
                                <Upload className="w-12 h-12 mx-auto text-slate-400 mb-4" />
                                <p className="text-slate-600 font-medium mb-2">
                                    Click to upload or drag and drop
                                </p>
                                <p className="text-sm text-slate-400">
                                    PNG, JPG, JPEG up to 10MB
                                </p>
                            </label>
                        </div>

                        {previewUrl && (
                            <div className="mt-6">
                                <div className="relative w-full h-64 bg-slate-100 rounded-lg overflow-hidden">
                                    <Image
                                        src={previewUrl}
                                        alt="Preview"
                                        fill
                                        className="object-contain"
                                    />
                                </div>
                                <button
                                    onClick={handleAnalyze}
                                    disabled={loading}
                                    className="w-full mt-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            <Shield className="w-5 h-5" />
                                            Analyze Image
                                        </>
                                    )}
                                </button>
                            </div>
                        )}

                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="font-semibold text-red-800">Error</p>
                                    <p className="text-sm text-red-600">{error}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Results Section */}
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h2 className="text-xl font-semibold text-slate-800 mb-4">Detection Results</h2>

                        {!result && !loading && (
                            <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                                <Shield className="w-16 h-16 mb-4" />
                                <p className="text-center">Upload and analyze an image to see results</p>
                            </div>
                        )}

                        {loading && (
                            <div className="flex flex-col items-center justify-center h-64">
                                <Loader2 className="w-12 h-12 animate-spin text-blue-500 mb-4" />
                                <p className="text-slate-600">Analyzing image...</p>
                            </div>
                        )}

                        {result && stats && (
                            <div className="space-y-6">
                                {/* Summary Cards */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                                        <p className="text-sm text-blue-600 font-medium mb-1">Total Detections</p>
                                        <p className="text-3xl font-bold text-blue-700">{result.predictions.length}</p>
                                    </div>
                                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                                        <p className="text-sm text-purple-600 font-medium mb-1">Categories Found</p>
                                        <p className="text-3xl font-bold text-purple-700">{Object.keys(stats).length}</p>
                                    </div>
                                </div>

                                {/* Detailed Results */}
                                <div>
                                    <h3 className="font-semibold text-slate-700 mb-3">Detected Objects</h3>
                                    <div className="space-y-2 max-h-96 overflow-y-auto">
                                        {Object.entries(stats).map(([className, count]) => (
                                            <div
                                                key={className}
                                                className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-3 h-3 rounded-full ${activeTab === 'fire'
                                                        ? 'bg-orange-500'
                                                        : 'bg-blue-500'
                                                        }`}></div>
                                                    <span className="font-medium text-slate-800 capitalize">
                                                        {className.replace(/-/g, ' ')}
                                                    </span>
                                                </div>
                                                <span className="px-3 py-1 bg-slate-200 rounded-full text-sm font-semibold text-slate-700">
                                                    {count}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Individual Predictions */}
                                <div>
                                    <h3 className="font-semibold text-slate-700 mb-3">Confidence Scores</h3>
                                    <div className="space-y-2 max-h-64 overflow-y-auto">
                                        {result.predictions.map((pred, idx) => (
                                            <div key={idx} className="flex items-center gap-3 p-2 bg-slate-50 rounded">
                                                <span className="text-sm text-slate-600 capitalize flex-1">
                                                    {pred.class.replace(/-/g, ' ')}
                                                </span>
                                                <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
                                                    <div
                                                        className={`h-full ${pred.confidence > 0.8 ? 'bg-green-500' :
                                                            pred.confidence > 0.6 ? 'bg-yellow-500' :
                                                                'bg-orange-500'
                                                            }`}
                                                        style={{ width: `${pred.confidence * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-sm font-semibold text-slate-700 w-12 text-right">
                                                    {(pred.confidence * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
