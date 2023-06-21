#!/usr/bin/env python3

import json
import time
import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

LOG = logging.getLogger("__name__")


class Apic(object):

	def __init__(self, address, credentials=None):
		requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
		LOG.debug("Creating a new APIC handle on %s address" % address)

		# Attribute initialization
		self._address = address
		self._url = "https://%s/api" % address
		self._token = None
		self._top_system = None
		self._token_timeout = None
		self._credentials = credentials
		if credentials:
			self.get_apic_token(self.credentials)

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
	def token(self):
		"""Get token"""
		return self._token

	@token.setter
	def token(self, value):
		"""Set the token"""
		self._token = value

	@property
	def token_timeout(self):
		"""Get token_timeout"""
		return self._token_timeout

	@token_timeout.setter
	def token_timeout(self, value):
		"""Set the token_timeout"""
		self._token_timeout = value

	@property
	def url(self):
		"""Get url"""
		return self._url

	@url.setter
	def url(self, value):
		"""Set the url"""
		self._url = value

	def get_aaa_domains(self):
		"""
		This APIC call can be run before authentication. It will list the available Auth domains
		:return: A tuple;
		[0] - bool - will tell if connection was good,
		[1] if [0] si False will return the reason why connection failed. Else will return a set of domains.
		"""
		try:
			r = requests.get("%s/aaaListDomains.json" % self.url, verify=False, timeout=2)
		except requests.exceptions.Timeout:
			return False, "Timeout reaching the APIC"
		if not r.status_code == 200:
			return False, r.text
		r_json = r.json()
		domains = set()
		for record in r_json["imdata"]:
			domains.add(record["name"])
		return True, domains

	def get_apic_token(self, credentials):
		"""
		Gets and Sets APIC Cookie. Cookie will be maintained active across script usage on a clock base check
		:param credentials: a dictionary like {'username': '', 'password': '', 'domain': ''}
		:return: Bool
		"""
		if not self.credentials:
			self._credentials = credentials
		if credentials["domain"] == "":
			auth = {"aaaUser": {"attributes": {"name": "%s" % (
				credentials["username"]), "pwd": "%s" % (credentials["password"])}}}
		else:
			auth = {"aaaUser": {"attributes": {"name": "apic:%s\\\\%s" % (
				credentials["domain"], credentials["username"]), "pwd": "%s" % (credentials["password"])}}}
		r = requests.post("%s/aaaLogin.json" % self.url, json=auth, verify=False)
		if not r.status_code == 200:
			LOG.error("APIC %s authentication failed. Code: %s. Error %s" % (
				self.address, r.status_code, r.text))
			return False
		LOG.debug("APIC %s authentication succeeded " % self.address)
		r_json = r.json()
		self.token = {"APIC-cookie": "%s" % (r_json["imdata"][0]["aaaLogin"]["attributes"]["token"])}
		self.token_timeout = int(r_json["imdata"][0]["aaaLogin"]["attributes"]["refreshTimeoutSeconds"]) + int(
			time.time())


		return True

	def check_token_validity(self):
		"""
		This function will reset the token if timeout is less than 100 seconds from now
		If timeout is expired it will re-auth
		:return: Nothing
		"""
		LOG.debug(f"Current Token Timeout: {self.token_timeout}")
		if self.token_timeout - int(time.time()) > 100:
			return True
		elif 100 > self.token_timeout - int(time.time()) > 5:
			LOG.debug("Token Valid for %s seconds, refreshing" % (self.token_timeout - int(time.time())))
			r = requests.get("%s/aaaRefresh.json" % self.url, cookies=self.token, verify=False)
			if not 199 < r.status_code < 300:
				return False
			r_json = r.json()
			self.token = {"APIC-cookie": "%s" % (r_json["imdata"][0]["aaaLogin"]["attributes"]["token"])}
			self.token_timeout = int(r_json["imdata"][0]["aaaLogin"]["attributes"]["refreshTimeoutSeconds"]) + int(
				time.time())
		else:
			LOG.debug("Token invalid, re-authentication required")
			self.get_apic_token(self.credentials)

	def api_get(self, url):
		"""
		:param url: A well formatted URL
		:return: A requests answer if status_code == 200
		"""
		self.check_token_validity()
		if self.url not in url:
			url = "%s/%s" % (self.url, url)
		LOG.debug("Getting: %s" % url)
		result = requests.get(url, cookies=self.token, verify=False)
		if not 199 < result.status_code < 300:
			LOG.warning("API GET failed. URL: %s ; Code %s and Error: %s" % (
				url, result.status_code, result.text))
			return False
		else:
			return result

	def api_delete(self, url):
		"""
		:param url: A well formatted URL
		:return: A requests answer if status_code == 200
		"""
		self.check_token_validity()
		if self.url not in url:
			url = "%s/%s" % (self.url, url)
		LOG.debug("Deleting: %s" % url)
		result = requests.delete(url, cookies=self.token, verify=False)
		if not 199 < result.status_code < 300:
			LOG.warning("API DELETE failed. URL: %s ; Code %s and Error: %s" % (
				url, result.status_code, result.text))
			return False
		else:
			return result

	def api_post(self, url, json_body=None, xml_body=None, debug=False):
		"""
		Json has preference over XML if both are set.
		:param url: A well formatted URL
		:param json_body: payload to post
		:param xml_body: payload to post
		:param debug: payload to post
		:return: A requests answer if status_code == 200
		"""
		self.check_token_validity()
		if self.url not in url:
			url = "%s/%s" % (self.url, url)
		if json_body:
			if debug:
				LOG.debug("POST Body: %s " % json_body)
			headers = {'content-type': 'application/json'}
			result = requests.post(url, cookies=self.token, json=json_body, verify=False, headers=headers)
		else:
			if debug:
				LOG.debug("POST Body: %s " % xml_body)
			headers = {'content-type': 'application/xml'}
			result = requests.post(url, cookies=self.token, data=xml_body, verify=False, headers=headers)

		if not 199 < result.status_code < 300:
			LOG.debug("API POST FAILED. URL: %s ; Code %s and Error: %s" % (
				url, result.status_code, result.text))
			return False
		else:
			LOG.debug("API POST PASSED. URL: %s ; Code %s and Message: %s" % (
				url, result.status_code, result.text))
			return result

	def get_aci_object(self, dn, query_target=None, target_subtree_class=None, query_target_filter=None,
						rsp_subtree=None, rsp_prop_include=None, rsp_subtree_filter=None):
		"""
		This function prepares the URL formatting for querying the MIT
		:param dn: full MIT to reach the object
		:param query_target: Refer to Cisco APIC REST API Configuration Guide
		:param target_subtree_class: Refer to Cisco APIC REST API Configuration Guide
		:param query_target_filter: Refer to Cisco APIC REST API Configuration Guide
		:param rsp_subtree: Specifies child object level included in the response
		:param rsp_prop_include: This statement specifies what type of properties should be included
				in the response when the rsp-subtree option is used with an argument other than
		:param rsp_subtree_filter: Refer to Cisco APIC REST API Configuration Guide
		:return: json
		"""

		args = locals()
		if rsp_subtree or rsp_prop_include or rsp_subtree_filter or query_target or target_subtree_class or query_target_filter:
			url_filter = "?"
		else:
			url_filter = ""
		for arg in args:
			if arg in ["self", "dn"]:
				continue
			if args[arg]:
				url_filter += "%s=%s&" % (arg.replace("_", "-"), args[arg])
		url = "%s/%s%s" % (self.url, dn, url_filter)
		data = self.api_get(url)
		return data.json()

	def take_snapshot(self, description, timeout=15):
		"""
		:param description: description to set in the snapshot
		:param timeout: how much time we should wait before checking if it was completed
		:return: Bool
		"""
		body = {"configExportP": {
			"attributes": {"snapshot": "true", "status": "created,modified", "adminSt": "triggered",
							"descr": description}}}

		if self.api_post("mo/uni/fabric/configexp-devnet-1369.json", json_body=body):
			time.sleep(timeout)
			current_snapshots = self.get_aci_object(
				"class/configSnapshot.json?query-target-filter=eq(configSnapshot.descr,\"%s\")" % description)
			if not int(current_snapshots["totalCount"]) == 1:
				LOG.warning("Unable to find any existing snapshot")
				return False
			else:
				LOG.info("Snapshot completed")
				return True
		else:
			LOG.warning("Snapshot failed")
			return False