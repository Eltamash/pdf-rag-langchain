import pdfplumber

with pdfplumber.open("Report_serviceorder_list.pdf") as pdf:
    page = pdf.pages[3]

    words = page.extract_words()

    for w in words[:100]:
        print(
            w["text"],
            w["x0"],
            w["top"],
            w["x1"],
            w["bottom"],
        )