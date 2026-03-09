"""
Gameplay tests for edge cases discovered during debugging.

Tests for:
1. Hint messages (were backwards)
2. Correct guess comparison logic
3. Parse guess edge cases
4. Range selection for difficulty levels
"""

import pytest
from logic_utils import check_guess, parse_guess, get_range_for_difficulty, update_score


class TestCheckGuessHints:
    """Test the check_guess function hints (were backwards originally)."""
    
    def test_guess_too_high_returns_correct_message(self):
        """When guess > secret, should return 'Too High' with 'Go LOWER!' hint."""
        outcome, message = check_guess(75, 50)
        assert outcome == "Too High"
        assert "LOWER" in message
    
    def test_guess_too_low_returns_correct_message(self):
        """When guess < secret, should return 'Too Low' with 'Go HIGHER!' hint."""
        outcome, message = check_guess(25, 50)
        assert outcome == "Too Low"
        assert "HIGHER" in message
    
    def test_correct_guess_wins(self):
        """When guess == secret, should return 'Win'."""
        outcome, message = check_guess(50, 50)
        assert outcome == "Win"
        assert "Correct" in message
    
    def test_boundary_high(self):
        """Test boundary: guess at upper limit."""
        outcome, message = check_guess(100, 50)
        assert outcome == "Too High"
        assert "LOWER" in message
    
    def test_boundary_low(self):
        """Test boundary: guess at lower limit."""
        outcome, message = check_guess(1, 50)
        assert outcome == "Too Low"
        assert "HIGHER" in message
    
    def test_off_by_one_high(self):
        """Test off-by-one: guess one above secret."""
        outcome, message = check_guess(51, 50)
        assert outcome == "Too High"
        assert "LOWER" in message
    
    def test_off_by_one_low(self):
        """Test off-by-one: guess one below secret."""
        outcome, message = check_guess(49, 50)
        assert outcome == "Too Low"
        assert "HIGHER" in message


class TestParseGuess:
    """Test parse_guess edge cases."""
    
    def test_valid_integer(self):
        """Parse a valid integer string."""
        ok, guess, error = parse_guess("42")
        assert ok is True
        assert guess == 42
        assert error is None
    
    def test_floating_point_conversion(self):
        """Parse float and convert to int."""
        ok, guess, error = parse_guess("50.7")
        assert ok is True
        assert guess == 50
        assert error is None
    
    def test_empty_string(self):
        """Empty string should return error."""
        ok, guess, error = parse_guess("")
        assert ok is False
        assert guess is None
        assert error is not None
    
    def test_none_input(self):
        """None input should return error."""
        ok, guess, error = parse_guess(None)
        assert ok is False
        assert guess is None
        assert error is not None
    
    def test_non_numeric_string(self):
        """Non-numeric string should return error."""
        ok, guess, error = parse_guess("abc")
        assert ok is False
        assert guess is None
        assert error is not None
    
    def test_negative_number(self):
        """Parse negative numbers."""
        ok, guess, error = parse_guess("-5")
        assert ok is True
        assert guess == -5
        assert error is None
    
    def test_large_number(self):
        """Parse large numbers."""
        ok, guess, error = parse_guess("999999")
        assert ok is True
        assert guess == 999999
        assert error is None


class TestDifficultyRanges:
    """Test get_range_for_difficulty."""
    
    def test_easy_range(self):
        """Easy difficulty should be 1-20."""
        low, high = get_range_for_difficulty("Easy")
        assert low == 1
        assert high == 20
    
    def test_normal_range(self):
        """Normal difficulty should be 1-100."""
        low, high = get_range_for_difficulty("Normal")
        assert low == 1
        assert high == 100
    
    def test_hard_range(self):
        """Hard difficulty should be 1-50."""
        low, high = get_range_for_difficulty("Hard")
        assert low == 1
        assert high == 50
    
    def test_invalid_difficulty_defaults(self):
        """Invalid difficulty should default to 1-100."""
        low, high = get_range_for_difficulty("Impossible")
        assert low == 1
        assert high == 100


class TestUpdateScore:
    """Test score updating logic."""
    
    def test_win_score_first_attempt(self):
        """Winning on first attempt should give max points."""
        score = update_score(0, "Win", 0)
        assert score == 90  # 100 - 10*(0+1) = 90
    
    def test_win_score_later_attempt(self):
        """Winning on later attempt should give fewer points."""
        score = update_score(0, "Win", 5)
        assert score == 40  # 100 - 10*(5+1) = 40
    
    def test_win_score_minimum_points(self):
        """Winning after many attempts should give minimum 10 points."""
        score = update_score(0, "Win", 15)
        assert score == 10  # min(100 - 10*16, 10) = 10
    
    def test_too_high_even_attempt(self):
        """Too High on even attempt number gets +5 bonus."""
        score = update_score(50, "Too High", 0)
        assert score == 55
    
    def test_too_high_odd_attempt(self):
        """Too High on odd attempt number loses -5."""
        score = update_score(50, "Too High", 1)
        assert score == 45
    
    def test_too_low_always_loses(self):
        """Too Low always loses -5 points."""
        score = update_score(50, "Too Low", 0)
        assert score == 45
        score = update_score(50, "Too Low", 99)
        assert score == 45


class TestStateManagement:
    """Test scenarios that relate to the "New Game" bug."""
    
    def test_multiple_wins_possible(self):
        """Winning multiple times in sequence should work."""
        # First game
        outcome1, _ = check_guess(50, 50)
        assert outcome1 == "Win"
        
        # Second game (different secret)
        outcome2, _ = check_guess(75, 25)
        assert outcome2 == "Too High"
        
        # Can still win second game
        outcome3, _ = check_guess(25, 25)
        assert outcome3 == "Win"
    
    def test_game_over_scenarios(self):
        """Test that different outcomes are distinct."""
        # Win
        outcome1, msg1 = check_guess(50, 50)
        assert "Correct" in msg1
        
        # Lose (too high)
        outcome2, msg2 = check_guess(100, 50)
        assert outcome2 == "Too High"
        assert outcome2 != outcome1
        
        # Lose (too low)
        outcome3, msg3 = check_guess(1, 50)
        assert outcome3 == "Too Low"
        assert outcome3 != outcome1
        assert outcome3 != outcome2
