const askButton = document.getElementById("askButton");
const questionBox = document.getElementById("question");
const answerBox = document.getElementById("answer");


askButton.addEventListener("click", async () => {

    const question = questionBox.value.trim();

    if (!question) {
        answerBox.textContent =
            "Please enter a question.";
        return;
    }

    askButton.disabled = true;
    answerBox.textContent = "Thinking...";

    try {

        const response = await fetch(
            "/api/query",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            }
        );

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {

            const errorData =
                await response.json();

            throw new Error(
                errorData.detail ||
                `HTTP error ${response.status}`
            );
        }

        const data =
            await response.json();

        let output = data.answer;

        if (
            data.sources &&
            data.sources.length > 0
        ) {

            output += "\n\nSources:\n";

            data.sources.forEach(
                (source, index) => {

                    output +=
                        `${index + 1}. ${source.file}` +
                        ` | page ${source.page}` +
                        ` | chunk ${source.chunk}\n`;
                }
            );
        }

        answerBox.textContent = output;

    } catch (error) {

        console.error(error);

        answerBox.textContent =
            `Query failed: ${error.message}`;

    } finally {

        askButton.disabled = false;
    }
});
