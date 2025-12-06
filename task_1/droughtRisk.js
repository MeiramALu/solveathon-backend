// droughtRisk.js
// Core logic for drought risk analysis using Open-Meteo.
/**
 * Configuration for the drought model.
 */
const DROUGHT_CONFIG = {
    pastDays: 30,
    forecastDays: 7,
    // Thresholds (mm)
    waterBalanceMediumMin: -30, // P30 - ET30 >= -30 => medium risk
    // "Hot & dry" bump criteria
    hotDryTempThreshold: 35, // °C
    hotDryPrecipThreshold: 5 // mm in forecast window
};

/**
 * Classify drought risk based on:
 *  - waterBalance: P30 - ET30 (mm)
 *  - precipNext: total precipitation next N days (mm)
 *  - tmaxNext: max T_max next N days (°C)
 *
 * Returns one of: 'low' | 'medium' | 'high'
 */
export function classifyDroughtRisk(waterBalance, precipNext, tmaxNext, cfg = DROUGHT_CONFIG) {
    let level;

    if (waterBalance > 0) {
        level = 'low';
    } else if (waterBalance >= cfg.waterBalanceMediumMin) {
        level = 'medium';
    } else {
        level = 'high';
    }

    const hotAndDry = (precipNext < cfg.hotDryPrecipThreshold) &&
        (tmaxNext >= cfg.hotDryTempThreshold);

    // Increase risk by one level if both hot and dry in forecast
    if (hotAndDry && level !== 'high') {
        level = (level === 'low') ? 'medium' : 'high';
    }

    return level;
}

/**
 * Fetch daily precipitation, ET0 and Tmax from Open-Meteo.
 * This is a single call that includes both history (past_days)
 * and forecast (forecast_days).
 *
 * Returns raw data plus aggregated indicators.
 */
export async function fetchDroughtIndicators(lat, lon, cfg = DROUGHT_CONFIG) {
    const baseUrl = 'https://api.open-meteo.com/v1/forecast';

    const params = new URLSearchParams({
        latitude: lat,
        longitude: lon,
        timezone: 'auto',
        past_days: String(cfg.pastDays),
        forecast_days: String(cfg.forecastDays),
        daily: [
            'precipitation_sum',
            'et0_fao_evapotranspiration',
            'temperature_2m_max'
        ].join(',')
    });

    const url = `${baseUrl}?${params.toString()}`;
    const res = await fetch(url);

    if (!res.ok) {
        throw new Error(`Open-Meteo error ${res.status}`);
    }

    const data = await res.json();
    const daily = data.daily;

    if (!daily || !daily.precipitation_sum) {
        throw new Error('Unexpected Open-Meteo response format');
    }

    const times = daily.time;
    const precip = daily.precipitation_sum;
    const et0 = daily.et0_fao_evapotranspiration;
    const tmax = daily.temperature_2m_max;
    const len = times.length;

    const histCount = Math.min(cfg.pastDays, len);

    // 30-day history aggregates
    const P30 = precip
        .slice(0, histCount)
        .reduce((sum, v) => sum + (v ?? 0), 0);

    const ET30 = et0
        .slice(0, histCount)
        .reduce((sum, v) => sum + (v ?? 0), 0);

    const waterBalance = P30 - ET30;

    // Forecast aggregates
    const precipForecastArr = precip.slice(histCount);
    const tmaxForecastArr = tmax.slice(histCount);

    const forecastPrecip = precipForecastArr
        .reduce((sum, v) => sum + (v ?? 0), 0);

    const forecastTmax = tmaxForecastArr.length
        ? Math.max(...tmaxForecastArr)
        : NaN;

    return {
        apiUrl: url,
        raw: data,
        indicators: {
            P30,
            ET30,
            waterBalance,
            forecastPrecip,
            forecastTmax
        }
    };
}

/**
 * High-level helper:
 * 1) fetch indicators from Open-Meteo
 * 2) classify drought risk
 *
 * Returns a structured object ready for UI.
 */
export async function analyzeDroughtAtLocation(lat, lon, cfg = DROUGHT_CONFIG) {
    const { apiUrl, raw, indicators } = await fetchDroughtIndicators(lat, lon, cfg);
    const { P30, ET30, waterBalance, forecastPrecip, forecastTmax } = indicators;

    const level = classifyDroughtRisk(waterBalance, forecastPrecip, forecastTmax, cfg);

    return {
        location: { lat, lon },
        level,
        indicators,
        source: {
            apiUrl,
            provider: 'Open-Meteo',
            units: raw.daily_units || {}
        },
        modelConfig: cfg
    };
}
