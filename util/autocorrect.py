"""Autocorrection engine."""
import os
import sys
import re
from collections import Counter

class Corrector():
    """Autocorrection engine."""
    letters = 'abcdefghijklmnopqrstuvwxyz'
    special_chars = ['.', ',', '!', '?', ';', ':']
    def __init__(self, text=None, file_path=None):
        if text is None:
            if file_path is None:
                file_path = os.path.join(os.path.dirname(os.path.realpath(sys.modules['__main__'].core_file)), 'data', 'autocorrect.txt')
            self.dictionary = Counter(self.get_words(file_path))
        else:
            self.dictionary = Counter(re.findall(r'\w+', text.lower()))

    def __call__(self, word):
        return self.correct(word)
    def __getitem__(self, word):
        return self.correct(word)

    def get_words(self, path):
        """Get words from a file."""
        with open(path) as f:
            text = f.read()
        return re.findall(r'\w+', text.lower())

    def prob(self, word, num=None):
        "Probability of `word`."
        if num is None:
            num = sum(self.dictionary.values())
        return self.dictionary[word] / num

    def correct(self, word):
        "Most probable spelling correction for word."
        return max(self.candidates(word), key=self.prob)

    def candidates(self, word):
        "Generate possible spelling corrections for word."
        return self.known([word]) or self.known(self.edits1(word)) or self.known(self.edits2(word)) or [word]

    def known(self, iwords):
        "The subset of `words` that appear in the dictionary of words."
        return set(w for w in iwords if w in self.dictionary)

    def edits1(self, word):
        "All edits that are one edit away from `word`."
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in self.letters]
        inserts = [L + c + R for L, R in splits for c in self.letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(self, word):
        "All edits that are two edits away from `word`."
        return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))

    def correct_sentence(self, sentence):
        """We essentially take each word out, and pass through the correct function
        And later append it into an empty string.
        Special characters are not passed through the correct function."""
        words = self.get_words(sentence)
        sentence = ''
        for word in words:
            if word in self.special_chars:
                sentence = sentence[:-1]
                sentence = sentence + word + ' '
            else:
                sentence = sentence + self.correct(word) + ' '
        return sentence
