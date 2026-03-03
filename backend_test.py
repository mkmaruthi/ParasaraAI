#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ParasaraAstroAPITester:
    def __init__(self, base_url: str = "https://parasara-charts.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_session_id = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def log(self, message: str, level: str = "INFO"):
        print(f"[{level}] {datetime.now().strftime('%H:%M:%S')} - {message}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, data: Optional[Dict] = None, timeout: int = 30) -> tuple[bool, Any]:
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('http') else endpoint
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name} - {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}", "SUCCESS")
                if isinstance(response_data, dict) and len(str(response_data)) < 200:
                    self.log(f"   Response: {response_data}")
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}", "ERROR")
                self.log(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.Timeout:
            self.log(f"❌ FAILED - Request timeout after {timeout}s", "ERROR")
            return False, "Timeout"
        except Exception as e:
            self.log(f"❌ FAILED - Error: {str(e)}", "ERROR")
            return False, str(e)

    def test_health_endpoints(self):
        """Test basic health and connectivity"""
        self.log("=== Testing Health & Connectivity ===")
        
        # Test root endpoint
        self.run_test("Root endpoint", "GET", "", 200)
        
        # Test health endpoint
        self.run_test("Health check", "GET", "health", 200)

    def test_geocoding(self):
        """Test geocoding functionality"""
        self.log("=== Testing Geocoding ===")
        
        # Test valid place search
        success, response = self.run_test(
            "Geocode Mumbai", "POST", 
            "geocode?place_name=Mumbai,%20India", 
            200, 
            timeout=15
        )
        
        if success and isinstance(response, dict):
            results = response.get('results', [])
            if results:
                self.log(f"   Found {len(results)} locations")
                first_result = results[0]
                required_fields = ['place_name', 'latitude', 'longitude', 'timezone']
                for field in required_fields:
                    if field not in first_result:
                        self.log(f"   Missing field: {field}", "WARNING")
            else:
                self.log("   No results returned", "WARNING")
        
        # Test invalid place search
        self.run_test(
            "Geocode invalid place", "POST", 
            "geocode?place_name=InvalidPlace12345", 
            200
        )

    def test_chart_generation(self):
        """Test chart generation with sample birth data"""
        self.log("=== Testing Chart Generation ===")
        
        # Sample birth data
        birth_data = {
            "name": "Test User",
            "date_of_birth": "1990-01-15",
            "time_of_birth": "10:30:00", 
            "place_of_birth": "Mumbai, India",
            "gender": "male",
            "latitude": None,
            "longitude": None,
            "timezone_str": None
        }
        
        success, response = self.run_test(
            "Generate chart with place name", "POST", 
            "chart/generate", 
            200, 
            birth_data,
            timeout=45  # Chart generation can be slow
        )
        
        if success and isinstance(response, dict):
            # Verify response structure
            required_fields = ['session_id', 'chart_data', 'birth_details', 'created_at']
            for field in required_fields:
                if field not in response:
                    self.log(f"   Missing field in response: {field}", "WARNING")
                else:
                    self.log(f"   ✓ Found {field}")
            
            # Store session ID for later tests
            if 'session_id' in response:
                self.test_session_id = response['session_id']
                self.log(f"   Session ID: {self.test_session_id}")
            
            # Verify chart data structure
            chart_data = response.get('chart_data', {})
            if chart_data:
                chart_sections = ['birth_info', 'ascendant', 'planets', 'houses', 'chart_layout']
                for section in chart_sections:
                    if section in chart_data:
                        self.log(f"   ✓ Chart has {section}")
                    else:
                        self.log(f"   Missing chart section: {section}", "WARNING")
                
                # Check planets data
                planets = chart_data.get('planets', [])
                if planets:
                    self.log(f"   Found {len(planets)} planets")
                    planet_names = [p.get('name') for p in planets if p.get('name')]
                    self.log(f"   Planets: {', '.join(planet_names[:5])}...")
                else:
                    self.log("   No planets found in chart", "WARNING")
        
        # Test with manual coordinates
        birth_data_coords = {
            "name": "Test User Manual",
            "date_of_birth": "1985-06-20",
            "time_of_birth": "14:30:00",
            "place_of_birth": "Delhi, India", 
            "gender": "female",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone_str": "Asia/Kolkata"
        }
        
        self.run_test(
            "Generate chart with coordinates", "POST", 
            "chart/generate", 
            200, 
            birth_data_coords,
            timeout=45
        )
        
        # Test with missing required data
        invalid_data = {
            "name": "Test Invalid",
            # Missing other required fields
        }
        
        self.run_test(
            "Generate chart with invalid data", "POST", 
            "chart/generate", 
            422,  # FastAPI validation error
            invalid_data
        )

    def test_session_management(self):
        """Test session retrieval and management"""
        self.log("=== Testing Session Management ===")
        
        # Get all sessions
        success, response = self.run_test(
            "Get all sessions", "GET", 
            "chart/sessions", 
            200
        )
        
        if success and isinstance(response, dict):
            sessions = response.get('sessions', [])
            self.log(f"   Found {len(sessions)} total sessions")
        
        # Get specific session (if we have one)
        if self.test_session_id:
            success, response = self.run_test(
                "Get specific session", "GET", 
                f"chart/session/{self.test_session_id}", 
                200
            )
            
            if success and isinstance(response, dict):
                session = response.get('session')
                messages = response.get('messages', [])
                if session:
                    self.log(f"   Session name: {session.get('name', 'N/A')}")
                    self.log(f"   Messages: {len(messages)}")
                else:
                    self.log("   No session data returned", "WARNING")
        else:
            self.log("   No test session ID available, skipping specific session test", "WARNING")
        
        # Test non-existent session
        self.run_test(
            "Get non-existent session", "GET", 
            "chart/session/invalid-session-id", 
            404
        )

    def test_chat_functionality(self):
        """Test chat functionality"""
        self.log("=== Testing Chat Functionality ===")
        
        if not self.test_session_id:
            self.log("   No test session ID available, skipping chat tests", "WARNING")
            return
        
        # Send a chat message
        chat_data = {
            "session_id": self.test_session_id,
            "message": "What does my Sun sign mean?"
        }
        
        success, response = self.run_test(
            "Send chat message", "POST", 
            "chat", 
            200, 
            chat_data,
            timeout=30
        )
        
        if success and isinstance(response, dict):
            ai_response = response.get('response', '')
            message_id = response.get('message_id', '')
            if ai_response:
                self.log(f"   AI response length: {len(ai_response)} chars")
                self.log(f"   Message ID: {message_id}")
            else:
                self.log("   No AI response received", "WARNING")
        
        # Test chat with invalid session
        invalid_chat = {
            "session_id": "invalid-session",
            "message": "Test message"
        }
        
        self.run_test(
            "Chat with invalid session", "POST", 
            "chat", 
            404, 
            invalid_chat
        )
        
        # Test empty message
        empty_chat = {
            "session_id": self.test_session_id,
            "message": ""
        }
        
        # This might return 422 or still 200 depending on validation
        self.run_test(
            "Chat with empty message", "POST", 
            "chat", 
            200, 
            empty_chat
        )

    def test_session_deletion(self):
        """Test session deletion"""
        self.log("=== Testing Session Deletion ===")
        
        if self.test_session_id:
            # Delete the test session
            self.run_test(
                "Delete test session", "DELETE", 
                f"chart/session/{self.test_session_id}", 
                200
            )
            
            # Verify it's gone
            self.run_test(
                "Verify session deleted", "GET", 
                f"chart/session/{self.test_session_id}", 
                404
            )
        else:
            self.log("   No test session to delete", "WARNING")
        
        # Test deleting non-existent session
        self.run_test(
            "Delete non-existent session", "DELETE", 
            "chart/session/non-existent-id", 
            200  # Usually returns 200 even if not found
        )

    def run_all_tests(self):
        """Run the complete test suite"""
        start_time = datetime.now()
        self.log("🚀 Starting Parasara Astro AI API Tests")
        self.log(f"Base URL: {self.base_url}")
        
        try:
            self.test_health_endpoints()
            self.test_geocoding()
            self.test_chart_generation()
            self.test_session_management() 
            self.test_chat_functionality()
            self.test_session_deletion()
            
        except KeyboardInterrupt:
            self.log("Tests interrupted by user", "WARNING")
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.log("=" * 50)
        self.log(f"📊 TEST SUMMARY")
        self.log(f"   Tests Run: {self.tests_run}")
        self.log(f"   Tests Passed: {self.tests_passed}")
        self.log(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        self.log(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        self.log(f"   Duration: {duration:.1f}s")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 ALL TESTS PASSED!", "SUCCESS")
            return 0
        else:
            self.log(f"❌ {self.tests_run - self.tests_passed} TESTS FAILED", "ERROR")
            return 1

def main():
    tester = ParasaraAstroAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())