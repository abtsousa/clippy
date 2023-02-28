import pandas
import re


def searchLinkLocation(db):
    i = 0
    while "Material Multimédia" not in db[i][0][0][0]:
        i = i + 1
    return i


tb_list = pandas.read_html("testUC.html", extract_links="body")  # editar com link para unidade curricular

index = searchLinkLocation(tb_list)
files = tb_list[index]

reg = re.compile(r'^(.+) \((\d+)\)$')
for header, url in files[0]:
    header_name = reg.search(header).group(1)
    header_count = int(reg.search(header).group(2))
    print('%s [%d] -- %s' % (header_name, header_count, url))
print("Finished.")
