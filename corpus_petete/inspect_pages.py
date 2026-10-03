from attach_bbox import load_bbox

pages = load_bbox("petete_01_azul_bbox.html")

for n, page in enumerate(pages, start=1):

    words = []

    for block in page["blocks"]:
        for line in block["lines"]:
            for word in line["words"]:
                words.append(word["text"])

    text = " ".join(words)
    text = " ".join(text.split())

    print(f"{n:03d} | {text[:180]}")
