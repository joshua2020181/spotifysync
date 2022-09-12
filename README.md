# spotifysync
Website to sync Spotify playback between multiple Spotify premium users (API limitation). Collaborative queue between listeners in same "room". Future discord bot integration

# completed features:
- syncing with initiator (person who clicked the button)
- progress bar (with song updating after every song finishes)
- queue builder page (search)
- collaborative queue (tested with 2 users)

# features to add (required-ish):
- pick device to start playback
- sync after every song mode
- online list (user pings server every x seconds)
- re ping server every x seconds to get current song state
- fix linking page ui
- friends/inviting (email?)
- 
- queueing:
- [ ] my playlists
- [ ] my favorite songs
- [ ] recently played
- [ ] "successfully added song" banner

# nice to have:
- waiting room
- inviting friends
- chat/video call
- marquees to see long song titles
- don't have to login, just use spotify oauth
- "protected" mode (only host/admin can clear, add)

# long in the future:
- discord bot integration
- speed up search by 

# bugs
- skipping/finishing song doesn't always update website
- syncing still has a +- 1 second delay sometimes
- shuffling doesn't work for 50+ songs i think
- repeats last song if queue is empty


