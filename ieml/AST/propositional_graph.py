import logging

import numpy as np

from ieml.exceptions import InvalidGraphNode
from ..exceptions import NodeHasNoParent, NodeHasTooMuchParents, NoRootNodeFound, SeveralRootNodeFound

class PropositionGraph:
    """Stores a representation of the graph described in the visual web interface"""

    def __init__(self, clause_list):
        # this table stores each parent node (node that is a substance in a clause) and
        # the clause that it is the substance of
        self.parent_nodes = {}
        self.vertices_list = clause_list #
        self.nodes_set = set()

        for clause in self.vertices_list:
            #we add the current clause to the "parent" node table
            if clause.subst not in self.parent_nodes:
                self.parent_nodes[clause.subst] = list()
            self.parent_nodes[clause.subst].append(clause)
            #we add the end and start node to the node table
            for node in [clause.attr, clause.subst]:
                self.nodes_set.add(node)

        # since this list has been built from a set, every nodes are unique
        self.nodes_list = list(self.nodes_set)
        self.nodes_list.sort()
        self.adjacency_matrix = None
        self._build_adjacency_matrix()
        self.graph_checker = PropositionGraphChecker(self)

        self.root_node = None # this'll be set once the graph_checker has checked its existence and found it
        self.generations_table = None # This'll store the clauses by *generations* upon a method call
        self.has_been_checked = False

    def _build_adjacency_matrix(self):
        """Once the graph is fully built, this function is called to build the adjacency matrix"""

        self.adjacency_matrix = np.zeros((len(self.nodes_list), len(self.nodes_list)), dtype=bool)
        for vertice in self.vertices_list:
            # A cell is true if node x -> node y, else it's false
            # thus, for each vertice, we set the (subst_node_index,attr_node_index) cell to true
            x,y = self.nodes_list.index(vertice.subst), self.nodes_list.index(vertice.attr)
            self.adjacency_matrix[x][y] = True

    def check(self):
        try:
            self.graph_checker.do_checks()
        except InvalidGraphNode as err:
            err.set_node_ieml(str(self.nodes_list[err.node_id]))

        self.root_node = self.nodes_list[self.graph_checker.root_node_index]
        logging.debug("Root node for sentence is %s" % str(self.root_node))
        self.has_been_checked = True

    def _build_generation_table(self):
        """This needs the reference of the root node to work"""
        # this works using a simple graph-traversing algorithm, using a stack.
        # it works the assumption that the graph is a tree, and that assumption
        # should have been checked by the graph_checker

        # buffer variables and lists
        self.generations_table = [] #list of lists of clauses
        current_gen = 0
        current_gen_parent_nodes = [self.root_node]
        while current_gen_parent_nodes: #as long as we have parents nodes...
            # finding all the clauses for the current generation
            self.generations_table.append([])
            for parent_node in current_gen_parent_nodes:
                self.generations_table[current_gen] += self.parent_nodes[parent_node]

            # retrieving all the child nodes of this generation that are parents for the next,
            # and setting them as the next iterations's parent nodes
            next_gen_parent_nodes = []
            for clause in self.generations_table[current_gen]:
                if clause.attr in self.parent_nodes:
                    next_gen_parent_nodes.append(clause.attr)

            # "closing" the loop
            current_gen_parent_nodes = next_gen_parent_nodes
            current_gen += 1

    def get_ordereded_clauses_list(self):
        """Returns the same set of clauses as the one in input, but put in the right order"""
        if not self.has_been_checked:
            self.check()

        self._build_generation_table()
        ordered_clauses = []
        for generation in self.generations_table:
            generation.sort() # clauses/sperclauses are totally ordered, so sort works on a list of those
            ordered_clauses += generation

        return ordered_clauses



class PropositionGraphChecker:
    """Takes care of checking if a graph describing an IEMl proposition respects the IEML structura
    rules """

    def __init__(self, graph):
        self.adjacency_matrix = graph.adjacency_matrix
        self.node_count = self.adjacency_matrix.shape[0]
        self.ones_bool = np.full(self.node_count, True, dtype=bool)
        self.ones_int = np.full(self.node_count, 1,  dtype=int)
        self.row_and = np.dot(self.adjacency_matrix, self.ones_bool)
        self.column_and = np.dot(self.adjacency_matrix.transpose(), self.ones_bool)

    def do_checks(self):
        """Runs the multiple checks the graph checker is in charge of, and 'finds' the graph root"""
        self._check_has_unique_root()
        self._check_only_unique_parent()


    def _check_has_unique_root(self):
        """Using the adjacency matrix, checks that the graph has a unique root, and that this root
        has at least one child"""
        # checking the "root count"
        has_parent_count = np.dot(self.column_and.astype(dtype=int), self.column_and.astype(dtype=int))
        root_count = self.node_count - has_parent_count
        if root_count == 0: # only one root
            raise NoRootNodeFound()
        elif root_count > 1:# more than one root
            raise SeveralRootNodeFound()
        else :
            #saving the index of the root_node
            for index, node_xor in enumerate(self.column_and):
                if not node_xor:
                    self.root_node_index = index
                    logging.debug("Found root of graph : node %i" % index)
                    break

    def _check_only_unique_parent(self):
        """checks that each element of the graph only has one parent (making the graph a tree).
        This check depends on the root_node check """
        # getting the "incoming" vertices count for each node in an array
        incoming_connection_count = np.dot(self.adjacency_matrix.transpose().astype(dtype=int), self.ones_int)

        # for all node, except the root, there can and should only be ONE parent.
        for index, conn_sum in enumerate(incoming_connection_count):
            if conn_sum != 1 and index != self.root_node_index:
                if conn_sum > 1:
                    raise NodeHasTooMuchParents(index)
                else:
                    raise NodeHasNoParent(index)
