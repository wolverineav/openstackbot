import os
import random
import time
import twitter

from slackclient import SlackClient
from difflib import SequenceMatcher as sm

# openstackbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
JENKINS_DOMAIN = os.environ.get("JENKINS_DOMAIN")
OAUTH_TOKEN = os.environ.get("OAUTH_TOKEN")
OAUTH_TOKEN_SECRET = os.environ.get("OAUTH_TOKEN_SECRET")
CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")

# constants
AT_BOT = "<@" + BOT_ID + ">:"
EXAMPLE_COMMAND = "latest version of x"
TWITTER_HANDLES = [
    "TheMarkTwain",
    "Kurt_Vonnegut"
]

def oauth_login():
    # Creating the authentification
    auth = twitter.oauth.OAuth( OAUTH_TOKEN,
                                OAUTH_TOKEN_SECRET,
                                CONSUMER_KEY,
                                CONSUMER_SECRET )
    # Twitter instance
    twitter_api = twitter.Twitter(auth=auth)
    return twitter_api

# instantiate Slack & Twitter clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# LogIn
twitter_api = oauth_login()


completeNonsense = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
                   "* command with numbers, delimited by spaces."

versionNonsense = ("hmm..not sure what you mean. could you rephrase"
               " with *latest version* and the package name?")

verFmt = "latest build for {} is here: https://%s/job/openstack_{}" % JENKINS_DOMAIN

MIN_GUESS_CONFIDENCE = 0.5

TWITTER_QUOTE = "TWITTER_QUOTE"

responses = {
  'latest version' : {
     'horizon-bsn' : {
       'kilo':     verFmt.format("'horizon-bsn' *openstack kilo*",    'horizon_bsn/50/'),
       'liberty':  verFmt.format("'horizon-bsn' *openstack liberty*", 'horizon_bsn/49/'),
       'default':  verFmt.format("'horizon-bsn'",                     'horizon_bsn/lastSuccessfulBuild/') 
     },
     'bsnstacklib' : {
        'kilo':     verFmt.format("'bsnstacklib' *openstack kilo*",   'bsnstacklib/62/'),
        'liberty':  verFmt.format("'bsnstacklib' *openstack liberty*",'bsnstacklib/60/'),
        'default':  verFmt.format("'bsnstacklib'",                    'bsnstacklib/lastSuccessfulBuild/') 
     },
     'default' : versionNonsense
  },
  "entertain" : TWITTER_QUOTE,
  "quote"     : TWITTER_QUOTE,
  'default'   : completeNonsense
}

def mostAlikeRatio(key, command):
    cmd = command if len(key) <= len(command) else command.ljust(len(key))
    bestRatio = 0.0
    for i in xrange(len(cmd)-(len(key)-1)):
        ratio = sm(None, cmd[i:i+len(key)], key).ratio()
        bestRatio = max(bestRatio, ratio)
        if bestRatio == 1:
            return 1
    return bestRatio

def findMatchRecursive(tree, command):
    if isinstance(tree, basestring):
        return tree
    confidence={mostAlikeRatio(key,command): key for key in tree if key != 'default'}
    highestConfidence = max(confidence)
    if highestConfidence >= MIN_GUESS_CONFIDENCE:
        return findMatchRecursive(tree[confidence[highestConfidence]], command)
    else:
        return tree['default'] if 'default' in tree else None

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = findMatchRecursive(responses, command)
 
    if response == TWITTER_QUOTE:
        twitter_handle = random.choice(TWITTER_HANDLES)
        statuses = twitter_api.statuses.user_timeline(screen_name=twitter_handle)
        status = random.choice(statuses)
        author = "Mark Twain" if "Mark" in twitter_handle else "Kurt Vonnegut"
        response = status['text'] + " -_" + author + "_"
    else:
        response = ("hmm..not sure what you mean. could you rephrase "
                    "with *latest version* and the package name?")

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("OpenstackBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

