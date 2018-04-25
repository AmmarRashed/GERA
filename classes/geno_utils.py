from functools import lru_cache
from itertools import product

from joblib import Parallel, delayed
import numpy as np
import warnings
import GEOparse
import pyhgnc


@lru_cache(maxsize=None)
def lookup_gene(gene_symbol):
    try:
        query = lookup_gene.query
    except Exception as e:
        lookup_gene.query = query = pyhgnc.query()

    return query.hgnc(symbol=gene_symbol)


def get_genes_fold_changes(sample):
    genes_fold_changes = dict()
    for gene in np.unique(sample.index):
        hgnc = lookup_gene(gene)
        if hgnc:
            genes_fold_changes["HGNC:{}".format(hgnc[0].identifier)] = np.median(sample.loc[gene])

    return genes_fold_changes


def get_geo_database(geo_dataset_id):
    return GEOparse.get_GEO(geo=geo_dataset_id).table


def get_genes_fold_changes_wrapper(sample_name, dataframe):
    return (sample_name, get_genes_fold_changes(dataframe[[sample_name]]))


def parse_database(source, labels, index_column="IDENTIFIER", n_jobs=-1):
    dataframe_uncleaned = get_geo_database(source) if type(source) is str else source
    dataframe_cleaned = dataframe_uncleaned[list(labels.keys()) + [index_column]].dropna().set_index(index_column)

    X, y = [], []
    results = Parallel(verbose=10, n_jobs=n_jobs)(delayed(get_genes_fold_changes_wrapper)(*args)
                                                  for args in product(labels.keys(), [dataframe_cleaned]))
    
    for sample_name, fold_changes in results:
        X.append(fold_changes)
        y.append(labels[sample_name])
        print("{} added with length {}".format(sample_name, len(fold_changes)))

    return X, y
