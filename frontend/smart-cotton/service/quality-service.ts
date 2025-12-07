import axios from "axios";

const API_BASE_URL =
	process.env.NEXT_PUBLIC_API_URL ||
	"https://smart-cotton-ai-system.onrender.com/api";

export interface HVIData {
	micronaire: number;
	strength: number;
	length: number;
	uniformity: number;
	trash_grade: number;
	trash_cnt: number;
	trash_area: number;
	sfi: number;
	sci: number;
	color_grade: string;
}

export interface HVIPredictionResponse {
	success: boolean;
	quality_class: string;
	confidence: number;
	probabilities: {
		low_grade: number;
		premium: number;
		standard: number;
	};
	input_data: HVIData;
}

export interface ImageAnalysisResponse {
	success: boolean;
	label: string;
	confidence: number;
	score: number;
	filename: string;
}

export interface SeedRecommendation {
	variety: string;
	type: string;
	brand: string;
	predicted_yield: number;
	predicted_quality: number;
	score: number;
}

export interface SeedRecommendationResponse {
	success: boolean;
	location: string;
	recommendations: SeedRecommendation[];
}

export interface LocationsResponse {
	success: boolean;
	locations: string[];
}

class QualityService {
	/**
	 * HVI Lab - Predict cotton quality from HVI parameters
	 */
	async predictQuality(data: HVIData): Promise<HVIPredictionResponse> {
		const response = await axios.post(
			`${API_BASE_URL}/factory/batches/predict-quality/`,
			data
		);
		return response.data;
	}

	/**
	 * Computer Vision - Analyze cotton image for cleanliness
	 */
	async analyzeImage(imageFile: File): Promise<ImageAnalysisResponse> {
		const formData = new FormData();
		formData.append("image", imageFile);

		const response = await axios.post(
			`${API_BASE_URL}/factory/batches/analyze-image/`,
			formData,
			{
				headers: {
					"Content-Type": "multipart/form-data",
				},
			}
		);
		return response.data;
	}

	/**
	 * Seed Recommendation - Get top 3 seed varieties for a location
	 */
	async recommendSeeds(location: string): Promise<SeedRecommendationResponse> {
		const response = await axios.post(
			`${API_BASE_URL}/agronomy/seeds/recommend/`,
			{ location }
		);
		return response.data;
	}

	/**
	 * Get available locations for seed recommendations
	 */
	async getAvailableLocations(): Promise<LocationsResponse> {
		const response = await axios.get(
			`${API_BASE_URL}/agronomy/seeds/available-locations/`
		);
		return response.data;
	}
}

export const qualityService = new QualityService();
