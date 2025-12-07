'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Droplets, Factory, DollarSign, Sprout, ShieldAlert, MapIcon, Menu, X } from 'lucide-react'

const MODULES = [
    { href: '/', id: 'water', title: 'Water Management (Soil moisture)', icon: Droplets, color: 'text-blue-500', desc: 'Soil moisture' },
    { href: '/water', id: 'water-2', title: 'Water Management (Irrigation)', icon: Droplets, color: 'text-blue-500', desc: 'Irrigation' },
    { href: '/quality', id: 'quality', title: 'Cotton Quality', icon: Sprout, color: 'text-green-500', desc: 'HVI Analysis' },
    { href: '/finance', id: 'finance', title: 'Market & Finance', icon: DollarSign, color: 'text-yellow-500', desc: 'Price prediction' },
    { href: '/factory', id: 'factory', title: 'Smart Factory', icon: Factory, color: 'text-gray-500', desc: 'Digital Twin' },
    { href: '/routes', id: 'routes', title: 'Route Optimization', icon: MapIcon, color: 'text-purple-500', desc: 'AI route planning' },
    { href: '/safety', id: 'safety', title: 'Safety AI', icon: ShieldAlert, color: 'text-red-500', desc: 'Safety monitoring' },
    { href: '/monitoring', id: 'monitoring', title: 'Safety Monitoring', icon: ShieldAlert, color: 'text-red-600', desc: 'Worker safety system' },
    { href: '/agronomy', id: 'agronomy', title: 'Agronomy AI', icon: Sprout, color: 'text-green-700', desc: 'Crop health insights' },
]

export default function Sidebar() {
    const pathname = usePathname()
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

    return (
        <>
            {/* Mobile Menu Button - Always visible on mobile */}
            <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden fixed top-4 left-4 z-9999 p-3 bg-green-600 text-white border-0 rounded-lg shadow-lg hover:bg-green-700 transition-all active:scale-95"
                aria-label="Toggle menu"
            >
                {isMobileMenuOpen ? (
                    <X className="w-5 h-5" />
                ) : (
                    <Menu className="w-5 h-5" />
                )}
            </button>

            {/* Overlay for mobile */}
            {isMobileMenuOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-45"
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
                fixed lg:relative inset-y-0 left-0 z-9999
                w-full sm:w-80 lg:w-1/3 lg:min-w-[300px] lg:max-w-[400px]
                flex flex-col gap-4 overflow-y-auto
                h-full border-r border-slate-200 bg-slate-50 p-4 lg:pr-2
                transition-transform duration-300 ease-in-out
                ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            `}>
                <div className="mb-4 pt-16 lg:pt-0">
                    <h1 className="text-2xl font-bold text-slate-800">Smart Cotton</h1>
                    <p className="text-slate-500 text-sm">AI-Driven Agriculture Platform</p>
                </div>

            <div className="grid gap-3">
                {MODULES.map((module) => {
                    const Icon = module.icon
                    // Check if active. Handle root path specially.
                    const isActive = module.href === '/' ? pathname === '/' : pathname.startsWith(module.href)

                    return (
                        <Link
                            key={module.id}
                            href={module.href}
                            onClick={() => setIsMobileMenuOpen(false)}
                            className={`
                    flex items-center gap-3 lg:gap-4 p-3 lg:p-4 rounded-xl border transition-all text-left group
                    ${isActive
                                    ? 'bg-white border-green-600 shadow-md ring-1 ring-green-600'
                                    : 'bg-white border-slate-200 hover:border-green-300 hover:shadow-sm'
                                }
                `}
                        >
                            <div className={`p-2 lg:p-3 rounded-lg ${isActive ? 'bg-green-50' : 'bg-slate-50 group-hover:bg-green-50'}`}>
                                <Icon className={`w-5 h-5 lg:w-6 lg:h-6 ${module.color}`} />
                            </div>
                            <div className="min-w-0 flex-1">
                                <h3 className={`font-semibold text-sm lg:text-base ${isActive ? 'text-slate-900' : 'text-slate-700'}`}>
                                    {module.title}
                                </h3>
                                <p className="text-xs text-slate-500 truncate">{module.desc}</p>
                            </div>
                        </Link>
                    )
                })}
            </div>
        </aside>
        </>
    )
}