"""
Retrieval evaluation for the PDF RAG application.

Compares:

1. Similarity search + distance threshold
2. Similarity search + reranking + neighboring-chunk expansion

No LLM is called. This evaluates whether the retrieved context itself
contains the expected answer evidence.
"""

from langchain_core.documents import Document

from app.config import (
    MAX_DISTANCE,
    NEIGHBOR_WINDOW,
    RERANK_FETCH_K,
    RERANK_TOP_K,
    TOP_K,
)
from app.query import (
    expand_with_neighbors,
    get_file_name,
    vector_store,
)
from app.reranker import rerank_documents


TEST_CASES = [
    {
        "question": "What is the key strength of Amjad?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
        "expected_keywords": [
            "integration",
            "automation",
        ],
        "keyword_match": "any",
    },
    {
        "question": "What are the education details of Amjad?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
        "expected_keywords": [
            "shaheed zulfikar ali bhutto",
            "mcs",
            "computer programming",
        ],
        "keyword_match": "any",
    },
    {
        "question": "What languages does Amjad speak?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
        "expected_keywords": [
            "urdu",
            "english",
        ],
        "keyword_match": "all",
    },

    {
        "question": "Explain the purchase order process.",
        "expected_file": "CCEE_BusOps- Drone Design Document_V1.pdf",
        "should_answer": True,
    },
    {
        "question": "How many Sales Types are there?",
        "expected_file": "CCEE_BusOps- Drone Design Document_V1.pdf",
        "should_answer": True,
    },    
    {
        "question": "Sales Invoices are generated from which document?",
        "expected_file": "CCEE_BusOps- Drone Design Document_V1.pdf",
        "should_answer": True,
    },    
    {
        "question": "Who won the FIFA World Cup in 2018?",
        "expected_file": None,
        "should_answer": False,
    },
    {
        "question": "What is the weather in Dubai today?",
        "expected_file": None,
        "should_answer": False,
    },
    {
        "question": "What is missing in Insurance claim policy?",
        "expected_file": "MotorClaimForm.pdf",
        "should_answer": False,
    }, 

    {
        "question": "What are all the Sales Order types?",
        "expected_file": "CCEE_BusOps- Drone Design Document_V1.pdf",
        "should_answer": True,
        "expected_keywords": [
            "3pp",
            "b2b",
            "b2c",
            "brc",
            "drf",
            "drs",
            "ppr",
            "spf",
            "sps",
            "swc",
            "swn",
            "usp",
            "oth",
        ],
        # For this completeness test, every code must exist.
        "keyword_match": "all",
    },
    {
        "question": "Who won the FIFA World Cup in 2018?",
        "expected_file": None,
        "should_answer": False,
        "expected_keywords": [],
        "keyword_match": "any",
    },
    {
        "question": "What is the weather in Dubai today?",
        "expected_file": None,
        "should_answer": False,
        "expected_keywords": [],
        "keyword_match": "any",
    },
    {
        "question": "What is the capital of Brazil?",
        "expected_file": None,
        "should_answer": False,
        "expected_keywords": [],
        "keyword_match": "any",
    },
]


def document_text(documents: list[Document]) -> str:
    """Combine retrieved chunk text for keyword evaluation."""

    return "\n".join(
        document.page_content.lower()
        for document in documents
    )


def contains_expected_keywords(
    documents: list[Document],
    expected_keywords: list[str],
    keyword_match: str = "any",
) -> bool:
    """
    Check whether retrieved chunks contain expected answer evidence.

    keyword_match="any":
        At least one expected keyword must appear.

    keyword_match="all":
        Every expected keyword must appear.
    """

    if not expected_keywords:
        return True

    combined_text = document_text(documents)

    matches = [
        keyword.lower() in combined_text
        for keyword in expected_keywords
    ]

    if keyword_match == "all":
        return all(matches)

    return any(matches)


def find_missing_keywords(
    documents: list[Document],
    expected_keywords: list[str],
) -> list[str]:
    """Return expected keywords absent from the retrieved context."""

    combined_text = document_text(documents)

    return [
        keyword
        for keyword in expected_keywords
        if keyword.lower() not in combined_text
    ]


def first_answer_bearing_rank(
    results: list[tuple[Document, float]],
    expected_keywords: list[str],
    keyword_match: str,
) -> int | None:
    """
    Return the earliest rank at which accumulated chunks contain
    the expected evidence.
    """

    accumulated_documents: list[Document] = []

    for rank, (document, _) in enumerate(
        results,
        start=1,
    ):
        accumulated_documents.append(document)

        if contains_expected_keywords(
            documents=accumulated_documents,
            expected_keywords=expected_keywords,
            keyword_match=keyword_match,
        ):
            return rank

    return None


def evaluate_test_case(test_case: dict) -> dict:
    """Evaluate one test case against both retrieval pipelines."""

    question = test_case["question"]
    expected_file = test_case["expected_file"]
    should_answer = test_case["should_answer"]

    expected_keywords = test_case.get(
        "expected_keywords",
        [],
    )

    keyword_match = test_case.get(
        "keyword_match",
        "any",
    )

    # Retrieve a wider set because the reranker needs candidates.
    raw_results = vector_store.similarity_search_with_score(
        query=question,
        k=RERANK_FETCH_K,
    )

    threshold_results = [
        (document, distance)
        for document, distance in raw_results
        if distance <= MAX_DISTANCE
    ]

    baseline_results = threshold_results[:TOP_K]

    baseline_documents = [
        document
        for document, _ in baseline_results
    ]

    # Rerank the original candidate set.
    reranked_results = rerank_documents(
        question=question,
        results=raw_results,
        top_k=RERANK_TOP_K,
    )

    reranked_documents = [
        item.document
        for item in reranked_results
    ]

    expanded_documents = expand_with_neighbors(
        documents=reranked_documents,
        neighbor_window=NEIGHBOR_WINDOW,
    )

    retrieved_files = [
        get_file_name(document)
        for document, _ in raw_results
    ]

    threshold_files = [
        get_file_name(document)
        for document, _ in threshold_results
    ]

    reranked_files = [
        get_file_name(item.document)
        for item in reranked_results
    ]

    best_distance = (
        raw_results[0][1]
        if raw_results
        else None
    )

    rank_1_file = (
        retrieved_files[0]
        if retrieved_files
        else None
    )

    baseline_answer_bearing = contains_expected_keywords(
        documents=baseline_documents,
        expected_keywords=expected_keywords,
        keyword_match=keyword_match,
    )

    expanded_answer_bearing = contains_expected_keywords(
        documents=expanded_documents,
        expected_keywords=expected_keywords,
        keyword_match=keyword_match,
    )

    baseline_missing_keywords = find_missing_keywords(
        documents=baseline_documents,
        expected_keywords=expected_keywords,
    )

    expanded_missing_keywords = find_missing_keywords(
        documents=expanded_documents,
        expected_keywords=expected_keywords,
    )

    answer_bearing_rank = first_answer_bearing_rank(
        results=raw_results,
        expected_keywords=expected_keywords,
        keyword_match=keyword_match,
    )

    if should_answer:
        rank_1_pass = rank_1_file == expected_file
        top_k_pass = expected_file in retrieved_files[:TOP_K]
        threshold_pass = expected_file in threshold_files

        reranked_file_pass = (
            expected_file in reranked_files
        )

        baseline_pipeline_pass = (
            bool(baseline_documents)
            and baseline_answer_bearing
        )

        expanded_pipeline_pass = (
            bool(expanded_documents)
            and expanded_answer_bearing
        )

        correct_refusal = None
    else:
        rank_1_pass = None
        top_k_pass = None
        threshold_pass = len(threshold_results) == 0
        reranked_file_pass = None

        # The current refusal gate is still the vector-distance threshold.
        correct_refusal = len(threshold_results) == 0

        baseline_pipeline_pass = correct_refusal
        expanded_pipeline_pass = correct_refusal

    return {
        "question": question,
        "expected_file": expected_file,
        "should_answer": should_answer,
        "expected_keywords": expected_keywords,
        "keyword_match": keyword_match,
        "raw_results": raw_results,
        "threshold_results": threshold_results,
        "reranked_results": reranked_results,
        "expanded_documents": expanded_documents,
        "best_distance": best_distance,
        "rank_1_file": rank_1_file,
        "rank_1_pass": rank_1_pass,
        "top_k_pass": top_k_pass,
        "threshold_pass": threshold_pass,
        "reranked_file_pass": reranked_file_pass,
        "baseline_answer_bearing": baseline_answer_bearing,
        "expanded_answer_bearing": expanded_answer_bearing,
        "baseline_missing_keywords": baseline_missing_keywords,
        "expanded_missing_keywords": expanded_missing_keywords,
        "answer_bearing_rank": answer_bearing_rank,
        "baseline_pipeline_pass": baseline_pipeline_pass,
        "expanded_pipeline_pass": expanded_pipeline_pass,
        "correct_refusal": correct_refusal,
    }


def print_status(passed: bool | None) -> str:
    """Format PASS, FAIL, or N/A."""

    if passed is None:
        return "N/A"

    return "PASS" if passed else "FAIL"


def print_test_result(
    test_number: int,
    result: dict,
) -> None:
    """Print diagnostics for one test case."""

    print("\n" + "=" * 100)
    print(f"TEST {test_number}")
    print("=" * 100)

    print(f"Question:       {result['question']}")
    print(
        "Expected file:  "
        f"{result['expected_file'] or 'No relevant document'}"
    )
    print(f"Should answer:  {result['should_answer']}")
    print(f"MAX_DISTANCE:   {MAX_DISTANCE:.4f}")
    print(f"RERANK_FETCH_K: {RERANK_FETCH_K}")
    print(f"RERANK_TOP_K:   {RERANK_TOP_K}")
    print(f"NEIGHBOR_WINDOW:{NEIGHBOR_WINDOW}")

    print("\nVector candidates:")

    for rank, (document, distance) in enumerate(
        result["raw_results"],
        start=1,
    ):
        status = (
            "ACCEPTED"
            if distance <= MAX_DISTANCE
            else "REJECTED"
        )

        print(
            f"{rank}. "
            f"{get_file_name(document)} "
            f"| page={document.metadata.get('page', 'Unknown')} "
            f"| chunk={document.metadata.get('chunk_index', 'Unknown')} "
            f"| distance={distance:.4f} "
            f"| {status}"
        )

    print("\nReranked selections:")

    for rank, item in enumerate(
        result["reranked_results"],
        start=1,
    ):
        document = item.document

        print(
            f"{rank}. "
            f"{get_file_name(document)} "
            f"| page={document.metadata.get('page', 'Unknown')} "
            f"| chunk={document.metadata.get('chunk_index', 'Unknown')} "
            f"| reranker={item.reranker_score:.4f} "
            f"| vector={item.retrieval_distance:.4f}"
        )

    print("\nExpanded neighboring context:")

    for document in result["expanded_documents"]:
        print(
            f"- {get_file_name(document)} "
            f"| page={document.metadata.get('page', 'Unknown')} "
            f"| chunk={document.metadata.get('chunk_index', 'Unknown')}"
        )

    print("\nEvaluation:")

    if result["should_answer"]:
        print(
            "Expected file at Rank 1:           "
            f"{print_status(result['rank_1_pass'])}"
        )
        print(
            "Expected file in vector Top-K:    "
            f"{print_status(result['top_k_pass'])}"
        )
        print(
            "Expected file passed threshold:   "
            f"{print_status(result['threshold_pass'])}"
        )
        print(
            "Expected file after reranking:    "
            f"{print_status(result['reranked_file_pass'])}"
        )
        print(
            "Baseline answer evidence:         "
            f"{print_status(result['baseline_answer_bearing'])}"
        )
        print(
            "Reranked + neighbor evidence:     "
            f"{print_status(result['expanded_answer_bearing'])}"
        )

        print(
            "First answer-bearing vector rank: "
            f"{result['answer_bearing_rank'] or 'Not found'}"
        )

        if result["baseline_missing_keywords"]:
            print(
                "Baseline missing keywords:      "
                + ", ".join(
                    result["baseline_missing_keywords"]
                )
            )

        if result["expanded_missing_keywords"]:
            print(
                "Expanded missing keywords:      "
                + ", ".join(
                    result["expanded_missing_keywords"]
                )
            )
    else:
        print(
            "Correctly refused by threshold:   "
            f"{print_status(result['correct_refusal'])}"
        )


def run_evaluation() -> None:
    """Run every test and print baseline versus expanded summaries."""

    results = []

    for test_number, test_case in enumerate(
        TEST_CASES,
        start=1,
    ):
        result = evaluate_test_case(test_case)
        results.append(result)

        print_test_result(
            test_number=test_number,
            result=result,
        )

    answerable_tests = [
        result
        for result in results
        if result["should_answer"]
    ]

    unanswerable_tests = [
        result
        for result in results
        if not result["should_answer"]
    ]

    rank_1_passes = sum(
        bool(result["rank_1_pass"])
        for result in answerable_tests
    )

    top_k_passes = sum(
        bool(result["top_k_pass"])
        for result in answerable_tests
    )

    threshold_file_passes = sum(
        bool(result["threshold_pass"])
        for result in answerable_tests
    )

    reranked_file_passes = sum(
        bool(result["reranked_file_pass"])
        for result in answerable_tests
    )

    baseline_evidence_passes = sum(
        bool(result["baseline_answer_bearing"])
        for result in answerable_tests
    )

    expanded_evidence_passes = sum(
        bool(result["expanded_answer_bearing"])
        for result in answerable_tests
    )

    refusal_passes = sum(
        bool(result["correct_refusal"])
        for result in unanswerable_tests
    )

    overall_baseline_passes = sum(
        bool(result["baseline_pipeline_pass"])
        for result in results
    )

    overall_expanded_passes = sum(
        bool(result["expanded_pipeline_pass"])
        for result in results
    )

    print("\n" + "=" * 100)
    print("EVALUATION SUMMARY")
    print("=" * 100)

    print(f"Total tests:                        {len(results)}")
    print(f"Answerable tests:                   {len(answerable_tests)}")
    print(f"Unanswerable tests:                 {len(unanswerable_tests)}")

    print(
        "Correct expected file at Rank 1:    "
        f"{rank_1_passes}/{len(answerable_tests)}"
    )

    print(
        "Correct expected file in Top-K:     "
        f"{top_k_passes}/{len(answerable_tests)}"
    )

    print(
        "Expected file passed threshold:     "
        f"{threshold_file_passes}/{len(answerable_tests)}"
    )

    print(
        "Expected file after reranking:      "
        f"{reranked_file_passes}/{len(answerable_tests)}"
    )

    print(
        "Baseline answer-bearing context:    "
        f"{baseline_evidence_passes}/{len(answerable_tests)}"
    )

    print(
        "Reranked + neighbor answer context: "
        f"{expanded_evidence_passes}/{len(answerable_tests)}"
    )

    print(
        "Correct refusals:                    "
        f"{refusal_passes}/{len(unanswerable_tests)}"
    )

    print(
        "Overall baseline pipeline:           "
        f"{overall_baseline_passes}/{len(results)}"
    )

    print(
        "Overall reranked + neighbor pipeline:"
        f" {overall_expanded_passes}/{len(results)}"
    )


if __name__ == "__main__":
    run_evaluation()