"""Tests for the High School Management System API endpoints using AAA pattern."""

import pytest


class TestGetActivities:
    """Test suite for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities with correct structure."""
        # Arrange
        # (Activities are already set up by reset_activities fixture)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 3
    
    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """Test that each activity has the required fields."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(set(activity_data.keys()))
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_get_activities_includes_existing_participants(self, client, reset_activities):
        """Test that activities include participants signed up."""
        # Arrange
        # (Chess Club has michael@mergington.edu and daniel@mergington.edu)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 2


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_participant_success(self, client, reset_activities):
        """Test successful signup of a new participant to an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert email in data[activity_name]["participants"]
        assert len(data[activity_name]["participants"]) == 3  # Original 2 + 1 new
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up twice with same email fails."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signup fails when activity doesn't exist."""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_multiple_participants_to_same_activity(self, client, reset_activities):
        """Test that multiple different participants can sign up to the same activity."""
        # Arrange
        activity_name = "Programming Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        response2 = client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        activities_response = client.get("/activities")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data = activities_response.json()
        assert email1 in data[activity_name]["participants"]
        assert email2 in data[activity_name]["participants"]
        assert len(data[activity_name]["participants"]) == 4  # Original 2 + 2 new
    
    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with URL-encoded email addresses."""
        # Arrange
        activity_name = "Chess Club"
        email = "first.last+tag@example.com"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        verify_response = client.get("/activities")
        assert email in verify_response.json()[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_unregister_existing_participant_success(self, client, reset_activities):
        """Test successful unregistration of an existing participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    def test_unregister_removes_participant_from_activity(self, client, reset_activities):
        """Test that unregister actually removes the participant from the activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert email not in data[activity_name]["participants"]
        assert len(data[activity_name]["participants"]) == 1  # Original 2 - 1 removed
        assert "daniel@mergington.edu" in data[activity_name]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client, reset_activities):
        """Test that unregistering a participant not in the activity fails."""
        # Arrange
        activity_name = "Chess Club"
        email = "notaparticipant@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from a nonexistent activity fails."""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple different participants."""
        # Arrange
        activity_name = "Gym Class"
        email1 = "john@mergington.edu"
        email2 = "olivia@mergington.edu"
        
        # Act
        response1 = client.delete(f"/activities/{activity_name}/signup", params={"email": email1})
        response2 = client.delete(f"/activities/{activity_name}/signup", params={"email": email2})
        activities_response = client.get("/activities")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        data = activities_response.json()
        assert email1 not in data[activity_name]["participants"]
        assert email2 not in data[activity_name]["participants"]
        assert len(data[activity_name]["participants"]) == 0


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""
    
    def test_full_signup_and_unregister_flow(self, client, reset_activities):
        """Test a complete workflow: signup, verify, unregister, verify."""
        # Arrange
        activity_name = "Programming Class"
        email = "integration@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        activities_after_signup = client.get("/activities").json()
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_after_unregister = client.get("/activities").json()
        
        # Assert
        assert signup_response.status_code == 200
        assert email in activities_after_signup[activity_name]["participants"]
        
        assert unregister_response.status_code == 200
        assert email not in activities_after_unregister[activity_name]["participants"]
    
    def test_simultaneous_signups_to_different_activities(self, client, reset_activities):
        """Test that a single participant can sign up to multiple activities."""
        # Arrange
        email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        responses = []
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup", params={"email": email})
            responses.append(response)
        
        all_activities = client.get("/activities").json()
        
        # Assert
        for response in responses:
            assert response.status_code == 200
        
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
