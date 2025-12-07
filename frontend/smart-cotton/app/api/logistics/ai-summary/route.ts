import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

interface Facts {
	totals: {
		distance: number;
		time: number;
		capacity: number;
	};
	vehicles: Array<{
		name: string;
		distance: number;
		hours: number;
		load: number;
	}>;
	unassignedCount: number;
}

export async function POST(request: NextRequest) {
	try {
		const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

		if (!GEMINI_API_KEY) {
			return NextResponse.json(
				{
					error: "Gemini not configured on server (missing GEMINI_API_KEY).",
				},
				{ status: 503 }
			);
		}

		const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
		const geminiModel = genAI.getGenerativeModel({
			model: "gemini-2.0-flash-exp",
		});

		const body = await request.json();
		const facts: Facts = body.facts;

		if (!facts) {
			return NextResponse.json(
				{ error: "Missing 'facts' in request body." },
				{ status: 400 }
			);
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

		return NextResponse.json({ text });
	} catch (err: unknown) {
		const error = err as { message?: string };
		console.error("Gemini /ai-summary error:", error?.message || err);
		return NextResponse.json(
			{ error: "Failed to generate AI summary" },
			{ status: 500 }
		);
	}
}
