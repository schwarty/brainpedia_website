

def shelve(dicts, names):
    shelved = {}
    for d, n in zip(dicts, names):
        for k, v in d.items():
            print n, k, v
            shelved.setdefault(k, {}).setdefault(n, v)
    return shelved


def prettify_label(label):
    pretties = {
        'auditory_words': 'voice',
        'human_sound': 'voice',
        'visual_words': 'words',
        'non_human_sound': 'sound',
        }
    return pretties.get(label, label).replace('_', ' ')
