import numpy as np


def build_sequences(X, y, sequence_length=10):
    sequences = []
    labels = []

    for i in range(len(X) - sequence_length):
        seq = X[i:i + sequence_length]
        label = y[i + sequence_length - 1]
        sequences.append(seq)
        labels.append(label)

    return np.array(sequences), np.array(labels)
