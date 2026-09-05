const pdfFile = document.getElementById("pdfFile");
const ingestButton = document.getElementById("ingestButton");
const ingestStatus = document.getElementById("ingestStatus");


ingestButton.addEventListener("click", async () => {

    const file = pdfFile.files[0];

    if (!file) {
        ingestStatus.textContent =
            "Please select a PDF file.";

        return;
    }

    ingestButton.disabled = true;

    ingestStatus.textContent =
        "Ingesting document...";

    const formData = new FormData();

    formData.append(
        "file",
        file
    );

    try {

        const response = await fetch(
            "/api/ingest",
            {
                method: "POST",
                body: formData
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
