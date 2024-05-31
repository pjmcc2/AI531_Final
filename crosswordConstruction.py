import pickle
import numpy as np
import random
import string
from numpy.random import default_rng

def get_words(file):
    with open(file, "rb") as f:
        word_list = pickle.load(f)
    return word_list


def filter_words(words, length):
    return [w for w in words if (len(w) <= length) and (len(w) > 1)]


def insert_word(array, word, position, direction):
    row, col = position
    word_length = len(word)

    if direction == "h":
        if col + word_length > len(array):
            raise ValueError("Word exceeds array bounds horizontally")
        array[row, col : col + word_length] = list(word)
    elif direction == "v":
        if row + word_length > len(array):
            raise ValueError("Word exceeds array bounds vertically")
        array[row : row + word_length, col] = list(word)
    else:
        raise ValueError("Direction must be 'horizontal' or 'vertical'")

    return array


def score_encode(array, dict): # TODO change this to "find largest word in list (row or col)" but also don't let letters be double counted
    # horizontal first
    valid = True
    word_score = 0
    letter_score = 0
    letter_count = 0
    state = []
    pos = None
    word = ""
    style = ""
    seen = set()
    for i in range(array.shape[0]):
        curr_word = ""
        letter_count = 0
        style = "h"
        for j in range(array.shape[0]):
            if isinstance(array[i, j], str):
                if len(curr_word) == 0:
                    pos = (i, j)
                curr_word = curr_word + array[i, j]
                if (i, j) not in seen:
                    letter_count += 1
            if len(curr_word) > 1:
                if curr_word in dict:
                    if j + 1 < len(array):
                        if curr_word + array[(i,j+1)] in dict:
                            continue
                    word_score += 1
                    letter_score += letter_count
                    letter_count = 0
                    state.append((curr_word, pos, style))
                    for k in range(len(curr_word)):
                        seen.add((i, j - len(curr_word) + k))
                else:
                    valid = False
                curr_word = ""

    for i in range(array.shape[0]):
        curr_word = ""
        letter_count = 0
        style = "v"
        for j in range(array.shape[0]):
            if isinstance(array[j, i], str):
                if len(curr_word) == 0:
                    pos = (j, i)
                curr_word = curr_word + array[j, i]
                if (j, i) not in seen:
                    letter_count += 1

            if len(curr_word) > 1:
                if curr_word in dict:
                    if curr_word in dict:
                        if j + 1 < len(array):
                            if curr_word + array[(j+1,i)] in dict:
                                continue
                    word_score += 1
                    letter_score += letter_count
                    letter_count = 0
                    state.append((curr_word, pos, style))
                    for k in range(len(curr_word)):
                        seen.add((j - len(curr_word) + k, i))
                else:
                    valid = False
                curr_word = ""
    return word_score, letter_score, valid, state


# Crossover selects randomly  (without repetition) real words from array 1 and array 2: a sample is considered
# Viable if there the corresponding location on the other array does not contain any valid words
# If no viable words are found, a random inviable word is selected.
# The new arrays are generated by overwriting whatever is at the other array's word location
def crossover(array1, array2):
    arr1, g1 = array1
    arr2, g2 = array2
    s1 = random.sample(g1, len(g1))
    s2 = random.sample(g2, len(g2))
    cross1 = None
    cross2 = None
    for s in s1:
        if not check_conflict(g2, s):
            cross1 = s
            break
    if cross1 is None:
        cross1 = random.sample(g1, 1)
    for s in s2:
        if not check_conflict(g1, s):
            cross2 = s
            break
    if cross2 is None:
        cross2 = random.sample(g2, 1)
    g2.append(cross1)
    g1.append(cross2)


def word_positions(word, position, direction):
    row, col = position
    positions = set()

    if direction == "h":
        for i in range(len(word)):
            positions.add((row, col + i))
    elif direction == "v":
        for i in range(len(word)):
            positions.add((row + i, col))

    return positions


def check_conflict(existing_triples, new_triple):

    new_word, new_position, new_direction = new_triple
    new_positions = word_positions(new_word, new_position, new_direction)

    for word, position, direction in existing_triples:
        existing_positions = word_positions(word, position, direction)
        if new_positions & existing_positions:
            return True

    return False


# With probability M mutation occurs. mutation is performed in 3 ways, with probability p and (1-p) The primary way, with probability p assigns all
# blank cells a random letter. This encourages small (2-3) letter words to form which are common in crosswords and will increase the number of real words.
# With probablity (1-p)/2, an entirely new word will be sampled from the lexicon and randomly placed. And with prob: (1-p)/2 both previous ways happen sequentially
def mutate(array, gene,p, dict, seed=None,rng=None):
    if rng is None:
        rng = default_rng(seed)
    sample = rng.uniform()
    if sample < p:
        array = saturate(array)
        return array,gene
    sample = rng.uniform()
    word = random.sample(dict,1)
    dir = random.sample(["h","v"],1)
    pos1 = rng.integers(0,len(array)-len(word))
    pos2 = rng.integers(0,len(array))
    if dir == "v":
        pos = (pos1,pos2)
    else:
        pos = (pos2,pos1)
    if sample < 0.5:
        gene.append((word,pos,dir))
        return array,gene
    else:
        array = saturate(array)
        gene.append((word,pos,dir))
        return array,gene




def saturate(array):
    letters = list(string.ascii_lowercase)
    for i in range(len(array)):
        for j in range(len(array)):
            if not isinstance(array[(i,j)],str):
                array[(i,j)] = random.sample(letters,1)[0]
    return array

t = np.zeros((5, 5), dtype=object)
t[0, 0] = "a"
t[1, 0] = "b"
t[2, 0] = "i"

t = insert_word(t, "test", (0, 1), "v")
t = saturate(t)
print(t)
test_dict = {"test": 1, "at": 1, "be": 1, "is": 1,
             "kiss": 1,
             "could":1,
             "sound":1

}
ws, ls, valid, state = score_encode(t, test_dict)
print(f"Valid puzzle: {valid} Word score: {ws}, letter score: {ls}")
print(state)

h = np.zeros((5, 5), dtype=object)
h = insert_word(h,"kiss",(0,1),"h")
h = insert_word(h,"could",(4,0),"h")
h = insert_word(h,"sound",(0,4),"v")
h = saturate(h)
print(h)
ws, ls, valid, state = score_encode(h, test_dict)
print(f"Valid puzzle: {valid} Word score: {ws}, letter score: {ls}")
print(state)
