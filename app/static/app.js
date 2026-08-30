const pdfFile = document.getElementById("pdfFile");
const ingestButton = document.getElementById("ingestButton");
const ingestStatus = document.getElementById("ingestStatus");

const askButton = document.getElementById("askButton");
const questionBox = document.getElementById("question");
const answerBox = document.getElementById("answer");


ingestButton.addEventListener("click", async () => {
    const file = pdfFile.files[0];

    if (!file) {
        ingestStatus.textContent = "Please select a PDF file.";
        return;
    }

    ingestButton.disabled = true;
    ingestStatus.textContent = "Ingesting...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/ingest", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();

            throw new Error(
                errorData.detail || `HTTP error ${response.status}`
            );
        }

        const data = await response.json();

        if (data.status === "skipped") {
            ingestStatus.textContent =
                `${data.file_name}: already ingested.`;
        } else {
            ingestStatus.textContent =
                `${data.file_name}: successfully ingested ` +
                `(${data.chunks_added} chunks).`;
        }

        pdfFile.value = "";

    } catch (error) {
        console.error(error);

        ingestStatus.textContent =
            `Ingestion failed: ${error.message}`;

    } finally {
        ingestButton.disabled = false;
    }
});


askButton.addEventListener("click", async () => {
    const question = questionBox.value.trim();

    if (!question) {
        answerBox.textContent = "Please enter a question.";
        return;
    }

    askButton.disabled = true;
    answerBox.textContent = "Thinking...";

    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        if (!response.ok) {
            throw new Error(
                `HTTP error ${response.status}`
            );
        }

        const data = await response.json();

        let output = data.answer;

        if (data.sources && data.sources.length > 0) {
            output += "\n\nSources:\n";

            data.sources.forEach((source, index) => {
                output +=
                    `${index + 1}. ${source.file}` +
                    ` | page ${source.page}` +
                    ` | chunk ${source.chunk}\n`;
            });
        }

        answerBox.textContent = output;

    } catch (error) {
        console.error(error);

        answerBox.textContent =
            "An error occurred while processing the question.";

    } finally {
        askButton.disabled = false;
    }
});
