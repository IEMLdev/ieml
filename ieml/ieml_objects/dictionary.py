import json
from collections import defaultdict, namedtuple
import yaml
from bidict import bidict
import numpy as np
import os

from ieml.commons import LANGUAGES
from ieml.ieml_objects.terms import Term
from ieml.script.constants import MAX_LAYER
from ieml.script.script import AdditiveScript, NullScript, MultiplicativeScript
from metaclasses import Singleton

Relations = namedtuple('Relations', ['contains', 'contained', 'father', 'children',
                                     'opposed', 'associated', 'twins', 'crossed'])


RELATION_TYPES_TO_INDEX = bidict({
    'CONTAINS': 0,
    'CONTAINED': 1,
    'FATHER.SUBSTANCE': 2,
    'FATHER.ATTRIBUTE': 3,
    'FATHER.MODE': 4,
    'CHILDREN.SUBSTANCE': 5,
    'CHILDREN.ATTRIBUTE': 6,
    'CHILDREN.MODE': 7,
    'OPPOSED': 8,
    'ASSOCIATED':9,
    'TWIN': 10,
    'CROSSED': 11
})


class Dictionary(metaclass=Singleton):
    def __init__(self, cache=True):

        super().__init__()

        self.terms = {}
        self.translations = {l: bidict() for l in LANGUAGES}
        self.roots = {}
        self.relations = None

        # terms -> int
        self.ranks = None

        # terms -> terms[] all the terms that decompose the key into subtable
        self.partitions = None

        self.singular_sequences_map = {}

        # list layer (int) -> list of terms at this layer
        self._layers = None         # make layers stacks
        self._index = None
        self._singular_sequences = None

        folder = os.path.join(os.path.dirname(__file__), "../../data/dictionary")
        if cache:
            load_dictionary(folder, dictionary=self)

    def define_terms(self):
        for i, t in enumerate(self.index):
            t.index = i

        for r, v in self.roots.items():
            for t in v:
                t.root = r

        for t in self.terms.values():
            t.translation = {l: self.translations[l][t] for l in self.translations}
            t.inhibitions = []
            t.rank = self.ranks[t]

        for t0, v in self.partitions.items():
            t0.partitions = v
            for t1 in v:
                t1.parent = t0

        self._set_terms_relations()

    @property
    def singular_sequences(self):
        if self._singular_sequences is None:
            self._singular_sequences = sorted(self.terms[ss] for r in self.roots for ss in r.script.singular_sequences)

        return self._singular_sequences

    @property
    def index(self):
        if self._index is None:
            self._index = sorted(self.terms.values())
        return self._index

    @property
    def layers(self):
        if self._layers is None:
            self._layers = [[] for _ in range(MAX_LAYER + 1)]
            for t in self.index:
                self._layers[t.script.layer].append(t)

        return self._layers

    def rel(self, type):
        return self.relations[RELATION_TYPES_TO_INDEX[type], :, :]

    def add_term(self, script, root=False, inhibitions=(), translation=None):
        term = Term(script, self)

        if term.script in self.terms:
            # print("Term %s already defined."%str(term))
            return

        root_p = self.get_root(term)
        if root_p is None:
            if root:
                if not term.script.paradigm:
                    raise ValueError("Can't add the singular sequence term %s as a root paradigm." % str(term))

                self._add_root(term, inhibitions, translation)

            else:
                raise ValueError(
                    "Can't add term %s to the dictionary, it is not defined within a root paradigm." % str(term))

        else:
            if root:
                raise ValueError("Root paradigm intersection with term %s when adding root term %s" %
                                 (str(root_p), str(term)))
            else:
                self._add_term(term, root_p=root_p, inhibitions=inhibitions, translation=translation)

    def compute_relations(self):
        for i, t in enumerate(self.index):
            t.index = i

        contains, contained = self._compute_contains()
        father, children = self._compute_father()
        siblings = self._compute_siblings()

        self.relations = np.concatenate((contains[None, :, :],
                                         contained[None, :, :],
                                         father,
                                         children,
                                         siblings), axis=0).astype(np.bool)
        self._set_terms_relations()

    def compute_ranks(self):
        tables = defaultdict(list)
        self.ranks = {}

        def get_rank_partition(term0, term1):
            def is_connexe_tilling(coords, t):
                shape_t = t.cells.shape
                # test if the table table is a connexe tiling of the table t
                size = 1
                for i, indexes in enumerate(zip(*coords)):
                    if i >= t.dim:
                        return False

                    indexes = sorted(set(indexes))
                    size *= len(indexes)

                    missing = [j for j in range(shape_t[i]) if j not in indexes]
                    # more than one transition from missing -> included
                    if sum(1 for j in missing if (j + 1) % shape_t[i] not in missing) > 1:
                        return False

                    # at least a square of 2x2x1
                    if len(indexes) < 2 and i != 2:
                        return False

                if len(coords) == size:
                    return True

                return False

            def is_dim_subset(coords, t):
                """
                Return if it is a dim subset (only one dimension, the others are not touched)
                If True, return (True, nb_dim)
                else (False, 0)

                :param coords:
                :param t:
                :return:
                """
                shape_ts0 = tuple(len(set(indexes)) for indexes in zip(*coords))
                shape_t = t.cells.shape

                if shape_ts0[2] != shape_t[2]:
                    # subset of tabs, return True if no subset in row/columns
                    return shape_ts0[0] == shape_t[0] and shape_ts0[1] == shape_t[1], shape_ts0[2]

                if shape_ts0[0] == shape_t[0]:
                    return True, shape_ts0[1]

                if shape_ts0[1] == shape_t[1]:
                    return True, shape_ts0[0]

                return False, 0

            # if not table.defined:
            #     raise ValueError("Can't determine if a term is a partition of a non defined table.")

            if term0.script not in term1.script:
                return None, None

            if len(term0.script.tables) != 1:
                # the paradigm is split between tables (weird case)
                # in this case, term0 can be a subset of tabs of each table of term1
                # its must match the tabs headers of term1 tables
                for t1 in term1.script.tables:
                    for t0 in term0.script.tables:
                        if len(t0.headers) != 1:
                            raise ValueError()

                        h = next(t0.headers.__iter__())

                        if h in t1.headers:
                            break
                    else:
                        break
                else:
                    return 1, None

            for table in tables[term1]:
                if term0.script not in table.paradigm:
                    continue

                coords = sorted(table.index(term0.script))

                is_dim, count = is_dim_subset(coords, table)
                if is_dim and count == 1:
                    # one dimension subset, it is a rank 3/5 paradigm
                    return 2, table

                # the coordinates sorted of the ss of s0 in the table t
                # rank is then 2/4
                if is_connexe_tilling(coords, table) or is_dim:
                    return 1, table
            return None, None

        self.partitions = defaultdict(list)
        for ss in self.singular_sequences:
            self.ranks[ss] = 6

        for root in self.roots:
            self.ranks[root] = 1
            tables[root] += root.script.tables

            defined = [root]

            for t in root.script.tables:
                # t.define_table(term=root)
                tables[self.terms[t.paradigm]] += [t]
                self.ranks[self.terms[t.paradigm]] = 1

                defined.append(self.terms[t.paradigm])

            # order by the cardinal (ieml order reversed)
            for term in sorted(self.roots[root], reverse=True)[1:]:
                if term in defined:
                    continue

                if not term.script.paradigm:
                    break

                for term1 in defined:
                    rank, parent_table = get_rank_partition(term, term1)
                    if rank is not None:
                        break
                else:
                    raise ValueError("No rank candidates for %s" % str(term))

                self.ranks[term] = self.ranks[term1] + rank
                tables[term] += term.script.tables

                self.partitions[term1].append(term)
                defined.append(term)

                for t in term.script.tables:
                    tables[self.terms[t.paradigm]] += [t]
                    self.ranks[self.terms[t.paradigm]] = self.ranks[term]
                    self.partitions[term1].append(self.terms[t.paradigm])

                    defined.append(self.terms[t.paradigm])

    def __len__(self):
        return len(self.terms)

    def get_root(self, term):
        try:
            res = {self.singular_sequences_map[ss] for ss in term.script.singular_sequences}
        except KeyError:
            return None

        if len(res) > 1:
            raise ValueError("Term %s is in multiples root paradigms [%s]" % (str(term), ', '.join(map(str, res))))

        return next(res.__iter__())

    def set_translation(self, term, translation):
        if not isinstance(translation, dict) or len(translation) != 2 or any(not isinstance(v, str) for v in translation.values()):
            raise ValueError("Invalid translation format for term %s."%str(term))

        for l in LANGUAGES:
            if l not in translation:
                raise ValueError("Missing translation for %s language for term %s"%(l, str(term)))

            if translation[l] in self.translations[l].inv:
                raise ValueError("Translation %s provided for term %s already used for term %s."%
                                 (translation[l], str(self.translations[l].inv[translation[l]]), str(term)))

            self.translations[l][term] = translation[l]

    def _compute_contains(self):
        print("Compute contains")
        # contain/contained
        contains = np.diag(np.ones(len(self), dtype=np.int8))
        for r_p, v in self.roots.items():
            paradigms = {t for t in v if t.script.paradigm}

            for p in paradigms:
                _contains = [self.terms[ss].index for ss in p.script.singular_sequences] + \
                           [k.index for k in paradigms if k.script in p.script]
                contains[p.index, _contains] = 1

        contained = contains.transpose()
        return [contains, contained]

    def _compute_father(self):
        print("Compute father/child")
        # father/children
        father = np.zeros((3, len(self), len(self)))
        for t in self.terms.values():
            s = t.script

            for sub_s in s if isinstance(s, AdditiveScript) else [s]:
                if len(sub_s.children) == 0 or isinstance(sub_s, NullScript):
                    continue

                for i in range(3):
                    if isinstance(sub_s.children[i], NullScript):
                        continue


                    if sub_s.children[i] in self.terms:
                        father[i, t.index, self.terms[sub_s.children[i]].index] = 1

        children = np.transpose(father, (0, 2, 1))
        return [father, children]

    def _compute_siblings(self):
        # siblings
        # 1 dim => the sibling type
        #  -0 opposed
        #  -1 associated
        #  -2 twin
        #  -3 crossed

        siblings = np.zeros((4, len(self), len(self)))

        print("Compute siblings")

        _twins = []
        for l in self.layers[1:]:
            for i, t0 in enumerate(l):
                if not isinstance(t0.script, MultiplicativeScript):
                    continue

                if t0.script.children[0] == t0.script.children[1]:
                    _twins.append(t0)

                for t1 in [t for t in l[i:] if isinstance(t.script, MultiplicativeScript)]:

                    def _opposed_sibling(s0, s1):
                        return s0.children[0] == s1.children[1] and s0.children[1] == s1.children[0]

                    def _associated_sibling(s0, s1):
                        return s0.children[0] == s1.children[0] and \
                               s0.children[1] == s1.children[1] and \
                               s0.children[2] != s1.children[2]

                    def _crossed_sibling(s0, s1):
                        return s0.layer > 2 and \
                               _opposed_sibling(s0.children[0], s1.children[1]) and \
                               _opposed_sibling(s0.children[1], s1.children[0])

                    if _opposed_sibling(t0.script, t1.script):
                        siblings[0, t0.index, t1.index] = 1
                        siblings[0, t1.index, t0.index] = 1

                    if _associated_sibling(t0.script, t1.script):
                        siblings[1, t0.index, t1.index] = 1
                        siblings[1, t1.index, t0.index] = 1

                    if _crossed_sibling(t0.script, t1.script):
                        siblings[3, t0.index, t1.index] = 1
                        siblings[3, t1.index, t0.index] = 1

        twin_indexes = [t.index for t in _twins]
        siblings[2, twin_indexes, twin_indexes] = 1

        return siblings

    def _set_terms_relations(self):
        _res = defaultdict(dict)

        for i in range(len(self)):
            t = self.index[i]
            _res[t]['contained'] = [self.index[j] for j in np.where(self.rel('CONTAINED')[i, :] == 1)[0]]
            _res[t]['contains'] = [self.index[j] for j in np.where(self.rel('CONTAINS')[i, :] == 1)[0]]

            _res[t]['father'] = [[], [], []]
            _res[t]['children'] = [[], [], []]
            for k in range(3):
                _res[t]['father'][k] = [self.index[j] for j in
                               np.where(self.relations[RELATION_TYPES_TO_INDEX['FATHER.SUBSTANCE'] + k, i, :] == 1)[0]]
                _res[t]['children'][k] = [self.index[j] for j in
                                 np.where(self.relations[RELATION_TYPES_TO_INDEX['CHILDREN.SUBSTANCE'] + k, i, :] == 1)[0]]

            _res[t]['opposed'] = [self.index[j] for j in np.where(self.rel("OPPOSED")[i, :] == 1)[0]]
            _res[t]['associated'] = [self.index[j] for j in np.where(self.rel("ASSOCIATED")[i, :] == 1)[0]]
            _res[t]['crossed'] = [self.index[j] for j in np.where(self.rel("CROSSED")[i, :] == 1)[0]]
            _res[t]['twins'] = []

        _twins = [self.index[j] for j in np.where(self.rel('TWIN')[:, :] == 1)[0]]
        for t in _twins:
            _res[t]['twins'] = _twins

        for t in _res:
            t.relations = Relations(**_res[t])

    def _add_term(self, term, root_p, inhibitions, translation):
        self.set_translation(term, translation)
        self.roots[root_p].append(term)
        self.terms[term.script] = term

    def _add_root(self, term, inhibitions, translation):
        self.roots[term] = list()
        for ss in term.script.singular_sequences:
            self.singular_sequences_map[ss] = term

        self._add_term(term, root_p=term, inhibitions=inhibitions, translation=translation)

    def __getstate__(self):
        return {
            'index': [str(t.script) for t in self.index],
            'translations': {l: {str(t.script): text for t, text in v.items()} for l, v in self.translations.items()},
            'roots': [str(t.script) for t in self.roots],
            'relations': self.relations,
            'ranks': {str(t.script): r for t, r in self.ranks.items()},
            'partitions': {str(t.script): [str(tt.script) for tt in v] for t, v in self.partitions.items()}
        }

    def __setstate__(self, state):
        self._index = [Term(t, dictionary=self) for t in state['index']]
        assert sorted(self._index) == self._index

        self.terms = {t.script: t for t in self.index}
        self.translations = {l: {self.terms[t]: text for t, text in v.items()} for l, v in
                             state['translations'].items()}

        self.roots = {self.terms[r]: [] for r in state['roots']}
        self.ranks = {}
        self.partitions = {self.terms[t]: [self.terms[tt] for tt in v] for t, v in state['partitions'].items()}

        self.singular_sequences_map = {ss: r for r in self.roots for ss in r.script.singular_sequences}
        for t in self.index:
            self.ranks[t] = state['ranks'][str(t.script)]
            self.roots[self.singular_sequences_map[t.script.singular_sequences[0]]].append(t)

        self.relations = state['relations']

        # reset the cache properties
        self._layers = None
        self._singular_sequences = None

        self.define_terms()
        print("\t[*] Dictionary loaded")


def save_dictionary(directory):
    file = os.path.join(directory, "dictionary.json")
    relations_file = os.path.join(directory, "dictionary_relations.npy")

    state = Dictionary().__getstate__()

    # save relations as numpy array
    np.save(arr=state['relations'], file=relations_file)
    del state['relations']

    with open(file, 'w') as fp:
        json.dump(state, fp)


def load_dictionary(directory, dictionary):
    dic_json = os.path.join(directory, "dictionary.json")
    dic_rel = os.path.join(directory, "dictionary_relations.npy")

    with open(dic_json, 'r') as fp:
        state = json.load(fp)

    state['relations'] = np.load(dic_rel)
    dictionary.__setstate__(state)


if __name__ == '__main__':
    Dictionary()