const pdfFile = document.getElementById("pdfFile");
const securityLevel = document.getElementById("securityLevel");
const ingestButton = document.getElementById("ingestButton");
const ingestStatus = document.getElementById("ingestStatus");


ingestButton.addEventListener("click", async (event) => {

    event.preventDefault();
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
    formData.append(
        "security_level_id",
        securityLevel.value
    );

    try {

        console.log("PDF:", file.name);
        console.log("Security:", securityLevel.value);
        console.log("Calling /api/ingest");
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

            const detail =
                typeof errorData.detail === "string"
                    ? errorData.detail
                    : JSON.stringify(errorData.detail);

            throw new Error(
                detail ||
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
