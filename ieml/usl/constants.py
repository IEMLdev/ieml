from collections import defaultdict
import re
from itertools import chain, count
from typing import List, Set

from ieml.constants import AUXILIARY_CLASS
from ieml.dictionary.script import script, Script

SYNTAGMATIC_FUNCTION_PROCESS_TYPE_SCRIPT = script('E:.b.E:S:.-')
SYNTAGMATIC_FUNCTION_ACTANT_TYPE_SCRIPT = script('E:.b.E:B:.-')
SYNTAGMATIC_FUNCTION_QUALITY_TYPE_SCRIPT = script('E:.b.E:T:.-')

# Process : grammatical role (valence)
ONE_ACTANT_PROCESS = script('E:S:.')
TWO_ACTANTS_PROCESS = script('E:T:.')
THREE_ACTANTS_PROCESS = script('E:B:.')
ADDRESS_PROCESS_VALENCE_SCRIPTS = [ONE_ACTANT_PROCESS, TWO_ACTANTS_PROCESS, THREE_ACTANTS_PROCESS]  # process



# Process : mandatory address
ADDRESS_PROCESS_VOICES_SCRIPTS = {
    ONE_ACTANT_PROCESS: {script("E:.-wa.-t.o.-'"), # Actif
                         script("E:.-wo.-t.o.-'"),}, # Passif
    TWO_ACTANTS_PROCESS: script("E:.-O:O:.-t.o.-'").singular_sequences_set,
    THREE_ACTANTS_PROCESS: script("E:.-O:O:.-t.o.-'").singular_sequences_set
}
assert all(e in ADDRESS_PROCESS_VOICES_SCRIPTS[THREE_ACTANTS_PROCESS]
           for e in ADDRESS_PROCESS_VOICES_SCRIPTS[ONE_ACTANT_PROCESS])
ADDRESS_PROCESS_VERBAL_MODE_SCRIPTS = script("E:.-'O:O:.-M:.-'t.o.-',").singular_sequences_set

# Process : optional address
ADDRESS_PROCESS_ASPECT_SCRIPTS = script("E:F:.-t.o.-'").singular_sequences_set
ADDRESS_PROCESS_TENSE_SCRIPTS = script("E:M:.-O:.-t.o.-'").singular_sequences_set

TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS = script("E:O:O:.").singular_sequences_set
TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS = script("E:M:O:.").singular_sequences_set
TRANSFORMATION_PROCESS_TETRADE_MODE_SCRIPTS = script("E:.b.O:O:.-").singular_sequences_set
TRANSFORMATION_PROCESS_HEXADE_MODE_SCRIPTS = script("E:.b.O:M:.-").singular_sequences_set


ADDRESS_PROCESS_POLYMORPHEME_SCRIPTS = {
    *ADDRESS_PROCESS_VOICES_SCRIPTS[THREE_ACTANTS_PROCESS],  # voix / voice
    *ADDRESS_PROCESS_ASPECT_SCRIPTS,  # aspect
    *ADDRESS_PROCESS_TENSE_SCRIPTS,  # temps / tense
    *ADDRESS_PROCESS_VERBAL_MODE_SCRIPTS,  # mode
    *TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS,
    *TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS,
    *TRANSFORMATION_PROCESS_TETRADE_MODE_SCRIPTS,
    *TRANSFORMATION_PROCESS_HEXADE_MODE_SCRIPTS

}

FLEXION_SCRIPTS = list(map(script, [
    "E:M:.-d.u.-'", #definite/indefinite/demonstrative
    "E:.-n.E:U:.+F:.-'", # genders

    "E:O:O:.", # logic: affirmation, negation, interrogation, quotation
    "E:M:O:.", # logic: inference types
    "E:.+E:U:S:+T:.-M:M:.o.-'", # modes de l'enneage
    "E:.b.O:M:.-", # modes from the hexad
    "E:.b.O:O:.-", # modes from the tetrad
    "E:S:.j.-'M:O:.-O:.-',", # number: clusters, one by one (each), in pairs, etc.
    "E:.-',b.-S:.U:.-'y.-'O:.-',_", # number: continuous / discontinuous
    "E:.O:O:.-", # number: one, two, three, many
    "E:I:.-t.u.-'", # nubmer: qualitative quantification

    "E:F:.-t.o.-'", # process: duration aspects
    "E:.-'O:O:.-M:.-'t.o.-',", # process: grammatical moods
    "E:.-O:O:.-t.o.-'", # process: voice (passive / active / reflexive / reciprocal)
    "E:.-F:.M:M:.-l.-'", # relations in space: places, movements
    "E:.O:O:.O:.-t.o.-'", # relations in time: markers, durations
    "E:M:.-O:.-t.o.-'", # relations in time: past / present / future, relative/absolute
    "E:M:.d.+M:O:.-", # relations: determinations, causes
    "E:F:M:.", # relations: gradients (quality, quantity, distribution, frequency)
    "E:.O:.M:O:.-", # relations: qualities, manners
]))



SYNTAGMATIC_FUNCTION_SCRIPT = script('E:.b.-')

# Actant : grammatical roles
INITIATOR_SCRIPT = script('E:.n.-')
INTERACTANT_SCRIPT = script('E:.d.-')
RECIPIENT_SCRIPT = script('E:.k.-')
ADDRESS_ACTANTS_MOTOR_SCRIPTS = [INITIATOR_SCRIPT, INTERACTANT_SCRIPT, RECIPIENT_SCRIPT]

TIME_SCRIPT = script('E:.t.-')
LOCATION_SCRIPT = script('E:.l.-')
MANNER_SCRIPT = script('E:.f.-')
CAUSE_SCRIPT = script('E:.s.-')
INTENTION_SCRIPT = script('E:.m.-')
ADDRESS_CIRCONSTANTIAL_ACTANTS_SCRIPTS = [TIME_SCRIPT, LOCATION_SCRIPT, INTENTION_SCRIPT, MANNER_SCRIPT, CAUSE_SCRIPT]
ACTANTS_SCRIPTS = [*ADDRESS_ACTANTS_MOTOR_SCRIPTS,
                   *ADDRESS_CIRCONSTANTIAL_ACTANTS_SCRIPTS]

ADDRESS_ROLE_IN_PROCESS = [*ADDRESS_PROCESS_VALENCE_SCRIPTS, *ACTANTS_SCRIPTS]

JUNCTION_INDEX = list(map(script, [
    "j.-U:.-'d.o.-l.o.-',",
    "j.-A:.-'d.o.-l.o.-',",
    "g.-U:.-'d.o.-l.o.-',",
    "g.-A:.-'d.o.-l.o.-',",
    "h.-U:.-'d.o.-l.o.-',",
    "h.-A:.-'d.o.-l.o.-',",
    "c.-U:.-'d.o.-l.o.-',",
    "c.-A:.-'d.o.-l.o.-',",
    "p.-U:.-'d.o.-l.o.-',",
    "p.-A:.-'d.o.-l.o.-',",
    "x.-U:.-'d.o.-l.o.-',",
    "x.-A:.-'d.o.-l.o.-',"
]))


# logical connections
JUNCTION_AND = script("E:S:.-k.u.-'")
JUNCTION_XOR = script("E:T:.-k.u.-'")
JUNCTION_OR = script("E:B:.-k.u.-'")
JUNCTION_LOGICAL = [JUNCTION_AND, JUNCTION_XOR, JUNCTION_OR]

# JUNCTION_COMPARISON_ANCHOR = script("E:.U:.g.-k.u.-'")
# JUNCTION_COMPARISON_LINK = script("E:.A:.j.-k.u.-'") # like

# JUNCTION_COMPARISON_RELATIVE_WORSE_THAN = script("E:U:S:.-U:.-k.u.-'")
# JUNCTION_COMPARISON_RELATIVE_AS_GOOD_AS = script("E:U:B:.-U:.-k.u.-'")
# JUNCTION_COMPARISON_RELATIVE_BETTER_THAN = script("E:U:T:.-U:.-k.u.-'")
# JUNCTION_COMPARISON_RELATIVE_LESS_THAN = script("E:A:S:.-U:.-k.u.-'")
# JUNCTION_COMPARISON_RELATIVE_AS_MUCH_AS = script("E:A:B:.-U:.-k.u.-'")
# JUNCTION_COMPARISON_RELATIVE_MORE_THAN = script("E:A:T:.-U:.-k.u.-'")
# JUNCTION_COMPARISON_RELATIVE_LINK = script("E:O:M:.-U:.-k.u.-'").singular_sequences_set

# formal
JUNCTION_COMPARISON_FORMAL_SAME = script("E:.-s.a.-k.u.-'")
JUNCTION_COMPARISON_FORMAL_SIMILAR = script("E:.-b.a.-k.u.-'")
JUNCTION_COMPARISON_FORMAL_DISTINCT = script("E:.-t.a.-k.u.-'")
JUNCTION_COMPARISON_FORMAL = [JUNCTION_COMPARISON_FORMAL_SAME,
                              JUNCTION_COMPARISON_FORMAL_SIMILAR,
                              JUNCTION_COMPARISON_FORMAL_DISTINCT]

# Qualitative
JUNCTION_COMPARISON_QUALITATIVE_WORSE = script("E:.-k.a.-k.u.-'")
JUNCTION_COMPARISON_QUALITATIVE_AS_GOOD = script("E:.-m.a.-k.u.-'")
JUNCTION_COMPARISON_QUALITATIVE_BETTER = script("E:.-n.a.-k.u.-'")
JUNCTION_COMPARISON_QUALITATIVE = [JUNCTION_COMPARISON_QUALITATIVE_WORSE,
                                   JUNCTION_COMPARISON_QUALITATIVE_AS_GOOD,
                                   JUNCTION_COMPARISON_QUALITATIVE_BETTER]

# Quantitative
JUNCTION_COMPARISON_QUANTITATIVE_LESS = script("E:.-d.a.-k.u.-'")
JUNCTION_COMPARISON_QUANTITATIVE_AS_MUCH = script("E:.-f.a.-k.u.-'")
JUNCTION_COMPARISON_QUANTITATIVE_MORE = script("E:.-l.a.-k.u.-'")
JUNCTION_COMPARISON_QUANTITATIVE = [JUNCTION_COMPARISON_QUANTITATIVE_LESS,
                                    JUNCTION_COMPARISON_QUANTITATIVE_AS_MUCH,
                                    JUNCTION_COMPARISON_QUANTITATIVE_MORE]
JUNCTION_COMPARISON = [*JUNCTION_COMPARISON_FORMAL,
                       *JUNCTION_COMPARISON_QUALITATIVE,
                       *JUNCTION_COMPARISON_QUANTITATIVE]


# Rankings
# Qualitative
JUNCTION_RANKINGS_QUALITATIVE_WORST = script("E:.-y.-k.u.-'")
JUNCTION_RANKINGS_QUALITATIVE_AVERAGE = script("E:.-o.-k.u.-'")
JUNCTION_RANKINGS_QUALITATIVE_BEST = script("E:.-e.-k.u.-'")
JUNCTION_RANKINGS_QUALITATIVE = [JUNCTION_RANKINGS_QUALITATIVE_WORST,
                                 JUNCTION_RANKINGS_QUALITATIVE_AVERAGE,
                                 JUNCTION_RANKINGS_QUALITATIVE_BEST]
# Quantitative
JUNCTION_RANKINGS_QUANTITATIVE_MINIMUM = script("E:.-u.-k.u.-'")
JUNCTION_RANKINGS_QUANTITATIVE_AVERAGE = script("E:.-a.-k.u.-'")
JUNCTION_RANKINGS_QUANTITATIVE_MAXIMUM = script("E:.-i.-k.u.-'")
JUNCTION_RANKINGS_QUANTITATIVE = [JUNCTION_RANKINGS_QUANTITATIVE_MINIMUM,
                                  JUNCTION_RANKINGS_QUANTITATIVE_AVERAGE,
                                  JUNCTION_RANKINGS_QUANTITATIVE_MAXIMUM]
JUNCTION_RANKINGS = [*JUNCTION_RANKINGS_QUALITATIVE,
                     *JUNCTION_RANKINGS_QUANTITATIVE]

# Antinomies
# Explanations
JUNCTION_ANTINOMIES_EXPLANATIONS_EXPLAINS = script("E:.-s.u.-k.u.-'")
JUNCTION_ANTINOMIES_EXPLANATIONS_NOTHING_TO_DO = script("E:.-b.u.-k.u.-'")
JUNCTION_ANTINOMIES_EXPLANATIONS_CONTRADICT = script("E:.-t.u.-k.u.-'")
JUNCTION_ANTINOMIES_EXPLANATION = [JUNCTION_ANTINOMIES_EXPLANATIONS_EXPLAINS,
                                   JUNCTION_ANTINOMIES_EXPLANATIONS_NOTHING_TO_DO,
                                   JUNCTION_ANTINOMIES_EXPLANATIONS_CONTRADICT]
# Qualitative
JUNCTION_ANTINOMIES_QUALITATIVE_UNFORTUNATELY_OPPOSES = script("E:.-k.u.-k.u.-'")
JUNCTION_ANTINOMIES_QUALITATIVE_BALANCES = script("E:.-m.u.-k.u.-'")
JUNCTION_ANTINOMIES_QUALITATIVE_FORTUNATELY_OPPOSES = script("E:.-n.u.-k.u.-'")
JUNCTION_ANTINOMIES_QUALITATIVE = [JUNCTION_ANTINOMIES_QUALITATIVE_UNFORTUNATELY_OPPOSES,
                                   JUNCTION_ANTINOMIES_QUALITATIVE_BALANCES,
                                   JUNCTION_ANTINOMIES_QUALITATIVE_FORTUNATELY_OPPOSES]

JUNCTION_ANTINOMIES_CAUSAL_OPPOSITE_EFFECT = script("E:.-d.u.-k.u.-'")
JUNCTION_ANTINOMIES_CAUSAL_REDUCE_EFFECT = script("E:.-f.u.-k.u.-'")
JUNCTION_ANTINOMIES_CAUSAL_INCREASE_EFFECT = script("E:.-l.u.-k.u.-'")
JUNCTION_ANTINOMIES_CAUSAL = [JUNCTION_ANTINOMIES_CAUSAL_OPPOSITE_EFFECT,
                              JUNCTION_ANTINOMIES_CAUSAL_REDUCE_EFFECT,
                              JUNCTION_ANTINOMIES_CAUSAL_INCREASE_EFFECT]
JUNCTION_ANTINOMIES = [*JUNCTION_ANTINOMIES_EXPLANATION,
                       *JUNCTION_ANTINOMIES_QUALITATIVE,
                       *JUNCTION_ANTINOMIES_CAUSAL]


JUNCTION_CAUSAL_IS_EFFECT = script("E:.-wo.-k.u.-'")
JUNCTION_CAUSAL_IS_CAUSE = script("E:.-wa.-k.u.-'")
JUNCTION_CAUSAL_IS_ANALOGY_CAUSE_TO_EFFECT = script("E:.-we.-k.u.-'")
JUNCTION_CAUSAL_IS_ANALOGY_EFFECT_TO_CAUSE = script("E:.-wu.-k.u.-'")
JUNCTION_CAUSAL = [JUNCTION_CAUSAL_IS_EFFECT,
                  JUNCTION_CAUSAL_IS_CAUSE,
                  JUNCTION_CAUSAL_IS_ANALOGY_CAUSE_TO_EFFECT,
                  JUNCTION_CAUSAL_IS_ANALOGY_EFFECT_TO_CAUSE]


JUNCTION_SCRIPTS = [*JUNCTION_LOGICAL,
             *JUNCTION_COMPARISON,
             *JUNCTION_RANKINGS,
             *JUNCTION_CAUSAL,
             *JUNCTION_ANTINOMIES,
             # *JUNCTION_EXPLICATION
                    ]


INDEPENDANT_QUALITY = script('E:U:.')
DEPENDANT_QUALITY = script('E:A:.')
SCRIPTS_ADDRESS_QUALITY = [DEPENDANT_QUALITY, INDEPENDANT_QUALITY]
ADDRESS_SCRIPTS = [*ADDRESS_PROCESS_VALENCE_SCRIPTS, *ACTANTS_SCRIPTS, *SCRIPTS_ADDRESS_QUALITY, *JUNCTION_SCRIPTS, *JUNCTION_INDEX]

ADDRESS_SCRIPTS_ORDER = dict(zip(ADDRESS_SCRIPTS, count()))

# Grammatical classes
TYPES_OF_WORDS = [script('E:.b.E:S:.-'), #mot de process
                  script('E:.b.E:B:.-'), #mot d'actant
                  script('E:.b.E:T:.-')] #mot de qualité

NAMES_TO_ADDRESS = {
    ONE_ACTANT_PROCESS: 'process',
    TWO_ACTANTS_PROCESS: 'process',
    THREE_ACTANTS_PROCESS: 'process',

    INITIATOR_SCRIPT: 'initiator',
    INTERACTANT_SCRIPT: 'interactant',
    RECIPIENT_SCRIPT: 'recipient',

    TIME_SCRIPT: 'time',
    LOCATION_SCRIPT: 'location',
    MANNER_SCRIPT: 'manner',
    INTENTION_SCRIPT: 'intention',
    CAUSE_SCRIPT: 'cause',

    INDEPENDANT_QUALITY: 'independant',
    DEPENDANT_QUALITY: 'dependant',

    JUNCTION_AND: 'and',
    JUNCTION_OR: 'or (inclusive)',
    JUNCTION_XOR: 'or (exclusive)',

    JUNCTION_COMPARISON_FORMAL_SAME: 'is the same as the precedent',
    JUNCTION_COMPARISON_FORMAL_SIMILAR: 'is similar to the precedent',
    JUNCTION_COMPARISON_FORMAL_DISTINCT: 'is distinct from the precedent',

    JUNCTION_COMPARISON_QUALITATIVE_WORSE: 'is worse than the precedent',
    JUNCTION_COMPARISON_QUALITATIVE_AS_GOOD: 'is as good as the precedent',
    JUNCTION_COMPARISON_QUALITATIVE_BETTER: 'is better than the precedent',

    JUNCTION_COMPARISON_QUANTITATIVE_LESS: 'is less than the precedent',
    JUNCTION_COMPARISON_QUANTITATIVE_AS_MUCH: 'is as much as the precedent',
    JUNCTION_COMPARISON_QUANTITATIVE_MORE: 'is more than the precedent',

    JUNCTION_RANKINGS_QUALITATIVE_WORST: "is the worst of the precedent",
    JUNCTION_RANKINGS_QUALITATIVE_AVERAGE: "is the qualitative average of the precedent",
    JUNCTION_RANKINGS_QUALITATIVE_BEST: "is the best of the precedent",

    JUNCTION_RANKINGS_QUANTITATIVE_MINIMUM: "is the minimum of the precedent",
    JUNCTION_RANKINGS_QUANTITATIVE_AVERAGE: "is the quantitative average of the precedent",
    JUNCTION_RANKINGS_QUANTITATIVE_MAXIMUM: "is the maximum of the precedent",

    JUNCTION_ANTINOMIES_EXPLANATIONS_EXPLAINS: "explains the precedent",
    JUNCTION_ANTINOMIES_EXPLANATIONS_NOTHING_TO_DO: "has nothing to do with the precedent",
    JUNCTION_ANTINOMIES_EXPLANATIONS_CONTRADICT: "contradicts the precedent",

    JUNCTION_ANTINOMIES_QUALITATIVE_UNFORTUNATELY_OPPOSES: "unfortunately opposes the precedent",
    JUNCTION_ANTINOMIES_QUALITATIVE_BALANCES: "balances the precedent (neutral)",
    JUNCTION_ANTINOMIES_QUALITATIVE_FORTUNATELY_OPPOSES: "is fortunately opposed to the precedent",

    JUNCTION_ANTINOMIES_CAUSAL_OPPOSITE_EFFECT: "has the opposite effect of the precedent",
    JUNCTION_ANTINOMIES_CAUSAL_REDUCE_EFFECT: "reduces the effect of the previous one",
    JUNCTION_ANTINOMIES_CAUSAL_INCREASE_EFFECT: "increases the effect of the previous one",

    JUNCTION_CAUSAL_IS_EFFECT: "is the effect of the precedent (therefore)",
    JUNCTION_CAUSAL_IS_CAUSE: "is the cause of the precedent (because)",
    JUNCTION_CAUSAL_IS_ANALOGY_CAUSE_TO_EFFECT: "is an analogy of the precedent cause to effect relationship (a fortiori, a contrario, etc.)",
    JUNCTION_CAUSAL_IS_ANALOGY_EFFECT_TO_CAUSE: "is an analogy of the precedent effect to cause relationship",

    **{j: "*{}".format(i+1) for i, j in enumerate(JUNCTION_INDEX)}

}
NAMES_TO_ADDRESS_WITH_VALENCE_IN_PROCESS = {
    **NAMES_TO_ADDRESS,
    ONE_ACTANT_PROCESS: 'process_1',
    TWO_ACTANTS_PROCESS: 'process_2',
    THREE_ACTANTS_PROCESS: 'process_3',

}





ROLE_NAMES_TO_SCRIPT= {**dict(map(reversed, NAMES_TO_ADDRESS_WITH_VALENCE_IN_PROCESS.items())),
                        'process': THREE_ACTANTS_PROCESS
                       }

ROLE_REGEX=r"({})".format('|'.join(map(re.escape, map(str, set(ROLE_NAMES_TO_SCRIPT.values())))))


NAMES_ORDERING = {
    'process': 0,

    'initiator': 0,
    'interactant': 0,
    'recipient': 0,

    'time': 0,
    'location': 0,
    'manner': 0,
    'intention': 0,
    'cause': 0,

    'independant': 2,
    'dependant': 1
}

# Actant : mandatory address
ADDRESS_ACTANTS_DEFINITION_SCRIPTS = script("E:M:.-d.u.-'").singular_sequences_set
ADDRESS_ACTANTS_GRAMMATICAL_NUMBER_SCRIPTS = script("E:.O:O:.-").singular_sequences_set

# Actant : optional address
ADDRESS_ACTANTS_CONTINUITY_SCRIPTS = script("E:.-',b.-S:.U:.-'y.-'O:.-',_").singular_sequences_set
ADDRESS_ACTANTS_GRAMMATICAL_GENDER_SCRIPTS = script("E:.-n.E:U:.+F:.-'").singular_sequences_set
ADDRESS_ACTANTS_QUANTIFICATION_SCRIPTS = script("E:I:.-t.u.-'").singular_sequences_set
ADDRESS_QUALITY_GRADIENT_EMM_SCRIPTS = script("E:M:M:.").singular_sequences_set
ADDRESS_QUALITY_GRADIENT_EFM_SCRIPTS = script("E:F:M:.").singular_sequences_set

GROUPEMENT_SCRIPTS = script("E:S:.j.-'M:O:.-O:.-',").singular_sequences_set

ADDRESS_CIRCONSTANTIAL_TIME_DISTRIBUTION_SCRIPTS = script("E:S:M:.").singular_sequences_set
ADDRESS_CIRCONSTANTIAL_FREQUENCY_DISTRIBUTION_SCRIPTS = script("E:B:M:.").singular_sequences_set

ADDRESS_CIRCONSTANTIAL_SPACE_DISTRIBUTION_SCRIPTS = script("E:T:M:.").singular_sequences_set
ADDRESS_CIRCONSTANTIAL_LOCATION_TOWARDS_AXES_SCRIPTS = script("E:.-O:.M:M:.-l.-'").singular_sequences_set
ADDRESS_CIRCONSTANTIAL_LOCATION_PATH_SCRIPTS = script("E:.-M:.M:M:.-l.-'").singular_sequences_set

ADDRESS_CIRCONSTANTIAL_LOCATION_SCRIPTS = script("E:.-F:.M:M:.-l.-'").singular_sequences_set

assert {*ADDRESS_CIRCONSTANTIAL_LOCATION_TOWARDS_AXES_SCRIPTS,
        *ADDRESS_CIRCONSTANTIAL_LOCATION_PATH_SCRIPTS} == ADDRESS_CIRCONSTANTIAL_LOCATION_SCRIPTS

ADDRESS_CIRCONSTANTIAL_INTENTION_SCRIPTS = {script("E:T:.p.-"), script("E:.A:.h.-")}

ADDRESS_CIRCONSTANTIAL_MANNER_SCRIPTS = script("E:.O:.M:O:.-").singular_sequences_set
ADDRESS_CIRCONSTANTIAL_GRADIENT_ADVERB_EOM_SCRIPTS = script("E:O:M:.").singular_sequences_set

ADDRESS_CIRCONSTANTIAL_CAUSE_SCRIPTS = script("E:M:.d.+M:O:.-").singular_sequences_set

ADDRESS_ENNEADE_ADVERBS_SCRIPTS=script("E:.+E:U:S:+T:.-M:M:.o.-'").singular_sequences_set

#TODO
ADDRESS_TIME_FRAME_SCRIPTS = script("E:.O:O:.O:.-t.o.-'").singular_sequences_set


ADDRESS_ACTANT_SCRIPTS = {
    *ADDRESS_ACTANTS_DEFINITION_SCRIPTS,  # definition
    *ADDRESS_ACTANTS_CONTINUITY_SCRIPTS,  # continuity
    *ADDRESS_ACTANTS_GRAMMATICAL_GENDER_SCRIPTS,  # genre / gender
    *ADDRESS_ACTANTS_GRAMMATICAL_NUMBER_SCRIPTS,  # nombre / number
    *ADDRESS_ACTANTS_QUANTIFICATION_SCRIPTS,  # quantité / quantity

    *TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS,
    *TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS,
    *ADDRESS_QUALITY_GRADIENT_EFM_SCRIPTS,
    *ADDRESS_CIRCONSTANTIAL_MANNER_SCRIPTS,
    *ADDRESS_CIRCONSTANTIAL_CAUSE_SCRIPTS,

    *ADDRESS_CIRCONSTANTIAL_LOCATION_SCRIPTS,
    *GROUPEMENT_SCRIPTS,
    *ADDRESS_ENNEADE_ADVERBS_SCRIPTS,
    *ADDRESS_TIME_FRAME_SCRIPTS
}



ADDRESS_QUALITY_SCRIPTS = {
    *TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS,  # construction
    *TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS,  # mode
    *ADDRESS_ACTANTS_DEFINITION_SCRIPTS,  # definition
    *ADDRESS_QUALITY_GRADIENT_EFM_SCRIPTS,  # nombre / number
    *ADDRESS_CIRCONSTANTIAL_MANNER_SCRIPTS,

    *ADDRESS_CIRCONSTANTIAL_CAUSE_SCRIPTS,
    *ADDRESS_CIRCONSTANTIAL_LOCATION_SCRIPTS,
    *ADDRESS_ENNEADE_ADVERBS_SCRIPTS,
    *ADDRESS_TIME_FRAME_SCRIPTS
}


def assert_(cond, message):
    if not cond:
        raise ValueError(message)


def assert_all_in(l: List[Script], _set: Set[Script], name_l):
    assert_(all(s in _set or s.empty for s in l),
            "Invalid scripts [{}] in {}. Received: [{}]".format(
                " ".join(map(str, sorted(set(l) - _set))),
                name_l,
                ' '.join(map(str, sorted(l)))))


def assert_only_one_from(l: List[Script], _set: Set[Script], name_l, name_set) -> Script:
    assert_(sum(1 if s in _set else 0 for s in l) == 1,
            "One and only one of the {} scripts [{}] required in {}. Received: [{}]".format(
                            name_set,
                            ' '.join(map(str, sorted(_set))),
                            name_l,
                            ' '.join(map(str, sorted(l)))))

    return next(iter(s for s in l if s in _set))


def assert_atmost_one_from(l: List[Script], _set: Set[Script], name_l, name_set):
    assert_(sum(1 if s in _set else 0 for s in l) <= 1,
            "Maximum one of the {} scripts [{}] required in {}. Received: [{}]".format(
                            name_set,
                            ' '.join(map(str, sorted(_set))),
                            name_l,
                            ' '.join(map(str, sorted(l)))))


def assert_no_one_from(l: List[Script], _set: Set[Script], name_l, name_set):
    assert_(sum(1 if s in _set else 0 for s in l) == 0,
            "The {} scripts [{}] are forbidden in {}. Received: [{}]".format(
                            name_set,
                            ' '.join(map(str, sorted(_set))),
                            name_l,
                            ' '.join(map(str, sorted(l)))))

def class_from_address(address):
    if any(s in ADDRESS_PROCESS_VALENCE_SCRIPTS for s in address.constant):
        return SYNTAGMATIC_FUNCTION_PROCESS_TYPE_SCRIPT
    elif any(s == INDEPENDANT_QUALITY for s in address.constant):
        return SYNTAGMATIC_FUNCTION_QUALITY_TYPE_SCRIPT
    elif any(s in ACTANTS_SCRIPTS + [DEPENDANT_QUALITY] for s in address.constant):
        return SYNTAGMATIC_FUNCTION_ACTANT_TYPE_SCRIPT
    else:
        raise ValueError("Invalid role, no grammatical class associated.")



def check_flexion_process_scripts(l: List[Script], sfun=None):
    # check all
    assert_all_in(l, ADDRESS_PROCESS_POLYMORPHEME_SCRIPTS, "a flexion of a process")

    #check voice
    assert_atmost_one_from(l, ADDRESS_PROCESS_VOICES_SCRIPTS[sfun.valence], "a flexion of a process", "voices")

    #check mode
    assert_atmost_one_from(l, ADDRESS_PROCESS_VERBAL_MODE_SCRIPTS, "a flexion of a process", "verbal modes")

    #check aspect
    assert_atmost_one_from(l, ADDRESS_PROCESS_ASPECT_SCRIPTS, "a flexion of a process", "aspects")

    #check tense
    assert_atmost_one_from(l, ADDRESS_PROCESS_TENSE_SCRIPTS, "a flexion of a process", "tenses")

    # check logical constructions
    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS, "a flexion of a process", "logical constructions")

    # check logical modes
    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS, "a flexion of a process", "logical modes")

    # check tetrade modes
    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_TETRADE_MODE_SCRIPTS, "a flexion of a process", "tetrade modes")

    # check hexade modes
    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_HEXADE_MODE_SCRIPTS, "a flexion of a process", "hexade modes")


def check_address_script(l: List[Script], sfun_type):
    assert_all_in(l, set(ADDRESS_SCRIPTS), "an address")

    if any(e in {*ADDRESS_PROCESS_VALENCE_SCRIPTS, *ACTANTS_SCRIPTS} for e in l):
        assert_only_one_from(l, {*ADDRESS_PROCESS_VALENCE_SCRIPTS, *ACTANTS_SCRIPTS}, "an address", "grammatical roles")

    assert_atmost_one_from(l, {INDEPENDANT_QUALITY}, "an address", "independant quality")

    from ieml.usl.syntagmatic_function import DependantQualitySyntagmaticFunction, IndependantQualitySyntagmaticFunction
    if sfun_type == DependantQualitySyntagmaticFunction:
        assert_no_one_from(l, {*ADDRESS_PROCESS_VALENCE_SCRIPTS, *ADDRESS_ACTANTS_MOTOR_SCRIPTS, *ADDRESS_CIRCONSTANTIAL_ACTANTS_SCRIPTS},
                           "an address of an ActantSyntagmaticFunction", "grammatical roles")
    elif sfun_type == IndependantQualitySyntagmaticFunction:
        assert_no_one_from(l, {*ADDRESS_PROCESS_VALENCE_SCRIPTS, *ADDRESS_ACTANTS_MOTOR_SCRIPTS, *ADDRESS_CIRCONSTANTIAL_ACTANTS_SCRIPTS, DEPENDANT_QUALITY},
                           "an address of an IndependantQualitySyntagmaticFunction", "grammatical roles")

def check_flexion_actant_scripts(l: List[Script], sfun=None):
    assert_all_in(l, ADDRESS_ACTANT_SCRIPTS, "a flexion of an actant")

    assert_atmost_one_from(l, ADDRESS_ACTANTS_DEFINITION_SCRIPTS, "a flexion of an actant", "definitions")

    assert_atmost_one_from(l, ADDRESS_ACTANTS_GRAMMATICAL_NUMBER_SCRIPTS, "a flexion of an actant", "grammatical numbers")

    assert_atmost_one_from(l, ADDRESS_ACTANTS_CONTINUITY_SCRIPTS, "a flexion of an actant", "continuities")

    assert_atmost_one_from(l, ADDRESS_ACTANTS_GRAMMATICAL_GENDER_SCRIPTS, "a flexion of an actant", "grammatical genders")

    assert_atmost_one_from(l, ADDRESS_ACTANTS_QUANTIFICATION_SCRIPTS, "a flexion of an actant", "quantifications")

    assert_atmost_one_from(l, ADDRESS_ENNEADE_ADVERBS_SCRIPTS, "a flexion of an actant", "enneade adverbs")

    assert_atmost_one_from(l, ADDRESS_QUALITY_GRADIENT_EFM_SCRIPTS, "a flexion of an actant", "gradients")

    assert_atmost_one_from(l, ADDRESS_CIRCONSTANTIAL_LOCATION_SCRIPTS, "a flexion of an actant",
                           "space location")
    assert_atmost_one_from(l, ADDRESS_TIME_FRAME_SCRIPTS, "a flexion of an actant", "time frames")

    assert_atmost_one_from(l, set(ADDRESS_CIRCONSTANTIAL_MANNER_SCRIPTS),
                                "a flexion of an actant",
                                "manner")
    assert_atmost_one_from(l, set(GROUPEMENT_SCRIPTS),
                                    "an address of an actant",
                                    "groupements")

    assert_atmost_one_from(l, set(ADDRESS_CIRCONSTANTIAL_CAUSE_SCRIPTS),
                                "an address of an actant",
                                "causes")

    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS, "a flexion of a quality",
                           "logical constructions")
    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS, "a flexion of a quality", "logical modes")

    return sfun


def check_flexion_quality(l: List[Script], sfun=None):
    assert_all_in(l, ADDRESS_QUALITY_SCRIPTS, "an address of a quality")

    # if role is None:
    #     assert_only_one_from(l, set(ACTANTS_SCRIPTS), "an address of an actant", "grammatical roles")
    #     assert_only_one_from(l, {INDEPENDANT_QUALITY}, "an address of an actant", "dependant")

    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_LOGICAL_CONSTRUCTION_SCRIPTS, "a flexion of a quality",
                           "logical constructions")
    assert_atmost_one_from(l, TRANSFORMATION_PROCESS_LOGICAL_MODE_SCRIPTS, "a flexion of a quality", "logical modes")
    assert_atmost_one_from(l, ADDRESS_ACTANTS_DEFINITION_SCRIPTS, "a flexion of a quality", "definitions")

    assert_atmost_one_from(l, ADDRESS_QUALITY_GRADIENT_EFM_SCRIPTS, "a flexion of a quality", "gradients")

    assert_atmost_one_from(l, ADDRESS_CIRCONSTANTIAL_MANNER_SCRIPTS, "a flexion of a quality", "manners")

    assert_atmost_one_from(l, ADDRESS_CIRCONSTANTIAL_CAUSE_SCRIPTS, "a flexion of a quality", "causals")

    assert_atmost_one_from(l, ADDRESS_CIRCONSTANTIAL_LOCATION_SCRIPTS, "a flexion of a quality", "locations")
    assert_atmost_one_from(l, ADDRESS_TIME_FRAME_SCRIPTS, "a flexion of a quality", "time frames")

    assert_atmost_one_from(l, ADDRESS_ENNEADE_ADVERBS_SCRIPTS, "a flexion of a quality", "enneade adverbs")


def check_lexeme_scripts(l_pf: List[Script], l_pc: List[Script], sfun=None):
    # if len(role) != 1:
    #     raise ValueError("Invalid role : {}".format(' '.join(map(str, role))))
    # _role = role[0]
    from ieml.usl.syntagmatic_function import ProcessSyntagmaticFunction, DependantQualitySyntagmaticFunction, \
        IndependantQualitySyntagmaticFunction

    if sfun.__class__ == ProcessSyntagmaticFunction:
        check_flexion_process_scripts(l_pf, sfun=sfun)
    elif sfun.__class__ == DependantQualitySyntagmaticFunction:
        check_flexion_actant_scripts(l_pf, sfun=sfun)
    elif sfun.__class__ == IndependantQualitySyntagmaticFunction:
        check_flexion_quality(l_pf, sfun=sfun)
    elif sfun is None:
        pass
    else:
        raise ValueError("Invalid sfun context: {}".format(str(sfun)))
