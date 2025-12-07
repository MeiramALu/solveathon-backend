const API_BASE =
	process.env.NEXT_PUBLIC_API_URL ||
	"https://smart-cotton-ai-system.onrender.com";

export interface Location {
	lat: number;
	lon: number;
}

export interface DroughtIndicators {
	P30: number;
	ET30: number;
	waterBalance: number;
	forecastPrecip: number;
	forecastTmax: number;
}

export interface DroughtResult {
	location: Location;
	level: "low" | "medium" | "high";
	indicators: DroughtIndicators;
}

export interface IrrigationExplanation {
	crop: string;
	growthStage: string;
	droughtLevel: string;
	forecastPrecip_mm_7d: number;
	forecastTmax_c_7d: number;
	waterBalance_mm_30d: number;
	soilMoisture_pct: number | null;
}

export interface IrrigationResult {
	recommended_mm: number;
	recommended_minutes: number;
	priority: number;
	explanation: IrrigationExplanation;
}

export interface SmartPlan {
	location: Location;
	drought: DroughtResult;
	irrigation: IrrigationResult;
}

export interface SensorData {
	soil_humidity: number;
	soil_temperature: number;
	rain?: number;
	daily_mean_temperature: number;
	irrigation_amount?: number;
	days_since_irrigation?: number;
	location_x: number;
	location_y: number;
}

export interface IrrigationPrediction {
	predicted_humidity: number;
	dry_risk: boolean;
	irrigation_action: "IRRIGATE" | "SKIP";
	recommended_irrigation: number;
	risk_level: "low" | "medium" | "high";
}

export interface FuturePrediction extends IrrigationPrediction {
	date: string;
}

export interface FieldMapData {
	field_id: number;
	date: string;
	predictions: Array<{
		location_x: number;
		location_y: number;
		predicted_humidity: number;
		current_humidity: number;
		dry_risk: boolean;
		risk_level: string;
		irrigation_action: string;
		recommended_irrigation: number;
	}>;
}

export interface TimeSeriesData {
	dates: string[];
	actual_humidity: (number | null)[];
	predicted_humidity: number[];
	irrigation: number[];
	risk_levels: string[];
}

// --- Configuration ---
const DROUGHT_CONFIG = {
	pastDays: 30,
	forecastDays: 7,
	waterBalanceMediumMin: -30,
	hotDryTempThreshold: 35,
	hotDryPrecipThreshold: 5,
};

// --- Logic: Classify Risk ---
function classifyDroughtRisk(
	waterBalance: number,
	precipNext: number,
	tmaxNext: number
) {
	let level: "low" | "medium" | "high";

	if (waterBalance > 0) level = "low";
	else if (waterBalance >= DROUGHT_CONFIG.waterBalanceMediumMin)
		level = "medium";
	else level = "high";

	const hotAndDry =
		precipNext < DROUGHT_CONFIG.hotDryPrecipThreshold &&
		tmaxNext >= DROUGHT_CONFIG.hotDryTempThreshold;

	if (hotAndDry && level !== "high") {
		level = level === "low" ? "medium" : "high";
	}
	return level;
}

// --- Logic: Fetch Data ---
export async function fetchDroughtIndicators(lat: number, lon: number) {
	const params = new URLSearchParams({
		latitude: String(lat),
		longitude: String(lon),
		timezone: "auto",
		past_days: String(DROUGHT_CONFIG.pastDays),
		forecast_days: String(DROUGHT_CONFIG.forecastDays),
		daily: [
			"precipitation_sum",
			"et0_fao_evapotranspiration",
			"temperature_2m_max",
		].join(","),
	});

	const res = await fetch(
		`https://api.open-meteo.com/v1/forecast?${params.toString()}`
	);
	if (!res.ok) throw new Error("Open-Meteo API Error");

	const data = await res.json();
	const daily = data.daily;
	const histCount = Math.min(DROUGHT_CONFIG.pastDays, daily.time.length);

	// Aggregates
	const P30 = daily.precipitation_sum
		.slice(0, histCount)
		.reduce((a: number, b: number) => a + (b || 0), 0);
	const ET30 = daily.et0_fao_evapotranspiration
		.slice(0, histCount)
		.reduce((a: number, b: number) => a + (b || 0), 0);
	const forecastPrecip = daily.precipitation_sum
		.slice(histCount)
		.reduce((a: number, b: number) => a + (b || 0), 0);
	const tmaxForecastArr = daily.temperature_2m_max.slice(histCount);
	const forecastTmax = tmaxForecastArr.length
		? Math.max(...tmaxForecastArr)
		: 0;

	return {
		P30,
		ET30,
		waterBalance: P30 - ET30,
		forecastPrecip,
		forecastTmax,
	};
}

// --- Logic: Recommend Irrigation ---
function recommendIrrigation(
	droughtLevel: "low" | "medium" | "high",
	indicators: DroughtIndicators,
	crop = "cotton",
	growthStage = "vegetative"
): IrrigationResult {
	// 1. Base Dose
	const baseDose = 12; // Simplified for cotton vegetative

	// 2. Drought Multiplier
	const multipliers = { low: 0.6, medium: 1.0, high: 1.3 };
	let dose = baseDose * multipliers[droughtLevel];

	// 3. Forecast Adjustments
	if (indicators.forecastPrecip > 15) dose *= 0.6;
	else if (indicators.forecastPrecip < 5) dose *= 1.2;

	// 4. Bounds
	if (dose < 0) dose = 0;
	if (dose > 0 && dose < 1) dose = 1;

	// 5. Calculate Priority
	let priority = 0;
	if (dose > 0) {
		const droughtScore = { low: 0.3, medium: 0.6, high: 1.0 }[droughtLevel];
		const deficitScore = Math.max(
			0,
			Math.min(1, -indicators.waterBalance / 60)
		);
		priority = Math.max(droughtScore, deficitScore);
	}

	return {
		recommended_mm: Number(dose.toFixed(1)),
		recommended_minutes: Number((dose * 1.2).toFixed(0)), // 1.2 min per mm assumption
		priority: Number(priority.toFixed(2)),
		explanation: {
			crop,
			growthStage,
			droughtLevel,
			forecastPrecip_mm_7d: Number(indicators.forecastPrecip.toFixed(1)),
			forecastTmax_c_7d: Number(indicators.forecastTmax.toFixed(1)),
			waterBalance_mm_30d: Number(indicators.waterBalance.toFixed(1)),
			soilMoisture_pct: null,
		},
	};
}

export const waterService = {
	async predictIrrigation(
		sensorData: SensorData
	): Promise<IrrigationPrediction> {
		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/predict/`,
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(sensorData),
			}
		);

		if (!response.ok) {
			throw new Error("Failed to predict irrigation");
		}

		return response.json();
	},

	async simulateFuture(
		sensorData: SensorData,
		daysAhead: number = 7
	): Promise<{ predictions: FuturePrediction[] }> {
		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/simulate/`,
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ ...sensorData, days_ahead: daysAhead }),
			}
		);

		if (!response.ok) {
			throw new Error("Failed to simulate future irrigation");
		}

		return response.json();
	},

	async getFieldIrrigationMap(
		fieldId: number,
		date?: string
	): Promise<FieldMapData> {
		const params = new URLSearchParams();
		if (date) params.append("date", date);

		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/field/${fieldId}/map/?${params}`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch field irrigation map");
		}

		return response.json();
	},

	async getTimeSeries(
		fieldId: number,
		locX: number,
		locY: number,
		daysBack: number = 30
	): Promise<TimeSeriesData> {
		const params = new URLSearchParams({
			field_id: fieldId.toString(),
			loc_x: locX.toString(),
			loc_y: locY.toString(),
			days_back: daysBack.toString(),
		});

		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/timeseries/?${params}`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch time series data");
		}

		return response.json();
	},

	async getFieldSummary(fieldId: number) {
		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/field/${fieldId}/summary/`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch field summary");
		}

		return response.json();
	},

	async bulkGeneratePredictions(fieldId: number, date?: string) {
		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/bulk-predict/`,
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ field_id: fieldId, date }),
			}
		);

		if (!response.ok) {
			throw new Error("Failed to generate predictions");
		}

		return response.json();
	},

	async getAvailableDates(fieldId: number) {
		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/field/${fieldId}/dates/`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch available dates");
		}

		return response.json();
	},

	async getMapData(fieldId: number, date: string, threshold?: number) {
		const params = new URLSearchParams({ date });
		if (threshold !== undefined) {
			params.append("threshold", threshold.toString());
		}

		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/field/${fieldId}/map-data/?${params}`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch map data");
		}

		return response.json();
	},

	async getDateSummary(fieldId: number) {
		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/field/${fieldId}/date-summary/`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch date summary");
		}

		return response.json();
	},

	async getLocationTimeSeries(fieldId: number, locX: number, locY: number) {
		const params = new URLSearchParams({
			loc_x: locX.toString(),
			loc_y: locY.toString(),
		});

		const response = await fetch(
			`${API_BASE}/api/agronomy/irrigation/field/${fieldId}/location-timeseries/?${params}`
		);

		if (!response.ok) {
			throw new Error("Failed to fetch location time series");
		}

		return response.json();
	},
};

// --- Main Service Function ---
export async function getSmartIrrigationPlan(
	lat: number,
	lon: number
): Promise<SmartPlan> {
	const indicators = await fetchDroughtIndicators(lat, lon);
	const level = classifyDroughtRisk(
		indicators.waterBalance,
		indicators.forecastPrecip,
		indicators.forecastTmax
	);

	const irrigation = recommendIrrigation(level, indicators);

	return {
		location: { lat, lon },
		drought: { location: { lat, lon }, level, indicators },
		irrigation,
	};
}
