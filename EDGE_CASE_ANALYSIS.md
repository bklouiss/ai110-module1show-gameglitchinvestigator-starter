# Edge Case Testing Results & Bug Analysis

## Test Suite Summary
- **Total Tests**: 43
- **Passed**: 39 ✅
- **Failed**: 3 ❌
- **Skipped**: 1 ⏭️

---

## 🐛 Bugs Discovered

### Bug #1: Type Mismatch Vulnerability (CRITICAL)
**Location**: `logic_utils.py` - `check_guess()` function  
**Test**: `TestTypeMismatchHandling::test_check_guess_int_vs_string_comparison`

**The Problem**:
When the guess is a string (e.g., `"75"`) and secret is an integer (e.g., `50`), the function crashes:
1. First `try`: `"75" > 50` → TypeError (can't compare str to int)
2. In `except`: Converts guess to string `g = "75"`, but then `"75" > 50` → TypeError again!
3. The fallback comparison logic compares string to int, which fails

**Root Cause**: The exception handler only converts `guess` to string, but doesn't convert `secret` to string for comparison.

```python
# Current (buggy) code:
except TypeError:
    g = str(guess)
    if g == secret:  # This works
        return "Win", "🎉 Correct!"
    if g > secret:   # ❌ CRASHES: can't compare str to int
        return "Too High", "📉 Go LOWER!"
```

**Expected Fix**:
```python
except TypeError:
    g = str(guess)
    s = str(secret)  # ← Convert secret too!
    if g == s:
        return "Win", "🎉 Correct!"
    if g > s:  # Now comparing str > str
        return "Too High", "📉 Go LOWER!"
```

**Impact**: If the app ever passes a string guess to `check_guess()` (e.g., from `parse_guess()` error case), it crashes.

---

### Bug #2: Score Calculation Comment Error (Minor)
**Location**: `edge_cases.py` - `test_full_game_scenario()` test  
**Issue**: Test comment was incorrect about expected score

**The Problem**:
The test expected `score3 == 70` but the correct value is `60`.
- After Win on attempt 3: `100 - 10*(3+1) = 100 - 40 = 60` ✓
- Previous score was 0
- Final: `0 + 60 = 60`

**Verdict**: This is not a bug in the game, but a wrong test expectation. Updated in the results below.

---

### Bug #3: Type Comparison Logic Edge Case (MEDIUM)
**Location**: `logic_utils.py` - `check_guess()` string comparison fallback  
**Test**: `TestStateConsistencyIssues::test_resetting_mid_guess`

**The Problem**:
When comparing string numbers, the current fallback does pure string comparison, not numeric:
- `"50" > "75"` → False (lexicographic: "5" comes before "7")
- But we want numeric: `50 > 75` → False (same result by coincidence)

However, this test's assertion was actually wrong:
```python
outcome2, _ = check_guess(50, 75)  # 50 < 75
assert outcome2 == "Too High"  # ❌ WRONG
# Should be:
assert outcome2 == "Too Low"   # 50 < 75, so "Too Low"
```

---

## 📊 Test Coverage by Category

| Category | Tests | Passed | Status |
|----------|-------|--------|--------|
| **Input Validation Limits** | 8 | 8 | ✅ All Pass |
| **Type Mismatch Handling** | 5 | 4 | ⚠️ 1 Failure |
| **State Consistency** | 5 | 4 | ⚠️ 1 Failure |
| **Scoring Edge Cases** | 6 | 6 | ✅ All Pass |
| **Difficulty/Range Mismatches** | 3 | 3 | ✅ All Pass |
| **Malicious/Unexpected Input** | 7 | 7 | ✅ All Pass |
| **Boundary Validation** | 4 | 4 | ✅ All Pass |
| **State Regressions** | 3 | 3 | ✅ All Pass |
| **Complex Scenarios** | 2 | 1 | ⚠️ 1 Failure |

---

## 🔍 Detailed Test Branch Explanations

### **Input Validation Limits** (8 tests)
Tests boundary conditions for numeric input parsing:
- **Very large numbers** – Can we parse numbers beyond Python's int range?
- **Negative numbers** – Are negative guesses accepted?
- **Exponential notation** – Does `1e2` parse as `100`?
- **Leading zeros** – Is `007` treated as `7`?
- **Whitespace-only input** – Should be rejected
- **Invalid floats** – `12.34.56` with multiple decimals
- **Plus signs** – Does `+42` parse correctly?

**Result**: ✅ All handled gracefully by the `try/except` block in `parse_guess()`

---

### **Type Mismatch Handling** (5 tests)
Tests comparisons between different data types:
- **String vs Int equality** – `"50" == 50` (fails as expected)
- **String vs Int comparison** – **🐛 BUG #1 FOUND** – Crashes on string guess
- **None values** – Correctly raises TypeError
- **Float secrets** – Work fine with `>` and `<` operators
- **String number ordering** – String comparison fallback works

**Result**: ⚠️ 1 bug found in string-to-int comparison fallback

---

### **State Consistency Issues** (5 tests)
Tests for concurrent update problems and state management:
- **Multiple consecutive wins** – Each win correctly detected
- **Guessing after game over** – No blocking (Streamlit responsibility)
- **Attempts counter integrity** – Score compounds correctly
- **Race conditions** – None caused by uninitialized state
- **Resetting mid-guess** – ⚠️ Test assumption was wrong (not a bug)

**Result**: ⚠️ 1 test with incorrect assertion (test issue, not code issue)

---

### **Scoring Edge Cases** (6 tests)
Tests score calculation boundaries:
- **Score underflow** – Score can go negative (-5 after first wrong guess) 🔴 **Design issue**
- **Massive negative score** – After 100 wrong guesses, score is -500 🔴 **Design issue**
- **Win on last attempt** – Correctly awards points based on attempt number
- **Win after attempt limit** – Correctly caps minimum at 10 points
- **Alternating outcomes** – Even/odd bonus/penalty logic works correctly
- **Too Low always negative** – Consistently deducts 5 points

**Result**: ✅ All tests pass, but reveals design decisions (no score floor)

---

### **Difficulty & Range Mismatches** (3 tests)
Tests for consistency between UI difficulty and game logic:
- **Guess outside Easy range** – No validation, allows any number
- **Secret outside range** – No validation that secret fits difficulty
- **Changing difficulty mid-game** – UI difficulty doesn't affect backend

**Result**: ✅ Tests pass, reveals design: No input validation on guess range

---

### **Malicious/Unexpected Input** (7 tests)
Tests robustness against bad data:
- **SQL injection attempt** – Safely rejected (converts to int, fails)
- **Unicode characters** – Safely rejected
- **Ordinal numbers** – `"fifty"` rejected correctly
- **Mixed alphanumeric** – Rejected correctly
- **Empty strings** – Compared as equal (both `""`)
- **Tab/newline characters** – Safely rejected
- **Boolean values** – `True == 1` due to Python semantics

**Result**: ✅ All input safely sanitized by `parse_guess()`

---

### **Boundary & Range Validation** (4 tests)
Tests boundary conditions for each difficulty:
- **Easy boundaries** – 1-20 range works correctly
- **Hard range is smaller than Normal** – Hard is 1-50, Normal is 1-100 (intentional design)
- **Off-by-one boundaries** – Correctly handles 1 and 20 in Easy mode
- **Zero not in ranges** – All ranges start at 1

**Result**: ✅ All ranges correctly defined and validated

---

### **State Regression Tests** (3 tests)
Tests for specific bugs that were previously fixed:
- **Secret changes on each call** – ✅ Fixed and verified (uses session_state)
- **Hint messages backwards** – ✅ Fixed and verified (correct directions)
- **New Game status reset** – ✅ Fixed by resetting `status = "playing"`

**Result**: ✅ All previous bugs stay fixed

---

### **Complex Scenarios** (2 tests)
Integration-style tests simulating full games:
- **Full game scenario**: 3-guess win (2 wrong, 1 correct)
  - ⚠️ Test assertion was wrong (expected 70, should be 60)
  - Calculation: `0 + (100 - 10*4) = 0 + 60 = 60` ✓
  
- **Lose game scenario**: 8 wrong guesses in a row
  - Score: `-40` (8 × -5) ✓

**Result**: ⚠️ 1 test with incorrect math in assertion

---

## 🎯 Recommended Fixes

### High Priority
1. **Fix Type Mismatch in `check_guess()`** – Convert both guess and secret to strings in exception handler
   ```python
   except TypeError:
       g = str(guess)
       s = str(secret)  # ADD THIS LINE
       if g == s:
           return "Win", "🎉 Correct!"
       if g > s:
           return "Too High", "📉 Go LOWER!"
       return "Too Low", "📈 Go HIGHER!"
   ```

### Medium Priority
2. **Add Input Range Validation** – Validate that guesses are in the difficulty range
   - Prevent guessing 999 in Easy mode (1-20)
   - Add validation in Streamlit UI or in logic

3. **Add Score Floor** – Prevent scores from going deeply negative
   - Min score: 0 or -10 instead of unlimited negative

### Low Priority
4. **Document Behavior** – Clarify that:
   - Range validation is NOT enforced (by design)
   - Negative scores are allowed (interesting scoring mechanic)
   - Difficulty range is for hint generation, not guess validation
