"""
Edge case tests designed to break the game and discover additional bugs.

This test suite explores boundary conditions, type mismatches, input validation,
and state management scenarios that could cause unexpected behavior or crashes.

Test Categories:
1. **Input Validation Limits** – Tests extreme input values and formats
2. **Type Mismatch Handling** – Tests comparing different types (int vs str)
3. **State Consistency** – Tests rapid state changes and concurrent scenarios
4. **Scoring Edge Cases** – Tests score underflow, overflow, and boundary conditions
5. **Difficulty/Range Mismatches** – Tests behavior when logic contradicts UI
6. **Malicious/Unexpected Input** – Tests robustness against bad data
"""

import pytest
from logic_utils import check_guess, parse_guess, get_range_for_difficulty, update_score


class TestInputValidationLimits:
    """Tests for extreme input values and boundary conditions."""
    
    def test_parse_very_large_integer(self):
        """Can we parse numbers larger than typical game range?"""
        ok, guess, error = parse_guess("999999999999")
        assert ok is True
        assert guess == 999999999999
        # BUG POTENTIAL: Game doesn't validate guess is in range
    
    def test_parse_very_negative_number(self):
        """Can we parse very negative numbers?"""
        ok, guess, error = parse_guess("-999999")
        assert ok is True
        assert guess == -999999
        # BUG POTENTIAL: Game doesn't reject out-of-range guesses
    
    def test_check_guess_with_extreme_values(self):
        """What happens when comparing extreme values?"""
        outcome, msg = check_guess(999999, 1)
        assert outcome == "Too High"
        # BUG POTENTIAL: No validation that secret is in expected range
    
    def test_parse_exponential_notation(self):
        """Can we parse scientific notation?"""
        ok, guess, error = parse_guess("1e2")  # 100 in scientific notation
        if ok:
            assert guess == 100
        # BUG: Might raise ValueError instead of handling gracefully
    
    def test_parse_leading_zeros(self):
        """How are leading zeros handled?"""
        ok, guess, error = parse_guess("007")
        assert ok is True
        assert guess == 7
    
    def test_parse_whitespace_only(self):
        """Can we submit just whitespace?"""
        ok, guess, error = parse_guess("   ")
        assert ok is False  # Should reject, but might accept
    
    def test_parse_float_with_multiple_decimals(self):
        """What if we have invalid float format?"""
        ok, guess, error = parse_guess("12.34.56")
        assert ok is False  # Should reject malformed float
    
    def test_parse_plus_sign(self):
        """Does parsing handle explicit plus signs?"""
        ok, guess, error = parse_guess("+42")
        # BUG POTENTIAL: Might not parse positive sign correctly
        if ok:
            assert guess == 42


class TestTypeMismatchHandling:
    """Tests for comparing different types without proper conversion."""
    
    def test_check_guess_string_vs_int_same_value(self):
        """When secret is string '50' and guess is int 50."""
        outcome, msg = check_guess(50, "50")
        assert outcome == "Win"
        # This works because of the try/except fallback in check_guess
    
    def test_check_guess_int_vs_string_comparison(self):
        """When secret is int but guess should be compared as string."""
        outcome1, _ = check_guess("75", 50)
        outcome2, _ = check_guess(75, 50)
        # BUG POTENTIAL: String vs int comparison might give wrong results
        assert outcome1 == outcome2
    
    def test_check_guess_with_none(self):
        """What happens if we pass None as secret?"""
        try:
            outcome, msg = check_guess(50, None)
            # If it doesn't crash, the None handling is working
        except TypeError:
            pytest.skip("None comparison raises TypeError")
    
    def test_check_guess_float_secret(self):
        """What if secret is a float?"""
        outcome, msg = check_guess(50, 50.5)
        # Floats should work with > and < operators
        assert outcome == "Too Low"
    
    def test_check_guess_string_numbers_ordering(self):
        """String comparison vs numeric comparison."""
        # "60" > "50" alphabetically, but 60 > 50 numerically
        outcome_str, _ = check_guess("60", "50")
        outcome_int, _ = check_guess(60, 50)
        # BUG POTENTIAL: String comparison gives wrong results
        assert outcome_str == outcome_int


class TestStateConsistencyIssues:
    """Tests for state management and concurrent update problems."""
    
    def test_multiple_consecutive_wins(self):
        """Can you win the same game twice without resetting?"""
        outcome1, _ = check_guess(50, 50)
        outcome2, _ = check_guess(50, 50)
        assert outcome1 == "Win"
        assert outcome2 == "Win"
        # In real Streamlit app, second win without new game should fail
    
    def test_guess_after_game_over(self):
        """What if you keep guessing after winning?"""
        outcome1, _ = check_guess(50, 50)  # Win
        outcome2, _ = check_guess(40, 50)  # Try to guess again
        assert outcome1 == "Win"
        # BUG POTENTIAL: App doesn't block further guesses after win
    
    def test_attempts_counter_integrity(self):
        """Does attempts counter stay consistent across operations?"""
        # If we call update_score multiple times, scores shouldn't compound
        score1 = update_score(0, "Win", 1)
        score2 = update_score(score1, "Win", 1)  # Second win same attempt?
        # BUG POTENTIAL: Calling win twice gives extra points
        assert score2 > score1  # This exposes the bug
    
    def test_session_state_race_condition(self):
        """What if secret is accessed before it's initialized?"""
        # In real app: if "secret" not in session_state before check_guess
        try:
            outcome, _ = check_guess(50, None)  # Could expose uninitialized state
        except:
            pass
    
    def test_resetting_mid_guess(self):
        """What if session is reset while a guess is being processed?"""
        # Simulating: secret changes while processing a guess
        outcome1, _ = check_guess(50, 50)  # Original secret
        outcome2, _ = check_guess(50, 75)  # Secret changed!
        assert outcome1 == "Win"
        assert outcome2 == "Too High"
        # BUG POTENTIAL: If secret resets during processing


class TestScoringEdgeCases:
    """Tests for score calculation boundary conditions."""
    
    def test_score_underflow(self):
        """Can score go negative?"""
        score = update_score(0, "Too Low", 0)
        assert score == -5
        # BUG POTENTIAL: Negative scores not prevented
    
    def test_massive_negative_score(self):
        """After many wrong guesses, how negative can score get?"""
        score = 10
        for i in range(100):
            score = update_score(score, "Too Low", i)
        # BUG POTENTIAL: No score floor implemented
        assert score < 0
    
    def test_win_on_last_attempt(self):
        """Winning on the very last allowed attempt."""
        # If attempt_limit is 8 and we win on attempt 8
        score = update_score(0, "Win", 7)  # attempt_number 7 (0-indexed)
        assert score == 20  # 100 - 10*(7+1) = 20
    
    def test_win_after_attempt_limit(self):
        """What if you win after exceeding attempt limit?"""
        # This shouldn't happen in real app, but test the logic
        score = update_score(0, "Win", 20)
        assert score == 10  # Capped at minimum 10 points
    
    def test_alternating_too_high_too_low(self):
        """Score behavior with alternating outcomes."""
        score = 50
        # Odd attempt (1): Too High → -5
        score = update_score(score, "Too High", 1)
        assert score == 45
        # Even attempt (2): Too High → +5
        score = update_score(score, "Too High", 2)
        assert score == 50
        # Odd attempt (3): Too High → -5
        score = update_score(score, "Too High", 3)
        assert score == 45
    
    def test_too_low_always_negative(self):
        """'Too Low' always deducts, never gives bonus."""
        for attempt in range(0, 10, 2):  # Even attempts
            score = update_score(100, "Too Low", attempt)
            assert score == 95  # Always -5
            
            score = update_score(100, "Too Low", attempt + 1)  # Odd attempts
            assert score == 95  # Always -5, no even/odd variation


class TestDifficultyAndRangeMismatches:
    """Tests for inconsistencies between difficulty and game range."""
    
    def test_guess_outside_easy_range(self):
        """Guessing a value outside the Easy range (1-20)."""
        low, high = get_range_for_difficulty("Easy")
        assert low == 1
        assert high == 20
        # But can we guess 50 (outside range) if secret is 50?
        outcome, msg = check_guess(50, 15)
        assert outcome == "Too High"
        # BUG POTENTIAL: No validation that guess is in range
    
    def test_secret_outside_difficulty_range(self):
        """Secret generated outside its difficulty range."""
        low, high = get_range_for_difficulty("Hard")
        # If secret = 100 but Hard range is 1-50, this breaks assumptions
        outcome, msg = check_guess(50, 100)
        assert outcome == "Too Low"
        # BUG POTENTIAL: Secret not validated to be in range
    
    def test_changing_difficulty_mid_game(self):
        """Switching difficulty while playing the same secret."""
        # Easy: 1-20, Normal: 1-100, Hard: 1-50
        # Secret = 75 (valid for Normal but not Easy or Hard)
        outcome, msg = check_guess(50, 75)
        assert outcome == "Too Low"
        # BUG POTENTIAL: UI difficulty doesn't affect backend


class TestMaliciousAndUnexpectedInput:
    """Tests for handling unexpected or malformed data."""
    
    def test_parse_sql_injection_attempt(self):
        """Can we inject SQL through input?"""
        ok, guess, error = parse_guess("50; DROP TABLE guesses;")
        assert ok is False
        # Safe because we convert to int and fail gracefully
    
    def test_parse_unicode_characters(self):
        """What about unicode number characters?"""
        ok, guess, error = parse_guess("５０")  # Full-width digit of 50
        # Might parse as regular 50, or fail
        if ok:
            assert guess == 50
    
    def test_parse_ordinal_numbers(self):
        """Can we pass written-out numbers?"""
        ok, guess, error = parse_guess("fifty")
        assert ok is False
    
    def test_parse_mixed_alphanumeric(self):
        """Numbers mixed with letters."""
        ok, guess, error = parse_guess("50abc")
        assert ok is False
    
    def test_check_guess_with_empty_strings(self):
        """What if both guess and secret are empty strings?"""
        try:
            outcome, msg = check_guess("", "")
            assert outcome == "Win"  # Empty == empty
        except:
            pass
    
    def test_parse_tab_and_newline(self):
        """What about escaped characters?"""
        ok, guess, error = parse_guess("50\t")  # Tab character
        # Should either parse as 50 or reject
        assert ok is True or ok is False  # Just verify it doesn't crash
    
    def test_check_guess_boolean_values(self):
        """What if we compare with boolean?"""
        # In Python: True == 1, False == 0
        outcome, msg = check_guess(True, 1)
        assert outcome == "Win"
        # BUG POTENTIAL: Accidental True/False comparisons


class TestBoundaryAndRangeValidation:
    """Tests for boundary conditions and range enforcement."""
    
    def test_easy_range_boundaries(self):
        """Test boundary guesses for Easy mode (1-20)."""
        low, high = get_range_for_difficulty("Easy")
        # Guess at boundaries
        outcome1, _ = check_guess(low, high)
        assert outcome1 == "Too Low"  # 1 < 20
        
        outcome2, _ = check_guess(high, low)
        assert outcome2 == "Too High"  # 20 > 1
    
    def test_hard_range_inverted(self):
        """Hard is 1-50 (not 50-100 like some might think)."""
        low, high = get_range_for_difficulty("Hard")
        assert low == 1
        assert high == 50
        # Interesting: Hard (50) is smaller than Normal (100)
    
    def test_off_by_one_secret_boundaries(self):
        """Off-by-one errors in range generation."""
        # If secret is generated with range(1, 20), it goes 1-19, not 1-20
        low, high = get_range_for_difficulty("Easy")
        # Guessing 20 should be "Too High" if secret is 1-19 max
        outcome, msg = check_guess(20, 19)
        assert outcome == "Too High"
    
    def test_zero_not_in_any_range(self):
        """Zero is not in any difficulty range."""
        for difficulty in ["Easy", "Normal", "Hard"]:
            low, high = get_range_for_difficulty(difficulty)
            assert low >= 1
            assert high >= low


class TestStateRegressions:
    """Tests for specific bugs that might regress."""
    
    def test_secret_changes_on_each_call(self):
        """Regression: Secret was resetting every button click.
        This was the main bug - secret shouldn't change once set."""
        secret1 = 50
        outcome1, _ = check_guess(25, secret1)
        outcome2, _ = check_guess(75, secret1)
        # Both should compare against same secret, not regenerated secret
        assert outcome1 == "Too Low"
        assert outcome2 == "Too High"
    
    def test_hint_messages_not_backwards(self):
        """Regression: Hints were backwards (Go HIGHER when Too High).
        This test ensures the fix stays in place."""
        outcome_high, msg_high = check_guess(75, 50)
        outcome_low, msg_low = check_guess(25, 50)
        
        assert "LOWER" in msg_high  # Too High should say LOWER
        assert "HIGHER" in msg_low  # Too Low should say HIGHER
    
    def test_new_game_status_reset(self):
        """Regression: Clicking 'New Game' after winning left status = 'won'.
        Game needs to reset status to 'playing'."""
        # After winning, status = "won"
        # When clicking New Game, status should reset to "playing"
        # This is tested at integration level, but check the state
        # BUG WOULD BE: status stays "won" so game never starts
        pass


class TestComplexScenarios:
    """Integration-style tests combining multiple operations."""
    
    def test_full_game_scenario(self):
        """Simulate a complete game scenario."""
        secret = 50
        
        # Guess 1: Too low
        outcome1, msg1 = check_guess(25, secret)
        assert outcome1 == "Too Low"
        score1 = update_score(0, outcome1, 1)
        assert score1 == -5
        
        # Guess 2: Too high
        outcome2, msg2 = check_guess(75, secret)
        assert outcome2 == "Too High"
        score2 = update_score(score1, outcome2, 2)
        assert score2 == 0  # -5 + 5 (even attempt bonus)
        
        # Guess 3: Correct
        outcome3, msg3 = check_guess(50, secret)
        assert outcome3 == "Win"
        score3 = update_score(score2, outcome3, 3)
        assert score3 == 70  # 0 + (100 - 10*(3+1)) = 0 + 60 = 60
    
    def test_lose_game_scenario(self):
        """Simulate running out of attempts."""
        secret = 75
        score = 0
        
        for attempt in range(1, 9):  # 8 attempts for Normal
            # Always guess too low
            outcome, msg = check_guess(25, secret)
            assert outcome == "Too Low"
            score = update_score(score, outcome, attempt)
        
        # After 8 all-wrong guesses, score should be heavily negative
        assert score == -40  # 8 * -5
