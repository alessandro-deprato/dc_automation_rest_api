#!/usr/bin/env python3

import json
import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

LOG = logging.getLogger("__name__")


class Nexus_api(object):

	def __init__(self, address:str, credentials:dict):
		"""Creates an handler to make API calls towards an NX-OS switch

		Args:
			address (str): IP Address or FQDN
			credentials (dict): username and password in a dictionary {"username":"","password":""}
		"""
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		LOG.debug("Creating a new NXAPI handle on %s address" % address)

		# Attribute initialization
		self._address = address
		self._url = f"https://{address}/ins"
		self._credentials = credentials
		

	@property
	def address(self):
		"""Get credentials"""
		return self._address

	@address.setter
	def address(self, value):
		"""Set the credentials"""
		self._address = value

	@property
	def credentials(self):
		"""Get credentials"""
		return self._credentials

	@credentials.setter
	def credentials(self, value):
		"""Set the credentials"""
		self._credentials = value

	@property
	def url(self):
		"""Get url"""
		return self._url

	@url.setter
	def url(self, value):
		"""Set the url"""
		self._url = value

	def show_command(self, command:str) -> dict:
		""" This function takes a series of commands and pushes them to the device

		Args:
			commands (str): show command
		Returns:
			bool: API Call Result
		"""
		myheaders={'content-type':'application/json'}

		payload={
		  "ins_api": {
		    "version": "1.0",
		    "type": "cli_show",
		    "chunk": "0",
		    "sid": "sid",
		    "input": command,
		    "output_format": "json",
		  }
		}
		response = requests.post(self.url,data=json.dumps(payload), headers=myheaders,auth=(
			self.credentials["username"],self.credentials["password"]),verify=False).json()
		if not response["ins_api"]["outputs"]["output"]["code"] == "200":
			return False
		else:
			return response["ins_api"]["outputs"]["output"]["body"]

	def push_config(self, commands:str, rollback:str ="rollback-on-error") -> bool:
		""" This function takes a series of commands and pushes them to the device

		Args:
			commands (str): commands separated by " ;" !! Mind the space before the semicolon
			
			rollback (str, optional): Valid only for configuration CLIs, not for show commands. Specifies the configuration rollback options. Specify one of the following options.. Defaults to "rollback-on-error", other options: stop-on-error, continue-on-error

		Returns:
			bool: True if all the commands have been executed, False if any of them failed. Result is decoupled from the rollback option.
		"""
		myheaders={'content-type':'application/json'}

		payload={
		  "ins_api": {
		    "version": "1.0",
		    "type": "cli_conf",
		    "chunk": "0",
		    "sid": "sid",
		    "input": commands,
		    "output_format": "json",
		    "rollback": rollback
		  }
		}
		response = requests.post(self.url,data=json.dumps(payload), headers=myheaders,auth=(
			self.credentials["username"],self.credentials["password"]),verify=False).json()
		for command_response in response["ins_api"]["outputs"]["output"]:
			if not command_response["msg"] == "Success":
				return False
		return True
