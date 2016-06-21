import os
import random
import time
import twitter

from slackclient import SlackClient

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


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if "latest version" in command:
        if "horizon-bsn" in command:
            if "kilo" in command:
                response = ("latest build for `horizon-bsn` *openstack kilo* is here: "
                            "https://" + JENKINS_DOMAIN + "/job/openstack_horizon_bsn/50/")
            elif "liberty" in command:
                response = ("latest build for `horizon-bsn` *openstack liberty* is here: "
                            "https://" + JENKINS_DOMAIN + "/job/openstack_horizon_bsn/49/")
            else:
                response = ("latest build for `horizon-bsn` is here: "
                            "https://" + JENKINS_DOMAIN + "/job/openstack_horizon_bsn/lastSuccessfulBuild/")
        elif "bsnstacklib" in command:
            if "kilo" in command:
                response = ("latest build for `bsnstacklib` *openstack kilo* is here: "
                            "https://" + JENKINS_DOMAIN + "/job/openstack_bsnstacklib/62/")
            elif "liberty" in command:
                response = ("latest build for `bsnstacklib` *openstack liberty* is here: "
                            "https://" + JENKINS_DOMAIN + "/job/openstack_bsnstacklib/60/")
            else:
                response = ("latest build for `bsnstacklib` is here: "
                            "https://" + JENKINS_DOMAIN + "/job/openstack_bsnstacklib/lastSuccessfulBuild/")
        else:
            response = ("hmm..not sure what you mean. could you rephrase "
                        "with *latest version* and the package name?")
    elif any(keyword in command for keyword in ("entertain", "quote")):
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

