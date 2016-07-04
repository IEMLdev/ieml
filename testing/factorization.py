from ieml.script.tools import factorize
import unittest

from models.terms.terms import TermsConnector
from ieml.operator import sc

class FactorizationTest(unittest.TestCase):
    def setUp(self):
        self.terms = TermsConnector()

    def test_all_terms(self):
        term = self.terms.get_all_terms()
        for t in term:
            print(t['_id'])
            self.assertEqual(t['_id'], str(factorize(sc(t['_id']))))
