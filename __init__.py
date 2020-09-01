# Average Ease
# Anki 2 addon
# Author EJS
# https://eshapard.github.io/
#
# Sets the initial ease factor of a deck options group to the average
# ease factor of the mature cards within that deck options group.
from anki.hooks import addHook
from aqt import mw
#import time

# Find decks in settings group
def find_decks_in_settings_group(group_id):
    return mw.col.decks.didsForConf(get_deck_config(group_id))

# Find deck configuration for settings group
def get_deck_config(group_id):
    try:
        return mw.col.decks.get_config(group_id)
    except AttributeError:
        return mw.col.decks.dconf[str(group_id)]

# Find average ease and number of mature cards in deck
#   mature defined as having an interval > 90 day
def find_average_ease_in_deck(deck_id):
    mature_cards = mw.col.db.scalar("""select
        count()
        from cards where
        type = 2 and
        ivl > 90 and
        did = ?""", deck_id)
    if not mature_cards:
        mature_cards = 0
    mature_ease = mw.col.db.scalar("""select
        avg(factor)
        from cards where
        type = 2 and
        ivl > 90 and
        did = ?""", deck_id)
    if not mature_ease:
        mature_ease = 0
    return mature_cards, mature_ease


# Average mature card ease factor in settings group
def mature_ease_in_settings_group(dogID):
    tot_mature_cards = 0
    weighted_ease = 0
    avg_mature_ease = 0
    cur_ease = 0
    group_id = dogID
    if group_id:
        # Find decks and cycle through
        decks = mw.col.decks.didsForConf(get_deck_config(group_id))
        for d in decks:
            mature_cards, mature_ease = find_average_ease_in_deck(d)
            tot_mature_cards += mature_cards
            weighted_ease += mature_cards * mature_ease
        if tot_mature_cards > 0 and weighted_ease:
            avg_mature_ease = int(weighted_ease / tot_mature_cards)
        else:
            # not enough data; don't change the init ease factor
            avg_mature_ease = get_deck_config(group_id)["new"]["initialFactor"]
        cur_ease = get_deck_config(group_id)["new"]["initialFactor"]
    return avg_mature_ease, cur_ease


# update initial ease factor of a settings group
def update_initial_ease_factor(dogID, ease_factor):
    group_id = dogID
    if group_id:
        dconf = get_deck_config(group_id)
        dconf["new"]["initialFactor"] = int(ease_factor)
        mw.col.decks.save(dconf)
        #mw.col.decks.flush()

# main function
def update_ease_factor(dogID):
    avg_ease, cur_ease = mature_ease_in_settings_group(dogID)
    #utils.showInfo("dogID: %s AvgEase: %s" % (dogID, avg_ease))
    update_initial_ease_factor(dogID, avg_ease)

# run this on profile load
def update_ease_factors():
    #find all deck option groups
    try:
        all_config = mw.col.decks.all_config
    except AttributeError:
        all_config = mw.col.decks.allConf
    #create progress bar
    #ogs = len(all_config(mw.col.decks))
    #mw.progress.start(max = ogs, label = "Init Ease Factor: %s" % ogs)
    #cycle through them one by one
    #i = 1
    for dconf in all_config():
        update_ease_factor(dconf['id'])
        #mw.progress.update("Init Ease Factor: %s" % dconf['name'], i)
        #i += 1
        #time.sleep(1)
    #mw.progress.finish()
    mw.reset()

# add hook to 'profileLoaded'
addHook("profileLoaded", update_ease_factors)
