import { analyzeDroughtAtLocation } from './droughtRisk.js';
import { recommendIrrigation } from './irrigation.js';

/**
 * High-level service:
 * Given a location + field metadata, return
 * both drought info and irrigation recommendation.
 */
export async function getSmartIrrigationPlanForField(field) {
    const { lat, lon, crop, growthStage, soilMoisture } = field;

    // 1) Drought analysis from Open-Meteo
    const droughtResult = await analyzeDroughtAtLocation(lat, lon);
    const { level, indicators } = droughtResult;
    const { waterBalance, forecastPrecip, forecastTmax } = indicators;

    // 2) Irrigation recommendation based on drought + crop info
    const irrigation = recommendIrrigation({
        droughtLevel: level,
        waterBalance,
        forecastPrecip,
        forecastTmax,
        crop,
        growthStage,
        soilMoisture
    });

    // 3) One combined object
    return {
        fieldId: field.id ?? null,
        location: { lat, lon },
        drought: droughtResult,
        irrigation
    };
}
