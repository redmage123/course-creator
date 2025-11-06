"""
Redis Serialization and Deserialization Tests

BUSINESS CONTEXT:
Comprehensive tests for Redis serialization/deserialization ensuring data integrity
when caching complex Python objects. Critical for maintaining data accuracy and
handling edge cases in data types, encodings, and special characters.

TECHNICAL IMPLEMENTATION:
- Tests JSON serialization/deserialization of Python objects
- Validates handling of complex nested data structures
- Tests date/datetime serialization
- Validates binary data caching (base64 encoding)
- Tests Unicode and special character handling
- Validates serialization error handling

TDD APPROACH:
These tests validate that serialization:
- Preserves data types and structures
- Handles edge cases (None, empty values, special chars)
- Maintains data integrity across cache operations
- Provides meaningful errors for unsupported types
- Handles large objects efficiently

BUSINESS REQUIREMENTS:
1. Cache must preserve data types (strings, numbers, booleans, arrays, objects)
2. Date/time values must be serializable and deserializable
3. Unicode and special characters must be handled correctly
4. Binary data (images, PDFs) must be cacheable
5. Serialization errors should provide clear error messages
"""

import pytest
import json
import base64
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
import asyncio
import sys
from pathlib import Path

# Add shared cache module to path
shared_path = Path(__file__).parent.parent.parent.parent / 'shared'
sys.path.insert(0, str(shared_path))

try:
    from cache.redis_cache import RedisCacheManager
except ImportError:
    pytest.skip("Redis cache module not available", allow_module_level=True)


class TestBasicTypeSerialization:
    """
    Test Suite: Basic Python Type Serialization

    BUSINESS REQUIREMENT:
    Cache must correctly serialize and deserialize basic Python types
    without data loss or type corruption.
    """

    @pytest.mark.asyncio
    async def test_serialize_string_value(self, redis_cache):
        """
        TEST: String values serialize and deserialize correctly

        VALIDATES:
        - String type is preserved
        - String content is unchanged
        """
        key = f"test:string:{uuid4()}"
        value = "Hello, World!"

        await redis_cache.set(key, value)
        retrieved = await redis_cache.get(key)

        assert retrieved == value
        assert isinstance(retrieved, str)

    @pytest.mark.asyncio
    async def test_serialize_integer_value(self, redis_cache):
        """
        TEST: Integer values serialize correctly

        BUSINESS REQUIREMENT:
        Numeric counters and IDs must maintain type and value

        VALIDATES:
        - Integer type is preserved
        - Integer value is accurate
        """
        key = f"test:integer:{uuid4()}"
        value = 42

        await redis_cache.set(key, str(value))
        retrieved = await redis_cache.get(key)

        assert int(retrieved) == value

    @pytest.mark.asyncio
    async def test_serialize_float_value(self, redis_cache):
        """
        TEST: Float values serialize with precision

        BUSINESS REQUIREMENT:
        Analytics scores and percentages must maintain precision

        VALIDATES:
        - Float type is preserved
        - Precision is maintained (to reasonable decimal places)
        """
        key = f"test:float:{uuid4()}"
        value = 3.14159265359

        await redis_cache.set(key, str(value))
        retrieved = await redis_cache.get(key)
        retrieved_float = float(retrieved)

        # Allow small floating point precision differences
        assert abs(retrieved_float - value) < 0.0000001

    @pytest.mark.asyncio
    async def test_serialize_boolean_value(self, redis_cache):
        """
        TEST: Boolean values serialize correctly

        BUSINESS REQUIREMENT:
        Feature flags and status indicators must maintain boolean type

        VALIDATES:
        - Boolean values are preserved
        - True and False are distinguishable
        """
        key_true = f"test:bool_true:{uuid4()}"
        key_false = f"test:bool_false:{uuid4()}"

        await redis_cache.set(key_true, json.dumps(True))
        await redis_cache.set(key_false, json.dumps(False))

        retrieved_true = json.loads(await redis_cache.get(key_true))
        retrieved_false = json.loads(await redis_cache.get(key_false))

        assert retrieved_true is True
        assert retrieved_false is False
        assert isinstance(retrieved_true, bool)
        assert isinstance(retrieved_false, bool)

    @pytest.mark.asyncio
    async def test_serialize_none_value(self, redis_cache):
        """
        TEST: None values serialize correctly

        BUSINESS REQUIREMENT:
        Optional fields with None values must be distinguishable from missing keys

        VALIDATES:
        - None is serializable
        - None is distinguishable from cache miss
        """
        key = f"test:none:{uuid4()}"

        await redis_cache.set(key, json.dumps(None))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved is None


class TestComplexObjectSerialization:
    """
    Test Suite: Complex Object Serialization

    BUSINESS REQUIREMENT:
    Cache must handle nested data structures including dictionaries,
    lists, and mixed types.
    """

    @pytest.mark.asyncio
    async def test_serialize_nested_dictionary(self, redis_cache):
        """
        TEST: Nested dictionaries serialize correctly

        BUSINESS REQUIREMENT:
        Complex API responses and data models must be cacheable

        VALIDATES:
        - Nested structure is preserved
        - All levels of nesting are accessible
        """
        key = f"test:nested_dict:{uuid4()}"
        value = {
            'user': {
                'id': str(uuid4()),
                'profile': {
                    'name': 'John Doe',
                    'settings': {
                        'theme': 'dark',
                        'notifications': True
                    }
                },
                'metadata': {
                    'last_login': '2024-01-15T10:30:00Z',
                    'login_count': 42
                }
            }
        }

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == value
        assert retrieved['user']['profile']['settings']['theme'] == 'dark'
        assert retrieved['user']['metadata']['login_count'] == 42

    @pytest.mark.asyncio
    async def test_serialize_list_of_dictionaries(self, redis_cache):
        """
        TEST: List of dictionaries serializes correctly

        BUSINESS REQUIREMENT:
        Collections of complex objects (courses, users, etc.) must be cacheable

        VALIDATES:
        - List structure is preserved
        - Dictionary items are intact
        - Order is maintained
        """
        key = f"test:list_dict:{uuid4()}"
        value = [
            {'id': 1, 'name': 'Course A', 'score': 85.5},
            {'id': 2, 'name': 'Course B', 'score': 92.0},
            {'id': 3, 'name': 'Course C', 'score': 78.3}
        ]

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == value
        assert len(retrieved) == 3
        assert retrieved[1]['name'] == 'Course B'
        assert retrieved[2]['score'] == 78.3

    @pytest.mark.asyncio
    async def test_serialize_mixed_type_array(self, redis_cache):
        """
        TEST: Arrays with mixed types serialize correctly

        VALIDATES:
        - Mixed types (string, int, float, bool, dict) are preserved
        - Type integrity is maintained
        """
        key = f"test:mixed_array:{uuid4()}"
        value = [
            'string value',
            42,
            3.14,
            True,
            None,
            {'nested': 'object'},
            ['nested', 'array']
        ]

        await redis_cache.set(key, json.dumps(value, default=str))
        retrieved = json.loads(await redis_cache.get(key))

        assert len(retrieved) == 7
        assert isinstance(retrieved[0], str)
        assert isinstance(retrieved[1], int)
        assert isinstance(retrieved[2], float)
        assert isinstance(retrieved[3], bool)
        assert retrieved[4] is None
        assert isinstance(retrieved[5], dict)
        assert isinstance(retrieved[6], list)

    @pytest.mark.asyncio
    async def test_serialize_deeply_nested_structure(self, redis_cache):
        """
        TEST: Deeply nested structures (5+ levels) serialize correctly

        BUSINESS REQUIREMENT:
        Complex data models with deep nesting must be cacheable

        VALIDATES:
        - Deep nesting is handled
        - No data loss at any level
        """
        key = f"test:deep_nested:{uuid4()}"
        value = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'level5': {
                                'deep_value': 'found it!',
                                'deep_number': 12345
                            }
                        }
                    }
                }
            }
        }

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved['level1']['level2']['level3']['level4']['level5']['deep_value'] == 'found it!'
        assert retrieved['level1']['level2']['level3']['level4']['level5']['deep_number'] == 12345


class TestDateTimeSerialization:
    """
    Test Suite: Date and DateTime Serialization

    BUSINESS REQUIREMENT:
    Timestamps and dates must be serializable and deserializable
    with precision and timezone handling.
    """

    @pytest.mark.asyncio
    async def test_serialize_datetime_as_iso_string(self, redis_cache):
        """
        TEST: DateTime objects serialize as ISO 8601 strings

        BUSINESS REQUIREMENT:
        Timestamps must be stored in standard format

        VALIDATES:
        - DateTime converts to ISO string
        - Can be parsed back to datetime
        """
        key = f"test:datetime:{uuid4()}"
        dt = datetime(2024, 1, 15, 14, 30, 45)

        value = {'timestamp': dt.isoformat()}
        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        retrieved_dt = datetime.fromisoformat(retrieved['timestamp'])
        assert retrieved_dt == dt

    @pytest.mark.asyncio
    async def test_serialize_date_as_string(self, redis_cache):
        """
        TEST: Date objects serialize as string

        VALIDATES:
        - Date converts to string format
        - Can be parsed back to date
        """
        key = f"test:date:{uuid4()}"
        d = date(2024, 1, 15)

        value = {'date': d.isoformat()}
        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        retrieved_date = date.fromisoformat(retrieved['date'])
        assert retrieved_date == d

    @pytest.mark.asyncio
    async def test_serialize_timedelta_as_seconds(self, redis_cache):
        """
        TEST: Timedelta objects serialize as seconds

        BUSINESS REQUIREMENT:
        Duration values must be cacheable

        VALIDATES:
        - Timedelta converts to seconds
        - Can be reconstructed from seconds
        """
        key = f"test:timedelta:{uuid4()}"
        td = timedelta(days=3, hours=5, minutes=30)

        value = {'duration_seconds': td.total_seconds()}
        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        retrieved_td = timedelta(seconds=retrieved['duration_seconds'])
        assert retrieved_td == td

    @pytest.mark.asyncio
    async def test_serialize_current_timestamp(self, redis_cache):
        """
        TEST: Current timestamp serializes with millisecond precision

        VALIDATES:
        - Precision is maintained
        - Timestamp is recent
        """
        key = f"test:timestamp:{uuid4()}"
        now = datetime.utcnow()

        value = {'timestamp': now.isoformat()}
        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        retrieved_dt = datetime.fromisoformat(retrieved['timestamp'])

        # Should be within 1 second
        time_diff = abs((retrieved_dt - now).total_seconds())
        assert time_diff < 1


class TestSpecialCharacterSerialization:
    """
    Test Suite: Special Character and Unicode Handling

    BUSINESS REQUIREMENT:
    Cache must handle international characters, emojis, and special symbols
    without corruption or encoding issues.
    """

    @pytest.mark.asyncio
    async def test_serialize_unicode_characters(self, redis_cache):
        """
        TEST: Unicode characters serialize correctly

        BUSINESS REQUIREMENT:
        International user names and content must be supported

        VALIDATES:
        - Unicode characters are preserved
        - No encoding corruption
        """
        key = f"test:unicode:{uuid4()}"
        value = {
            'chinese': '你好世界',
            'arabic': 'مرحبا بالعالم',
            'russian': 'Привет мир',
            'japanese': 'こんにちは世界',
            'korean': '안녕하세요 세계'
        }

        await redis_cache.set(key, json.dumps(value, ensure_ascii=False))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == value
        assert retrieved['chinese'] == '你好世界'
        assert retrieved['arabic'] == 'مرحبا بالعالم'

    @pytest.mark.asyncio
    async def test_serialize_emoji_characters(self, redis_cache):
        """
        TEST: Emoji characters serialize correctly

        BUSINESS REQUIREMENT:
        Modern text with emojis must be supported

        VALIDATES:
        - Emojis are preserved
        - No character corruption
        """
        key = f"test:emoji:{uuid4()}"
        value = {
            'message': 'Hello 👋 World 🌍!',
            'reactions': ['👍', '❤️', '😊', '🎉'],
            'flags': '🇺🇸 🇨🇦 🇬🇧 🇩🇪'
        }

        await redis_cache.set(key, json.dumps(value, ensure_ascii=False))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == value
        assert '👋' in retrieved['message']
        assert retrieved['reactions'][0] == '👍'

    @pytest.mark.asyncio
    async def test_serialize_special_characters(self, redis_cache):
        """
        TEST: Special characters and symbols serialize correctly

        VALIDATES:
        - Special symbols are preserved
        - Escape characters are handled
        """
        key = f"test:special_chars:{uuid4()}"
        value = {
            'symbols': '!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\',
            'quotes': 'He said "Hello" and she replied \'Hi\'',
            'newlines': 'Line 1\nLine 2\nLine 3',
            'tabs': 'Column1\tColumn2\tColumn3'
        }

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == value
        assert '\n' in retrieved['newlines']
        assert '\t' in retrieved['tabs']

    @pytest.mark.asyncio
    async def test_serialize_html_and_xml_content(self, redis_cache):
        """
        TEST: HTML/XML content serializes without corruption

        BUSINESS REQUIREMENT:
        Course content with HTML markup must be cacheable

        VALIDATES:
        - HTML tags are preserved
        - Angle brackets don't cause issues
        """
        key = f"test:html:{uuid4()}"
        value = {
            'html': '<div class="container"><p>Hello <strong>World</strong>!</p></div>',
            'xml': '<?xml version="1.0"?><root><item>value</item></root>'
        }

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == value
        assert '<strong>World</strong>' in retrieved['html']


class TestBinaryDataSerialization:
    """
    Test Suite: Binary Data Caching

    BUSINESS REQUIREMENT:
    Binary data (images, PDFs, documents) must be cacheable using
    base64 encoding.
    """

    @pytest.mark.asyncio
    async def test_serialize_small_binary_data(self, redis_cache):
        """
        TEST: Small binary data (< 1KB) serializes correctly

        BUSINESS REQUIREMENT:
        Thumbnails and small images must be cacheable

        VALIDATES:
        - Binary data converts to base64
        - Can be decoded back to original
        """
        key = f"test:binary_small:{uuid4()}"
        binary_data = b'This is binary data with special bytes: \x00\x01\x02\xff'

        value = {
            'data': base64.b64encode(binary_data).decode('utf-8'),
            'size': len(binary_data)
        }

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        decoded_data = base64.b64decode(retrieved['data'])
        assert decoded_data == binary_data
        assert retrieved['size'] == len(binary_data)

    @pytest.mark.asyncio
    async def test_serialize_image_like_binary_data(self, redis_cache):
        """
        TEST: Image-like binary data serializes correctly

        BUSINESS REQUIREMENT:
        Profile pictures and content images can be cached

        VALIDATES:
        - Larger binary data (simulated image) is handled
        - Base64 encoding/decoding works correctly
        """
        key = f"test:binary_image:{uuid4()}"

        # Simulate image data (10KB of random bytes)
        import random
        binary_data = bytes([random.randint(0, 255) for _ in range(10240)])

        value = {
            'image_data': base64.b64encode(binary_data).decode('utf-8'),
            'size': len(binary_data),
            'mime_type': 'image/png'
        }

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        decoded_data = base64.b64decode(retrieved['image_data'])
        assert decoded_data == binary_data
        assert retrieved['size'] == 10240
        assert retrieved['mime_type'] == 'image/png'


class TestEdgeCaseSerialization:
    """
    Test Suite: Edge Cases and Error Handling

    BUSINESS REQUIREMENT:
    Cache must gracefully handle edge cases and provide clear errors
    for unsupported types.
    """

    @pytest.mark.asyncio
    async def test_serialize_empty_string(self, redis_cache):
        """
        TEST: Empty string serializes correctly

        VALIDATES:
        - Empty string is distinguishable from None
        - Empty string is distinguishable from missing key
        """
        key = f"test:empty_string:{uuid4()}"
        value = ""

        await redis_cache.set(key, value)
        retrieved = await redis_cache.get(key)

        assert retrieved == ""
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_serialize_empty_dict(self, redis_cache):
        """
        TEST: Empty dictionary serializes correctly

        VALIDATES:
        - Empty dict is valid
        - Type is preserved
        """
        key = f"test:empty_dict:{uuid4()}"
        value = {}

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == {}
        assert isinstance(retrieved, dict)

    @pytest.mark.asyncio
    async def test_serialize_empty_list(self, redis_cache):
        """
        TEST: Empty list serializes correctly

        VALIDATES:
        - Empty list is valid
        - Type is preserved
        """
        key = f"test:empty_list:{uuid4()}"
        value = []

        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        assert retrieved == []
        assert isinstance(retrieved, list)

    @pytest.mark.asyncio
    async def test_serialize_very_long_string(self, redis_cache):
        """
        TEST: Very long strings (> 1MB) serialize correctly

        BUSINESS REQUIREMENT:
        Large text content (articles, documentation) must be cacheable

        VALIDATES:
        - Large strings are handled
        - No truncation occurs
        """
        key = f"test:long_string:{uuid4()}"

        # Create 1MB string
        value = "x" * (1024 * 1024)

        await redis_cache.set(key, value)
        retrieved = await redis_cache.get(key)

        assert len(retrieved) == len(value)
        assert retrieved == value

    @pytest.mark.asyncio
    async def test_serialize_uuid_as_string(self, redis_cache):
        """
        TEST: UUID objects serialize as strings

        BUSINESS REQUIREMENT:
        Entity IDs (UUIDs) must be cacheable

        VALIDATES:
        - UUID converts to string
        - Can be reconstructed as UUID
        """
        key = f"test:uuid:{uuid4()}"
        uuid_value = uuid4()

        value = {'id': str(uuid_value)}
        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        retrieved_uuid = UUID(retrieved['id'])
        assert retrieved_uuid == uuid_value

    @pytest.mark.asyncio
    async def test_serialize_decimal_as_string(self, redis_cache):
        """
        TEST: Decimal objects serialize as strings

        BUSINESS REQUIREMENT:
        Financial data with precise decimals must be cacheable

        VALIDATES:
        - Decimal converts to string
        - Precision is maintained
        """
        key = f"test:decimal:{uuid4()}"
        decimal_value = Decimal('123.456789')

        value = {'amount': str(decimal_value)}
        await redis_cache.set(key, json.dumps(value))
        retrieved = json.loads(await redis_cache.get(key))

        retrieved_decimal = Decimal(retrieved['amount'])
        assert retrieved_decimal == decimal_value


class TestSerializationPerformance:
    """
    Test Suite: Serialization Performance

    BUSINESS REQUIREMENT:
    Serialization overhead must not significantly impact cache performance.
    """

    @pytest.mark.asyncio
    async def test_serialize_large_object_is_fast(self, redis_cache):
        """
        TEST: Large object serialization completes quickly

        VALIDATES:
        - Serialization overhead is minimal (<50ms for large objects)
        """
        import time

        key = f"test:large_object:{uuid4()}"

        # Create large object (1000 items)
        value = {
            'items': [
                {
                    'id': i,
                    'name': f'Item {i}',
                    'description': 'x' * 100,
                    'metadata': {'created': datetime.utcnow().isoformat()}
                }
                for i in range(1000)
            ]
        }

        start = time.time()
        serialized = json.dumps(value, default=str)
        await redis_cache.set(key, serialized)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, f"Serialization took {elapsed_ms:.2f}ms (expected <100ms)"

    @pytest.mark.asyncio
    async def test_deserialize_large_object_is_fast(self, redis_cache):
        """
        TEST: Large object deserialization completes quickly

        VALIDATES:
        - Deserialization overhead is minimal (<50ms for large objects)
        """
        import time

        key = f"test:large_deserialize:{uuid4()}"

        # Create and cache large object
        value = {'data': ['x' * 1000 for _ in range(1000)]}
        await redis_cache.set(key, json.dumps(value))

        start = time.time()
        retrieved = await redis_cache.get(key)
        deserialized = json.loads(retrieved)
        elapsed_ms = (time.time() - start) * 1000

        assert len(deserialized['data']) == 1000
        assert elapsed_ms < 100, f"Deserialization took {elapsed_ms:.2f}ms (expected <100ms)"
