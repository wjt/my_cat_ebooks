#!/usr/bin/env python
from __future__ import unicode_literals, print_function, division

import argh
import json
import os
import sys
import textwrap

import pattern.en

from nltk.corpus import cmudict, wordnet
cmu_pronounciations = cmudict.dict()


stanza_weights = {
    # """my cat
    # cool cat
    # good cat
    # pussy cat!""",

    # """when I see him walking
    # makes no sense to me
    # my cat is everywhere
    # we watch him on TV""",

    # TODO: needs a musical instrument corpus
    # """my cat is amazing
    # #he# can play the guitar

    # TODO: ...and without it this isn't funny
    # """#he# may not be an #actor#
    # but #hes# a pussy #superstar#""",

    # """my cat is everywhere
    # sees what #he# can see
    """
    #he# may not be an #actor#
    #he# #acts# #atrociously#
    """: 2,

    # """my cat isn't crazy
    # #he#'s everything to me
    # my cat burns the bible and #he# thinks it's so funny""",

    # """#he# isn't very good
    # #he# isn't very smart
    # #he# may not be picasso
    # but #he# is a work of art""",

    """
    #he# can break my #arm# in #seven# places
    #he# can eat a whole #watermelon#
    """: 1,
}


def load_corpus(path):
    full_path = os.path.join(os.path.dirname(__file__), 'corpora', 'data', path)
    with open(full_path, 'r') as f:
        return json.load(fp=f)


def stress_patterns(word):
    return frozenset((
        tuple(chunk[-1] for chunk in chunks if chunk[-1].isdigit())
        for chunks in cmu_pronounciations.get(word, ())
    ))


def matching_stresses(word, wordlist):
    s = stress_patterns(word)
    return [
        c for c in wordlist if stress_patterns(c) & s
    ]


def adjly(word):
    wordlist = load_corpus("words/adjs.json")["adjs"]
    adjs = matching_stresses(word, wordlist)
    adjlys = [adj + "ly" for adj in adjs]
    return [
        a for a in adjlys if a in cmu_pronounciations
    ]


def common_prefix_length(xs, ys):
    n = 0
    for x, y in zip(xs, ys):
        if x != y: break
        n += 1

    return n


def occupation_action(occupation):
    lemma_names = {
        related_lemma.name()
        for synset in wordnet.synsets(occupation, pos='n')
        for lemma in synset.lemmas()
        for related_lemma in lemma.derivationally_related_forms()
        if related_lemma.synset().pos() == 'v'
    }
    if lemma_names:
        best = None
        best_prefix_length = 0

        for ln in lemma_names:
            n = common_prefix_length(ln, occupation)
            if ln != occupation and n > best_prefix_length:
                best = ln
                best_prefix_length = n

        if best:
            return pattern.en.conjugate(best, person=3)


def occupations():
    occs = load_corpus("humans/occupations.json")["occupations"]
    actions = map(occupation_action, occs)
    return [
        "[actor:{}][acts:{}]".format(occ, act)
        for (occ, act) in zip(occs, actions)
        if act
    ]


def main():
    '''Generates the tracery grammar for @my_cat_ebooks.'''

    fruits = load_corpus("foods/fruits.json")["fruits"]

    pronouns = [
        "[he:he][him:him][hes:he's]",
        "[he:she][him:her][hes:she's]",
        # TODO: reintroduce this, but it affects the conjugation of the occupation.
        #
        #   they may not be an cleaner
        #   they cleanses exultantly
        #
        # "[he:they][him:them][hes:they're]",
        "[he:it][him:it][hes:it's]",
    ]

    grammar = {
        "atrociously": adjly("atrocious"),
        "watermelon": fruits,
        "seven": "two three four five six seven eight nine ten eleven twelve".split(),
        "arm": load_corpus("humans/bodyParts.json")["bodyParts"],
        "superstar": [ln for s in wordnet.synsets('superstar') for ln in s.lemma_names()],
        "setPronouns": pronouns,
        "setOccupation": occupations(),
        "stanza": [
            textwrap.dedent(s).strip()
            for s, weight in stanza_weights.iteritems()
            for _ in xrange(weight)
        ],
        "origin": ["#[#setPronouns#][#setOccupation#]stanza#"],
    }

    with open('grammar.json', 'w') as f:
        json.dump(fp=f, indent=2, obj=grammar)


if __name__ == '__main__':
    argh.dispatch_command(main)
