import pickle
import numpy as np


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


def score_encode(array, dict):
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

            elif len(curr_word) > 1:
                if curr_word in dict:
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

            elif len(curr_word) > 1:
                if curr_word in dict:
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


t = np.zeros((5, 5), dtype=object)
t[0, 0] = "a"
t[1, 0] = "b"
t[2, 0] = "i"

t = insert_word(t, "test", (0, 1), "v")
print(t)
ws, ls, valid, state = score_encode(t, {"abi": 1, "test": 1, "at": 1, "be": 1, "is": 1})
print(f"Valid puzzle: {valid} Word score: {ws}, letter score: {ls}")
print(state)
