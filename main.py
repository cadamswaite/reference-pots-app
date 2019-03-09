import json
import uuid
import time
import requests
from pprint import pprint
import config
import oauth2
from utils import error

class PotClient:
    ''' An example single-account client of the Monzo Pot API. 
        For the underlying OAuth2 implementation, see oauth2.OAuth2Client.
    '''

    def __init__(self):
        self._api_client = oauth2.OAuth2Client()
        self._api_client_ready = False
        self._account_id = None
        self.transactions = []


    def do_auth(self):
        ''' Perform OAuth2 flow mostly on command-line and retrieve information of the
            authorised user's current account information, rather than from joint account, 
            if present.
        '''

        print("Starting OAuth2 flow...")
        token = input("If you already have a token, enter it now, otherwise press enter to continue")
        if token == "":
            self._api_client.start_auth()
        else:
            self._api_client.existing_access_token(token)

        print("OAuth2 flow completed, testing API call...")
        response = self._api_client.test_api_call()
        if "authenticated" in response:
            print("API call test successful!")
        else:
            error("OAuth2 flow seems to have failed.")
        self._api_client_ready = True

        print("Retrieving account information...")
        success, response = self._api_client.api_get("accounts", {})
        if not success or "accounts" not in response or len(response["accounts"]) < 1:
            error("Could not retrieve accounts information")
        
        # We will be operating on personal account only.
        for account in response["accounts"]:
            if "type" in account and account["type"] == "uk_retail":
                self._account_id = account["id"]
                print("Retrieved account information.")
                break

        if self._account_id is None:
            error("Could not find a personal account")
            return
        
    def list_pots(self):
        success, pots = self._api_client.api_get("pots", {})
        if not success or "pots" not in pots or len(pots["pots"]) < 1:
            error("Could not retrieve pots information")
            return
        self.pot_dict={}
        print("Your current pots are")
        for pot in pots["pots"]:
            print("\t",pot["name"],pot["balance"])
            self.pot_dict[pot["name"]] = pot["id"]
        #pprint(self.pot_dict)

    def deposit_pot(self,potname,amount):
        if potname not in self.pot_dict:
            print("Couldn't find a pot by the name %s :\\"%potname)
            return
        if int(amount)<0:
            print("For ammounts less than 0, use withdraw_pot instead.")
                  
        dedupe_id = uuid.uuid4().hex
        for x in range(1):
            path = "pots/"+self.pot_dict[potname]+"/deposit"
            payload = {"source_account_id":self._account_id,
                        "amount":str(int(amount)),
                        "dedupe_id":dedupe_id}          
            success, response = self._api_client.api_put(path, payload)
            if success:
                print("Successfully deposited %sp into pot %s"%(amount,potname))
                return
            print("Attempt %i failed to deposit, try again in 10s."%x+1)
            time.sleep(10)


    def withdraw_pot(self,potname,amount):
        if potname not in self.pot_dict:
            print("Couldn't find a pot by the name %s :\\"%potname)
            return
        if int(amount)<0:
            print("For ammounts less than 0, use deposit_pot instead.")
                  
        dedupe_id = uuid.uuid4().hex
        for x in range(1):
            path = "pots/"+self.pot_dict[potname]+"/withdraw"
            payload = {"destination_account_id":self._account_id,
                        "amount":str(int(amount)),
                        "dedupe_id":dedupe_id}          
            success, response = self._api_client.api_put(path, payload)
            if success:
                print("Successfully withdrew %sp from pot %s"%(amount,potname))
                return
            print("Attempt %i failed to withdraw due to %s."%(x+1,response))
            
            time.sleep(10) 
            
if __name__ == "__main__":
    client = PotClient()
    client.do_auth()
    client.list_pots()
    client.deposit_pot("TestPot","1")
    client.withdraw_pot("TestPot","1")
