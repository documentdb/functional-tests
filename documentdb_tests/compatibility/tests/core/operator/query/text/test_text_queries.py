"""
Tests for $text query operator search behavior.

Validates term matching, stemming, stop words, negation, exact phrases, case sensitivity,
diacritic sensitivity, special characters, language support, and edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

TEXT_SEARCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="term_single_word",
        filter={"$text": {"$search": "coffee"}},
        doc=[
            {"_id": 1, "content": "coffee is a database"},
            {"_id": 2, "content": "python is a language"},
        ],
        expected=[{"_id": 1, "content": "coffee is a database"}],
        msg="Single word should match document containing that word",
    ),
    QueryTestCase(
        id="term_multiple_words_or",
        filter={"$text": {"$search": "coffee python"}},
        doc=[
            {"_id": 1, "content": "coffee is a database"},
            {"_id": 2, "content": "python is a language"},
            {"_id": 3, "content": "java is compiled"},
        ],
        expected=[
            {"_id": 1, "content": "coffee is a database"},
            {"_id": 2, "content": "python is a language"},
        ],
        msg="Multiple words should perform OR and return docs with any word",
    ),
    QueryTestCase(
        id="term_stop_word_only",
        filter={"$text": {"$search": "the"}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[],
        msg="Stop word only should return no results",
    ),
    QueryTestCase(
        id="term_stop_words_with_content",
        filter={"$text": {"$search": "the fox"}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 1, "content": "the quick brown fox"}],
        msg="Stop words mixed with content words should match on content words",
    ),
    QueryTestCase(
        id="term_null_byte_in_search",
        filter={"$text": {"$search": "hello\x00world"}},
        doc=[{"_id": 1, "content": "hello world"}],
        expected=[{"_id": 1, "content": "hello world"}],
        msg="Null byte should act as delimiter, matching terms on either side",
    ),
    QueryTestCase(
        id="term_hyphenated_word",
        filter={"$text": {"$search": "well-known"}},
        doc=[
            {"_id": 1, "content": "this is a well-known fact"},
            {"_id": 2, "content": "this is well done"},
        ],
        expected=[
            {"_id": 1, "content": "this is a well-known fact"},
            {"_id": 2, "content": "this is well done"},
        ],
        msg="Hyphenated word should treat hyphen as delimiter matching both parts",
    ),
    QueryTestCase(
        id="term_empty_collection",
        filter={"$text": {"$search": "hello"}},
        doc=[],
        expected=[],
        msg="Empty collection should return no results",
    ),
    QueryTestCase(
        id="term_no_matching_documents",
        filter={"$text": {"$search": "coffee"}},
        doc=[
            {"_id": 1, "content": "python programming"},
            {"_id": 2, "content": "java development"},
        ],
        expected=[],
        msg="No matching documents should return empty result",
    ),
    QueryTestCase(
        id="term_matches_all_documents",
        filter={"$text": {"$search": "coffee"}},
        doc=[
            {"_id": 1, "content": "coffee database"},
            {"_id": 2, "content": "coffee system"},
        ],
        expected=[
            {"_id": 1, "content": "coffee database"},
            {"_id": 2, "content": "coffee system"},
        ],
        msg="Should return all matching documents",
    ),
    QueryTestCase(
        id="term_whitespace_only_search",
        filter={"$text": {"$search": "   "}},
        doc=[{"_id": 1, "content": "hello world"}],
        expected=[],
        msg="Whitespace-only search should return no results",
    ),
    QueryTestCase(
        id="term_empty_search_string",
        filter={"$text": {"$search": ""}},
        doc=[{"_id": 1, "content": "hello world"}],
        expected=[],
        msg="Empty search string should return no results",
    ),
    QueryTestCase(
        id="phrase_two_word",
        filter={"$text": {"$search": '"brown fox"'}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "the brown dog and fox"},
        ],
        expected=[{"_id": 1, "content": "the quick brown fox"}],
        msg="Exact two-word phrase should match only exact phrase",
    ),
    QueryTestCase(
        id="phrase_three_word",
        filter={"$text": {"$search": '"quick brown fox"'}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "quick fox brown"},
        ],
        expected=[{"_id": 1, "content": "the quick brown fox"}],
        msg="Exact three-word phrase should match only exact phrase",
    ),
    QueryTestCase(
        id="phrase_not_found",
        filter={"$text": {"$search": '"purple elephant"'}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "purple dog and elephant"},
        ],
        expected=[],
        msg="Exact phrase that doesn't exist should return no results",
    ),
    QueryTestCase(
        id="phrase_plus_terms",
        filter={"$text": {"$search": '"brown fox" quick'}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "brown fox jumps"},
            {"_id": 3, "content": "quick rabbit"},
        ],
        expected=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "brown fox jumps"},
        ],
        msg="Phrase plus terms should match docs with phrase (phrase required, terms optional)",
    ),
    QueryTestCase(
        id="negation_single_word",
        filter={"$text": {"$search": "fox -brown"}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "the red fox"},
        ],
        expected=[{"_id": 2, "content": "the red fox"}],
        msg="Negated word should exclude documents containing it",
    ),
    QueryTestCase(
        id="negation_only_negated",
        filter={"$text": {"$search": "-fox -dog"}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "the red dog"},
        ],
        expected=[],
        msg="Only negated words should return no results",
    ),
    QueryTestCase(
        id="negation_positive_and_negated",
        filter={"$text": {"$search": "animal -fox"}},
        doc=[
            {"_id": 1, "content": "the fox is an animal"},
            {"_id": 2, "content": "the dog is an animal"},
        ],
        expected=[{"_id": 2, "content": "the dog is an animal"}],
        msg="Positive and negated terms should return docs with positive excluding negated",
    ),
    QueryTestCase(
        id="term_running_matches_run",
        filter={"$text": {"$search": "running"}},
        doc=[
            {"_id": 1, "content": "I run every morning"},
            {"_id": 2, "content": "swimming is great"},
        ],
        expected=[{"_id": 1, "content": "I run every morning"}],
        msg="Stemming should match 'run' when searching 'running'",
    ),
    QueryTestCase(
        id="term_blueberries_matches_blueberry",
        filter={"$text": {"$search": "blueberry"}},
        doc=[
            {"_id": 1, "content": "I love blueberries"},
            {"_id": 2, "content": "strawberries are red"},
        ],
        expected=[{"_id": 1, "content": "I love blueberries"}],
        msg="Stemming should match 'blueberries' when searching 'blueberry'",
    ),
    QueryTestCase(
        id="term_blue_not_match_blueberry",
        filter={"$text": {"$search": "blue"}},
        doc=[
            {"_id": 1, "content": "I love blueberries"},
            {"_id": 2, "content": "the sky is blue"},
        ],
        expected=[{"_id": 2, "content": "the sky is blue"}],
        msg="'blue' should not match 'blueberry' (not a stem)",
    ),
    QueryTestCase(
        id="case_insensitive_default",
        filter={"$text": {"$search": "Coffee"}},
        doc=[
            {"_id": 1, "content": "coffee is great"},
            {"_id": 2, "content": "COFFEE rocks"},
        ],
        expected=[
            {"_id": 1, "content": "coffee is great"},
            {"_id": 2, "content": "COFFEE rocks"},
        ],
        msg="Default case insensitive should match regardless of case",
    ),
    QueryTestCase(
        id="case_sensitive_exact_match",
        filter={"$text": {"$search": "Coffee", "$caseSensitive": True}},
        doc=[
            {"_id": 1, "content": "Coffee is great"},
            {"_id": 2, "content": "coffee is good"},
            {"_id": 3, "content": "COFFEE rocks"},
        ],
        expected=[{"_id": 1, "content": "Coffee is great"}],
        msg="Case sensitive should match only exact case",
    ),
    QueryTestCase(
        id="case_sensitive_no_match",
        filter={"$text": {"$search": "PYTHON", "$caseSensitive": True}},
        doc=[
            {"_id": 1, "content": "python is great"},
            {"_id": 2, "content": "Python rocks"},
        ],
        expected=[],
        msg="Case sensitive with wrong case should return no match",
    ),
    QueryTestCase(
        id="case_sensitive_false_explicit",
        filter={"$text": {"$search": "Coffee", "$caseSensitive": False}},
        doc=[
            {"_id": 1, "content": "coffee is great"},
            {"_id": 2, "content": "COFFEE rocks"},
        ],
        expected=[
            {"_id": 1, "content": "coffee is great"},
            {"_id": 2, "content": "COFFEE rocks"},
        ],
        msg="Explicit caseSensitive false should match regardless of case",
    ),
    QueryTestCase(
        id="case_diacritic_insensitive_default",
        filter={"$text": {"$search": "cafe"}},
        doc=[
            {"_id": 1, "content": "café is nice"},
            {"_id": 2, "content": "cafe is good"},
        ],
        expected=[
            {"_id": 1, "content": "café is nice"},
            {"_id": 2, "content": "cafe is good"},
        ],
        msg="Default diacritic insensitive should match regardless of diacritics",
    ),
    QueryTestCase(
        id="case_diacritic_sensitive_exact",
        filter={"$text": {"$search": "café", "$diacriticSensitive": True}},
        doc=[
            {"_id": 1, "content": "café is nice"},
            {"_id": 2, "content": "cafe is good"},
        ],
        expected=[{"_id": 1, "content": "café is nice"}],
        msg="Diacritic sensitive should match only exact diacritics",
    ),
    QueryTestCase(
        id="case_diacritic_insensitive_accented_query",
        filter={"$text": {"$search": "café", "$diacriticSensitive": False}},
        doc=[
            {"_id": 1, "content": "cafe is nice"},
            {"_id": 2, "content": "café is good"},
        ],
        expected=[
            {"_id": 1, "content": "cafe is nice"},
            {"_id": 2, "content": "café is good"},
        ],
        msg="Diacritic insensitive with accented query should match unaccented docs",
    ),
    QueryTestCase(
        id="case_both_sensitive",
        filter={"$text": {"$search": "Café", "$caseSensitive": True, "$diacriticSensitive": True}},
        doc=[
            {"_id": 1, "content": "Café is nice"},
            {"_id": 2, "content": "café is good"},
            {"_id": 3, "content": "Cafe is ok"},
            {"_id": 4, "content": "cafe is fine"},
        ],
        expected=[{"_id": 1, "content": "Café is nice"}],
        msg="Both sensitive should match only exact case and diacritics",
    ),
    QueryTestCase(
        id="case_diacritic_sensitive_case_insensitive",
        filter={"$text": {"$search": "café", "$caseSensitive": False, "$diacriticSensitive": True}},
        doc=[
            {"_id": 1, "content": "Café is nice"},
            {"_id": 2, "content": "café is good"},
            {"_id": 3, "content": "Cafe is ok"},
            {"_id": 4, "content": "cafe is fine"},
        ],
        expected=[
            {"_id": 1, "content": "Café is nice"},
            {"_id": 2, "content": "café is good"},
        ],
        msg="Diacritic sensitive + case insensitive should match exact diacritics any case",
    ),
    QueryTestCase(
        id="case_case_sensitive_diacritic_insensitive",
        filter={"$text": {"$search": "Cafe", "$caseSensitive": True, "$diacriticSensitive": False}},
        doc=[
            {"_id": 1, "content": "Café is nice"},
            {"_id": 2, "content": "café is good"},
            {"_id": 3, "content": "Cafe is ok"},
            {"_id": 4, "content": "cafe is fine"},
        ],
        expected=[
            {"_id": 1, "content": "Café is nice"},
            {"_id": 3, "content": "Cafe is ok"},
        ],
        msg="Case sensitive + diacritic insensitive should match exact case any diacritics",
    ),
    QueryTestCase(
        id="query_numbers_in_search",
        filter={"$text": {"$search": "2024"}},
        doc=[
            {"_id": 1, "content": "released in 2024"},
            {"_id": 2, "content": "released in 2023"},
        ],
        expected=[{"_id": 1, "content": "released in 2024"}],
        msg="Numbers in search should match documents containing those numbers",
    ),
    QueryTestCase(
        id="query_special_chars_as_delimiters",
        filter={"$text": {"$search": "hello"}},
        doc=[
            {"_id": 1, "content": "hello@world"},
            {"_id": 2, "content": "goodbye world"},
        ],
        expected=[{"_id": 1, "content": "hello@world"}],
        msg="Special characters should act as delimiters",
    ),
    QueryTestCase(
        id="query_dollar_sign",
        filter={"$text": {"$search": "price"}},
        doc=[
            {"_id": 1, "content": "$price is high"},
            {"_id": 2, "content": "cost is low"},
        ],
        expected=[{"_id": 1, "content": "$price is high"}],
        msg="Dollar sign should be treated as delimiter",
    ),
    QueryTestCase(
        id="query_hash_sign",
        filter={"$text": {"$search": "tag"}},
        doc=[
            {"_id": 1, "content": "#tag is trending"},
            {"_id": 2, "content": "no tags here"},
        ],
        expected=[
            {"_id": 1, "content": "#tag is trending"},
            {"_id": 2, "content": "no tags here"},
        ],
        msg="Hash sign should be treated as delimiter, stemming matches 'tags' to 'tag'",
    ),
    QueryTestCase(
        id="query_with_and_non_text_condition",
        filter={"$text": {"$search": "coffee"}, "category": "tech"},
        doc=[
            {"_id": 1, "content": "coffee database", "category": "tech"},
            {"_id": 2, "content": "coffee guide", "category": "docs"},
            {"_id": 3, "content": "python language", "category": "tech"},
        ],
        expected=[{"_id": 1, "content": "coffee database", "category": "tech"}],
        msg="Should combine $text with non-text filter",
    ),
    QueryTestCase(
        id="negation_phrase",
        filter={"$text": {"$search": '"brown fox" -quick'}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "brown fox jumps"},
        ],
        expected=[{"_id": 2, "content": "brown fox jumps"}],
        msg="Negated word should exclude docs even when phrase matches",
    ),
    QueryTestCase(
        id="phrase_multiple_phrases",
        filter={"$text": {"$search": '"brown fox" "red dog"'}},
        doc=[
            {"_id": 1, "content": "the brown fox jumped"},
            {"_id": 2, "content": "the red dog barked"},
            {"_id": 3, "content": "the brown fox and red dog"},
        ],
        expected=[{"_id": 3, "content": "the brown fox and red dog"}],
        msg="Multiple phrases should require all phrases present",
    ),
    QueryTestCase(
        id="data_array_of_mixed_types",
        filter={"$text": {"$search": "hello"}},
        doc=[
            {"_id": 1, "content": [1, "hello", True, "world"]},
            {"_id": 2, "content": [42, False]},
        ],
        expected=[{"_id": 1, "content": [1, "hello", True, "world"]}],
        msg="Only string elements in mixed array should be matched by $text query",
    ),
    QueryTestCase(
        id="query_text_inside_or_in_find",
        filter={"$or": [{"$text": {"$search": "hello"}}]},
        doc=[
            {"_id": 1, "content": "hello world"},
            {"_id": 2, "content": "goodbye world"},
        ],
        expected=[{"_id": 1, "content": "hello world"}],
        msg="$text inside $or in find should succeed",
    ),
    QueryTestCase(
        id="query_language_empty_string_uses_default",
        filter={"$text": {"$search": "running", "$language": ""}},
        doc=[
            {"_id": 1, "content": "I run every day"},
            {"_id": 2, "content": "swimming is fun"},
        ],
        expected=[{"_id": 1, "content": "I run every day"}],
        msg="Empty $language string should use default language stemming",
    ),
    QueryTestCase(
        id="query_unicode_cjk_exact",
        filter={"$text": {"$search": "数据库系统"}},
        doc=[
            {"_id": 1, "content": "数据库系统"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 1, "content": "数据库系统"}],
        msg="CJK full string should match as single token",
    ),
    QueryTestCase(
        id="query_unicode_cjk_partial_no_match",
        filter={"$text": {"$search": "数据库"}},
        doc=[
            {"_id": 1, "content": "数据库系统"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[],
        msg="CJK partial string should not match without word-breaking",
    ),
    QueryTestCase(
        id="query_unicode_japanese",
        filter={"$text": {"$search": "こんにちは世界"}},
        doc=[
            {"_id": 1, "content": "こんにちは世界"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 1, "content": "こんにちは世界"}],
        msg="Japanese full string should match as single token",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEXT_SEARCH_TESTS))
def test_text_search(collection, test):
    """Test $text search behavior with default English language."""
    collection.create_index([("content", "text")])
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


LANGUAGE_NONE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="query_language_none_no_stemming",
        filter={"$text": {"$search": "running", "$language": "none"}},
        doc=[
            {"_id": 1, "content": "I like to run every day"},
            {"_id": 2, "content": "running is fun"},
        ],
        expected=[{"_id": 2, "content": "running is fun"}],
        msg="Language 'none' should disable stemming",
    ),
    QueryTestCase(
        id="query_language_none_matches_stop_words",
        filter={"$text": {"$search": "the", "$language": "none"}},
        doc=[
            {"_id": 1, "content": "the quick brown fox"},
            {"_id": 2, "content": "hello world"},
        ],
        expected=[{"_id": 1, "content": "the quick brown fox"}],
        msg="Language 'none' should not ignore stop words",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LANGUAGE_NONE_TESTS))
def test_text_language_none(collection, test):
    """Test $text with language 'none' disables stemming and stop word removal."""
    collection.create_index([("content", "text")], default_language="none")
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


LANGUAGE_STEMMING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="lang_english",
        filter={"$text": {"$search": "running", "$language": "english"}},
        doc=[
            {"_id": 1, "content": "I run every day"},
            {"_id": 2, "content": "swimming is fun"},
        ],
        expected=[{"_id": 1, "content": "I run every day"}],
        msg="English language should use English stemming",
    ),
    QueryTestCase(
        id="lang_spanish",
        filter={"$text": {"$search": "corriendo", "$language": "spanish"}},
        doc=[
            {"_id": 1, "content": "me gusta correr"},
            {"_id": 2, "content": "nadar es divertido"},
        ],
        expected=[{"_id": 1, "content": "me gusta correr"}],
        msg="Spanish language should use Spanish stemming",
    ),
    QueryTestCase(
        id="lang_french",
        filter={"$text": {"$search": "courant", "$language": "fr"}},
        doc=[
            {"_id": 1, "content": "je cours tous les jours"},
            {"_id": 2, "content": "nager est amusant"},
        ],
        expected=[{"_id": 1, "content": "je cours tous les jours"}],
        msg="French language should use French stemming",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LANGUAGE_STEMMING_TESTS))
def test_text_language_stemming(collection, test):
    """Test $text with specific language uses language-appropriate stemming."""
    language = test.filter["$text"]["$language"]
    collection.create_index([("content", "text")], default_language=language)
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_text_sort_by_non_textscore(collection):
    """Test $text with sort by a regular field (not textScore)."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 3, "content": "hello world"},
            {"_id": 1, "content": "hello there"},
            {"_id": 2, "content": "hello friend"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "hello"}},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "content": "hello there"},
            {"_id": 2, "content": "hello friend"},
            {"_id": 3, "content": "hello world"},
        ],
        msg="Should sort by _id after $text filter",
    )


def test_text_with_projection(collection):
    """Test $text in find() with projection."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee database", "extra": "data"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "coffee"}},
            "projection": {"content": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "content": "coffee database"}],
        msg="Should support projection with $text",
    )


def test_text_with_limit_and_skip(collection):
    """Test $text in find() with limit and skip."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee one"},
            {"_id": 2, "content": "coffee two"},
            {"_id": 3, "content": "coffee three"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "coffee"}},
            "sort": {"_id": 1},
            "skip": 1,
            "limit": 1,
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "content": "coffee two"}],
        msg="Should support limit and skip with $text",
    )


def test_text_in_match_first_stage(collection):
    """Test $text in $match as first pipeline stage succeeds."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee database"},
            {"_id": 2, "content": "python language"},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$text": {"$search": "coffee"}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"_id": 1, "content": "coffee database"}], msg="Should work as first stage"
    )


def test_text_inside_or_in_aggregation(collection):
    """Test $text inside $or in aggregation $match succeeds."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "hello world"},
            {"_id": 2, "content": "goodbye world"},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$or": [{"$text": {"$search": "hello"}}]}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "content": "hello world"}],
        msg="$text inside $or in aggregate $match should succeed",
    )
