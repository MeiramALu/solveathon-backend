// backend/server.js
require('dotenv').config();
const { GoogleGenerativeAI } = require("@google/generative-ai");

// --- Gemini client setup ---
const geminiApiKey = process.env.GEMINI_API_KEY;

let geminiModel = null;
if (!geminiApiKey) {
    console.warn("GEMINI_API_KEY not set – /ai-summary will be disabled.");
} else {
    const genAI = new GoogleGenerativeAI(geminiApiKey);
    geminiModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    // geminiModel = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
}


const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();

const ORS_API_KEY = process.env.ORS_API_KEY;
const PORT = process.env.PORT || 4000;

if (!ORS_API_KEY) {
    console.warn('⚠️ ORS_API_KEY is not set. Set it in backend/.env');
}

app.use(cors());
app.use(express.json());

/**
 * Simple feasibility checks BEFORE calling ORS.
 * We just check:
 *  - total demand <= total capacity
 *  - total service time <= total shift time
 *  - no single field service time > longest vehicle shift
 */
function checkFeasibility(body) {
    const fields = body.fields || [];
    const vehicles = body.vehicles || [];

    const result = {
        ok: true,
        errors: [],
        warnings: []
    };

    if (!fields.length) {
        result.ok = false;
        result.errors.push('No fields were provided.');
        return result;
    }

    if (!vehicles.length) {
        result.ok = false;
        result.errors.push('No vehicles were provided.');
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
        result.errors.push('Total vehicle capacity is zero or negative.');
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
        result.errors.push('Total vehicle shift time is zero. Please set shift minutes.');
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

    // You could add more "soft" checks here as warnings if you want.

    return result;
}

// Expected body:
// {
//   depot: { lat, lon },
//   vehicles: [
//     { id, name, capacity, shiftMinutes }
//   ],
//   fields: [
//     { id, lat, lon, demand, serviceTimeMinutes }
//   ]
// }
app.post('/optimize', async (req, res) => {
    try {
        const body = req.body;

        if (!body.depot || !Array.isArray(body.fields)) {
            return res.status(400).json({
                error: 'You must send a depot and a fields array.'
            });
        }

        if (!Array.isArray(body.vehicles) || body.vehicles.length === 0) {
            return res.status(400).json({
                error: 'You must send at least one vehicle.'
            });
        }

        const depotLon = Number(body.depot.lon);
        const depotLat = Number(body.depot.lat);

        if (Number.isNaN(depotLon) || Number.isNaN(depotLat)) {
            return res.status(400).json({ error: 'Depot lat/lon must be numbers.' });
        }

        // ---- 1) FEASIBILITY CHECK FIRST ----
        const feasibility = checkFeasibility(body);
        if (!feasibility.ok) {
            return res.status(400).json({
                error: 'Feasibility check failed',
                errorType: 'FEASIBILITY',
                details: feasibility
            });
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
                service: serviceSeconds
            };
        });

        // ---- 3) Build vehicles for ORS ----
        const vehicles = body.vehicles.map((v, idx) => {
            const capacity = Number(v.capacity);
            const shiftMinutes = Number(v.shiftMinutes);

            const capacityUnits = Number.isNaN(capacity)
                ? 20
                : Math.max(1, Math.round(capacity));
            let timeWindow = undefined;

            if (!Number.isNaN(shiftMinutes) && shiftMinutes > 0) {
                const shiftSeconds = Math.round(shiftMinutes * 60);
                // Vehicle available from t=0 to t=shiftSeconds
                timeWindow = [0, shiftSeconds];
            }

            const vehicle = {
                id: v.id || idx + 1,
                profile: 'driving-car',
                start: [depotLon, depotLat],
                end: [depotLon, depotLat],
                capacity: [capacityUnits]
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
                g: true // return geometry
            }
        };

        const orsRes = await axios.post(
            'https://api.openrouteservice.org/optimization',
            orsPayload,
            {
                headers: {
                    Authorization: ORS_API_KEY,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            }
        );

        res.json({
            request: body,
            orsRequest: orsPayload,
            orsSolution: orsRes.data
        });
    } catch (err) {
        console.error('Optimization error:', err.message);

        if (err.response) {
            console.error('ORS status:', err.response.status);
            console.error(
                'ORS error body:',
                JSON.stringify(err.response.data, null, 2)
            );
            return res.status(err.response.status || 500).json({
                error: 'ORS optimization call failed',
                errorType: 'ORS',
                orsError: err.response.data
            });
        }

        console.error(err.stack);
        res.status(500).json({
            error: 'Internal server error',
            errorType: 'INTERNAL',
            details: err.message
        });
    }
});
// POST /ai-summary
app.post("/ai-summary", async (req, res) => {
    try {
        if (!geminiModel) {
            return res.status(503).json({
                error: "Gemini not configured on server (missing GEMINI_API_KEY).",
            });
        }

        const facts = req.body.facts;
        if (!facts) {
            return res.status(400).json({ error: "Missing 'facts' in request body." });
        }

        const prompt = `
You are a logistics and farm operations expert.

You are helping optimize cotton harvest routes near Turkistan. You will receive a JSON object called "facts" which contains:

- totals: distance/time, capacity, savings vs a naive baseline
- vehicles: per-vehicle distance, hours, load
- unassignedCount: how many fields could not be served

TASK:
Write **exactly 3 bullet points** of practical insights for a farm manager.
Rules:
- Max 80 words total.
- Focus on: (1) utilization, (2) unassigned fields (if any), (3) distance/time savings and 1 simple recommendation.
- Do NOT output JSON, only plain text bullets starting with "- ".

facts:
${JSON.stringify(facts, null, 2)}
    `.trim();

        const result = await geminiModel.generateContent(prompt);
        const response = result.response;
        const text = response.text();

        return res.json({ text });
    } catch (err) {
        console.error("Gemini /ai-summary error:", err?.message || err);
        return res.status(500).json({ error: "Failed to generate AI summary" });
    }
});

app.listen(PORT, () => {
    console.log(`✅ Backend listening on http://localhost:${PORT}`);
    console.log(
        `   ORS key: ${ORS_API_KEY ? '***set***' : 'NOT SET (set ORS_API_KEY in .env)'}`
    );
});
