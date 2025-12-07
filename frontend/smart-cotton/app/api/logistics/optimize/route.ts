import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

interface Field {
	id: number;
	lat: number;
	lon: number;
	demand: number;
	serviceTimeMinutes: number;
}

interface Vehicle {
	id: number;
	name: string;
	capacity: number;
	shiftMinutes: number;
}

interface RequestBody {
	depot: { lat: number; lon: number };
	fields: Field[];
	vehicles: Vehicle[];
}

interface FeasibilityResult {
	ok: boolean;
	errors: string[];
	warnings: string[];
}

/**
 * Simple feasibility checks BEFORE calling ORS.
 */
function checkFeasibility(body: RequestBody): FeasibilityResult {
	const fields = body.fields || [];
	const vehicles = body.vehicles || [];

	const result: FeasibilityResult = {
		ok: true,
		errors: [],
		warnings: [],
	};

	if (!fields.length) {
		result.ok = false;
		result.errors.push("No fields were provided.");
		return result;
	}

	if (!vehicles.length) {
		result.ok = false;
		result.errors.push("No vehicles were provided.");
		return result;
	}

	const totalDemand = fields.reduce(
		(sum, f) => sum + (Number(f.demand) || 0),
		0
	);
	const totalCapacity = vehicles.reduce(
		(sum, v) => sum + (Number(v.capacity) || 0),
		0
	);

	if (totalCapacity <= 0) {
		result.ok = false;
		result.errors.push("Total vehicle capacity is zero or negative.");
	} else if (totalDemand > totalCapacity) {
		result.ok = false;
		result.errors.push(
			`Total field demand (${totalDemand.toFixed(1)} units) exceeds total vehicle capacity (${totalCapacity.toFixed(1)} units).`
		);
	}

	const totalServiceMinutes = fields.reduce(
		(sum, f) => sum + (Number(f.serviceTimeMinutes) || 0),
		0
	);
	const totalShiftMinutes = vehicles.reduce(
		(sum, v) => sum + (Number(v.shiftMinutes) || 0),
		0
	);
	const maxShiftMinutes = vehicles.reduce(
		(max, v) => Math.max(max, Number(v.shiftMinutes) || 0),
		0
	);

	if (totalShiftMinutes <= 0) {
		result.ok = false;
		result.errors.push(
			"Total vehicle shift time is zero. Please set shift minutes."
		);
	} else if (totalServiceMinutes > totalShiftMinutes) {
		result.ok = false;
		result.errors.push(
			`Total field service time (${totalServiceMinutes.toFixed(
				1
			)} min) exceeds total available vehicle shift time (${totalShiftMinutes.toFixed(
				1
			)} min).`
		);
	}

	fields.forEach((f) => {
		const svc = Number(f.serviceTimeMinutes) || 0;
		if (svc > maxShiftMinutes) {
			result.ok = false;
			result.errors.push(
				`Field #${f.id} requires ${svc.toFixed(
					1
				)} min service, which is longer than any single vehicle shift (${maxShiftMinutes.toFixed(
					1
				)} min).`
			);
		}
	});

	return result;
}

export async function POST(request: NextRequest) {
	try {
		const body: RequestBody = await request.json();

		if (!body.depot || !Array.isArray(body.fields)) {
			return NextResponse.json(
				{ error: "You must send a depot and a fields array." },
				{ status: 400 }
			);
		}

		if (!Array.isArray(body.vehicles) || body.vehicles.length === 0) {
			return NextResponse.json(
				{ error: "You must send at least one vehicle." },
				{ status: 400 }
			);
		}

		const depotLon = Number(body.depot.lon);
		const depotLat = Number(body.depot.lat);

		if (Number.isNaN(depotLon) || Number.isNaN(depotLat)) {
			return NextResponse.json(
				{ error: "Depot lat/lon must be numbers." },
				{ status: 400 }
			);
		}

		// ---- 1) FEASIBILITY CHECK FIRST ----
		const feasibility = checkFeasibility(body);
		if (!feasibility.ok) {
			return NextResponse.json(
				{
					error: "Feasibility check failed",
					errorType: "FEASIBILITY",
					details: feasibility,
				},
				{ status: 400 }
			);
		}

		// ---- 2) Build jobs for ORS ----
		const jobs = body.fields.map((field) => {
			const lon = Number(field.lon);
			const lat = Number(field.lat);

			if (Number.isNaN(lon) || Number.isNaN(lat)) {
				throw new Error(`Invalid coordinates for field ${field.id}`);
			}

			const demand = Number(field.demand);
			const serviceMinutes = Number(field.serviceTimeMinutes);

			const demandUnits = Number.isNaN(demand)
				? 1
				: Math.max(1, Math.round(demand));
			const serviceSeconds = Math.round(
				(Number.isNaN(serviceMinutes) ? 15 : serviceMinutes) * 60
			);

			return {
				id: field.id,
				location: [lon, lat], // [lon, lat]
				amount: [demandUnits],
				service: serviceSeconds,
			};
		});

		// ---- 3) Build vehicles for ORS ----
		const vehicles = body.vehicles.map((v, idx) => {
			const capacity = Number(v.capacity);
			const shiftMinutes = Number(v.shiftMinutes);

			const capacityUnits = Number.isNaN(capacity)
				? 20
				: Math.max(1, Math.round(capacity));
			let timeWindow: [number, number] | undefined = undefined;

			if (!Number.isNaN(shiftMinutes) && shiftMinutes > 0) {
				const shiftSeconds = Math.round(shiftMinutes * 60);
				// Vehicle available from t=0 to t=shiftSeconds
				timeWindow = [0, shiftSeconds];
			}

			const vehicle: Record<string, unknown> = {
				id: v.id || idx + 1,
				profile: "driving-car",
				start: [depotLon, depotLat],
				end: [depotLon, depotLat],
				capacity: [capacityUnits],
			};

			if (timeWindow) {
				vehicle.time_window = timeWindow;
			}

			return vehicle;
		});

		const orsPayload = {
			jobs,
			vehicles,
			options: {
				g: true, // return geometry
			},
		};

		const ORS_API_KEY = process.env.ORS_API_KEY;

		if (!ORS_API_KEY) {
			return NextResponse.json(
				{ error: "ORS_API_KEY is not configured on the server." },
				{ status: 503 }
			);
		}

		const orsRes = await axios.post(
			"https://api.openrouteservice.org/optimization",
			orsPayload,
			{
				headers: {
					Authorization: ORS_API_KEY,
					"Content-Type": "application/json",
				},
				timeout: 30000,
			}
		);

		return NextResponse.json({
			request: body,
			orsRequest: orsPayload,
			orsSolution: orsRes.data,
		});
	} catch (err: unknown) {
		const error = err as {
			message?: string;
			response?: { status?: number; data?: unknown };
			stack?: string;
		};
		console.error("Optimization error:", error.message);

		if (error.response) {
			console.error("ORS status:", error.response.status);
			console.error(
				"ORS error body:",
				JSON.stringify(error.response.data, null, 2)
			);
			return NextResponse.json(
				{
					error: "ORS optimization call failed",
					errorType: "ORS",
					orsError: error.response.data,
				},
				{ status: error.response.status || 500 }
			);
		}

		console.error(error.stack);
		return NextResponse.json(
			{
				error: "Internal server error",
				errorType: "INTERNAL",
				details: error.message,
			},
			{ status: 500 }
		);
	}
}
