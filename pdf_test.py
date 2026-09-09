from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("Printing Report_ Printing service order list.pdf")
pages = loader.load()

print(pages[3].page_content)
