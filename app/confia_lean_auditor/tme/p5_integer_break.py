"""Deterministic positive-integer partitions and replacement certificate math.

Global optimality is not a Lean theorem here. A finite maximum exists; merging
ones and splitting entries >=5 strictly improve it, 4->2+2 preserves it, and
three twos -> two threes strictly improves it. Thus a normal maximizer contains
only threes and at most two twos. Residues determine the counts. Only a pair of
twos can be merged back to a four, giving all unordered optimal forms.
"""
from functools import lru_cache
from math import prod


@lru_cache(maxsize=32)
def partitions(total, smallest=1):
    if type(total) is not int or not 0 <= total <= 32:
        raise ValueError('Only bounded small partition enumeration')
    if type(smallest) is not int or smallest < 1:
        raise ValueError('Positive smallest partition entry required')
    if total == 0:
        return ((),)
    return tuple((first,)+rest for first in range(smallest,total+1)
                 for rest in partitions(total-first,first))


def sum11_maximum():
    return max(prod(p) for p in partitions(11))


def normal_counts(total):
    if type(total) is not int or not 2 <= total <= 1000000:
        raise ValueError('Positive-integer break total out of bounds')
    q,r=divmod(total,3)
    twos,threes={0:(0,q),1:(2,q-1),2:(1,q)}[r]
    return {str(k):v for k,v in ((2,twos),(3,threes)) if v}


def optimal_forms(total):
    counts=normal_counts(total)
    result=[counts]
    if counts.get('2')==2:
        result.append({**{k:v for k,v in counts.items() if k!='2'},'4':1})
    return tuple(result)


def list_sum(counts):
    return sum(int(k)*v for k,v in counts.items())


def list_size(counts):
    return sum(counts.values())
