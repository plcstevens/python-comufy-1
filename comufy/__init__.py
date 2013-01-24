import logging
import urllib
import urllib2
import json
import os

from datetime import datetime

log = logging.getLogger(__name__)

"""
This is the heroku-specific comufy library which should grab everything it needs from the environment.
Optionally, you can instantiate your own comufy instance for development purposes.
"""

class Comufy(object):
    
    def __init__(self, access_token='', base_api_url='', username='', password=''):
        " instatiate a comufy instance - check the environment variables are set."
        self.access_token   = os.environ.get('COMUFY_TOKEN',    access_token)
        self.base_api_url   = os.environ.get('COMUFY_URL',      base_api_url)
        self.username       = os.environ.get('COMUFY_USERNAME', username)
        self.password       = os.environ.get('COMUFY_PASSWORD', password)

    def convert_from_comufy_timestamp(self, value):
        """
        This function deals with converting a comufy timestamp which is in unix
        timestamp (in millisecond) to a python DateTime object.  Basically the timestamp
        has three extra zeros on the end of it which means Python's built in datetime
        object complains about it.
        
        """
        if type(value) != type(int):
            value = int(value)
        value /= 1000
        return datetime.fromtimestamp( value )
    
    def send_api_call(self, data, add_access_token=True):
        """
        @return A boolean value that indicates if when communicating with Comufy's
        API, we got an 'OK' response from the request object.  NOTE: An 'OK' message
        does not mean that everything was successful, just that the web request was
        found.
        
        @return A JSON data structure which contains details of the actual response
        from Comufy's API call.  This contains information about if the API call was
        successful, or if not what error there was.  If the web request did not receive
        an 'OK' then this will be None
        """
        if add_access_token:
            if not self.get_access_token():
                return False, None
            data['token'] = self.access_token
        json_data = json.dumps(data)
        log.debug(json_data)
        comufy_request = urllib2.Request(self.base_api_url)
        response = urllib2.urlopen( comufy_request, urllib.urlencode(dict(request=json_data)))
        log.debug(response.msg)
        if response.msg == 'OK':
            message = response.read()
            return True, json.loads(message)
        else:
            return False, None
    
    def authenticate_app(self):
        """
        This function attempts to get a new access token for the specified comufy
        account.
        
        """
        #Step X: First build the request object which contains all the information that are required for the authenitcation of the user
        data = {
            u'cd':131,
            u'user':self.username,
            u'password':self.password
        }
        
        #Step X: Attempt to authenticate the user against Comufy's API
        success, message = self.send_api_call( data, add_access_token=False )
        
        #Step X: Check that the response from their server was OK
        if success:
            #Step X: Check the responded 'cd' value to make sure it matches 235
            if message.get(u'cd') == 235:
                self.access_token = message.get(u'tokenInfo').get(u'token')
                self.expiry_time = self.convert_from_comufy_timestamp( message.get(u'tokenInfo').get(u'expiryTime') )
                return True
            else:
                #This means that the provided creditials are incorrect.  As such we should nuke any access_tokens we currently have stored in the global space
                self.access_token = None
                self.expiry_time = None
                log.debug(
                    """
                    Could not authenticate against API.
                    
                    File:
                    support_comufy.py
                    
                    Function:
                    authenticate_app
                    
                    Reason:
                    System returned the following message: %s
                    """%(json.dumps(message))
                )
                return False
        else:
            log.error(
                """
                Could not authenticate against API.
                
                File:
                support_comufy.py
                
                Function:
                authenticate_app
                
                Reason:
                Did not recieve a successful web request message from server i.e. no 'OK' from request
                """
            )
        return False
    
    def has_token_expired(self):
        """
        This function simply determines if the access token we currently have stored
        has actually expired.  If it has expired, then this function will also null
        the access token and expiry time variables, so that future API calls will
        be forced to get a new token.
        
        @returns A boolean value to indicate if the currently stored access token
        has expired based on the expiry time value sent back with the access token.
        """
        
        if self.expiry_time is not None and self.expiry_time > datetime.now():
            return False
        
        #Else: Clear the current values
        self.expiry_time = None
        self.access_token = None
        return True
    
    def get_access_token(self):
        
        #Step 1: First determine if we actually need to authenticate the app, or if we have a currently valid access token
        if self.has_token_expired():
            #Step 2: If the token has expired (or null) then attempt to re-authenticate against Comufy's servers
            if not self.authenticate_app():
                #If we failed to authenticate against the server, then return false to the caller
                return False
        return True
    
    
    def get_application_tags(self, application_name):
        """
        This function simply returns a list of known tags for the application.  An
        exception will be thrown from this function under the following circumstances:
            - The application name could not be found in the list of registered applications
            returned by Comufy
            
            - If the command does not result in a 'cd' value of 219
            
            - If the query was unsuccessful for any other reason e.g. 404, 405,
            timeouts, etc.
        
        """
        #Step 1: First check that we currently have a valid access token.
        if not self.get_access_token():
            return False
        
        #Step 2: Build the data object with the specific command in that will be used to retreive all the tags
        data = {
            u'cd':101
        }
        
        #Step 3: Call Comufy's API with the specific command
        success, message = self.send_api_call( data )
        
        #Step 4: Check that the response from their server was OK
        if success:
            if message.get(u'cd') == 219:                                           #MAGIC NUMBER: 219 is the OK response from the Comufy API's for this particular command
                for app in message.get(u'applications'):
                    if app.get(u'name') == application_name:
                        return [ tag.get(u'name') for tag in app.get(u'tags') ]
                msg = 'Exception: File=%s, Function=%s, Message=Unable to find the application in the list of registered application on Comufy'%( 'support_comufy.py', 'get_application_tags' )
            else:
                msg = 'Exception: File=%s, Function=%s, Message=Comufy returned an error code, Code=%s'%( 'support_comufy.py', 'get_application_tags', message.get(u'cd') )
        else:
            msg = 'Exception: File=%s, Function=%s, Message=Comufy API query was unsuccessful'%( 'support_comufy.py', 'get_application_tags' )
    
        log.error( msg )
        raise Exception(msg)
    
    def add_application_user(self, application_name, user_details, add_new_tags=False):
        """
        This function allows the caller to add a single user to Comufy's user database.
        The function requires the caller to pass in a dictionary of the user's details
        including the user's facebook ID and a sub-dictionary of tags that should be
        associated with the user's details.  If the tags used are not found in the list
        of tags associated with the app, then these tags will be removed.  This behaviour
        can be overriden by providing a "True" value to the option argument "add_new_tags".
        If this value is "True", and a new tag that is not currently associated with
        the application is found, then the system will attempt to create the tag.
        If it is possible for us to determine the type of the data, then we will set
        it appropriately.  However, if this is not possible then the system will default
        to create any new tags to be of type 'string'.
        
        @param user_details A dictionary object that should contains the keys 'account'
        and 'tags' e.g.
            {
                'account':{
                    fbId:<Facebook Account Number>
                },
                'tags':{
                    <tag name>:<tag value>
                }
            }
        
        @param add_new_tags A boolean value that indicates what should happen if new
        tag values are found when adding an application user.  Defaults to false, in
        which case the tag value will be dropped from the dictionary.  Set to true,
        and any new tags will be created with a default type of 'string'.
        
        @return A boolean value to indicate if the system was able to send the user's
        details to Comufy's API correctly.
        
        """
        
        #Step 1: First check that we currently have a valid access token.
        if not self.get_access_token():
            return False
        
        #Step 2: Validate the tags being used with those associated with the app
        current_tags = self.get_application_tags(application_name)
        for key in user_details.get(u'tags').keys():
            if not key in current_tags:
                if not add_new_tags:
                    log.debug('removing user ')
                    del user_details.get(u'tags')[key]
                else:
                    #TODO: Add code to create a new tag for the application entry
                    log.error("Need to implement this bit")
        
        #Step 3: Build the data object that the API requires
        data = {
            u'cd':88,
            u'applicationName':application_name,
            u'accounts':[user_details]
        }
        success, message = self.send_api_call( data )
        
        #Step X: Check that the response from their server was OK
        if success:
            if message.get(u'cd') == 388:
                #If we get an OK message this means the user was successfully added/updated so return True to the caller
                return True
            else:
                log.debug(
                    """
                    Error adding an individual user to the Comufy's API.
                    
                    File:
                    support_comufy.py
                    
                    Function:
                    add_application_user
                    
                    Reason:
                    The data that was sent to the API was:
                    %s
                    
                    The API call returned the following details:
                    %s
                    """%( json.dumps(data), json.dumps(message) )
                )
                return False
    
    def add_application_users(self, application_name, users_details ):
        """
        
        @param users_details A list of dictionary objects that should contains the keys
        'account' and 'tags'
        
        @return A list of user's detail dictionaries that were sent successfully to 
        Comufy's API.  If no details were sent successfully, then this will be an
        empty list.
        
        @return A list of user's detail dictionaries that were NOT sent successfully
        to Comufy's API.  If no details were not sent then this will be an empty list.
        """
        
        #Step 1: First check that we currently have a valid access token.
        if not self.get_access_token():
            return [], users_details
        
        #Step 2: Validate the tags being used with those associated with the app
        #current_tags = self.get_application_tags()
        
        #Step 3: Create two new lists which will be used to store which user's details were sent successfully and which had errors on
        sent_details = []
        not_sent_details = []
        
        #Step 4: Start looping over the users_details variable until there are no entries left in it
        while len(users_details) > 0:
            
            #Step 5: Next we need to determine how many users are left and if there are more than 50 then batch them
            if len(users_details) > 50:                                             #MAGIC NUMBER: 50 is defined by Comufy's API as the maximum number of users that can be sent in a single registration/update request
                to_send = users_details[:50]
                users_details = users_details[50:]
            else:
                to_send = users_details
                users_details = []
            
            data = {
                u'cd':88,
                u'applicationName':application_name,
                u'accounts': to_send
            }
            
            success, message = self.send_api_call( data )
            
            if success:
                if message.get(u'cd') == 388:                                       #MAGIC NUMBER: 388 is the OK response from Comufy's API
                    sent_details.extend( to_send )
                else:
                    log.debug(
                        """
                        Error adding a batch of users to the Comufy's API.
                        
                        File:
                        support_comufy.py
                        
                        Function:
                        add_application_users
                        
                        Reason:
                        The data that was sent to the API was:
                        %s
                        
                        The API call returned the following details:
                        %s
                        """%( json.dumps(data), json.dumps(message) )
                    )
                    not_sent_details.extend( to_send )
            else:
                log.debug(
                    """
                    Could not add batch of users to Comufy's API
                    
                    File:
                    support_comufy.py
                    
                    Function:
                    add_application_users
                    
                    Reason:
                    Did not recieve a successful web request message from server i.e. no 'OK' from request
                    """
                )
                not_sent_details.extend( to_send )
        
        return sent_details, not_sent_details
    
    def get_application_users(self, application_name, filter=''):
        """
        """
        data = {
            u'cd':82,
            u'since':1314835200000,
            u'fetchMode':'STATS_ONLY',
            u'filter':filter,
            u'applicationName':application_name
        }
        success, message = self.send_api_call( data )
        if success:
            if message.get('cd') == 692:
                log.debug('Invalid filter/filter not found')
                return False, message
            return True, message
        
        return False, None
    
    def send_message(self, application_name, description, content, fb_ids,
                     privacy_mode="PRIVATE", notification=False):
        """Sends a message with the desicription or content to the
        facebook id or id's specified (singular or list).
    
        Optionally notify can be specified to send a facebook notification
        instead of a wall message - this requires fewer permissions but is
        not as public.
        :type privacy_mode: object
        """
        if privacy_mode not in ["PRIVATE", "PUBLIC"]:
            raise (Exception('PrivacyMode must be on of PRIVATE or PUBLIC'))
    
        if type(fb_ids) is not list:
            fb_ids=[fb_ids]
        data = {
            'cd': 83,
            'content':content,
            'description':description,
            'fbMessagePrivacyMode':privacy_mode,
            'applicationName': application_name,
            # This results in FACEBOOK_ID=123 OR FACEBOOK_ID=234 etc, no or's if only 1 element
            'filter':'FACEBOOK_ID="%s"'%(' OR FACEBOOK_ID='.join(fb_ids))
        }
        if notification==True:
            data["facebookTargetingMode"]="NOTIFICATION"
    
        log.debug( data )
    
        success, message = self.send_api_call( data )
        return success, message
    
    
    #TAG STUFF
    def register_facebook_application_tag(self, application_name, tags):
        """
        Takes a dictionary of tags ala [{"name":"dob", "type": "DATE"}]
        
        Types allowed are "STRING, DATE, GENDER, INT, FLOAT, default is STRING
        """
        allowed_types = ['STRING', 'DATE', 'GENDER', 'INT', 'FLOAT']
        for t in tags:
            if not t.has_key('name'):
                log.error('Name parameter is required for tag pair')
            if t.has_key('type'):
                if t['type'] not in allowed_types:
                    log.error('Incorrect type: %s, must be one of %s' % (t['type'], allowed_types))
        data = {
            'cd': '86',
            'tags': tags,
            'applicationName': application_name
            }
        
        success, message = self.send_api_call(data)
        log.debug(success, message)
        if success == 386:
            return True, message
        elif success == 607:
            return False, 'Unauthorised action'
        elif success == 603:
            return False, 'Application name not found'
        elif success == 618:
            return False, 'Application tag already registered'
        
    #TAG STUFF
    def unregister_facebook_application_tag(self, application_name, tag):
        """
        Takes a single tag name (string) ie how_much_bob_ate
        """
        data = {
            'cd': '85',
            'tag': tag,
            'applicationName': application_name
            }
        
        success, message = self.send_api_call(data)
        log.debug('%s: %s' % (success, message))
        return success, message

