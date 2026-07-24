"""
Basic retrieval evaluation for the PDF RAG application.

Runs a fixed set of questions against PGVector and checks whether
the expected PDF appears in the retrieved results.
"""

from app.config import TOP_K, MAX_DISTANCE
from app.query import vector_store


TEST_CASES = [
    {
        "question": "What are the education details of Amjad?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
        "expected_keywords": [
            "education",
            "university",
            "degree",
        ],
    },
    {
        "question": "What languages does Amjad speak?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
        "expected_keywords": [
            "urdu",
            "english",
        ],
    },
    {
        "question": "What are the education details of Amjad?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
    },
    {
        "question": "What languages does Amjad speak?",
        "expected_file": "Profile.pdf",
        "should_answer": True,
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
        "question": "What are the applicable Sales Order Types?",
        "expected_file": "CCEE_BusOps- Drone Design Document_V1.pdf",
        "should_answer": True,
    },
]


def get_file_name(document) -> str:
    """Return the best available file identifier from document metadata."""

    metadata = document.metadata

    return metadata.get(
        "file_name",
        metadata.get("source", "Unknown"),
    )


def evaluate_test_case(test_case: dict) -> dict:
    """Run retrieval for one test case and return its evaluation results."""

    question = test_case["question"]
    expected_file = test_case["expected_file"]
    should_answer = test_case["should_answer"]

    raw_results = vector_store.similarity_search_with_score(
        query=question,
        k=TOP_K,
    )

    accepted_results = [
        (document, score)
        for document, score in raw_results
        if score <= MAX_DISTANCE
    ]

    retrieved_files = [
        get_file_name(document)
        for document, _ in raw_results
    ]

    accepted_files = [
        get_file_name(document)
        for document, _ in accepted_results
    ]

    best_distance = (
        raw_results[0][1]
        if raw_results
        else None
    )

    expected_keywords = test_case.get(
        "expected_keywords",
        [],
    )

    answer_chunk_pass = contains_expected_keyword(
        accepted_results=accepted_results,
        expected_keywords=expected_keywords,
)
    rank_1_file = (
        retrieved_files[0]
        if retrieved_files
        else None
    )

    if should_answer:
        rank_1_pass = rank_1_file == expected_file
        top_k_pass = expected_file in retrieved_files
        threshold_pass = expected_file in accepted_files
        answerability_pass = len(accepted_results) > 0 and answer_chunk_pass
    else:
        rank_1_pass = None
        top_k_pass = None
        threshold_pass = len(accepted_results) == 0
        answerability_pass = len(accepted_results) == 0

    return {
        "question": question,
        "expected_file": expected_file,
        "should_answer": should_answer,
        "raw_results": raw_results,
        "accepted_results": accepted_results,
        "rank_1_file": rank_1_file,
        "best_distance": best_distance,
        "rank_1_pass": rank_1_pass,
        "top_k_pass": top_k_pass,
        "threshold_pass": threshold_pass,
        "answerability_pass": answerability_pass,
        "answer_chunk_pass": answer_chunk_pass,
    }


def print_test_result(
    test_number: int,
    result: dict,
) -> None:
    """Print one evaluation result in a readable format."""

    print("\n" + "=" * 90)
    print(f"TEST {test_number}")
    print("=" * 90)

    print(f"Question:       {result['question']}")
    print(
        "Expected file:  "
        f"{result['expected_file'] or 'No relevant document'}"
    )
    print(f"Should answer:  {result['should_answer']}")
    print(f"TOP_K:          {TOP_K}")
    print(f"MAX_DISTANCE:   {MAX_DISTANCE:.4f}")

    print("\nRetrieved chunks:")

    if not result["raw_results"]:
        print("No chunks retrieved.")
    else:
        for rank, (document, score) in enumerate(
            result["raw_results"],
            start=1,
        ):
            file_name = get_file_name(document)

            status = (
                "ACCEPTED"
                if score <= MAX_DISTANCE
                else "REJECTED"
            )

            print(
                f"{rank}. "
                f"{file_name} "
                f"| page={document.metadata.get('page', 'Unknown')} "
                f"| distance={score:.4f} "
                f"| {status}"
            )

    print("\nEvaluation:")

    if result["should_answer"]:
        print(
            "Rank-1 expected file: "
            f"{'PASS' if result['rank_1_pass'] else 'FAIL'}"
        )
        print(
            "Expected file in Top-K: "
            f"{'PASS' if result['top_k_pass'] else 'FAIL'}"
        )
        print(
            "Expected file passed threshold: "
            f"{'PASS' if result['threshold_pass'] else 'FAIL'}"
        )
        print(
            "System considered answerable: "
            f"{'PASS' if result['answerability_pass'] else 'FAIL'}"
        )
    else:
        print(
            "Unrelated chunks rejected: "
            f"{'PASS' if result['threshold_pass'] else 'FAIL'}"
        )
        print(
            "System correctly refused answer: "
            f"{'PASS' if result['answerability_pass'] else 'FAIL'}"
        )


def contains_expected_keyword(
    accepted_results: list,
    expected_keywords: list[str],
) -> bool:
    if not expected_keywords:
        return True

    combined_text = " ".join(
        document.page_content.lower()
        for document, _ in accepted_results
    )

    return any(
        keyword.lower() in combined_text
        for keyword in expected_keywords
    )


def run_evaluation() -> None:
    """Run all retrieval test cases and print a summary."""

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

    threshold_passes = sum(
        bool(result["threshold_pass"])
        for result in results
    )

    refusal_passes = sum(
        bool(result["answerability_pass"])
        for result in unanswerable_tests
    )

    answer_chunk_passes = sum(
        bool(result["answer_chunk_pass"])
        for result in answerable_tests
    )


    print("\n" + "=" * 90)
    print("EVALUATION SUMMARY")
    print("=" * 90)

    print(f"Total tests:                 {len(results)}")
    print(f"Answerable tests:            {len(answerable_tests)}")
    print(f"Unanswerable tests:          {len(unanswerable_tests)}")

    print(
        "Correct file at Rank 1:      "
        f"{rank_1_passes}/{len(answerable_tests)}"
    )

    print(
        "Correct file found in Top-K: "
        f"{top_k_passes}/{len(answerable_tests)}"
    )

    print(
        "Threshold tests passed:      "
        f"{threshold_passes}/{len(results)}"
    )

    print(
        "Correct refusals:             "
        f"{refusal_passes}/{len(unanswerable_tests)}"
    )
    print(
        "Answer-bearing chunk found: "
        f"{'PASS' if result['answer_chunk_pass'] else 'FAIL'}"
    )

    print(
        "Answer-bearing chunks found: "
        f"{answer_chunk_passes}/{len(answerable_tests)}"
    )

if __name__ == "__main__":
    run_evaluation()
