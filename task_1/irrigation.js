export function recommendIrrigation({
    droughtLevel,      // 'low' | 'medium' | 'high'
    waterBalance,      // mm (30 days P - ET0)
    forecastPrecip,    // mm (7 days)
    forecastTmax,      // °C
    crop = 'cotton',
    growthStage = 'vegetative', // 'early' | 'vegetative' | 'flowering' | 'late'
    soilMoisture = null         // optional, 0–100%
}) {
    // 1. Base dose by crop + stage (simple table, can be extended)
    const baseDoseByStage = {
        cotton: {
            early: 8,
            vegetative: 12,
            flowering: 18,
            late: 10
        }
    };

    const cropStages = baseDoseByStage[crop] || baseDoseByStage['cotton'];
    let baseDose = cropStages[growthStage] || cropStages['vegetative']; // mm

    // 2. Drought multiplier
    const droughtMultiplier = {
        low: 0.6,
        medium: 1.0,
        high: 1.3
    }[droughtLevel] || 1.0;

    let dose = baseDose * droughtMultiplier;

    // 3. Adjust for 7-day rain forecast
    if (forecastPrecip > 15) {
        dose *= 0.6; // expect good rainfall, reduce irrigation
    } else if (forecastPrecip < 5) {
        dose *= 1.2; // almost no rain, increase irrigation
    }

    // 4. Optional soil moisture adjustment
    if (soilMoisture !== null) {
        if (soilMoisture > 70) {
            dose = 0; // soil already wet, skip irrigation
        } else if (soilMoisture < 40) {
            dose *= 1.2; // very dry soil
        }
    }

    // 5. Avoid negative or tiny values
    if (dose < 0) dose = 0;
    if (dose < 1 && dose > 0) dose = 1; // minimum 1 mm if we irrigate

    // 6. Convert mm → minutes (assume 1 mm ~ 1.2 min; tweak for your system)
    const minutesPerMm = 1.2;
    const durationMinutes = dose * minutesPerMm;

    // 7. Priority rating (0–1) for water distribution
    // Combine drought + water balance into a simple score
    let priority;
    if (dose === 0) {
        priority = 0;
    } else {
        let droughtScore = {
            low: 0.3,
            medium: 0.6,
            high: 1.0
        }[droughtLevel] || 0.5;

        const deficitScore = Math.max(0, Math.min(1, -waterBalance / 60)); // normalize: -60mm => score 1
        priority = Math.max(droughtScore, deficitScore);
    }

    return {
        recommended_mm: Number(dose.toFixed(1)),
        recommended_minutes: Number(durationMinutes.toFixed(0)),
        priority: Number(priority.toFixed(2)),
        explanation: {
            crop,
            growthStage,
            droughtLevel,
            forecastPrecip_mm_7d: Number(forecastPrecip.toFixed(1)),
            forecastTmax_c_7d: Number(forecastTmax.toFixed(1)),
            waterBalance_mm_30d: Number(waterBalance.toFixed(1)),
            soilMoisture_pct: soilMoisture
        }
    };
}
