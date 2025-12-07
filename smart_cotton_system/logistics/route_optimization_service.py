"""
Route Optimization Service for Smart Cotton System
Integrates OpenRouteService (ORS) API for vehicle routing and Google Gemini for AI insights
"""

import os
import requests
import json
from typing import Dict, List, Any, Optional
from django.conf import settings
import google.generativeai as genai


class RouteOptimizationService:
    """Service for optimizing cotton harvest routes using ORS API"""
    
    def __init__(self):
        self.ors_api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQ2MThjYzA3YzNhMTQyYzJhZGVkMjM2MjJmMDRkNTRlIiwiaCI6Im11cm11cjY0In0"
        self.gemini_api_key = "AIzaSyB0C-rnKC0afj9DBuyFW5YhhF9Qrl7xtJ0"
        
        if not self.ors_api_key:
            print("⚠️ Warning: ORS_API_KEY not set in environment")
            
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            print("⚠️ Warning: GEMINI_API_KEY not set - AI summary will be disabled")
            self.gemini_model = None
    
    def check_feasibility(self, fields: List[Dict], vehicles: List[Dict]) -> Dict[str, Any]:
        """
        Check feasibility of the route optimization problem before calling ORS API
        
        Args:
            fields: List of field dictionaries with demand and service time
            vehicles: List of vehicle dictionaries with capacity and shift time
            
        Returns:
            Dictionary with ok, errors, and warnings
        """
        result = {
            'ok': True,
            'errors': [],
            'warnings': []
        }
        
        if not fields:
            result['ok'] = False
            result['errors'].append('No fields were provided.')
            return result
            
        if not vehicles:
            result['ok'] = False
            result['errors'].append('No vehicles were provided.')
            return result
        
        # Check total demand vs total capacity
        total_demand = sum(float(f.get('demand', 0)) for f in fields)
        total_capacity = sum(float(v.get('capacity', 0)) for v in vehicles)
        
        if total_capacity <= 0:
            result['ok'] = False
            result['errors'].append('Total vehicle capacity is zero or negative.')
        elif total_demand > total_capacity:
            result['ok'] = False
            result['errors'].append(
                f'Total field demand ({total_demand:.1f} units) exceeds '
                f'total vehicle capacity ({total_capacity:.1f} units).'
            )
        
        # Check total service time vs total shift time
        total_service_minutes = sum(float(f.get('serviceTimeMinutes', 0)) for f in fields)
        total_shift_minutes = sum(float(v.get('shiftMinutes', 0)) for v in vehicles)
        max_shift_minutes = max((float(v.get('shiftMinutes', 0)) for v in vehicles), default=0)
        
        if total_shift_minutes <= 0:
            result['ok'] = False
            result['errors'].append('Total vehicle shift time is zero. Please set shift minutes.')
        elif total_service_minutes > total_shift_minutes:
            result['ok'] = False
            result['errors'].append(
                f'Total field service time ({total_service_minutes:.1f} min) exceeds '
                f'total available vehicle shift time ({total_shift_minutes:.1f} min).'
            )
        
        # Check if any single field service time exceeds max shift
        for field in fields:
            service_time = float(field.get('serviceTimeMinutes', 0))
            if service_time > max_shift_minutes:
                result['ok'] = False
                result['errors'].append(
                    f'Field #{field.get("id")} requires {service_time:.1f} min service, '
                    f'which is longer than any single vehicle shift ({max_shift_minutes:.1f} min).'
                )
        
        return result
    
    def optimize_routes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize routes using OpenRouteService API
        
        Args:
            data: Dictionary containing depot, vehicles, and fields information
            
        Returns:
            Dictionary with optimization results or error information
        """
        # Validate input
        if 'depot' not in data or 'fields' not in data:
            return {
                'error': 'You must send a depot and a fields array.',
                'errorType': 'VALIDATION'
            }
            
        if 'vehicles' not in data or not data['vehicles']:
            return {
                'error': 'You must send at least one vehicle.',
                'errorType': 'VALIDATION'
            }
        
        depot = data['depot']
        fields = data['fields']
        vehicles = data['vehicles']
        
        # Validate depot coordinates
        try:
            depot_lon = float(depot['lon'])
            depot_lat = float(depot['lat'])
        except (KeyError, ValueError, TypeError):
            return {
                'error': 'Depot lat/lon must be numbers.',
                'errorType': 'VALIDATION'
            }
        
        # Check feasibility
        feasibility = self.check_feasibility(fields, vehicles)
        if not feasibility['ok']:
            return {
                'error': 'Feasibility check failed',
                'errorType': 'FEASIBILITY',
                'details': feasibility
            }
        
        # Build jobs for ORS
        jobs = []
        for field in fields:
            try:
                lon = float(field['lon'])
                lat = float(field['lat'])
                demand = float(field.get('demand', 1))
                service_minutes = float(field.get('serviceTimeMinutes', 15))
                
                demand_units = max(1, round(demand))
                service_seconds = round(service_minutes * 60)
                
                jobs.append({
                    'id': field['id'],
                    'location': [lon, lat],
                    'amount': [demand_units],
                    'service': service_seconds
                })
            except (KeyError, ValueError, TypeError) as e:
                return {
                    'error': f'Invalid field data: {str(e)}',
                    'errorType': 'VALIDATION'
                }
        
        # Build vehicles for ORS
        ors_vehicles = []
        for idx, vehicle in enumerate(vehicles):
            try:
                capacity = float(vehicle.get('capacity', 20))
                shift_minutes = float(vehicle.get('shiftMinutes', 480))
                
                capacity_units = max(1, round(capacity))
                
                vehicle_data = {
                    'id': vehicle.get('id', idx + 1),
                    'profile': 'driving-car',
                    'start': [depot_lon, depot_lat],
                    'end': [depot_lon, depot_lat],
                    'capacity': [capacity_units]
                }
                
                if shift_minutes > 0:
                    shift_seconds = round(shift_minutes * 60)
                    vehicle_data['time_window'] = [0, shift_seconds]
                
                ors_vehicles.append(vehicle_data)
            except (ValueError, TypeError) as e:
                return {
                    'error': f'Invalid vehicle data: {str(e)}',
                    'errorType': 'VALIDATION'
                }
        
        # Build ORS payload
        ors_payload = {
            'jobs': jobs,
            'vehicles': ors_vehicles,
            'options': {
                'g': True  # return geometry
            }
        }
        
        # Call ORS API
        if not self.ors_api_key:
            return {
                'error': 'ORS_API_KEY not configured. Please set it in your environment variables.',
                'errorType': 'CONFIG'
            }
        
        try:
            # OpenRouteService Optimization API endpoint (VROOM-based)
            # Note: Free tier might not support optimization API
            # Alternative: use v2/optimization or check if your key has optimization access
            response = requests.post(
                'https://api.openrouteservice.org/optimization',
                json=ors_payload,
                headers={
                    'Authorization': self.ors_api_key,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'error': 'ORS optimization call failed',
                    'errorType': 'ORS',
                    'orsError': response.json() if response.content else None,
                    'statusCode': response.status_code
                }
            
            ors_solution = response.json()
            
            return {
                'request': data,
                'orsRequest': ors_payload,
                'orsSolution': ors_solution
            }
            
        except requests.exceptions.Timeout:
            return {
                'error': 'ORS API request timed out',
                'errorType': 'TIMEOUT'
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': f'ORS API request failed: {str(e)}',
                'errorType': 'NETWORK'
            }
        except Exception as e:
            return {
                'error': f'Internal server error: {str(e)}',
                'errorType': 'INTERNAL'
            }
    
    def generate_ai_summary(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI summary using Google Gemini
        
        Args:
            facts: Dictionary containing optimization results and statistics
            
        Returns:
            Dictionary with AI-generated summary text or error
        """
        if not self.gemini_model:
            return {
                'error': 'Gemini not configured on server (missing GEMINI_API_KEY).',
                'errorType': 'CONFIG'
            }
        
        if not facts:
            return {
                'error': "Missing 'facts' in request.",
                'errorType': 'VALIDATION'
            }
        
        prompt = f"""
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
{json.dumps(facts, indent=2)}
        """.strip()
        
        try:
            result = self.gemini_model.generate_content(prompt)
            text = result.text
            
            return {'text': text}
            
        except Exception as e:
            return {
                'error': f'Failed to generate AI summary: {str(e)}',
                'errorType': 'GEMINI'
            }
