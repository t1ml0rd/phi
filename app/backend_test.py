import requests
import sys
import json
from datetime import datetime

class AIPhysicsAPITester:
    def __init__(self, base_url="https://ai-physics-lab-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.generated_task_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'List with ' + str(len(response_data)) + ' items'}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_get_topics(self):
        """Test getting physics topics"""
        success, response = self.run_test(
            "Get Physics Topics",
            "GET", 
            "topics",
            200
        )
        
        if success and response:
            expected_topics = ["Mechanics", "Electricity", "Optics", "Thermodynamics"]
            found_topics = list(response.keys()) if isinstance(response, dict) else []
            print(f"   Found topics: {found_topics}")
            
            # Check if all expected topics are present
            missing_topics = [topic for topic in expected_topics if topic not in found_topics]
            if missing_topics:
                print(f"   ⚠️  Missing topics: {missing_topics}")
            else:
                print(f"   ✅ All expected topics found")
        
        return success

    def test_generate_task(self):
        """Test physics task generation"""
        test_data = {
            "topic": "Mechanics",
            "difficulty": "easy",
            "count": 1
        }
        
        success, response = self.run_test(
            "Generate Physics Task",
            "POST",
            "generate", 
            200,
            data=test_data,
            timeout=60  # Longer timeout for AI generation
        )
        
        if success and response:
            if isinstance(response, list) and len(response) > 0:
                task = response[0]
                self.generated_task_id = task.get('id')
                print(f"   Generated task ID: {self.generated_task_id}")
                print(f"   Task text: {task.get('task_text', '')[:100]}...")
                print(f"   Topic: {task.get('topic')}")
                print(f"   Difficulty: {task.get('difficulty')}")
                print(f"   Answer: {task.get('numerical_answer')} {task.get('units')}")
                
                # Validate required fields
                required_fields = ['id', 'task_text', 'topic', 'difficulty', 'numerical_answer', 'units', 'latex']
                missing_fields = [field for field in required_fields if field not in task]
                if missing_fields:
                    print(f"   ⚠️  Missing required fields: {missing_fields}")
                else:
                    print(f"   ✅ All required fields present")
                    
                # Check if LaTeX formula is present
                if task.get('latex'):
                    print(f"   ✅ LaTeX formula: {task.get('latex')[:50]}...")
                
                # Check if SVG diagram is present
                if task.get('diagram_svg'):
                    print(f"   ✅ SVG diagram present (length: {len(task.get('diagram_svg'))} chars)")
                
            else:
                print(f"   ❌ Invalid response format: expected list with tasks")
                success = False
        
        return success

    def test_check_answer_correct(self):
        """Test answer checking with correct answer"""
        if not self.generated_task_id:
            print("❌ Skipping - No task ID available from generation test")
            return False
            
        # First get the task to know the correct answer
        success, history_response = self.run_test(
            "Get History for Answer Check",
            "GET",
            "history",
            200
        )
        
        if not success or not history_response:
            print("❌ Failed to get task history for answer checking")
            return False
            
        # Find our generated task
        task = None
        for t in history_response:
            if t.get('id') == self.generated_task_id:
                task = t
                break
                
        if not task:
            print("❌ Generated task not found in history")
            return False
            
        correct_answer = task.get('numerical_answer')
        print(f"   Using correct answer: {correct_answer}")
        
        test_data = {
            "task_id": self.generated_task_id,
            "user_answer": correct_answer,
            "tolerance": 0.001
        }
        
        success, response = self.run_test(
            "Check Correct Answer",
            "POST",
            "check",
            200,
            data=test_data
        )
        
        if success and response:
            is_correct = response.get('correct', False)
            feedback = response.get('feedback', '')
            print(f"   Answer marked as: {'Correct' if is_correct else 'Incorrect'}")
            print(f"   Feedback: {feedback}")
            
            if not is_correct:
                print(f"   ❌ Expected correct answer to be marked as correct")
                success = False
        
        return success

    def test_check_answer_incorrect(self):
        """Test answer checking with incorrect answer"""
        if not self.generated_task_id:
            print("❌ Skipping - No task ID available from generation test")
            return False
            
        test_data = {
            "task_id": self.generated_task_id,
            "user_answer": 999.999,  # Obviously wrong answer
            "tolerance": 0.001
        }
        
        success, response = self.run_test(
            "Check Incorrect Answer",
            "POST",
            "check",
            200,
            data=test_data
        )
        
        if success and response:
            is_correct = response.get('correct', True)  # Default to True to test
            feedback = response.get('feedback', '')
            print(f"   Answer marked as: {'Correct' if is_correct else 'Incorrect'}")
            print(f"   Feedback: {feedback}")
            
            if is_correct:
                print(f"   ❌ Expected incorrect answer to be marked as incorrect")
                success = False
        
        return success

    def test_get_history(self):
        """Test getting task history"""
        success, response = self.run_test(
            "Get Task History",
            "GET",
            "history",
            200
        )
        
        if success and response:
            if isinstance(response, list):
                print(f"   Found {len(response)} tasks in history")
                if len(response) > 0:
                    task = response[0]
                    print(f"   Latest task: {task.get('topic')} - {task.get('difficulty')}")
                    print(f"   Task text: {task.get('task_text', '')[:50]}...")
            else:
                print(f"   ❌ Invalid response format: expected list")
                success = False
        
        return success

    def test_invalid_endpoints(self):
        """Test invalid endpoints return proper errors"""
        success, response = self.run_test(
            "Invalid Endpoint",
            "GET",
            "nonexistent",
            404
        )
        return success

    def test_invalid_task_generation(self):
        """Test task generation with invalid data"""
        test_data = {
            "topic": "InvalidTopic",
            "difficulty": "impossible",
            "count": 1
        }
        
        # This might return 200 with a fallback task or 400/500 for invalid data
        # Let's see what happens
        success, response = self.run_test(
            "Invalid Task Generation Data",
            "POST",
            "generate",
            200,  # Expecting 200 because backend has fallback
            data=test_data,
            timeout=30
        )
        
        return success  # Any response is acceptable for this test

def main():
    print("🧪 AI Physics Task Generator API Testing")
    print("=" * 50)
    
    tester = AIPhysicsAPITester()
    
    # Run all tests in sequence
    tests = [
        tester.test_health_check,
        tester.test_get_topics,
        tester.test_generate_task,
        tester.test_check_answer_correct,
        tester.test_check_answer_incorrect,
        tester.test_get_history,
        tester.test_invalid_endpoints,
        tester.test_invalid_task_generation
    ]
    
    print(f"\n🚀 Running {len(tests)} API tests...")
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"❌ {failed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())