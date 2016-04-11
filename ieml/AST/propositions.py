import logging
from  functools import total_ordering
from helpers import LoggedInstantiator, Singleton
from models import DictionnaryQueries
from ieml.exceptions import IEMLTermNotFoundInDictionnary, IndistintiveTermsExist
from .propositional_graph import PropositionGraph


class TermsQueries(DictionnaryQueries, metaclass=Singleton):
    """A DB connector singleton class used by terms to prevent the number
    of DictionnaryQueries class instances from exploding"""
    pass


class ClosedProposition:
    """Interface class added to propositions that can be closed to be used in a USL
    These propositions, even if they're not truly closed in the script, are the only one
    that can link to USL's"""
    def __init__(self):
        self.hyperlink = []

    def add_hyperlink_list(self, usl_list):
        self.hyperlink += usl_list


class NonClosedProposition:
    """This class acts as an interface for propositions that *cannot* be closed"""
    pass


class AbstractProposition(metaclass=LoggedInstantiator):
    # these are used for the proposition rendering
    times_symbol = "*"
    left_parent_symbol = "("
    right_parent_symbol = ")"
    plus_symbol = "+"
    left_bracket_symbol = "["
    right_bracket_symbol = "]"

    def __init__(self):
        self.childs = None # will be an iterable (list or tuple)
        self._has_been_checked = False
        self._ieml_string = None

    def check(self):
        """Checks the IEML validity of the IEML proposition"""
        for child in self.childs:
            child.check()

    def _gather_child_links(self):
        return [couple for sublist in [child.gather_hyperlinks() for child in self.childs]
                for couple in sublist]

    def __eq__(self, other):
        """Two propositions are equal if their childs'list or tuple are equal"""
        return self.childs == other.childs

    def __hash__(self):
        """Since the IEML string for any proposition AST is supposed to be unique, it can be used as a hash"""
        return self.__str__().__hash__()

    def is_ordered(self):
        pass

    def order(self):
        pass


class AbstractAdditiveProposition(AbstractProposition):

    def __init__(self, child_elements):
        super().__init__()
        self.childs = child_elements

    def __str__(self):
        if not self._has_been_checked:
            logging.warning("Proposition hasn't been checked for ordering and consistency")

        return self.left_bracket_symbol + \
               self.plus_symbol.join([str(element) for element in self.childs]) + \
               self.right_bracket_symbol


class AbstractMultiplicativeProposition(AbstractProposition):

    def __init__(self, child_subst, child_attr=None, child_mode=None):
        super().__init__()
        self.subst = child_subst
        self.attr = child_attr
        self.mode = child_mode
        self.childs = (self.subst, self.attr, self.mode)

    def __str__(self):
        if not self._has_been_checked:
            logging.warning("Proposition hasn't been checked for ordering and consistency")

        return self.left_parent_symbol + \
               str(self.subst) + self.times_symbol + \
               str(self.attr) + self.times_symbol + \
               str(self.mode) + self.right_parent_symbol

    def check(self):
        for child in self.childs:
            child.check()
            if not child.is_oredered():
                logging.warning("Additive proposition %s is not ordered, ordering it now" % str(child))
                child.order()


class Morpheme(AbstractAdditiveProposition, NonClosedProposition):

    def __str__(self):
        if not self._has_been_checked:
            logging.warning("Proposition hasn't been checked for ordering and consistency")

        return self.left_parent_symbol + \
               self.plus_symbol.join([str(element) for element in self.childs]) + \
               self.right_parent_symbol

    def check(self):
        # first, we "ask" all the terms to check themselves through the parent method
        super().check()
        # then we check the terms for unicity turning their objectid's into a set
        terms_objectids_list = [term.objectid for term in self.childs]
        if len(terms_objectids_list) != len(set([node.id for node in terms_objectids_list])):
            raise IndistintiveTermsExist()
        # TODO : more checking
        # - term intersection
        # - paradigmatic intersection
        self._has_been_checked = True


    def is_ordered(self):
        """Returns true if its list of childs are sorted"""
        for i in range(len(self.childs)-1):
            if not self.childs[i] <= self.childs[i+1]:
                return False

        return True

    def order(self):
        """Orders the terms"""
        # terms have the TotalOrder decorator, as such, they can be automatically ordered
        self.childs = self.childs.sort()


class Word(AbstractMultiplicativeProposition, ClosedProposition):

    def __init__(self, child_subst, child_mode=None):
        super().__init__()
        self.subst = child_subst
        self.mode = child_mode
        self.childs = (self.subst, self.mode)

    def __str__(self):
        if self.mode is None:
            return self.left_bracket_symbol + \
                   str(self.subst) +\
                   self.right_bracket_symbol
        else:
            return self.left_bracket_symbol + \
                   str(self.subst) + self.times_symbol + \
                   str(self.mode) + self.right_bracket_symbol

    def gather_hyperlinks(self):
        # since morphemes cannot have hyperlinks, we don't gather links for the underlying childs
        return [(self, usl_ref) for usl_ref in self.hyperlink]

@total_ordering
class AbstractClause(AbstractMultiplicativeProposition, NonClosedProposition):

    def gather_hyperlinks(self):
        return self._gather_child_links()

    def __gt__(self, other):
        if self.subst != other.subst:
            # the comparison depends on the terms of the two substs
            pass
        else:
            if self.attr != other.attr:
                pass # the comparison depends on the terms of the two attrs
            else:
                # TODO : define exception for this case (which shouldn't really happen anyway)
                raise Exception()


class Clause(AbstractClause):
    pass


class SuperClause(AbstractClause):
    pass


class AbstractSentence(AbstractAdditiveProposition, ClosedProposition):

    def __init__(self, child_elements):
        super().__init__(child_elements)
        self.graph = None

    def gather_hyperlinks(self):
        # first we build the (object, usl) tuple list for the current object
        links_list = [(self, usl_ref) for usl_ref in self.hyperlink]
        # then we add the hyperlinks from the child elements
        return links_list + self._gather_child_links()

    def check(self):
        # first, we call the parent method, which, by calling the check methods on clauses or superclauses,
        # ensures that the child elements are well ordered (especially the terms, or the underlying sentence)
        super().check()
        # then, we build the (super)sentence's graph using the (super)clause list
        self.graph = PropositionGraph(self.childs)
        self.graph.check() #the graph does some checking

    def order(self):
        """Orders the clauses/superclauses inside the sentence/supersentence, using the graph"""
        if self.graph is not None:
            self.childs = self.graph.get_ordereded_clauses_list()
        else:
            raise Exception()


class Sentence(AbstractSentence):

    def __init__(self, child_elements):
        super().__init__(child_elements)
        self.graph = None


class SuperSentence(AbstractSentence):

    def __init__(self, child_elements):
        super().__init__(child_elements)


@total_ordering
class Term(metaclass=LoggedInstantiator):

    def __init__(self, ieml_string):
        self.ieml = ieml_string
        self.objectid = None
        self.canonical_forms = None

    def __str__(self):
        return "[" + self.ieml + "]"

    def check(self):
        """Checks that the term exists in the database, and if found, stores the terms's objectid"""
        # TODO : optimize this code :
        # for now, since I don't know how to do exact text queries in MongoDB,
        # i'm retrieving the list of ALL mathing IEML strings and then checking if the
        # self.ieml string is in the list
        query_result_list = TermsQueries().search_for_ieml_terms(self.ieml)
        try:
            index = query_result_list.index(self.ieml)
            self.objectid = query_result_list[index]["_id"]
            self.canonical_forms = query_result_list[index]["CANONICAL"]
        except ValueError:
            raise IEMLTermNotFoundInDictionnary(self.ieml)

    def __hash__(self):
        return self.objectid.__hash__()

    def __eq__(self, other):
        return self.objectid == other.objectid and self.objectid is not None

    def __gt__(self, other):
        # we use the DB's canonical forms
        # if the term has MORE canonical sequences, it's "BIGGER", so GT is TRUE
        if len(self.canonical_forms) > len(other.canonical_forms):
            return True
        else: # else, we have to compare sequences using the regular aphabetical order
            for i, seq in enumerate(self.canonical_forms):
                # for each sequence, if the sequences are different, we can return the comparison
                if self.canonical_forms[i] != other.canonical_forms[i]:
                    return self.canonical_forms[i] > other.canonical_forms[i]

        #TODO : Define an exception to be raised if the comparison doesn't return
        raise Exception()