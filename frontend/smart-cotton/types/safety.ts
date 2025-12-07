// Safety monitoring type definitions

export interface Worker {
	worker_id: number;
	name: string;
	role: string;

	// Location
	latitude: number;
	longitude: number;
	altitude: number;

	// Vitals
	heart_rate: number;
	steps: number;
	activity_level: number;
	temp_c: number;
	spo2: number;
	noise_level: number;
	hrv: number;
	sleep_score: number;

	// Analysis
	zone: string;
	safety_status: string;
	alert_panic: boolean;
	alert_fall: boolean;
	alert_fatigue: boolean;
	alert_environment: boolean;
	alert_acoustic: boolean;
	alert_geofence: boolean;
}

export interface RiskLevel {
	level: "LOW" | "MODERATE" | "HIGH";
	percentage: number;
	color: string;
}

export interface WorkerHealthMetric {
	id: number;
	worker: number;
	worker_name: string;
	timestamp: string;
	heart_rate: number;
	spo2: number;
	temp_c: number;
	hrv: number;
	steps: number;
	activity_level: number;
	noise_level: number;
	latitude: number;
	longitude: number;
	altitude: number;
	alert_panic: boolean;
	alert_fall: boolean;
	alert_fatigue: boolean;
	alert_environment: boolean;
	alert_acoustic: boolean;
	alert_geofence: boolean;
	safety_status: string;
	zone: string;
}

export interface Zone {
	id: number;
	name: string;
	zone_type: "CHEMICAL" | "ASSEMBLY" | "LOADING" | "SAFE";
	lat_min: number;
	lat_max: number;
	lon_min: number;
	lon_max: number;
	description: string;
}

export type SimulationType = "panic" | "toxic" | "fall" | "reset";

export interface AIAnalysisResponse {
	worker_id: number;
	name: string;
	ai_analysis: string;
	current_metrics: Partial<Worker>;
	alerts: {
		alert_panic: boolean;
		alert_fall: boolean;
		alert_fatigue: boolean;
		alert_environment: boolean;
		alert_acoustic: boolean;
		alert_geofence: boolean;
		zone: string;
		safety_status: string;
	};
}
