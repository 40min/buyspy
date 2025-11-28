# Fix Telegram Markdown Escaping Issue

## Problem Statement

The Telegram bot is failing to send messages with the error:
```
telegram.error.BadRequest: Can't parse entities: character '.' is reserved and must be escaped with the preceding '\'
```

### Problematic Output Example

The bot attempted to send:
```
💰 *Pricing Results:*

*Product:* Sony WH-CH720N wireless headphones
*Best Prices:*
- *54.98 EUR* at [Gigantti.fi](https://www.gigantti.fi/...) ✅ ⭐
- *69.00 EUR* at [Hinta.fi](https://hinta.fi/...) ✅ 💫
...
```

But the actual escaped output was:
```
💰 \*Pricing Results:\*

\*Product:\* Sony WH\-CH720N wireless headphones
\*Best Prices:\*
\- \*54\.98 EUR\* at [Gigantti\.fi](https://www.gigantti.fi/...) ✅ ⭐
```

**The Issue**: `[Gigantti\.fi]` - the period in the link text is incorrectly escaped.

## Root Cause Analysis

### Telegram MarkdownV2 Escaping Rules

According to Telegram's MarkdownV2 specification:

1. **Inside link text `[text]`**: Only `]` and `\` need escaping
2. **Inside link URL `(url)`**: Only `)` and `\` need escaping
3. **Outside links (regular text)**: All special characters need escaping: `_*[]()~`>#+-=|{}.!`

### Current Implementation Issues

1. **Duplicate Logic**: `telegram_service.py` has its own markdown escaping methods that duplicate functionality already present in `app/app_utils/telegram_markdown.py`

2. **Incorrect Escaping**: The `_escape_markdown_preserve_links()` method in `telegram_service.py` (lines 90-144) escapes ALL special characters including periods in link text, violating Telegram's rules

3. **Code Organization**: Formatting/escaping logic is embedded in the service layer instead of being in a dedicated utility module

### Files Affected

- `app/services/telegram_service.py` - Contains duplicate and incorrect escaping logic
- `app/app_utils/telegram_markdown.py` - Contains correct utility functions (but may need bug fixes)
- `tests/unit/services/test_markdown_escaping.py` - Tests the service's methods (needs updating)
- `tests/unit/app_utils/test_telegram_markdown.py` - Tests the utility functions

## Solution Design

### Architecture Changes

```
Before:
┌─────────────────────────────┐
│  telegram_service.py        │
│  ├─ _convert_urls_to_links  │ ❌ Duplicate
│  ├─ _escape_markdown_v2     │ ❌ Duplicate
│  └─ _escape_markdown_...    │ ❌ Incorrect
└─────────────────────────────┘

After:
┌─────────────────────────────┐
│  telegram_service.py        │
│  └─ Uses utility functions  │ ✅
└─────────────────────────────┘
         ↓ imports
┌─────────────────────────────┐
│  telegram_markdown.py       │
│  ├─ escape_markdown_v2()    │ ✅ Correct
│  └─ convert_urls_to_links() │ ✅ Correct
└─────────────────────────────┘
```

### Implementation Plan

#### Step 1: Analyze and Fix `telegram_markdown.py`

**Current Implementation Review:**

The `escape_markdown_v2()` function in `telegram_markdown.py`:
- ✅ Correctly identifies link segments
- ✅ Applies different escaping rules to link text, URLs, and regular text
- ⚠️ **Potential Bug**: The reconstruction logic may have issues

**Required Fixes:**

1. Review the segment parsing and reconstruction logic
2. Ensure link text only escapes `]` and `\`
3. Ensure link URLs only escape `)` and `\`
4. Ensure regular text escapes all special characters
5. Add comprehensive test coverage for edge cases

#### Step 2: Remove Duplicate Methods from `telegram_service.py`

**Methods to Remove:**
- `_convert_urls_to_links()` (lines 41-88)
- `_escape_markdown_preserve_links()` (lines 90-144)
- `_escape_markdown_v2()` (lines 146-180)

**Total Lines to Remove**: ~140 lines

#### Step 3: Update `telegram_service.py` Imports

**Add Import:**
```python
from app.app_utils.telegram_markdown import (
    escape_markdown_v2,
    convert_urls_to_links,
)
```

#### Step 4: Update `handle_message()` Method

**Current Code (lines 270-277):**
```python
# Convert raw URLs to Markdown links while preserving existing markdown formatting
formatted_text = self._convert_urls_to_links(response_text)
# Only escape markdown for text that's not already in link format
formatted_text = self._escape_markdown_preserve_links(formatted_text)
self.logger.info(f"Trying to output formatted text: {formatted_text}")
await update.message.reply_markdown_v2(
    formatted_text, disable_web_page_preview=False
)
```

**New Code:**
```python
# Convert raw URLs to Markdown links (if any exist)
formatted_text = convert_urls_to_links(response_text)
# Escape markdown while preserving link syntax
formatted_text = escape_markdown_v2(formatted_text)
self.logger.info(f"Sending formatted text: {formatted_text}")
await update.message.reply_markdown_v2(
    formatted_text, disable_web_page_preview=False
)
```

#### Step 5: Update Tests

**File: `tests/unit/services/test_markdown_escaping.py`**

Current tests call `telegram_service._escape_markdown_preserve_links()` which will be removed.

**Changes Required:**
1. Import utility functions directly: `from app.app_utils.telegram_markdown import escape_markdown_v2, convert_urls_to_links`
2. Update all test methods to call utility functions instead of service methods
3. Remove the `telegram_service` fixture dependency where not needed
4. Keep integration-style tests that verify the service uses utilities correctly

**Example Test Update:**
```python
# Before
def test_escape_markdown_preserve_links_basic(self, telegram_service: TelegramService):
    result = telegram_service._escape_markdown_preserve_links(input_text)

# After
def test_escape_markdown_v2_basic(self):
    from app.app_utils.telegram_markdown import escape_markdown_v2
    result = escape_markdown_v2(input_text)
```

#### Step 6: Verify with Problematic Example

**Test Case:**
```python
input_text = """💰 *Pricing Results:*

*Product:* Sony WH-CH720N wireless headphones
*Best Prices:*
- *54.98 EUR* at [Gigantti.fi](https://www.gigantti.fi/product/...) ✅ ⭐
- *69.00 EUR* at [Hinta.fi](https://hinta.fi/4026623/sony-wh-ch720n) ✅ 💫
📊 *Total Found:* 4"""

result = escape_markdown_v2(input_text)
```

**Expected Output:**
```
💰 \*Pricing Results\:\*

\*Product\:\* Sony WH\-CH720N wireless headphones
\*Best Prices\:\*
\- \*54\.98 EUR\* at [Gigantti.fi](https://www.gigantti.fi/product/...) ✅ ⭐
\- \*69\.00 EUR\* at [Hinta.fi](https://hinta.fi/4026623/sony-wh-ch720n) ✅ 💫
📊 \*Total Found\:\* 4
```

**Key Assertions:**
- ✅ `[Gigantti.fi]` - NO escaped period in link text
- ✅ `[Hinta.fi]` - NO escaped period in link text
- ✅ `\*54\.98 EUR\*` - Escaped period in regular text
- ✅ `\*69\.00 EUR\*` - Escaped period in regular text
- ✅ All asterisks, colons, hyphens escaped in regular text
- ✅ Emojis preserved unchanged

## Implementation Checklist

- [ ] **Step 1**: Analyze `telegram_markdown.py` for bugs
  - [ ] Review `escape_markdown_v2()` implementation
  - [ ] Test with problematic example
  - [ ] Fix any identified issues

- [ ] **Step 2**: Remove duplicate methods from `telegram_service.py`
  - [ ] Remove `_convert_urls_to_links()`
  - [ ] Remove `_escape_markdown_preserve_links()`
  - [ ] Remove `_escape_markdown_v2()`

- [ ] **Step 3**: Update imports in `telegram_service.py`
  - [ ] Add import for `escape_markdown_v2`
  - [ ] Add import for `convert_urls_to_links`
  - [ ] Remove unused `re` import from method scope

- [ ] **Step 4**: Update `handle_message()` method
  - [ ] Replace `self._convert_urls_to_links()` with `convert_urls_to_links()`
  - [ ] Replace `self._escape_markdown_preserve_links()` with `escape_markdown_v2()`
  - [ ] Update log message

- [ ] **Step 5**: Update tests
  - [ ] Update `test_markdown_escaping.py` to use utility functions
  - [ ] Ensure all existing tests pass
  - [ ] Add test for the specific problematic example

- [ ] **Step 6**: Run full test suite
  - [ ] `make test` - All tests pass
  - [ ] `make lint` - No linting issues

- [ ] **Step 7**: Verify fix
  - [ ] Test with problematic example manually
  - [ ] Verify Telegram accepts the formatted message
  - [ ] Check logs for correct output

## Expected Outcomes

### Code Quality Improvements

1. **Reduced Duplication**: ~140 lines removed from `telegram_service.py`
2. **Better Separation of Concerns**: Formatting logic in utility module, service handles business logic
3. **Improved Maintainability**: Single source of truth for markdown escaping
4. **Better Testability**: Utility functions can be tested independently

### Functional Improvements

1. **Correct Escaping**: Link text will no longer have incorrectly escaped periods
2. **Telegram Compatibility**: Messages will be accepted by Telegram's MarkdownV2 parser
3. **Reliable Formatting**: All special characters handled according to Telegram's specification

### Test Coverage

- All existing tests updated and passing
- New test added for the specific problematic example
- Edge cases covered in utility module tests

## Risk Assessment

### Low Risk
- Utility module already exists with correct logic
- Comprehensive test coverage exists
- Changes are localized to formatting logic

### Mitigation
- Run full test suite before deployment
- Test with real Telegram bot in development environment
- Monitor error logs after deployment

## References

- [Telegram Bot API - MarkdownV2 Style](https://core.telegram.org/bots/api#markdownv2-style)
- Existing implementation: `app/app_utils/telegram_markdown.py`
- Test suite: `tests/unit/app_utils/test_telegram_markdown.py`
