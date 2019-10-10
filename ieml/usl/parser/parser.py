import logging, os
import ply.yacc as yacc

from ieml.constants import PARSER_FOLDER
from ieml.dictionary.script import script, Script
from ieml.usl import Word, Phrase, PolyMorpheme, check_word
from ieml.exceptions import CannotParse
from ieml.usl.constants import ADDRESS_SCRIPTS
from ieml.usl.word import Lexeme
from ieml.usl.syntagmatic_function import SyntagmaticFunction
from .lexer import get_lexer, tokens
import threading

class IEMLParserSingleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(IEMLParserSingleton, cls).__call__()

        return cls._instance


class IEMLParser():
    tokens = tokens
    lock = threading.Lock()

    def __init__(self, dictionary=None):
        # Build the lexer and parser
        self.lexer = get_lexer()
        self.parser = yacc.yacc(module=self, errorlog=logging, start='proposition',
                                debug=True, optimize=True,
                                picklefile=os.path.join(PARSER_FOLDER, "ieml_parser.pickle"))
        self._ieml = None

        self.dictionary = dictionary

    def parse(self, s, factorize_script=False):
        """Parses the input string, and returns a reference to the created AST's root"""
        with self.lock:
            self.factorize_script = factorize_script
            try:
                return self.parser.parse(s, lexer=self.lexer)
            except ValueError as e:
                raise CannotParse(s, str(e))
            except CannotParse as e:
                e.s = s
                raise e


    # Parsing rules
    def p_ieml_proposition(self, p):
        """proposition :  morpheme
                        | poly_morpheme
                        | word

                        """
        p[0] = p[1]

    def p_literal_list(self, p):
        """literal_list : literal_list LITERAL
                        | LITERAL"""

        if len(p) == 3:
            p[0] = p[1] + [p[2][1:-1]]
        else:
            p[0] = [p[1][1:-1]]


    def p_morpheme(self, p):
        """morpheme : MORPHEME
                    | MORPHEME literal_list"""

        morpheme = script(p[1], factorize=self.factorize_script)
        if len(p) == 3:
            logging.error("Literals not supported on script for the moments, and are ignored.")

        if self.dictionary is not None and morpheme not in self.dictionary:
            raise ValueError("Morpheme {} not defined in dictionary".format(morpheme))

        p[0] = morpheme

    def p_morpheme_sum(self, p):
        """morpheme_sum : morpheme_sum morpheme
                        | morpheme"""

        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_group(self, p):
        """ group : GROUP_MULTIPLICITY LPAREN morpheme_sum RPAREN """
        p[0] = (p[3], int(p[1][1:]))

    def p_group_list(self, p):
        """ group_list : group group_list
                       | group """
        if len(p) == 3:
            p[0] = [p[1]] + p[2]
        else:
            p[0] = [p[1]]

    def p_poly_morpheme(self, p):
        """ poly_morpheme : morpheme_sum group_list
                           | morpheme_sum
                           | group_list"""
        if len(p) == 3:
            p[0] = PolyMorpheme(constant=p[1], groups=p[2])
        elif isinstance(p[1][0], Script):
            p[0] = PolyMorpheme(constant=p[1], groups=())
        else:
            p[0] = PolyMorpheme(constant=[], groups=p[1])


    def p_lexeme(self, p):
        """lexeme : LPAREN poly_morpheme RPAREN LPAREN poly_morpheme RPAREN LPAREN poly_morpheme RPAREN
                  | LPAREN RPAREN LPAREN poly_morpheme RPAREN LPAREN poly_morpheme RPAREN
                  | LPAREN RPAREN LPAREN RPAREN LPAREN poly_morpheme RPAREN
                  | LPAREN poly_morpheme RPAREN LPAREN poly_morpheme RPAREN
                  | LPAREN RPAREN LPAREN poly_morpheme RPAREN
                  | LPAREN poly_morpheme RPAREN
                  | LPAREN RPAREN"""

        if len(p) == 10:
            p[0] = Lexeme(pm_address=p[2], pm_content=p[5], pm_transformation=p[8])
        elif len(p) == 9:
            p[0] = Lexeme(pm_address=PolyMorpheme(constant=[]), pm_content=p[4], pm_transformation=p[7])
        elif len(p) == 8:
            p[0] = Lexeme(pm_address=PolyMorpheme(constant=[]), pm_content=PolyMorpheme(constant=[]), pm_transformation=p[6])
        elif len(p) == 7:
            p[0] = Lexeme(pm_address=p[2], pm_content=p[5], pm_transformation=PolyMorpheme(constant=[]))
        elif len(p) == 6:
            p[0] = Lexeme(pm_address=PolyMorpheme(constant=[]), pm_content=p[4], pm_transformation=PolyMorpheme(constant=[]))
        elif len(p) == 4:
            p[0] = Lexeme(pm_address=p[2], pm_content=PolyMorpheme(constant=[]),
                                pm_transformation=PolyMorpheme(constant=[]))
        else:
            p[0] = Lexeme(pm_address=PolyMorpheme(constant=[]), pm_content=PolyMorpheme(constant=[]),
                                pm_transformation=PolyMorpheme(constant=[]))

    def p_positioned_lexeme(self, p):
        """positioned_lexeme : morpheme_sum lexeme
                             | lexeme"""
        if len(p) == 3:
            p[0] = p[1], p[2]
        else:
            p[0] = [], p[1]

    def p_lexeme_list(self, p):
        """lexeme_list : lexeme_list RCHEVRON EXCLAMATION_MARK positioned_lexeme
                       | lexeme_list RCHEVRON positioned_lexeme
                       | EXCLAMATION_MARK positioned_lexeme
                       | positioned_lexeme"""
        if len(p) == 5:
            lex_list, _ = p[1]
            role, _ = p[4]
            p[0] = (lex_list + [p[4]], role)
        elif len(p) == 4:
            lex_list, address = p[1]
            p[0] = (lex_list + [p[3]], address)
        elif len(p) == 3:
            role, _ = p[2]
            p[0] = ([p[2]], role)
        else:
            p[0] = ([p[1]], None)

    def p_word(self, p):
        """word : LBRACKET morpheme lexeme_list RBRACKET"""
        lex_list, role = p[3]
        p[0] = Word(syntagmatic_fun=SyntagmaticFunction.from_list(lex_list, type=p[2]),
                    role=PolyMorpheme(constant=role))
        # check_word(p[0])
        assert p[2] == p[0].grammatical_class

    def p_error(self, p):
        if p:
            msg = "Syntax error at '%s' (%d, %d)" % (p.value, p.lineno, p.lexpos)
        else:
            msg = "Syntax error at EOF"

        raise CannotParse(None, msg)
