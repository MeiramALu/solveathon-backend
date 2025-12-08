/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

import { useState, useEffect } from 'react'
import { Sprout, Beaker, Camera, Leaf, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { qualityService, HVIData, SeedRecommendation } from '@/service/quality-service'

export default function QualityPage() {
  const [activeTab, setActiveTab] = useState<'hvi' | 'vision' | 'seeds'>('hvi')

  return (
    <div className="bg-white h-full w-full rounded-xl p-8 border border-slate-200 shadow-sm overflow-y-auto">
      <div className="flex items-center gap-4 mb-6">
        <div className="p-3 bg-green-100 rounded-lg text-green-600">
          <Sprout className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-bold text-slate-800">Cotton Quality Control & Analytics AI</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('hvi')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors ${activeTab === 'hvi'
            ? 'text-green-600 border-b-2 border-green-600'
            : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          <Beaker className="w-5 h-5" />
          HVI Laboratory
        </button>
        <button
          onClick={() => setActiveTab('vision')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors ${activeTab === 'vision'
            ? 'text-green-600 border-b-2 border-green-600'
            : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          <Camera className="w-5 h-5" />
          Computer Vision
        </button>
        <button
          onClick={() => setActiveTab('seeds')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors ${activeTab === 'seeds'
            ? 'text-green-600 border-b-2 border-green-600'
            : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          <Leaf className="w-5 h-5" />
          Seed Recommendation
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'hvi' && <HVILabTab />}
        {activeTab === 'vision' && <ComputerVisionTab />}
        {activeTab === 'seeds' && <SeedRecommendationTab />}
      </div>
    </div>
  )
}

// ==================== HVI LAB TAB ====================
function HVILabTab() {
  const [formData, setFormData] = useState<HVIData>({
    micronaire: 4.0,
    strength: 30.0,
    length: 1.12,
    uniformity: 83.0,
    trash_grade: 3,
    trash_cnt: 15,
    trash_area: 0.2,
    sfi: 9.0,
    sci: 130,
    color_grade: '31-1'
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const response = await qualityService.predictQuality(formData)
      setResult(response)
    } catch (error: any) {
      setResult({ error: error.response?.data?.error || error.message })
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (field: keyof HVIData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: field === 'color_grade' ? value : parseFloat(value) || 0
    }))
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-50 p-4 rounded-lg">
        <h3 className="font-semibold text-slate-700 mb-2">HVI Fiber Analysis</h3>
        <p className="text-sm text-slate-600">Enter laboratory HVI parameters to predict cotton quality classification</p>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Micronaire</label>
          <input
            type="number"
            step="0.1"
            value={formData.micronaire}
            onChange={(e) => handleChange('micronaire', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Strength (g/tex)</label>
          <input
            type="number"
            step="0.1"
            value={formData.strength}
            onChange={(e) => handleChange('strength', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Length (inches)</label>
          <input
            type="number"
            step="0.01"
            value={formData.length}
            onChange={(e) => handleChange('length', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Uniformity (%)</label>
          <input
            type="number"
            step="0.1"
            value={formData.uniformity}
            onChange={(e) => handleChange('uniformity', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Trash Grade (1-7)</label>
          <input
            type="number"
            min="1"
            max="7"
            value={formData.trash_grade}
            onChange={(e) => handleChange('trash_grade', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Trash Count</label>
          <input
            type="number"
            value={formData.trash_cnt}
            onChange={(e) => handleChange('trash_cnt', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Trash Area (%)</label>
          <input
            type="number"
            step="0.1"
            value={formData.trash_area}
            onChange={(e) => handleChange('trash_area', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">SFI</label>
          <input
            type="number"
            step="0.1"
            value={formData.sfi}
            onChange={(e) => handleChange('sfi', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">SCI</label>
          <input
            type="number"
            value={formData.sci}
            onChange={(e) => handleChange('sci', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Color Grade</label>
          <select
            value={formData.color_grade}
            onChange={(e) => handleChange('color_grade', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 text-slate-700 focus:ring-green-500"
          >
            <option value="11-1">11-1</option>
            <option value="21-1">21-1</option>
            <option value="21-2">21-2</option>
            <option value="31-1">31-1</option>
            <option value="31-2">31-2</option>
            <option value="41-1">41-1</option>
            <option value="51-1">51-1</option>
          </select>
        </div>

        <div className="col-span-3">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 text-slate-700 transition-colors flex items-center justify-center gap-2 disabled:bg-slate-400"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Beaker className="w-5 h-5" />
                Analyze Sample
              </>
            )}
          </button>
        </div>
      </form>

      {/* Results */}
      {result && (
        <div className={`p-6 rounded-lg border-2 ${result.error
          ? 'bg-red-50 border-red-300'
          : result.quality_class === 'Premium'
            ? 'bg-green-50 border-green-300'
            : result.quality_class === 'Low Grade'
              ? 'bg-red-50 border-red-300'
              : 'bg-yellow-50 border-yellow-300'
          }`}>
          {result.error ? (
            <div className="flex items-center gap-3">
              <XCircle className="w-8 h-8 text-red-600" />
              <div>
                <h3 className="font-semibold text-red-900">Error</h3>
                <p className="text-red-700">{result.error}</p>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <div>
                  <h3 className="text-2xl font-bold text-slate-800">{result.quality_class}</h3>
                  <p className="text-slate-600">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-white p-3 rounded">
                  <div className="text-xs text-slate-600">Premium</div>
                  <div className="text-lg font-semibold text-green-600">
                    {(result.probabilities.premium * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-white p-3 rounded">
                  <div className="text-xs text-slate-600">Standard</div>
                  <div className="text-lg font-semibold text-yellow-600">
                    {(result.probabilities.standard * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-white p-3 rounded">
                  <div className="text-xs text-slate-600">Low Grade</div>
                  <div className="text-lg font-semibold text-red-600">
                    {(result.probabilities.low_grade * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ==================== COMPUTER VISION TAB ====================
function ComputerVisionTab() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedImage) return

    setLoading(true)
    setResult(null)

    try {
      const response = await qualityService.analyzeImage(selectedImage)
      setResult(response)
    } catch (error: any) {
      setResult({ error: error.response?.data?.error || error.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-50 p-4 rounded-lg">
        <h3 className="font-semibold text-slate-700 mb-2">Visual Quality Assessment</h3>
        <p className="text-sm text-slate-600">Upload cotton image to detect cleanliness using AI computer vision</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block">
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center cursor-pointer hover:border-green-500 transition-colors">
              {preview ? (
                <img src={preview} alt="Cotton sample" className="max-h-64 mx-auto rounded" />
              ) : (
                <div className="space-y-3">
                  <Camera className="w-16 h-16 mx-auto text-slate-400" />
                  <p className="text-slate-600">Click to upload cotton image</p>
                  <p className="text-xs text-slate-400">JPG, PNG (max 10MB)</p>
                </div>
              )}
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="hidden"
            />
          </label>

          {selectedImage && (
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full mt-4 bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2 disabled:bg-slate-400"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Camera className="w-5 h-5" />
                  Analyze Image
                </>
              )}
            </button>
          )}
        </div>

        <div>
          {result && (
            <div className={`p-6 rounded-lg border-2 h-full flex flex-col justify-center ${result.error
              ? 'bg-red-50 border-red-300'
              : result.label === 'Clean'
                ? 'bg-green-50 border-green-300'
                : 'bg-orange-50 border-orange-300'
              }`}>
              {result.error ? (
                <div className="flex items-center gap-3">
                  <XCircle className="w-8 h-8 text-red-600" />
                  <div>
                    <h3 className="font-semibold text-red-900">Error</h3>
                    <p className="text-red-700">{result.error}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  {result.label === 'Clean' ? (
                    <CheckCircle className="w-20 h-20 mx-auto text-green-600 mb-4" />
                  ) : (
                    <XCircle className="w-20 h-20 mx-auto text-orange-600 mb-4" />
                  )}
                  <h2 className={`text-3xl font-bold mb-2 ${result.label === 'Clean' ? 'text-green-900' : 'text-orange-900'
                    }`}>
                    {result.label}
                  </h2>
                  <p className="text-lg mb-4">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                  <div className="w-full bg-slate-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${result.label === 'Clean' ? 'bg-green-600' : 'bg-orange-600'
                        }`}
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ==================== SEED RECOMMENDATION TAB ====================
function SeedRecommendationTab() {
  const [locations, setLocations] = useState<string[]>([])
  const [selectedLocation, setSelectedLocation] = useState('')
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState<SeedRecommendation[]>([])

  useEffect(() => {
    loadLocations()
  }, [])

  const loadLocations = async () => {
    try {
      const response = await qualityService.getAvailableLocations()
      setLocations(response.locations)
      if (response.locations.length > 0) {
        setSelectedLocation(response.locations[0])
      }
    } catch (error) {
      console.error('Error loading locations:', error)
    }
  }

  const handleRecommend = async () => {
    if (!selectedLocation) return

    setLoading(true)
    setRecommendations([])

    try {
      const response = await qualityService.recommendSeeds(selectedLocation)
      setRecommendations(response.recommendations)
    } catch (error: any) {
      console.error('Error getting recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-50 p-4 rounded-lg">
        <h3 className="font-semibold text-slate-700 mb-2">Seed Variety Selector</h3>
        <p className="text-sm text-slate-600">Get AI-powered seed recommendations based on your location for optimal yield and quality</p>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-slate-700 mb-2">Select Field Location</label>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {locations.map(loc => (
              <option key={loc} value={loc}>{loc}</option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={handleRecommend}
            disabled={loading || !selectedLocation}
            className="bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center gap-2 disabled:bg-slate-400"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <Leaf className="w-5 h-5" />
                Get Recommendations
              </>
            )}
          </button>
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-800">Top 3 Recommendations for {selectedLocation}</h3>

          {recommendations.map((rec, idx) => (
            <div key={idx} className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl font-bold text-green-600">#{idx + 1}</span>
                    <div>
                      <h4 className="text-xl font-bold text-slate-800">{rec.variety}</h4>
                      <p className="text-sm text-slate-600">{rec.brand}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${rec.type === 'Pima'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-blue-100 text-blue-700'
                      }`}>
                      {rec.type}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6 text-center">
                  <div>
                    <div className="text-sm text-slate-600 mb-1">Yield Forecast</div>
                    <div className="text-2xl font-bold text-green-700">{rec.predicted_yield}</div>
                    <div className="text-xs text-slate-500">lb/acre</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-600 mb-1">Quality</div>
                    <div className="text-2xl font-bold text-blue-700">{rec.predicted_quality}</div>
                    <div className="text-xs text-slate-500">g/tex</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}