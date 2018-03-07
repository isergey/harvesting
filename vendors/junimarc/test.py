# encoding: utf-8
import time
import cProfile, pstats, io
from junimarc.iso2709.reader import Reader
from junimarc.marc_query import MarcQuery


code = """
index_document['title'] = mq.get_field('200').get_subfield('a').get_data()
"""

def main():
    compiled = compile(code, '<string>', 'exec')
    reader = Reader(u'/home/sergey/IdeaProjects/zcollector/tmp/M2002.iso', extended_subfield_code='1')
    i = 0

    for rec in reader.read():
        print(str(rec))
        index_document = {}
        exec(compiled, {}, {'record': rec, 'mq': MarcQuery(rec), 'index_document': index_document})
        print(index_document['title'])
        break

if __name__ == '__main__':
    main()
    