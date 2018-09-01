import praw
import re
import itertools
import sys

# READ THIS TO RUN
# This was written with python3
# to run, do python3 nanodelinkbot.py <args>
# args must either comments or submissions
# the arg will be what it monitors for
# can also use printcomments to print out the comments

# General Bot information and rules
MY_BOT_USERNAME = "NanodeLinkBot"
MY_BOT_CONFIG_NAME = "nanodelinkbot"  # the bot name in praw.ini
SUBREDDITS = "nanocurrency+nanotrade+NanodeLinkBot"
# SUBREDDITS = "NanodeLinkBot"  # test only subreddit
ALLOW_POSTS = False

GITHUB_URL = "https://github.com/n9Mtq4/NanodeLinkBot"
CONTACT_ME_URL = "https://np.reddit.com/message/compose/?to=n9Mtq4&subject=NanodeLinkBot"

# Regex
# url regex is for checking if in url, so normal can have ^ and $ if needed
# the url regexes might need \b too?
NANO_ADDRESS_REGEX = r"\b(?:xrb|nano)_[13456789abcdefghijkmnopqrstuwxyz]{60}\b"
NANO_ADDRESS_URL_REGEX = r"(?:xrb|nano)_[13456789abcdefghijkmnopqrstuwxyz]{60}"
NANO_BLOCK_REGEX = r"\b[\dABCDEF]{64}\b"
NANO_BLOCK_URL_REGEX = r"[\dABCDEF]{64}"

# Explorer information
DEFAULT_EXPLORER = "nanode"
ALL_EXPLORERS = False  # if true will add all other explorers to the reply
EXPLORER_URLS = {
    "nanode": {
        "address": "https://nanode.co/account/%s",
        "block": "https://www.nanode.co/block/%s"
    },
    "meltingice": {
        "address": "https://nano.meltingice.net/explorer/account/%s",
        "block": "https://nano.meltingice.net/explorer/block/%s"
    },
    "nanowatch": {
        "address": "https://nanowat.ch/account/%s",
        "block": "https://nanowat.ch/block/%s"
    }
}

# Regex for finding urls
# http://www.regexguru.com/2008/11/detecting-urls-in-a-block-of-text/
URL_REGEX = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

# handle if we have already replied
REPLIED_POSTS_FILE_NAME = "replied_posts.txt"
replied_list = []


def process_reddit(reddit):
    """
    Using the reddit instance, stream the subreddits
    comments or submissions (based on sys.argsv) and
    processes them.
    :param reddit: the praw reddit instance
    :return: None
    """
    subreddits_to_monitor = reddit.subreddit(SUBREDDITS)
    if "comments" in sys.argv:
        print("Monitoring comments in subreddits: " + SUBREDDITS)
        for comment in subreddits_to_monitor.stream.comments():
            if "printcomment" in sys.argv:
                print(comment.body)
            process_comment(comment)
    elif "submissions" in sys.argv:
        print("Monitoring submissions in subreddits: " + SUBREDDITS)
        for submission in subreddits_to_monitor.stream.submissions():
            process_submission(submission)
    else:
        print("run with comments or submissions arg to specify what to search")


def process_submission(submission):
    """
    Processes a submission.
    Searches the title and selftext.
    See process_post
    :param submission: the reddit submission
    :return: None
    """
    title_text = submission.title
    selftext = submission.selftext
    text = title_text + " " + selftext
    process_post(submission, text)


def process_comment(comment):
    """
    Processes a comment.
    Searches the body.
    See process_post
    :param comment: the comment
    :return: None
    """
    process_post(comment, comment.body)


def process_post(post, text):
    """
    Searches the given text, and if
    it finds addresses or blocks,
    make a reply to the post.
    :param post: The post to reply to, if the text has addresses or blocks
    :param text: the text to search
    :return: None
    """
    if not should_reply(post):
        return
    addresses = find_addresses_in_text(text)
    blocks = find_blocks_in_text(text)
    if len(addresses) != 0 or len(blocks) != 0:
        # there is an address or a block and we should make a post
        print("Found address(es): " + str(addresses))
        print("Found block(s): " + str(blocks))
        post_reply(post, generate_reply_text(addresses, blocks))


def generate_reply_text(addresses, blocks):
    """
    Generates the reply post text, given
    the addresses and blocks that have been found
    :param addresses: The list of addresses
    :param blocks: The list of blocks
    :return: A string of the post body
    """
    text = ""
    if len(addresses) != 0:
        text += "Nano address(es) mentioned:\n\n"
        for address in addresses:
            text += create_body_entry("address", address).strip() + "\n\n"
    if len(blocks) != 0:
        text += "Nano block(s) mentioned:\n\n"
        for block in blocks:
            text += create_body_entry("block", block).strip() + "\n\n"
    text += "---------\n"
    text += "I am a bot | Made by n9Mtq4 | "
    text += "[Github](%s) | " % GITHUB_URL
    text += "[Send my human a message.](%s)" % CONTACT_ME_URL
    return text


def create_body_entry(etype, value):
    """
    Creates a reply post entry.
    :param etype: The type of the value. "address" or "block"
    :param value: The address or block
    :return: A string with the markdown url corresponding to the value
    """
    main_url = "[%s](%s)" % (value, (EXPLORER_URLS[DEFAULT_EXPLORER][etype] % value))
    second_urls = ""
    if ALL_EXPLORERS:
        for key, explorer in EXPLORER_URLS.items():
            if key == DEFAULT_EXPLORER:
                continue
            second_urls += "[(%s)](%s) " % (key, (explorer[etype] % value))
    return main_url + " " + second_urls


def post_reply(post, post_text):
    """
    Makes a reply post to the given post
    with the given post_text.
    Won't post if should_reply(post) is false.
    :param post: The parent post to reply to
    :param post_text: The reply post's body text
    :return: None
    """
    pid = post.id
    if not should_reply(post):
        print("Shouldn't happen. Check before calling this function")
        return
    print("Posting to: " + pid)
    if ALLOW_POSTS:
        replied_to(post.id)
        post.reply(post_text)
    else:
        print("Posting disallowed. Not posting")


def should_reply(post):
    """
    Checks if this bot should reply to the given
    post. Doesn't reply if it already has, or if
    the post is itself.
    :param post: the comment or submission
    :return: if the bot should reply to the post
    """
    my_own = post.author.name == MY_BOT_USERNAME
    return (not has_replied(post.id)) and (not my_own)


def has_replied(post_id):
    """
    Checks if the bot has already replied to the
    post with the given id
    :param post_id: the post id
    :return: if this bot has already replied to it
    """
    return post_id.strip() in replied_list


def replied_to(post_id):
    """
    Called to mark a post as relied.
    Writes the id to a file and
    adds it to the replied list
    :param post_id: the post id
    :return: None
    """
    with open(REPLIED_POSTS_FILE_NAME, "a") as f:
        f.write(post_id + "\n")
    replied_list.append(post_id.strip())


def load_replied_list():
    """
    Loads every id in the REPLIED_POSTS_FILE_NAME
    into a list
    :return: a list of id's already replied to
    """
    with open(REPLIED_POSTS_FILE_NAME, "r") as f:
        lines = f.readlines()
        return list(map(lambda it: it.strip(), lines))


def find_addresses_in_text(text):
    """
    Searches the text for valid addresses.
    See find_regex_in_text for what is valid
    :param text: the text to search
    :return: a list of addresses
    """
    return find_regex_in_text(NANO_ADDRESS_REGEX, NANO_ADDRESS_URL_REGEX, text)


def find_blocks_in_text(text):
    """
    Searches the text for valid nano blocks.
    See find_regex_in_text for what is valid
    :param text: the text to search
    :return: a list of blocks
    """
    return find_regex_in_text(NANO_BLOCK_REGEX, NANO_BLOCK_URL_REGEX, text)


def find_regex_in_text(regex, url_find_regex, text):
    """
    Searches the given text, with the regex.
    Also searches for urls, and ignores the matches
    that also appear in a url - to avoid replying to
    posts that already include an explorer.
    :param regex: the regex to search with
    :param url_find_regex: the regex to search inside a url
    :param text: the text to search
    :return: All unique matches, not in a url
    """
    # this is really messy :(
    all_matching = re.findall(regex, text)
    unique_matching = list(set(all_matching))
    all_urls = re.findall(URL_REGEX, text)
    all_url_matching_unflat = list(map(lambda it: re.findall(url_find_regex, it), all_urls))
    all_url_matching = itertools.chain(*all_url_matching_unflat)
    unique_url_matching = list(set(all_url_matching))
    matching_not_in_url = list(set(unique_matching) - set(unique_url_matching))
    return matching_not_in_url


if __name__ == "__main__":
    print("Running NanodeLinkBot...")
    replied_list.extend(load_replied_list())
    reddit = praw.Reddit(MY_BOT_CONFIG_NAME)
    process_reddit(reddit)
    print("Done")

